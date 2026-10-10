
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from auth.authentication import (
    authenticate_admin,
    authenticate_patient,
)
from src.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class PatientLoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


def set_login_session(request: Request, user: dict) -> None:
    # Prevent session fixation by starting a fresh session.
    request.session.clear()
    request.session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
    }


@router.post("/login")
def patient_login(data: PatientLoginRequest, request: Request):
    try:
        user = authenticate_patient(data.identifier, data.password)
    except Exception:
        logger.exception("Patient login encountered a server error.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable.",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    set_login_session(request, user)

    return {
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "role": user["role"],
        },
    }


@router.post("/admin-login")
def admin_login(data: AdminLoginRequest, request: Request):
    try:
        user = authenticate_admin(data.email, data.password)
    except Exception:
        logger.exception("Admin login encountered a server error.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable.",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    set_login_session(request, user)

    return {
        "message": "Admin login successful.",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "role": user["role"],
        },
    }


@router.get("/me")
def current_user(request: Request):
    user = request.session.get("user")

    if not isinstance(user, dict) or not user.get("id") or not user.get("role"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    return {
        "user": user,
    }


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully."}


import bcrypt

from database.connection import get_db


# class PatientRegisterRequest(BaseModel):
#     name: str = Field(min_length=2, max_length=100)
#     phone: str = Field(min_length=10, max_length=20)
#     email: str = Field(min_length=5, max_length=255)
#     password: str = Field(min_length=8, max_length=72)

from datetime import date
from pydantic import field_validator
class PatientRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=20)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)

    dob: date
    gender: str = Field(min_length=1, max_length=20)
    address: str = Field(min_length=5, max_length=500)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"male", "female", "other"}:
            raise ValueError("Gender must be male, female, or other.")
        return value

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Address cannot be empty.")
        return value


@router.post("/register", status_code=201)
def register_patient(data: PatientRegisterRequest):
    name = data.name.strip()
    phone = data.phone.strip()
    email = data.email.strip().lower()

    if not name or not phone or not email:
        raise HTTPException(
            status_code=400,
            detail="Name, phone and email are required.",
        )

    password_hash = bcrypt.hashpw(
        data.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    try:
        with get_db() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM patients
                    WHERE phone = %s OR email = %s
                    LIMIT 1
                    """,
                    (phone, email),
                )

                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail="This phone or email is already registered.",
                    )
                
                cursor.execute(
                    """
                    INSERT INTO patients
                        (name, phone, email, password_hash, dob, gender, address, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'user')
                    """,
                    (
                        name,
                        phone,
                        email,
                        password_hash,
                        data.dob,
                        data.gender,
                        data.address,
                    ),
                )

                patient_id = cursor.lastrowid

                

        return {
            "message": "Registration successful. You can now log in.",
            "patient": {
                "id": patient_id,
                "name": name,
                "phone": phone,
                "email": email,
                "role": "user",
            },
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Patient registration failed.")
        raise HTTPException(
            status_code=503,
            detail="Registration service is temporarily unavailable.",
        ) from None
