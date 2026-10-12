# Sanjivni Chatbot - System Design aur Architecture

Ye document batata hai ki system **kya hai, kaise bana hai, har file/folder ka kaam kya hai,
ek message ka poora safar kaisa hota hai, security kaise hai, aur naya kaam kaise jodte hain.**

---

## 1. System kya hai?

Sanjivni ek **healthcare clinic chatbot** hai. Patient website ke chat widget mein likhta hai
(Hindi / Hinglish / English), aur chatbot:

- general health ki jaankari deta hai (diagnosis nahi),
- **MySQL se asli data** laakar doctors dikhata hai, slots batata hai,
- appointment **book / cancel** karta hai,
- patient ki **medical history aur reports** dikhata hai,
- admin ko patients/doctors/appointments, aur super-admin ko system health dikhata hai.

**Main design idea:** LLM (Groq) ko database ka direct access *nahi* diya. LLM sirf ek chhoti
"tools ki list" dekhta hai. Jab use data chahiye, wo tool maangta hai, **hamara server** check karta
hai (kaun user hai? uska role kya? ijazat hai?) aur tab hi tool chalata hai.
Isse LLM galti kare ya koi use bahkaye, tab bhi data surakshit rehta hai.

| Layer | Technology |
|---|---|
| Web framework | FastAPI (Starlette sessions) |
| LLM | Groq API (`openai/gpt-oss-*` / `llama` models), function/tool calling |
| Database | MySQL via PyMySQL (raw parameterised SQL) |
| Passwords | bcrypt |
| Tool protocol | MCP-style registry (in-process) + optional stdio MCP server (locked) |
| Tests | pytest (119 tests, fake DB + fake LLM) |

---

## 2. Bade level ka architecture

```
                         ┌──────────────────────────────────────────────┐
                         │                  BROWSER                      │
                         │  Website pages + chat widget (static/*.js)    │
                         └───────────────┬──────────────────────────────┘
                                         │ HTTP (cookie session)
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI app  (root main.py  ->  chatbot_version_2)      │
│                                                                                  │
│  SessionMiddleware (signed cookie)                                               │
│                                                                                  │
│  ┌────────────── api/ (HTTP layer) ──────────────┐                               │
│  │  api/auth.py  /auth/login /register /me ...    │──► auth/  (bcrypt, RBAC,      │
│  │  api/chat.py  /api/chat/message                │      rate limit, session user)│
│  └───────────────────────┬────────────────────────┘                               │
│                          │ chat_with_tools(message, USER FROM SESSION)             │
│                          ▼                                                         │
│  ┌──────────── llm/ (AI layer) ──────────────────┐        ┌──────── Groq API ───┐ │
│  │  agent.py   tool-calling loop                  │◄──────►│  LLM (tool calling) │ │
│  │  llm_service.py  Groq client                   │        └─────────────────────┘ │
│  │  prompts.py   system prompt                    │                                │
│  └───────────────────────┬────────────────────────┘                               │
│                          │ execute_mcp(tool, USER, args)                           │
│                          ▼                                                         │
│  ┌──────────── mcp_app/ (tool layer) ────────────┐                               │
│  │  registry.py    tool dictionary                │                               │
│  │  router.py      execute_mcp(): ek hi darwaza   │                               │
│  │  permissions.py role + RBAC check              │                               │
│  │  user/  admin/  system/   tool functions       │                               │
│  └───────────────────────┬────────────────────────┘                               │
│                          ▼                                                         │
│  ┌──────────── services/ (business logic) ───────┐                               │
│  │  appointment / doctor / patient / report       │                               │
│  └───────────────────────┬────────────────────────┘                               │
│                          ▼                                                         │
│  ┌──────────── database/ ─────────────────────────┐                               │
│  │  connection.py  get_db() transaction manager   │                               │
│  └───────────────────────┬────────────────────────┘                               │
└──────────────────────────┼─────────────────────────────────────────────────────────┘
                           ▼
                        MySQL  (patients, doctors, appointments, ...)
```

