from chatbot.database.queries import (
    get_departments,
    search_departments,
    search_doctors,
    get_doctor_by_id,
    get_doctor_schedule,
)
import sys
from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)

def get_all_departments():
    try:
        return get_departments()

    except Exception as e:
        logger.error(
            f"Error fetching departments: {str(e)}"
        )
        raise CustomException(e,sys)


def find_departments(keyword):
    try:
        return search_departments(keyword)

    except Exception as e:
        logger.error(
            f"Error searching departments: {str(e)}"
        )
        raise CustomException(e,sys)


def find_doctors(keyword=None, department_id=None):
    try:
        return search_doctors(
            keyword=keyword,
            department_id=department_id
        )

    except Exception as e:
        logger.error(
            f"Error searching doctors: {str(e)}"
        )
        raise CustomException(e,sys)


def find_doctor(doctor_id):
    try:
        doctor = get_doctor_by_id(doctor_id)

        if not doctor:
            logger.info(
                f"Doctor not found. doctor_id={doctor_id}"
            )
            return None

        return doctor

    except Exception as e:
        logger.error(
            f"Error fetching doctor: {str(e)}"
        )
        raise CustomException(e,sys)


def get_schedule(doctor_id, day_of_week=None):
    try:
        return get_doctor_schedule(
            doctor_id=doctor_id,
            day_of_week=day_of_week
        )

    except Exception as e:
        logger.error(
            f"Error fetching doctor schedule: {str(e)}"
        )
        raise CustomException(e,sys)