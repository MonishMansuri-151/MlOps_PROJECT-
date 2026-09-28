import os
import sys
import uuid
from chatbot.services.doctor_service import find_departments, find_doctors
from chatbot.ai.vision import analyze_injury_image
from src.logger import get_logger
from src.exception import CustomException
from datetime import date

from chatbot.services.appointment_service import get_available_slots

logger = get_logger(__name__)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

UPLOAD_ROOT = os.path.join(
    "chatbot",
    "uploads",
    "injuries"
)


def analyze_uploaded_injury(
    patient_id: int,
    original_filename: str,
    file_content: bytes,
    content_type: str | None,
    appointment_date: date | None = None
):
    try:
        if not original_filename:
            return {
                "success": False,
                "message": "Please select an image."
            }

        extension = os.path.splitext(
            original_filename
        )[1].lower()

        # Extension validation
        if extension not in ALLOWED_EXTENSIONS:
            return {
                "success": False,
                "message": (
                    "Only JPG, JPEG and PNG images are allowed."
                )
            }

        # MIME validation
        if content_type not in ALLOWED_CONTENT_TYPES:
            return {
                "success": False,
                "message": "Invalid image type."
            }

        # Size validation
        if len(file_content) > MAX_FILE_SIZE:
            return {
                "success": False,
                "message": "Image size must be 5 MB or less."
            }

        if not file_content:
            return {
                "success": False,
                "message": "Uploaded image is empty."
            }

        # Patient-specific folder
        patient_folder = os.path.join(
            UPLOAD_ROOT,
            str(patient_id)
        )

        os.makedirs(
            patient_folder,
            exist_ok=True
        )

        # Never trust the original filename
        safe_filename = (
            f"{uuid.uuid4().hex}{extension}"
        )

        file_path = os.path.join(
            patient_folder,
            safe_filename
        )

        # Save image
        with open(file_path, "wb") as file:
            file.write(file_content)

        logger.info(
            f"Injury image uploaded for patient_id={patient_id}"
        )

        # Vision AI analysis
        analysis_result = analyze_injury_image(
            image_bytes=file_content,
            content_type=content_type
        )
        department_name = analysis_result["department"]

        department = None
        doctors = []

        if department_name:
            departments = find_departments(department_name)

            if departments:
                department = departments[0]

                doctors = find_doctors(
                    department_id=department["id"]
                )
        doctor_slots = []

        if appointment_date:
            for doctor in doctors:
                slots = get_available_slots(
                    doctor_id=doctor["id"],
                    appointment_date=appointment_date
                )

                doctor_slots.append({
                    "doctor": doctor,
                    "available_slots": slots
                })

        
        return {
            "success": True,
            "message": "Injury image analyzed successfully.",
            "file_path": file_path,
            "analysis": analysis_result["analysis"],
            "department": department,
            "doctors": doctors,
            "appointment_date": (
                appointment_date.isoformat()
                if appointment_date
                else None
            ),
            "doctor_slots": doctor_slots
        }

    except Exception as e:
        logger.error(
            f"Injury image processing failed: {e}"
        )
        raise CustomException(e, sys)