**Dependency rule (upar se neeche hi call jaati hai, kabhi ulta nahi):**
`api -> llm -> mcp_app -> services -> database`. `auth/` aur `src/` har layer use kar sakti hai.
Isse code samajhna, test karna aur badalna aasaan rehta hai.

---

## 3. Ek message ka poora safar (sequence)

Example: patient likhta hai **"Dr Neha Verma ke kal ke slots dikhao"**.

```
Widget            api/chat.py            llm/agent.py         Groq        mcp_app/router      services        MySQL
  │  POST message     │                       │                 │               │                │             │
  ├──────────────────►│ 1 session se user?    │                 │               │                │             │
  │                   │   (id=10, role=user)  │                 │               │                │             │
  │                   │ 2 rate limit (20/min) │                 │               │                │             │
  │                   │ 3 memory (10 msgs)    │                 │               │                │             │
  │                   ├──────────────────────►│ 4 system prompt │               │                │             │
  │                   │                       │   + history     │               │                │             │
  │                   │                       │   + user ke 10  │               │                │             │
  │                   │                       │   tools         │               │                │             │
  │                   │                       ├────────────────►│               │                │             │
  │                   │                       │◄────────────────┤ tool_call:    │                │             │
  │                   │                       │ get_available_  │ (doctor_id:"2",│                │             │
  │                   │                       │ appointment_slots date "...")  │                │             │
  │                   │                       │ 5 args saaf:    │               │                │             │
  │                   │                       │  - unknown param hata            │                │             │
  │                   │                       │  - "2" -> 2                     │                │             │
  │                   │                       │  - date text -> date            │                │             │
  │                   │                       │  - patient_id = SESSION id      │                │             │
  │                   │                       ├────────────────────────────────►│ 6 registered?  │             │
  │                   │                       │                 │               │ 7 role + RBAC  │             │
  │                   │                       │                 │               │ 8 tool.py check├────────────►│
  │                   │                       │                 │               │                │ SQL (%s)    │
  │                   │                       │◄────────────────────────────────┤ result JSON    │◄────────────┤
  │                   │                       ├────────────────►│ result dekh kar jawab likho      │             │
  │                   │                       │◄────────────────┤ "10:00, 10:30 free hain"          │             │
  │                   │◄──────────────────────┤ 9 reply         │               │                │             │
  │◄──────────────────┤ {"success":true,"reply":"..."}          │               │                │             │
  │  10 widget textContent se dikhata hai (XSS safe)
```

Loop **maximum 5 baar** chalta hai (LLM -> tool -> LLM -> tool ...). Phir bhi khatam na ho to
"Sorry, I couldn't finish that request" milta hai - infinite loop nahi.

---

## 4. File aur Folder architecture

