from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from chatbot.auth.session import get_current_user
from chatbot.services.injury_service import analyze_uploaded_injury
from src.logger import get_logger
from datetime import date, time
from chatbot.services.appointment_service import book_appointment
from pydantic import BaseModel

logger = get_logger(__name__)


router = APIRouter(
    prefix="/chatbot/injury",
    tags=["Injury Analysis"]
)

class InjuryAppointmentRequest(BaseModel):
    doctor_id: int
    appointment_date: date
    start_time: time
    reason: str | None = None
@router.post("/analyze")
async def analyze_injury(
    request: Request,
    file: UploadFile = File(...)
):
    try:
        # RBAC: patient identity session se milegi
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Please login first."
            )

        patient_id = user["id"]

        # Read uploaded image
        file_content = await file.read()

        result = analyze_uploaded_injury(
            patient_id=patient_id,
            original_filename=file.filename,
            file_content=file_content,
            content_type=file.content_type
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Injury analysis route error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to analyze injury image."
        )
        
@router.post("/book")
def book_injury_appointment(
    data: InjuryAppointmentRequest,
    request: Request
):
    try:
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Please login first."
            )

        patient_id = user["id"]

        result = book_appointment(
            patient_id=patient_id,
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            start_time=data.start_time,
            reason=data.reason
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
            f"Injury appointment booking error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to book appointment."
        )