import os
import sys
from pathlib import Path

# Must be set BEFORE main.py is imported.
os.environ.setdefault("SESSION_SECRET_KEY", "test-secret-key-for-tests")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_TO_FILE", "false")   # tests must not write logs/

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import api.auth as auth_api  # noqa: E402
import api.chat as chat_api  # noqa: E402
import llm.agent as agent  # noqa: E402
from main import app  # noqa: E402

from tests.fakes import FakeGroq  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    """Every test starts with empty limiters and chat memory."""
    auth_api.login_limiter._events.clear()
    chat_api.chat_limiter._events.clear()
    chat_api._CHAT_MEMORY.clear()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def login(client, monkeypatch):
    """login('user'|'admin'|'super_admin', user_id=7) -> logged-in client."""

    def _login(role="user", user_id=7):
        user = {"id": user_id, "name": "Test Person", "role": role}
        if role == "user":
            monkeypatch.setattr(auth_api, "authenticate_patient", lambda i, p: user)
            r = client.post("/auth/login", json={"identifier": "x@y.com", "password": "pw"})
        else:
            monkeypatch.setattr(auth_api, "authenticate_admin", lambda e, p: user)
            r = client.post("/auth/admin-login", json={"email": "a@b.com", "password": "pw"})
        assert r.status_code == 200, r.text
        return client

    return _login


@pytest.fixture
def fake_llm(monkeypatch):
    """fake_llm([responses...]) -> FakeGroq used by the chat agent."""

    def _install(script):
        groq = FakeGroq(script)
        monkeypatch.setattr(agent, "get_llm_client", lambda: groq)
        return groq

    return _install