```
chatbot_version_2/
│
├── main.py                  FastAPI app: session, routers, /health, tool registration (lifespan)
├── requirements.txt         Python packages
├── .env.example             Config ka template  (asli .env ko kabhi share/commit mat karo)
├── .gitignore               .env, logs/, uploads/*, __pycache__ ignore
├── test_mcp_client.py       Check: stdio MCP server direct calls ko mana karta hai (by design)
│
├── api/                     ── HTTP LAYER: sirf request lena aur response dena ──
│   ├── auth.py              /auth/login  /admin-login  /me  /logout  /register
│   └── chat.py              /api/chat/me  /api/chat/message  (+ chat memory, rate limit)
│
├── auth/                    ── PEHCHAAN aur IJAZAT ──
│   ├── authentication.py    Password verify (bcrypt), patient/admin login check
│   ├── authorization.py     Session se user nikalna, ownership check helpers
│   ├── rbac.py              Role -> permissions ki table  (user / admin / super_admin)
│   ├── permissions.py       Permission ke naam (Enum)
│   └── rate_limit.py        Sliding-window limiter (login + chat)
│
├── llm/                     ── AI LAYER ──
│   ├── agent.py             LLM <-> tools ka loop, argument safai, malformed-call recovery
│   ├── llm_service.py       Groq client + model naam
│   └── prompts.py           System prompt (rules, format, dates)
│
├── mcp_app/                 ── TOOL LAYER (MCP) ──
│   ├── server.py            FastMCP server object (stdio ke liye)
│   ├── run_server.py        stdio MCP server chalane ka entry point
│   ├── registry.py          MCP_REGISTRY: tool ka naam -> handler/role/permission
│   ├── register_tools.py    TOOLS list (18 tools) + register_all_tools() (idempotent)
│   ├── permissions.py       can_execute_mcp(): role + permission + RBAC
│   ├── router.py            execute_mcp(): tool chalane ka EKLAUTA safe tareeka
│   ├── user/                Patient ke tools
│   │   ├── mcp_user_01/     profile            -> get_patient_information
│   │   ├── mcp_user_02/     doctors            -> get_doctors
│   │   ├── mcp_user_03/     appointments       -> slots, create, list, cancel
│   │   ├── mcp_user_04/     medical history    -> list, record
│   │   └── mcp_user_05/     medical reports    -> list, detail
│   ├── admin/               Admin ke tools
│   │   ├── mcp_admin_01/    patients           -> get_patient_for_admin, search_patients
│   │   ├── mcp_admin_02/    doctors            -> get_doctor_for_admin, search_doctors
│   │   └── mcp_admin_03/    appointments       -> get_patient_appointments_for_admin
│   └── system/              Super-admin ke tools
│       ├── mcp_system_01/   db health          -> check_system_database_health
│       └── mcp_system_02/   tool registry info -> get_system_mcp_summary, get_system_mcps_by_role
│
├── services/                ── BUSINESS LOGIC + SQL ──
│   ├── appointment_service.py  slots, booking rules, cancel rules, TIME fix (_to_time)
│   ├── doctor_service.py       doctors by id / active / department
│   ├── patient_service.py      patient profile
│   └── report_service.py       medical history, report metadata, safe file path
│
├── database/
│   ├── connection.py        get_connection(), get_db() (commit/rollback/close), timeouts
│   ├── queries.py           check_database_connection() (health)
│   └── models.py            Table ke naam ke constants (schema MySQL mein pehle se hai)
│
├── src/
│   └── logger.py            Logging: console + logs/app.log (rotating)
│
├── uploads/                 Medical files (sirf yahin se padhi jaati hain)
├── logs/                    app.log (auto-banta hai)
│
├── tests/                   119 automated tests (pytest)
└── docs/
    ├── ARCHITECTURE.md      Ye file
    ├── MANUAL_TEST_SHEET.md UI se manual testing ki list
    └── examples/root_main.py  Website ke root main.py ka example (chatbot kaise jodte hain)
```

> **Folder ke naam (`mcp_user_01` jaise) jaan-boojhkar nahi badle** - taaki aapke existing
> imports/links na tootein. Upar ka table batata hai ki kaun sa folder kya hai.

### Har layer ka kaam aur kya NAHI karna chahiye

| Layer | Karta hai | Kabhi nahi karta |
|---|---|---|
| `api/` | request validate, session padhna, HTTP error codes | SQL, business rules |
| `auth/` | login check, role/permission, rate limit | HTTP routes banana |
| `llm/` | Groq se baat, tool loop, argument safai | seedha SQL |
| `mcp_app/` | tool registry, permission, input check | LLM se baat, SQL (admin_01 ko chhodkar - neeche dekhein) |
| `services/` | business rules + SQL + transactions | HTTP, LLM |
| `database/` | connection + transaction | business rules |

> Note: `mcp_admin_01/tool.py` mein SQL seedha likha hai (service layer ke bina). Ye chalta hai
> par ideal nahi - roadmap mein hai (section 14).

---

## 5. Authentication, Sessions aur Roles

### Login
1. `POST /auth/login` (patient: phone ya email + password) ya `/auth/admin-login`.
2. `auth/authentication.py` DB se row laata hai aur **bcrypt** se password check karta hai.
   Agar user hi nahi mila, tab bhi ek dummy bcrypt chalta hai (timing se pata na chale ki account hai ya nahi).
