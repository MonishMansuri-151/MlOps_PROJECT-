# Sanjivni Chatbot (chatbot_version_2)

Healthcare clinic chatbot: FastAPI + MySQL + Groq LLM + MCP-style tool layer.
Patients chat to find doctors, see free slots, book/cancel appointments and view their records.
Poora design samajhne ke liye **`docs/ARCHITECTURE.md`** padhein.

## Quick start

```bash
cd chatbot_version_2
python -m venv .venv && .venv\Scripts\activate      # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env                              # phir .env mein asli values bharein
python main.py                                      # http://127.0.0.1:8000   (API docs: /docs)
```

Terminal mein `Registered 18 MCP tools.` dikhna chahiye. `GET /health/database` -> `"connected"`.

## Tests

```bash
python -m pytest tests -q        # 119 tests, MySQL/Groq ki zaroorat nahi
python test_mcp_client.py        # stdio MCP server direct calls ko mana karta hai (expected)
```

UI se manual testing: `docs/MANUAL_TEST_SHEET.md`.

## Website ke saath jodna

Root `main.py` ka example: `docs/examples/root_main.py`
(root folder `sys.path` mein sabse aage, `chatbot_version_2` sabse peeche, aur `register_all_tools()` lifespan mein).

## API

| Method | URL | Kaam |
|---|---|---|
| POST | `/auth/login` | patient login `{identifier, password}` |
| POST | `/auth/admin-login` | admin login `{email, password}` |
| POST | `/auth/register` | patient register |
| GET | `/auth/me` | login status |
| POST | `/auth/logout` | logout |
| POST | `/api/chat/message` | `{"message": "..."}` -> `{"success": true, "reply": "..."}` |
| GET | `/health`, `/health/database` | health |

## Folder ek nazar mein

```
main.py  api/  auth/  llm/  mcp_app/  services/  database/  src/  tests/  docs/  uploads/
```

`api` (HTTP) -> `llm` (AI loop) -> `mcp_app` (tools + permissions) -> `services` (business logic) -> `database`.

## Zaroori suraksha baatein

- `.env` kabhi share/commit na karein. Agar kisi ko bheja ho to DB password, Groq key aur `SESSION_SECRET_KEY` badal dein.
- Production mein HTTPS par chalayein aur `SESSION_HTTPS_ONLY=true` rakhein.
- Tool calling ke liye `GROQ_MODEL=openai/gpt-oss-120b` behtar chalta hai.
