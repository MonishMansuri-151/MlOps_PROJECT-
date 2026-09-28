from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    UploadFile,
)

from pydantic import BaseModel

from chatbot.auth.session import get_current_user
from chatbot.services.medical_service import save_medical_file
from chatbot.services.medical_report_service import (
    analyze_patient_report
)

from src.logger import get_logger


logger = get_logger(__name__)


router = APIRouter(
    prefix="/chatbot/medical",
    tags=["Medical Files"]
)


class ReportAnalysisRequest(BaseModel):
    question: str = ""


@router.post("/upload")
async def upload_medical_file(
    request: Request,
    file: UploadFile = File(...)
):
    try:
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Please login first."
            )

        patient_id = user["id"]

        file_content = await file.read()

        result = save_medical_file(
            patient_id=patient_id,
            original_filename=file.filename,
            file_content=file_content,
            content_type=file.content_type,
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
            f"Medical upload route error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to upload medical file."
        )


@router.post("/reports/{file_id}/analyze")
def analyze_report(
    file_id: int,
    request: Request,
    data: ReportAnalysisRequest
):
    try:
        user = get_current_user(request)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Please login first."
            )

        patient_id = user["id"]

        result = analyze_patient_report(
            file_id=file_id,
            patient_id=patient_id,
            user_question=data.question
        )

        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Report analysis route error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to analyze medical report."
        )