3. Sahi hone par session mein sirf `{id, name, role}` store hota hai (signed cookie, `SessionMiddleware`).
   Purana session pehle `clear()` hota hai (**session fixation** se bachav).
4. **Patient ka role hamesha `"user"`** hota hai - `patients.role` column par bharosa nahi kiya jaata.
5. Cookie: `SameSite=Lax`, `HttpOnly` (Starlette default), expiry 8 ghante, `Secure` jab `SESSION_HTTPS_ONLY=true`.
6. **8 galat attempts / 10 minute** ke baad `429 Too many failed attempts` (client IP + account ke hisaab se).

### Roles aur tools (RBAC)

| Role | Kaun | Kitne tools | Kya kar sakta hai |
|---|---|---|---|
| `user` | Patient | 10 | Apna profile, doctors, slots, book/cancel, apni history, apni reports |
| `admin` | Staff | 5 | Patients search/detail, doctors search/detail, kisi patient ki appointments |
| `super_admin` | Owner | 3 | DB health, tool registry summary |

Roles **alag-alag hain, upar-neeche nahi**: admin patient-tools nahi chala sakta, super_admin admin-tools nahi.

Permission check **teen jagah ek saath** hota hai (`mcp_app/permissions.py`):
1. tool us role ka hai?
2. permission tool ki registration se match karti hai?
3. `auth/rbac.py` ki table mein role ko ye permission **sach mein** di gayi hai?

### Tools ki poori list

| Tool | Role | Permission | Service function |
|---|---|---|---|
| get_patient_information | user | patient.read | patient_service.get_patient_by_id |
| get_doctors | user | doctor.read | doctor_service.get_active_doctors / get_doctors_by_department |
| get_available_appointment_slots | user | appointment.manage | appointment_service.get_available_slots |
| create_appointment | user | appointment.manage | appointment_service.book_appointment |
| get_my_appointments | user | appointment.manage | appointment_service.get_patient_appointments |
| cancel_my_appointment | user | appointment.manage | appointment_service.cancel_appointment |
| get_my_medical_history | user | medical_history.read | report_service.get_patient_medical_history |
| get_my_medical_history_record | user | medical_history.read | report_service.get_medical_history_by_id |
| get_my_medical_reports | user | medical_report.read | report_service.get_patient_medical_images |
| get_my_medical_report | user | medical_report.read | report_service.get_medical_image |
| get_patient_for_admin | admin | patient.admin.read | (SQL tool ke andar) |
| search_patients | admin | patient.admin.read | (SQL tool ke andar) |
| get_doctor_for_admin | admin | doctor.admin.read | doctor_service.get_doctor_by_id |
| search_doctors | admin | doctor.admin.read | doctor_service |
| get_patient_appointments_for_admin | admin | appointment.admin.read | appointment_service.get_patient_appointments |
| check_system_database_health | super_admin | system.health.read | database.queries |
| get_system_mcp_summary | super_admin | system.mcp.read | registry |
| get_system_mcps_by_role | super_admin | system.mcp.read | registry |

---

## 6. MCP layer - kaise kaam karta hai

**Registry pattern.** `register_tools.py` mein ek `TOOLS` list hai. Startup par `register_all_tools()`
har tool ko `MCP_REGISTRY` (dictionary) mein daalta hai: `naam -> {handler, description, role, permission}`.
Ye function **idempotent** hai: dobara call karo to kuch nahi bigadta (reload/tests mein safe).

**`execute_mcp()` - ek hi darwaza.** Tool chalane ka sirf yahi raasta hai. Ye:
1. tool registered hai? 2. identity valid hai? (session se aayi `{id, role}`) 3. role + permission + RBAC theek hai?
4. arguments mein `role` / `authenticated_user` chhupe to nahi? (**identity smuggling roka jaata hai**)
5. handler chalata hai, har exception ko pakad kar `{"success": False, "error": ...}` banata hai (kabhi crash nahi).

**Do tarah ka "MCP":**

