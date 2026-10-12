"""
Chat agent: connects the LLM (Groq) with the MCP tools.

Flow for one user message:
    1. Build the list of tools the logged-in role may use.
    2. Ask the LLM. If it asks for a tool -> run it with execute_mcp()
       (identity comes from the SESSION, never from the LLM) and give the
       result back to the LLM.
    3. Repeat (max MAX_STEPS) until the LLM gives a normal text answer.
"""
import json
import re
from datetime import date, datetime, time
from typing import Any

from llm.llm_service import get_llm_client, get_model_name
from llm.prompts import HEALTHCARE_SYSTEM_PROMPT
from mcp_app.register_tools import register_all_tools
from mcp_app.router import execute_mcp, get_available_mcps
from src.logger import get_logger

logger = get_logger(__name__)

MAX_STEPS = 5
MAX_HISTORY = 10
MAX_TOOL_RESULT_CHARS = 6000

_INT = {"type": "integer"}
_STR = {"type": "string"}


def _obj(props: dict | None = None, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": props or {},
        "required": required or [],
    }


# Arguments the LLM is allowed to give. "patient_id" is NOT listed for the
# patient tools on purpose: the server injects it from the login session.
TOOL_PARAMS: dict[str, dict] = {
    "get_patient_information": _obj(),
    "get_doctors": _obj(
        {"department_id": {**_INT, "description": "Optional department id"}}
    ),
    "get_available_appointment_slots": _obj(
        {
            "doctor_id": _INT,
            "appointment_date": {**_STR, "description": "YYYY-MM-DD"},
        },
        ["doctor_id", "appointment_date"],
    ),
    "create_appointment": _obj(
        {
            "doctor_id": _INT,
            "department_id": {**_INT, "description": "From get_doctors result"},
            "appointment_date": {**_STR, "description": "YYYY-MM-DD"},
            "start_time": {**_STR, "description": "HH:MM (24h)"},
            "end_time": {**_STR, "description": "HH:MM (24h)"},
            "reason": _STR,
        },
        [
            "doctor_id",
            "department_id",
            "appointment_date",
            "start_time",
            "end_time",
        ],
    ),
    "get_my_appointments": _obj(),
    "cancel_my_appointment": _obj({"appointment_id": _INT}, ["appointment_id"]),
    "get_my_medical_history": _obj(),
    "get_my_medical_history_record": _obj({"history_id": _INT}, ["history_id"]),
    "get_my_medical_reports": _obj(),
    "get_my_medical_report": _obj({"image_id": _INT}, ["image_id"]),
    # admin
    "get_patient_for_admin": _obj({"patient_id": _INT}, ["patient_id"]),
    "search_patients": _obj(
        {"search": {**_STR, "description": "Name, phone or email"}}
    ),
    "get_doctor_for_admin": _obj({"doctor_id": _INT}, ["doctor_id"]),
    "search_doctors": _obj({"department_id": _INT}),
    "get_patient_appointments_for_admin": _obj(
        {"patient_id": _INT}, ["patient_id"]
    ),
    # system
    "check_system_database_health": _obj(),
    "get_system_mcp_summary": _obj(),
    "get_system_mcps_by_role": _obj({"role": _STR}, ["role"]),
}

# Tools whose first argument is the logged-in patient's id.
PATIENT_ID_TOOLS = {
    "get_patient_information",
    "create_appointment",
    "get_my_appointments",
    "cancel_my_appointment",
    "get_my_medical_history",
    "get_my_medical_history_record",
    "get_my_medical_reports",
    "get_my_medical_report",
}


def build_tools(role: str) -> list[dict]:
    """OpenAI/Groq style tool list for the role."""
    # Make sure the registry is filled even if the app forgot to do it.
    register_all_tools()

    tools = []
    for mcp in get_available_mcps(role):
        params = TOOL_PARAMS.get(mcp["name"])
        if params is None:
            continue
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": mcp["name"],
                    "description": mcp["description"],
                    "parameters": params,
                },
            }
        )
    return tools


def _parse_time(value: Any) -> time:
    text = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Invalid time: {value}")


def _coerce_types(name: str, args: dict) -> dict:
    """Models often send numbers as text ("2"). Convert to the schema type."""
    props = TOOL_PARAMS.get(name, {}).get("properties", {})
    for key, value in list(args.items()):
        wanted = props.get(key, {}).get("type")
        if wanted == "integer" and not isinstance(value, bool):
            if isinstance(value, float) and value.is_integer():
                args[key] = int(value)
            elif isinstance(value, str) and value.strip().lstrip("-").isdigit():
                args[key] = int(value.strip())
        elif wanted == "string" and isinstance(value, (int, float)):
            args[key] = str(value)
    return args


