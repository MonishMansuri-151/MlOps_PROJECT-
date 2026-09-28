from chatbot.database.queries import (
    get_patient_by_id,
    get_patient_by_phone,
    get_patient_by_email,
    get_patient_appointments,
    get_patient_medical_history,
)
import sys
from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)


def find_patient_by_id(patient_id):
    try:
        patient = get_patient_by_id(patient_id)

        if not patient:
            logger.info(
                f"Patient not found. patient_id={patient_id}"
            )
            return None

        return patient

    except Exception as e:
        logger.error(
            f"Error in find_patient_by_id: {str(e)}"
        )
        raise CustomException(e,sys)


def find_patient_by_phone(phone):
    try:
        patient = get_patient_by_phone(phone)

        if not patient:
            logger.info(
                "Patient not found using phone."
            )
            return None

        return patient

    except Exception as e:
        logger.error(
            f"Error in find_patient_by_phone: {str(e)}"
        )
        raise CustomException(e,sys)


def find_patient_by_email(email):
    try:
        patient = get_patient_by_email(email)

        if not patient:
            logger.info(
                "Patient not found using email."
            )
            return None

        return patient

    except Exception as e:
        logger.error(
            f"Error in find_patient_by_email: {str(e)}"
        )
        raise CustomException(e,sys)


def get_patient_history(patient_id):
    try:
        return get_patient_medical_history(patient_id)

    except Exception as e:
        logger.error(
            f"Error fetching patient history: {str(e)}"
        )
        raise CustomException(e,sys)


def get_patient_appointment_history(patient_id):
    try:
        return get_patient_appointments(patient_id)

    except Exception as e:
        logger.error(
            f"Error fetching patient appointments: {str(e)}"
        )
        raise CustomException(e,sys)