| | In-process (chatbot use karta hai) | stdio MCP server (`run_server.py`) |
|---|---|---|
| Kaun use karta hai | `llm/agent.py` -> `execute_mcp()` | Bahar ka MCP client (Claude Desktop jaisa) |
| Identity | Login session se (bharosemand) | **Koi nahi** |
| Nateeja | Tool chalta hai | **Har call mana** (`Authentication required`) |

stdio server jaan-boojhkar locked hai kyunki wahan koi trusted identity nahi hoti - warna koi bhi
bina login kisi bhi patient ka data maang leta. `test_mcp_client.py` isi ko verify karta hai.

---

## 7. LLM Agent ka design (`llm/agent.py`)

**Kaam:** Groq se baat karna, tool maange to chalana, result wapas dena, jawab nikalna.

| Cheez | Kaise hota hai |
|---|---|
| Kaun se tools dikhte hain | Sirf us role ke (user 10, admin 5, super_admin 3) |
| `patient_id` | Patient tools ke schema mein hai hi nahi; server **session se daalta hai**, LLM kuch bheje to overwrite |
| Galat argument naam | Schema mein na ho to hata diya jaata hai (`department:"All"` gaya) |
| Number text mein (`"2"`) | `int` mein badla jaata hai |
| Tarikh/samay | `"2026-10-12"` -> `date`, `"10:00"` ya `"10:00 AM"` -> `time` |
| Groq `tool_use_failed` (malformed call) | `failed_generation` se tool+args padh kar **khud chalate hain**; padh na paye to dobara try; tools kabhi hataye nahi jaate |
| Bahut bada result | 6000 characters par kaat diya (token bachane ke liye) |
| History | Sirf `user`/`assistant`, last 10, har ek <= 4000 char. `system`/`tool` role ignore (**prompt injection se bachav**) |
| Loop limit | 5 steps |
| Prompt mein | aaj ki tarikh, role, plain-text format, tarikh convert karne ke rules, "data invent mat karo" |

**Chat memory (server side)** - `api/chat.py`: widget history nahi bhejta, isliye server har login-session
ki last 10 baatein yaad rakhta hai (random `chat_id`, session mein). Logout par session saaf = memory gayi.
Maximum 1000 chats, memory mein (server restart par reset).

---

## 8. Data model (MySQL)

Schema MySQL mein pehle se hai (is project se banta nahi). Code jin tables/columns ko use karta hai:

```
patients          id, name, phone, email, password_hash, dob, gender, address, role, created_at, updated_at
admin_users       id, name, email, password, role(admin|super_admin)
departments       id, name, status
doctors           id, name, phone, email, specialization, department_id, qualification,
                  experience_years, consultation_fee, status(active|inactive)
doctor_schedules  doctor_id, day_of_week('Monday'...), start_time, end_time, slot_duration(min), status
appointments      id, patient_id, doctor_id, department_id, appointment_date, start_time, end_time,
                  status(booked|confirmed|cancelled|...), reason
medical_history   id, patient_id, doctor_id, condition_name, notes, record_date, created_at
medical_images    id, patient_id, chat_session_id, file_path, uploaded_at
chat_sessions / chat_messages   (names defined, abhi use nahi hote)
```

Relations: `appointments -> patients, doctors, departments`; `doctors -> departments`;
`doctor_schedules -> doctors`; `medical_* -> patients (+ doctors)`.

**Important rules jo code mein hain (`appointment_service.py`):**

| Rule | Kaise |
|---|---|
| Slot grid | Schedule ke `slot_duration` ke hisaab se slots; sirf us din ke `day_of_week` ka active schedule |
| Booked slot hide | `status IN ('booked','confirmed')` wali appointments overlap check |
| Beeti tarikh/samay | Slots khali; booking mana |
| Booking validations | doctor active, department doctor ki hi, patient exist, time schedule ke andar aur slot grid par |
| **Double booking** | Doctor row `SELECT ... FOR UPDATE` se lock, phir conflict check, phir INSERT - ek hi transaction mein |
| Cancel | Appointment row lock; sirf owner; sirf booked/confirmed; sirf future; doosre ki id par "not found" |
| **MySQL TIME bug** | PyMySQL `TIME` ko `timedelta` deta hai; `_to_time()` use `time` banata hai |

