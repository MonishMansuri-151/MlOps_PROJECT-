from datetime import date, time
from fastapi import Request
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(
    directory="chatbot/frontend"
)

from chatbot.services.chat_service import process_chat_message

from chatbot.services.patient_service import (

    find_patient_by_id,
    get_patient_history,
    get_patient_appointment_history,
)

from chatbot.services.doctor_service import (
    get_all_departments,
    find_departments,
    find_doctors,
    find_doctor,
    get_schedule,
)

from chatbot.services.appointment_service import (
    get_appointments_for_patient,
    get_available_slots,
    book_appointment,
)
# all convertion of chat_history_serivec file imports to add fast api
from chatbot.auth.session import get_current_user

from chatbot.services.chat_history_service import (
    create_session,
    get_patient_chat_sessions,
    get_session_messages,
    delete_session,
)

from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)


router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"]
)


# ============================================================
# REQUEST MODELS
# ============================================================

class AppointmentRequest(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: date
    start_time: time
    reason: str | None = None


# ============================================================
# HTML ROUTER 
# ============================================================
@router.get("/", response_class=HTMLResponse)
def chatbot_home(request: Request):

    user = get_current_user(request)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please login first."
        )

    return templates.TemplateResponse(
        request=request,
        name="chatbot.html",
        context={
        "user": user
        }
    )


# ============================================================
# PATIENT
# ============================================================

@router.get("/patient/{patient_id}")
def get_patient(patient_id: int):

    try:
        patient = find_patient_by_id(patient_id)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found."
            )

        return {
            "success": True,
            "data": patient
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error in get_patient route: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch patient information."
        )


@router.get("/patient/{patient_id}/history")
def patient_history(patient_id: int):

    try:
        patient = find_patient_by_id(patient_id)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found."
            )

        history = get_patient_history(patient_id)

        return {
            "success": True,
            "patient_id": patient_id,
            "history": history
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error fetching patient history: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch medical history."
        )


@router.get("/patient/{patient_id}/appointments")
def patient_appointments(patient_id: int):

    try:
        patient = find_patient_by_id(patient_id)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found."
            )

        appointments = get_patient_appointment_history(
            patient_id
        )

        return {
            "success": True,
            "patient_id": patient_id,
            "appointments": appointments
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error fetching patient appointments: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch appointments."
        )


# ============================================================
# DEPARTMENTS
# ============================================================

@router.get("/departments")
def departments():

    try:
        result = get_all_departments()

        return {
            "success": True,
            "departments": result
        }

    except Exception as e:
        logger.error(
            f"Error in departments route: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch departments."
        )


@router.get("/departments/search")
def department_search(
    keyword: str = Query(..., min_length=1)
):

    try:
        result = find_departments(keyword)

        return {
            "success": True,
            "keyword": keyword,
            "departments": result
        }

    except Exception as e:
        logger.error(
            f"Error searching departments: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to search departments."
        )


# ============================================================
# DOCTORS
# ============================================================

@router.get("/doctors")
def doctors(
    keyword: str | None = None,
    department_id: int | None = None
):

    try:
        result = find_doctors(
            keyword=keyword,
            department_id=department_id
        )

        return {
            "success": True,
            "doctors": result
        }

    except Exception as e:
        logger.error(
            f"Error searching doctors: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to search doctors."
        )


@router.get("/doctors/{doctor_id}")
def doctor_details(doctor_id: int):

    try:
        doctor = find_doctor(doctor_id)

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found."
            )

        return {
            "success": True,
            "doctor": doctor
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error fetching doctor details: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch doctor information."
        )


# ============================================================
# DOCTOR SCHEDULE
# ============================================================

@router.get("/doctors/{doctor_id}/schedule")
def doctor_schedule(
    doctor_id: int,
    day_of_week: str | None = None
):

    try:
        doctor = find_doctor(doctor_id)

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found."
            )

        schedule = get_schedule(
            doctor_id=doctor_id,
            day_of_week=day_of_week
        )

        return {
            "success": True,
            "doctor_id": doctor_id,
            "schedule": schedule
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error fetching doctor schedule: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch doctor schedule."
        )


# ============================================================
# AVAILABLE SLOTS
# ============================================================

@router.get("/doctors/{doctor_id}/slots")
def doctor_available_slots(
    doctor_id: int,
    appointment_date: date
):

    try:
        doctor = find_doctor(doctor_id)

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found."
            )

        slots = get_available_slots(
            doctor_id=doctor_id,
            appointment_date=appointment_date
        )

        return {
            "success": True,
            "doctor": {
                "id": doctor["id"],
                "name": doctor["name"],
                "specialization": doctor["specialization"]
            },
            "appointment_date": appointment_date,
            "available_slots": slots
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error fetching available slots: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch available slots."
        )


# ============================================================
# BOOK APPOINTMENT
# ============================================================

@router.post("/appointments")
def create_appointment(
    request: AppointmentRequest
):

    try:
        patient = find_patient_by_id(
            request.patient_id
        )

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found."
            )

        doctor = find_doctor(
            request.doctor_id
        )

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found."
            )

        result = book_appointment(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            appointment_date=request.appointment_date,
            start_time=request.start_time,
            reason=request.reason
        )

        if not result["success"]:
            raise HTTPException(
                status_code=409,
                detail=result["message"]
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error creating appointment route: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create appointment."
        )
        
class ChatMessageRequest(BaseModel):
    message: str

        
        
@router.post("/message")
def chat_message(
    chat_data: ChatMessageRequest,
    request: Request
):
    try:
        return process_chat_message(
            chat_data.message,
            request
        )

    except Exception as e:
        logger.error(
            f"Chat message route error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to process chat message."
        )
        
        

@router.post("/history/new")
def new_chat(request: Request):
    try:
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Please login first."
            )

        session_id = create_session(user["id"])

        request.session["chat_session_id"] = session_id
        request.session.pop("booking_context", None)

        return {
            "success": True,
            "session_id": session_id,
            "message": "New chat created."
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"New chat creation error: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to create new chat."
        )


@router.get("/history")
def get_chat_history(request: Request):
    try:
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required."
            )

        sessions = get_patient_chat_sessions(
            patient_id=user["id"]
        )

        return {
            "success": True,
            "sessions": sessions
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Get chat history error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch chat history."
        )


@router.get("/history/{session_id}")
def get_chat_history_messages(
    session_id: int,
    request: Request
):
    try:
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required."
            )

        messages = get_session_messages(
            patient_id=user["id"],
            session_id=session_id
        )

        return {
            "success": True,
            "session_id": session_id,
            "messages": messages
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Get chat session messages error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch chat messages."
        )


@router.delete("/history/{session_id}")
def delete_chat_history(
    session_id: int,
    request: Request
):
    try:
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required."
            )

        deleted = delete_session(
            patient_id=user["id"],
            session_id=session_id
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Chat conversation not found."
            )

        return {
            "success": True,
            "message": "Chat conversation deleted."
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Delete chat history error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to delete chat conversation."
        )
        
