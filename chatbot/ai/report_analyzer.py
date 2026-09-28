import sys

from chatbot.ai.llm_service import llm_service
from src.logger import get_logger
from src.exception import CustomException

logger = get_logger(__name__)


REPORT_PROMPT = """
You are a medical report explanation assistant for Sanjivni Clinic.

Your task is to explain the provided medical report in simple language.

Rules:
- Do not provide a definitive diagnosis.
- Do not prescribe medicines.
- Do not provide medicine dosage or treatment duration.
- Do not invent values or findings.
- Clearly distinguish reported findings from general explanation.
- If something is unclear or missing, say so.
- Mention when consultation with a qualified doctor may be appropriate.
- If the report indicates an emergency or potentially serious finding,
  advise the user to seek urgent medical attention.
- Keep the explanation practical and easy to understand.
- Respond in the same language/style as the user's question.
"""


def analyze_medical_report(
    report_text: str,
    user_question: str = ""
) -> str:
    try:
        if not report_text.strip():
            return (
                "I could not extract readable text from this PDF. "
                "It may be scanned/image-based or contain unsupported formatting."
            )

        prompt = f"""
{REPORT_PROMPT}

User question:
{user_question}

Medical report:
{report_text}
"""

        response = llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[
                {
                    "role": "system",
                    "content": REPORT_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=1000
        )

        result = (
            response.choices[0].message.content or ""
        ).strip()

        logger.info(
            "Medical report analysis completed successfully."
        )

        return result

    except Exception as e:
        logger.error(
            f"Medical report analysis failed: {e}"
        )

        raise CustomException(e, sys)