---

## 9. Security design (khatra -> bachav)

| Khatra | Bachav | Kahan |
|---|---|---|
| LLM ko bahkana ("mera id 999 hai") | `patient_id` hamesha session se | `llm/agent.py` |
| Patient admin tool chalaye | Tool list role se; execute par role+RBAC dobara check | `mcp_app/permissions.py` |
| Identity arguments mein chhupana | `role`/`authenticated_user` arguments reject | `mcp_app/router.py` |
| Doosre ka data (IDOR) | Har query mein `patient_id = session id` | `services/*` |
| ID guess karna (cancel) | Doosre ki id par bhi "not found" | `appointment_service.py` |
| SQL injection | Sirf parameterised queries (`%s`) | `services/*` |
| Password guessing | bcrypt + 8 attempts/10 min + timing-safe unknown user | `auth/*`, `api/auth.py` |
| Patient ko admin banana (DB role) | Patient login ka role hamesha `user` | `auth/authentication.py` |
| Session chori | signed cookie, HttpOnly, SameSite=Lax, expiry, Secure (HTTPS) | `main.py` |
| Session fixation | Login par naya session | `api/auth.py` |
| LLM kharcha / spam | 20 msgs/min per user; Groq timeout | `api/chat.py`, `llm_service.py` |
| History se prompt injection | Sirf user/assistant roles | `llm/agent.py` |
| XSS chat mein | Widget `textContent` use karta hai, HTML nahi | `static/chatbot.js` |
| Path traversal (files) | Path `uploads/` ke andar hi resolve hona chahiye | `report_service.py` |
| File path leak | Tool kabhi `file_path` wapas nahi deta | `mcp_user_05` |
| Bina login stdio MCP | Har call refuse | `register_tools.py` |
| DB hang | connect/read/write timeouts | `database/connection.py` |
| Secrets leak | `.env` gitignore, `.env.example` template | repo |
| Error se andar ki jaankari | Client ko generic message; traceback sirf logs mein | `api/chat.py` |

---

## 10. Errors aur failure modes

| Kya toota | Client ko kya milta hai | Logs mein |
|---|---|---|
| Login nahi hai | 401 "Authentication required" | - |
| Bahut messages | 429 "sending messages too fast" | - |
| Groq rate limit | 429 "assistant is busy..." | `RateLimitError` traceback |
| Groq down / koi aur error | 503 "Chat service is temporarily unavailable." | traceback |
| Groq ne tool call galat likha | User ko pata nahi chalta (recover) | WARNING `Recovered malformed tool call` |
| MySQL band (tool ke andar) | LLM ko `MCP execution failed`, user ko friendly jawab | ERROR traceback |
| MySQL band (login) | 503 "Login service temporarily unavailable." | traceback |
| Tool galat arguments | LLM ko error result, wo user se poochta hai | `Invalid arguments for MCP` |

Debugging ke liye hamesha **terminal / `logs/app.log`** dekhein. Important lines:
`LLM requested tool X` (model ne tool maanga) -> `MCP execution started` (tool chala) -> service ka
log (jaise `Appointment booked successfully`). `MCP execution denied` = ijazat nahi.

---

## 11. Configuration (`.env`)

| Variable | Zaroori? | Matlab |
|---|---|---|
| `DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME` | Haan | MySQL |
| `GROQ_API_KEY` | Haan | Groq key |
| `GROQ_MODEL` | Nahi | Default `openai/gpt-oss-20b`. Tool calling ke liye `openai/gpt-oss-120b` behtar |
| `SESSION_SECRET_KEY` | Haan | Cookie sign karne ki lambi random string |
| `SESSION_HTTPS_ONLY` | Nahi | Production (HTTPS) mein `true` |
| `SESSION_MAX_AGE_SECONDS` | Nahi | Default 28800 (8 ghante) |
| `LOG_LEVEL`, `LOG_TO_FILE` | Nahi | Logging |
| `UPLOAD_DIR` | Nahi | Medical files ka folder (default `<project>/uploads`) |
| `DB_CONNECT_TIMEOUT`, `GROQ_TIMEOUT` | Nahi | Seconds |