def _prepare_arguments(
    name: str, raw_args: dict, user: dict
) -> dict[str, Any]:
    allowed = set(TOOL_PARAMS.get(name, {}).get("properties", {}))
    args = _coerce_types(
        name, {k: v for k, v in raw_args.items() if k in allowed}
    )

    # Trusted identity from session - overrides anything the LLM sent.
    if name in PATIENT_ID_TOOLS:
        args["patient_id"] = user["id"]

    if "appointment_date" in args:
        args["appointment_date"] = date.fromisoformat(
            str(args["appointment_date"]).strip()
        )
    for key in ("start_time", "end_time"):
        if key in args:
            args[key] = _parse_time(args[key])

    return args


def _run_tool(name: str, raw_args: dict, user: dict) -> str:
    try:
        args = _prepare_arguments(name, raw_args, user)
    except (ValueError, TypeError) as exc:
        result = {"success": False, "error": f"Bad arguments: {exc}"}
    else:
        result = execute_mcp(name, user, args)

    text = json.dumps(result, default=str, ensure_ascii=False)
    if len(text) > MAX_TOOL_RESULT_CHARS:
        text = text[:MAX_TOOL_RESULT_CHARS] + "...[truncated]"
    return text


def _is_tool_use_failed(exc: Exception) -> bool:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error", body)
        return isinstance(err, dict) and err.get("code") == "tool_use_failed"
    return "tool_use_failed" in str(exc)


def _recover_failed_tool_call(exc: Exception) -> tuple[str, dict] | None:
    """
    Groq sometimes rejects a model's tool call as malformed
    (error code `tool_use_failed`) but includes what the model wrote in
    `failed_generation`. Try to read the tool name and arguments from it.
    Returns (name, args) or None.
    """
    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return None
    err = body.get("error", body)
    if not isinstance(err, dict) or err.get("code") != "tool_use_failed":
        return None

    text = err.get("failed_generation") or ""
    name, args = None, None

    # Format 1: {"name": "get_doctors", "arguments": {...}}
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            name = data.get("name")
            args = data.get("arguments") or data.get("parameters") or {}
    except (json.JSONDecodeError, TypeError):
        pass

    # Format 2: <function=get_doctors>{...}</function>
    if not name:
        match = re.search(r"<function=([\w]+)[^>]*>\s*(\{.*?\})?", text, re.S)
        if match:
            name = match.group(1)
            try:
                args = json.loads(match.group(2) or "{}")
            except json.JSONDecodeError:
                args = {}

    if name in TOOL_PARAMS and isinstance(args, dict):
        return name, args
    return None


def _clean_history(history: list[dict] | None) -> list[dict]:
    clean = []
    for item in (history or [])[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            if content.strip():
                clean.append({"role": role, "content": content[:4000]})
    return clean


def chat_with_tools(
    message: str,
    user: dict,
    history: list[dict] | None = None,
) -> str:
    """Return the assistant's reply for `message`."""
    client = get_llm_client()
    system_prompt = HEALTHCARE_SYSTEM_PROMPT.format(
        today=date.today().isoformat(), role=user["role"]
    )
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages += _clean_history(history)
    messages.append({"role": "user", "content": message})

    tools = build_tools(user["role"])

    for step in range(MAX_STEPS):
        kwargs: dict[str, Any] = dict(
            model=get_model_name(),
            messages=messages,
            temperature=0.2,
            max_tokens=800,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:
            recovered = _recover_failed_tool_call(exc)
            if recovered is None:
                if _is_tool_use_failed(exc):
                    # Unreadable malformed tool call: just ask the model again.
                    logger.warning("Unrecoverable tool_use_failed; retrying.")
                    continue
                raise

            # The model's tool call was rejected as malformed by Groq.
            # We can still read what it wanted, so run it ourselves.
            name, raw_args = recovered
            logger.warning("Recovered malformed tool call: %s", name)
            call_id = f"recovered_{step}"
            messages.append(
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(raw_args),
                            },
                        }
                    ],
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": _run_tool(name, raw_args, user),
                }
            )
            continue

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            answer = (msg.content or "").strip()
            return answer or (
                "Sorry, I couldn't generate a response. Please try again."
            )

        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments or "{}",
                        },
                    }
                    for call in tool_calls
                ],
            }
        )

        for call in tool_calls:
            name = call.function.name
            try:
                raw_args = json.loads(call.function.arguments or "{}")
                if not isinstance(raw_args, dict):
                    raw_args = {}
            except json.JSONDecodeError:
                raw_args = {}

            logger.info("LLM requested tool %s (user=%s)", name, user["id"])
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": _run_tool(name, raw_args, user),
                }
            )

    return "Sorry, I couldn't finish that request. Please try again."

