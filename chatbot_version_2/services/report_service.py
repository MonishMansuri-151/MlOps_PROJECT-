from pathlib import Path

from src.logger import get_logger
logger = get_logger(__name__)
from database.connection import get_db


UPLOAD_DIR = Path("uploads").resolve()


def get_patient_medical_history(patient_id: int):
    """
    Get medical history records for a patient.

    Only medical history data is returned.
    Passwords and unrelated patient data are never selected.
    """

    if not patient_id or patient_id <= 0:
        return []

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    mh.id,
                    mh.condition_name,
                    mh.notes,
                    mh.record_date,
                    mh.created_at,
                    d.id AS doctor_id,
                    d.name AS doctor_name,
                    d.specialization
                FROM medical_history mh
                LEFT JOIN doctors d
                    ON mh.doctor_id = d.id
                WHERE mh.patient_id = %s
                ORDER BY
                    mh.record_date DESC,
                    mh.id DESC
                """,
                (patient_id,),
            )

            history = cursor.fetchall()

    logger.info(
        "Patient medical history retrieved",
        extra={
            "event": "MEDICAL_HISTORY_RETRIEVED",
            "patient_id": patient_id,
            "count": len(history),
        },
    )

    return history


def get_medical_history_by_id(patient_id: int, history_id: int):
    """
    Get one medical history record.

    The patient_id check prevents a patient from accessing
    another patient's medical history.
    """

    if not patient_id or patient_id <= 0:
        return None

    if not history_id or history_id <= 0:
        return None

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    mh.id,
                    mh.patient_id,
                    mh.condition_name,
                    mh.notes,
                    mh.record_date,
                    mh.created_at,
                    d.id AS doctor_id,
                    d.name AS doctor_name,
                    d.specialization
                FROM medical_history mh
                LEFT JOIN doctors d
                    ON mh.doctor_id = d.id
                WHERE mh.id = %s
                  AND mh.patient_id = %s
                LIMIT 1
                """,
                (
                    history_id,
                    patient_id,
                ),
            )

            history = cursor.fetchone()

    if not history:
        logger.warning(
            "Medical history record not found",
            extra={
                "event": "MEDICAL_HISTORY_NOT_FOUND",
                "patient_id": patient_id,
                "history_id": history_id,
            },
        )
        return None

    logger.info(
        "Medical history record retrieved",
        extra={
            "event": "MEDICAL_HISTORY_RECORD_RETRIEVED",
            "patient_id": patient_id,
            "history_id": history_id,
        },
    )

    return history


def get_patient_medical_images(patient_id: int):
    """
    Get medical image/report metadata belonging to a patient.

    File contents are NOT returned here.
    Only safe metadata is returned.
    """

    if not patient_id or patient_id <= 0:
        return []

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    mi.id,
                    mi.chat_session_id,
                    mi.uploaded_at
                FROM medical_images mi
                WHERE mi.patient_id = %s
                ORDER BY mi.uploaded_at DESC
                """,
                (patient_id,),
            )

            images = cursor.fetchall()

    logger.info(
        "Patient medical image metadata retrieved",
        extra={
            "event": "MEDICAL_IMAGES_RETRIEVED",
            "patient_id": patient_id,
            "count": len(images),
        },
    )

    return images


def get_medical_image(patient_id: int, image_id: int):
    """
    Get one medical image record belonging to a patient.

    The database file path is kept internal.
    """

    if not patient_id or patient_id <= 0:
        return None

    if not image_id or image_id <= 0:
        return None

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    patient_id,
                    chat_session_id,
                    file_path,
                    uploaded_at
                FROM medical_images
                WHERE id = %s
                  AND patient_id = %s
                LIMIT 1
                """,
                (
                    image_id,
                    patient_id,
                ),
            )

            image = cursor.fetchone()

    if not image:
        logger.warning(
            "Medical image not found",
            extra={
                "event": "MEDICAL_IMAGE_NOT_FOUND",
                "patient_id": patient_id,
                "image_id": image_id,
            },
        )
        return None

    logger.info(
        "Medical image record retrieved",
        extra={
            "event": "MEDICAL_IMAGE_RETRIEVED",
            "patient_id": patient_id,
            "image_id": image_id,
        },
    )

    return image


def get_secure_image_path(patient_id: int, image_id: int):
    """
    Return a validated local file path for a patient's medical image.

    Security checks:
    - Image must belong to the patient.
    - Path must remain inside uploads/.
    - Path traversal is rejected.
    - File must actually exist.
    """

    image = get_medical_image(
        patient_id=patient_id,
        image_id=image_id,
    )

    if not image:
        return None

    file_path = Path(image["file_path"])

    if not file_path.is_absolute():
        file_path = UPLOAD_DIR / file_path

    try:
        safe_path = file_path.resolve()

        safe_path.relative_to(UPLOAD_DIR)

    except ValueError:
        logger.warning(
            "Blocked unsafe medical file path",
            extra={
                "event": "UNSAFE_MEDICAL_FILE_PATH",
                "patient_id": patient_id,
                "image_id": image_id,
            },
        )
        return None

    if not safe_path.is_file():
        logger.warning(
            "Medical file does not exist",
            extra={
                "event": "MEDICAL_FILE_NOT_FOUND",
                "patient_id": patient_id,
                "image_id": image_id,
            },
        )
        return None

    return safe_path


def delete_medical_image(patient_id: int, image_id: int):
    """
    Delete a patient's medical image record and its file.

    Ownership is checked before deletion.
    """

    image = get_medical_image(
        patient_id=patient_id,
        image_id=image_id,
    )

    if not image:
        return {
            "success": False,
            "message": "Medical file not found.",
        }

    safe_path = get_secure_image_path(
        patient_id=patient_id,
        image_id=image_id,
    )

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM medical_images
                WHERE id = %s
                  AND patient_id = %s
                """,
                (
                    image_id,
                    patient_id,
                ),
            )

            deleted = cursor.rowcount

    if safe_path and safe_path.is_file():
        try:
            safe_path.unlink()
        except OSError:
            logger.exception(
                "Medical file could not be deleted from storage",
                extra={
                    "event": "MEDICAL_FILE_DELETE_FAILED",
                    "patient_id": patient_id,
                    "image_id": image_id,
                },
            )

    if deleted == 0:
        return {
            "success": False,
            "message": "Medical file could not be deleted.",
        }

    logger.info(
        "Medical image deleted",
        extra={
            "event": "MEDICAL_IMAGE_DELETED",
            "patient_id": patient_id,
            "image_id": image_id,
        },
    )

    return {
        "success": True,
        "message": "Medical file deleted successfully.",
    }