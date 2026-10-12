"""
Authentication API  (prefix: /auth)

POST /auth/login        patient login  (phone or email + password)
POST /auth/admin-login  admin / super_admin login
GET  /auth/me           who is logged in?
POST /auth/logout       end the session
POST /auth/register     create a patient account
"""
import re
from datetime import date

import bcrypt
import pymysql
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from auth.authentication import authenticate_admin, authenticate_patient
from auth.rate_limit import RateLimiter
from database.connection import get_db
from src.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 8 failed logins per 10 minutes per (client + account). Success resets it.
login_limiter = RateLimiter(max_events=8, window_seconds=600)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{10,15}$")


# ---------------------------------------------------------------- schemas

class PatientLoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class PatientRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=20)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    dob: date
    gender: str = Field(min_length=1, max_length=20)
    address: str = Field(min_length=5, max_length=500)

    @field_validator("name", "address")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        value = re.sub(r"[\s-]", "", value.strip())
        if not PHONE_RE.match(value):
            raise ValueError("Phone must be 10-15 digits (optional leading +).")
        return value

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def valid_password(cls, value: str) -> str:
        # bcrypt only uses the first 72 BYTES; reject longer input
        # instead of silently truncating (or crashing on newer bcrypt).
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes).")
        return value

    @field_validator("dob")
    @classmethod
    def valid_dob(cls, value: date) -> date:
        today = date.today()
        if value >= today:
            raise ValueError("Date of birth must be in the past.")
        if value.year < today.year - 120:
            raise ValueError("Enter a valid date of birth.")
        return value

    @field_validator("gender")
    @classmethod
    def valid_gender(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"male", "female", "other"}:
            raise ValueError("Gender must be male, female, or other.")
        return value


# ---------------------------------------------------------------- helpers

def _client_key(request: Request, account: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}|{account.strip().lower()}"


def _set_login_session(request: Request, user: dict) -> None:
    # Start a brand-new session (prevents session fixation).
    request.session.clear()
    request.session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
    }


def _login(request: Request, account: str, authenticate, *args) -> dict:
    key = _client_key(request, account)

    if login_limiter.is_blocked(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please try again later.",
            headers={"Retry-After": str(login_limiter.retry_after(key))},
        )

    try:
        user = authenticate(*args)
    except Exception:
        logger.exception("Login encountered a server error.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable.",
        ) from None

    if not user:
        login_limiter.hit(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    login_limiter.reset(key)
    _set_login_session(request, user)
    return {"id": user["id"], "name": user["name"], "role": user["role"]}


# ----------------------------------------------------------------- routes

@router.post("/login")
def patient_login(data: PatientLoginRequest, request: Request):
    identifier = data.identifier.strip()
    if "@" in identifier:
        identifier = identifier.lower()          # emails are stored lowercase
    else:
        identifier = re.sub(r"[\s-]", "", identifier)  # same cleanup as register

    user = _login(
        request, identifier, authenticate_patient,
        identifier, data.password,
    )
    return {"message": "Login successful.", "user": user}


@router.post("/admin-login")
def admin_login(data: AdminLoginRequest, request: Request):
    user = _login(
        request, data.email, authenticate_admin,
        data.email.strip().lower(), data.password,
    )
    return {"message": "Admin login successful.", "user": user}


@router.get("/me")
def current_user(request: Request):
    user = request.session.get("user")

    if (
        not isinstance(user, dict)
        or user.get("id") is None
        or not user.get("role")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    return {"user": user}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully."}


@router.post("/register", status_code=201)
def register_patient(data: PatientRegisterRequest):
    password_hash = bcrypt.hashpw(
        data.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    try:
        with get_db() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM patients WHERE phone = %s OR email = %s LIMIT 1",
                    (data.phone, data.email),
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail="This phone or email is already registered.",
                    )

                cursor.execute(
                    """
                    INSERT INTO patients
                        (name, phone, email, password_hash, dob, gender,
                         address, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'user')
                    """,
                    (
                        data.name, data.phone, data.email, password_hash,
                        data.dob, data.gender, data.address,
                    ),
                )
                patient_id = cursor.lastrowid

        return {
            "message": "Registration successful. You can now log in.",
            "patient": {
                "id": patient_id,
                "name": data.name,
                "phone": data.phone,
                "email": data.email,
                "role": "user",
            },
        }

    except HTTPException:
        raise
    except pymysql.err.IntegrityError:
        # Two people registering the same phone/email at the same moment.
        raise HTTPException(
            status_code=409,
            detail="This phone or email is already registered.",
        ) from None
    except Exception:
        logger.exception("Patient registration failed.")
        raise HTTPException(
            status_code=503,
            detail="Registration service is temporarily unavailable.",
        ) from None
