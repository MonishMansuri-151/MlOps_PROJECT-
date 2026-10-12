import bcrypt

import auth.authentication as authentication
from tests.fakes import ScriptedDB

PW = "Secret123"


def _patient_row(role="user"):
    return {
        "id": 3, "name": "Asha", "phone": "9999999999", "email": "a@b.com",
        "password_hash": bcrypt.hashpw(PW.encode(), bcrypt.gensalt()).decode(),
        "role": role,
    }


def test_login_success_sets_session(client, monkeypatch):
    monkeypatch.setattr(authentication, "get_db", ScriptedDB([_patient_row()]))
    r = client.post("/auth/login", json={"identifier": "a@b.com", "password": PW})
    assert r.status_code == 200
    assert r.json()["user"] == {"id": 3, "name": "Asha", "role": "user"}
    assert client.get("/auth/me").json()["user"]["id"] == 3


def test_wrong_password_401(client, monkeypatch):
    monkeypatch.setattr(authentication, "get_db", ScriptedDB([_patient_row()]))
    r = client.post("/auth/login", json={"identifier": "a@b.com", "password": "nope"})
    assert r.status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_unknown_user_gets_same_401(client, monkeypatch):
    monkeypatch.setattr(authentication, "get_db", ScriptedDB([None]))
    r = client.post("/auth/login", json={"identifier": "ghost@b.com", "password": PW})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials."


def test_patient_role_is_always_user_even_if_db_says_admin(client, monkeypatch):
    """patients.role must never be able to grant admin rights."""
    monkeypatch.setattr(authentication, "get_db", ScriptedDB([_patient_row(role="super_admin")]))
    r = client.post("/auth/login", json={"identifier": "a@b.com", "password": PW})
    assert r.json()["user"]["role"] == "user"


def test_admin_login_only_for_admin_roles(client, monkeypatch):
    row = {"id": 1, "name": "Boss", "email": "boss@x.com", "role": "admin",
           "password": bcrypt.hashpw(PW.encode(), bcrypt.gensalt()).decode()}
    monkeypatch.setattr(authentication, "get_db", ScriptedDB([row]))
    r = client.post("/auth/admin-login", json={"email": "BOSS@x.com", "password": PW})
    assert r.status_code == 200 and r.json()["user"]["role"] == "admin"

    row["role"] = "user"
    monkeypatch.setattr(authentication, "get_db", ScriptedDB([row]))
    r = client.post("/auth/admin-login", json={"email": "boss@x.com", "password": PW})
    assert r.status_code == 401


def test_login_is_rate_limited_after_8_failures(client, monkeypatch):
    monkeypatch.setattr(authentication, "get_db", lambda: ScriptedDB([None])())
    for _ in range(8):
        assert client.post("/auth/login", json={"identifier": "x@y.com", "password": "bad"}).status_code == 401
    r = client.post("/auth/login", json={"identifier": "x@y.com", "password": "bad"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_logout_clears_session(login):
    c = login("user")
    assert c.get("/auth/me").status_code == 200
    c.post("/auth/logout")
    assert c.get("/auth/me").status_code == 401


def test_db_down_on_login_is_503_not_crash(client, monkeypatch):
    def boom():
        raise RuntimeError("mysql down")
    monkeypatch.setattr(authentication, "get_db", boom)
    r = client.post("/auth/login", json={"identifier": "a@b.com", "password": PW})
    assert r.status_code == 503


# ------------------------------------------------------------- register

GOOD = {
    "name": "Ravi Kumar", "phone": "9876543210", "email": "Ravi@Example.com",
    "password": "Passw0rd!", "dob": "1995-05-20", "gender": "Male",
    "address": "12 Park Street, Delhi",
}


def _register(client, **over):
    return client.post("/auth/register", json={**GOOD, **over})


def test_register_success_hashes_password(client, monkeypatch):
    import api.auth as auth_api
    db = ScriptedDB([None])               # duplicate check -> nobody found
    monkeypatch.setattr(auth_api, "get_db", db)
    r = _register(client)
    assert r.status_code == 201
    assert r.json()["patient"]["email"] == "ravi@example.com"       # lowercased
    insert_sql, params = db.queries[-1]
    assert insert_sql.startswith("INSERT INTO patients")
    assert "Passw0rd!" not in params                                  # never plain text
    assert params[3].startswith("$2")                                 # bcrypt hash
    assert params[-2] == "male"                                       # normalised gender


def test_register_duplicate_is_409(client, monkeypatch):
    import api.auth as auth_api
    monkeypatch.setattr(auth_api, "get_db", ScriptedDB([{"id": 1}]))
    assert _register(client).status_code == 409


def test_register_validation(client):
    assert _register(client, email="not-an-email").status_code == 422
    assert _register(client, phone="12ab").status_code == 422
    assert _register(client, password="short").status_code == 422
    assert _register(client, gender="robot").status_code == 422
    assert _register(client, dob="2999-01-01").status_code == 422
    assert _register(client, dob="1800-01-01").status_code == 422
    assert _register(client, name="   ").status_code == 422
    # 30 chars but 90 bytes -> bcrypt would silently cut it
    assert _register(client, password="é" * 40).status_code == 422