Real environment variables `.env` par **jeet** jaate hain (deployment ke liye sahi).

---

## 12. ML Website ke saath jodna (root `main.py`)

Aapka outer project (ML workshop website) aur chatbot ek hi FastAPI app mein chalte hain.
Example: `docs/examples/root_main.py`. Teen cheezein dhyan mein rakhein:

1. **`sys.path` ka order.** Root folder sabse **aage**, `chatbot_version_2` sabse **peeche**.
   Dono mein `src/` naam ka package hai; root wala jeetna chahiye (varna uvicorn `--reload` ke child
   process mein `src.exception` nahi milta tha - ye pehle ka bug tha).
2. **Naam takrav.** Root mein `api`, `auth`, `database`, `services`, `llm`, `mcp_app` naam ke folder
   **nahi** hone chahiye, warna chatbot ke wale dab jayenge.
3. **Tools register.** Root `main.py` ke `lifespan` mein `register_all_tools()` call hota hai
   (idempotent). Wo chhoot bhi jaye to `llm/agent.py` pehli request par khud register kar leta hai.

Chatbot ko root ka `src/logger.py` hi milta hai (shadowing) - bas us mein `get_logger(name)` hona chahiye.

Frontend ke liye zaroori endpoints: `POST /auth/login`, `/auth/register`, `/auth/logout`, `GET /auth/me`,
`POST /api/chat/message` (`{"message": "..."}` -> `{"success": true, "reply": "..."}`).

---

## 13. Testing

**Automated** (`python -m pytest tests -q`) - 119 tests, na MySQL chahiye na Groq:

| File | Kya jaanchti hai |
|---|---|
| `test_auth.py` | login, role=user force, rate limit, register validation, hashing, logout |
| `test_rbac_and_router.py` | 18 tools x 3 roles ka matrix, RBAC enforce, identity smuggling, stdio lock |
| `test_agent.py` | patient_id injection, type/date conversion, malformed-call recovery, loop cap, history safai |
| `test_chat_api.py` | login zaroori, memory, memory isolation, rate limit, 429/503 errors |
| `test_appointments.py` | slots (timedelta), booking rules, double-booking lock, cancel rules |
| `test_misc_security.py` | path traversal, patient scoping, rate limiter, DB commit/rollback, logger |

**Manual** (`docs/MANUAL_TEST_SHEET.md`) - asli MySQL + Groq ke saath UI se, har query ke saath
batata hai kaun si logic chalti hai aur terminal mein kya dikhna chahiye.

---

## 14. Naya kaam kaise jodein

**Naya tool (jaise "doctor ki fees compare karo"):**
1. SQL/rules `services/<x>_service.py` mein likhein (parameterised, `get_db()` ke saath).
2. `mcp_app/<role>/<naam>/tool.py` mein chhota function: input check, service call, `{"success":..., "data":...}`.
3. Naya permission ho to `auth/permissions.py` aur `auth/rbac.py` (role ko dein).
4. `mcp_app/register_tools.py` ke `TOOLS` mein ek entry.
5. `llm/agent.py` ke `TOOL_PARAMS` mein parameters ka schema (aur agar `patient_id` chahiye to `PATIENT_ID_TOOLS` mein).
6. `tests/` mein test, aur `python -m pytest tests -q`.

**Naya role:** `auth/rbac.py` (`VALID_ROLES` + `ROLE_PERMISSIONS`), `mcp_app/permissions.py` ka `VALID_ROLES`,
`mcp_app/router.py` ke valid roles, aur login ka raasta.

**Naya table:** MySQL mein banayein, `database/models.py` mein naam, service mein queries.

---

## 15. Known limitations aur aage ke sudhaar (roadmap)

