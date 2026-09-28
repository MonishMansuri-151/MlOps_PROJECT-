import os
import sys
import uuid

from chatbot.database.connection import get_connection
from src.logger import get_logger
from src.exception import CustomException

logger = get_logger(__name__)

UPLOAD_DIR = "chatbot/uploads"

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


# def save_medical_file(
#     patient_id: int,
#     original_filename: str,
#     file_content: bytes,
#     content_type: str | None = None,
# ):
def save_medical_file(
    patient_id: int,
    original_filename: str,
    file_content: bytes,
    content_type: str | None = None,
    chat_session_id: int | None = None,
):
    connection = None

    try:
        if not original_filename:
            return {
                "success": False,
                "message": "Filename is required."
            }

        file_extension = os.path.splitext(
            original_filename
        )[1].lower()

        if file_extension not in ALLOWED_EXTENSIONS:
            return {
                "success": False,
                "message": "Only JPG, JPEG, PNG and PDF files are allowed."
            }

        if not file_content:
            return {
                "success": False,
                "message": "Uploaded file is empty."
            }

        if len(file_content) > MAX_FILE_SIZE:
            return {
                "success": False,
                "message": "File size must not exceed 5 MB."
            }

        os.makedirs(
            UPLOAD_DIR,
            exist_ok=True
        )

        # Random filename for security
        stored_filename = (
            f"{uuid.uuid4().hex}{file_extension}"
        )

        patient_directory = os.path.join(
            UPLOAD_DIR,
            str(patient_id)
        )

        os.makedirs(
            patient_directory,
            exist_ok=True
        )

        file_path = os.path.join(
            patient_directory,
            stored_filename
        )

        with open(file_path, "wb") as file:
            file.write(file_content)

        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO medical_images
                (
                    patient_id,
                    chat_session_id,
                    file_path
                )
                VALUES (%s, %s, %s)
                """,
                (
                    patient_id,
                    chat_session_id,
                    file_path,
                )
            )

        connection.commit()

        logger.info(
            f"Medical file uploaded successfully: "
            f"patient_id={patient_id}, "
            f"filename={original_filename}"
        )

        return {
            "success": True,
            "message": "Medical file uploaded successfully.",
            "file_name": original_filename,
            "stored_file": stored_filename,
        }

    except Exception as e:
        if connection:
            connection.rollback()

        logger.error(
            f"Medical file upload failed: {e}"
        )

        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()