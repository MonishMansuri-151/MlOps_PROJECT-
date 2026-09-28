from fastapi import APIRouter, Request
from pydantic import BaseModel
import sys
from chatbot.auth.authentication import (
    authenticate_patient,
    authenticate_admin,
)
from chatbot.auth.session import (
    set_user_session,
    get_current_user,
    clear_user_session,
)
import bcrypt
from chatbot.database.queries import create_patient
from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    identifier: str
    password: str
class RegisterRequest(BaseModel):
    name: str
    phone: str
    email: str | None = None
    password: str
    dob: str | None = None
    gender: str | None = None
    address: str | None = None
    
@router.post("/register")
def register(request: Request, register_data: RegisterRequest):
    try:
        password_hash = bcrypt.hashpw(
            register_data.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        result = create_patient(
            name=register_data.name,
            phone=register_data.phone,
            email=register_data.email,
            password_hash=password_hash,
            dob=register_data.dob,
            gender=register_data.gender,
            address=register_data.address,
        )

        return {
            "success": True,
            "message": "Registration successful. You can now login."
        }

    except Exception as e:
        logger.error(f"Registration route error: {e}")
        raise CustomException(e, sys)
@router.post("/login")
def login(request: Request, login_data: LoginRequest):
    try:
        patient = authenticate_patient(
            identifier=login_data.identifier,
            password=login_data.password,
        )

        if patient is None:
            return {
                "success": False,
                "message": "Invalid phone/email or password."
            }

        set_user_session(request, patient)

        return {
            "success": True,
            "message": "Login successful.",
            "user": {
                "id": patient["id"],
                "name": patient["name"],
                "phone": patient["phone"],
                "email": patient.get("email"),
            }
        }

    except Exception as e:
        logger.error(f"Login route error: {e}")
        raise CustomException(e,sys)

@router.post("/admin-login")
def admin_login(request: Request, login_data: LoginRequest):
    try:
        admin = authenticate_admin(
            email=login_data.identifier,
            password=login_data.password,
        )

        if admin is None:
            return {
                "success": False,
                "message": "Invalid admin email or password."
            }

        request.session["admin_user"] = {
            "id": admin["id"],
            "name": admin["name"],
            "email": admin["email"],
            "role": admin["role"],
        }

        logger.info(
            f"Admin login successful: "
            f"admin_id={admin['id']}, role={admin['role']}"
        )

        return {
            "success": True,
            "message": "Admin login successful.",
            "user": {
                "id": admin["id"],
                "name": admin["name"],
                "email": admin["email"],
                "role": admin["role"],
            }
        }

    except Exception as e:
        logger.error(f"Admin login route error: {e}")
        raise CustomException(e, sys)
    
@router.post("/logout")
def logout(request: Request):
    try:
        clear_user_session(request)

        return {
            "success": True,
            "message": "Logout successful."
        }

    except Exception as e:
        logger.error(f"Logout route error: {e}")
        raise CustomException(e,sys)


@router.get("/me")
def current_user(request: Request):
    try:
        user = get_current_user(request)

        if user is None:
            return {
                "authenticated": False,
                "user": None
            }

        return {
            "authenticated": True,
            "user": user
        }

    except Exception as e:
        logger.error(f"Current user route error: {e}")
        raise CustomException(e,sys)