| Cheez | Abhi | Behtar |
|---|---|---|
| Chat memory, rate limiter | Process ki memory mein; restart par reset; 1 worker | Redis / DB (`chat_sessions`, `chat_messages` tables ready hain) |
| DB connection | Har query par naya connection | Connection pool (`DBUtils`/SQLAlchemy) |
| `mcp_admin_01` | SQL tool ke andar | Service layer mein le jaana |
| Audit trail | Sirf log files | `audit_log` table (kisne kab kya dekha/badla) |
| Patient data Groq ko jaata hai | Tool results LLM provider tak pahunchte hain | Privacy policy/consent; sensitive fields mask karna; local LLM option |
| CSRF | SameSite=Lax + JSON API se kaafi | Production mein CSRF token |
| Admin login UI | Widget mein nahi (sirf `/docs` se) | Alag admin page |
| Medical report ka text | Tool sirf metadata deta hai | Report parsing (PDF/vision) alag secure pipeline mein |
| Reschedule | Nahi hai | `reschedule_my_appointment` tool |
| Migrations | Schema manual | Alembic / SQL migration files |
| Deployment | `uvicorn main:app --reload` (dev) | Gunicorn+uvicorn workers, HTTPS reverse proxy, `SESSION_HTTPS_ONLY=true` |

---

## 16. Original code mein jo bugs mile aur theek hue

| # | Bug | Asar | Fix |
|---|---|---|---|
| 1 | Chat tools ko call hi nahi karta tha | Chatbot sirf general baat karta | `llm/agent.py` tool loop |
| 2 | Tools register hi nahi hote the (kahin call nahi) | Tool list khali | `lifespan` + lazy register, idempotent |
| 3 | `mcp` package requirements mein nahi; v2 code tod deta | App start nahi hoti | `mcp>=1.2,<2` |
| 4 | MySQL `TIME` = `timedelta` | Slots/booking `TypeError` | `_to_time()` |
| 5 | Beeti tarikh par booking ho jaati | Galat appointments | Past check |
| 6 | RBAC table sirf dikhawe ki thi (permission khud registry se leke compare hoti thi) | Table badalne ka koi asar nahi | `has_permission()` ab enforce |
| 7 | Patient login ka role DB column se aata tha | Galat DB value = admin ban sakta tha | Hamesha `user` |
| 8 | Login par koi limit nahi | Password guessing | 8 attempts / 10 min |
| 9 | Chat par koi limit nahi | LLM kharcha/abuse | 20 msgs / min |
| 10 | Unknown user ka login jaldi return (timing) | User enumeration | Dummy bcrypt |
| 11 | Doosre ki appointment cancel par alag message | ID ka pata chalta | "not found" |
| 12 | Past appointment cancel ho jaati | Itihaas bigadta | Mana |
| 13 | DB timeout nahi | DB band = request atakti | 5s/15s timeouts |
| 14 | `.env`, `logs/`, `uploads/` ka path cwd par depend | Root se chalane par toot-ta | Project-relative |
| 15 | `load_dotenv(override=True)` | Real env vars dab jaate | `override=False` |
| 16 | Har start par naya log file | Logs ka dher | Rotating `app.log` |
| 17 | Register: email/phone/dob/72-byte password ki jaanch nahi, duplicate race 503 | Kachra data, crash | Validators + IntegrityError -> 409 |
| 18 | Chat widget history nahi bhejta | Follow-up samajh nahi aata | Server-side memory |
| 19 | LLM ke malformed tool call par 503 | "Chat unavailable" | Recovery + type coercion |
| 20 | Chat ke 500/503 mein andar ki detail | Info leak | Generic message, detail logs mein |
| 21 | `/register` template route (template tha hi nahi) | Crash | Hataya |
| 22 | `src` package naam takrav (root vs chatbot) | Reload par `ModuleNotFoundError` | sys.path order (root pehle) |
| 23 | Admin search 100 rows LLM ko | Tokens/privacy | 25 rows |
| 24 | `test_mcp_client.py` hamesha fail | Confusion | Ab verify karta hai ki lock sahi kaam kar raha hai |
| 25 | `requirements.txt` mein 9 bekaar packages | Bhaari install | Sirf zaroori |
