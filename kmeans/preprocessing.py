import sys

from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)

def prepare_appointment_data(rows):
    try:
        if not rows:
            return []

        processed_data = []

        for row in rows:
            processed_data.append(
                {
                    "appointment_id": row["appointment_id"],
                    "patient_id": row["patient_id"],
                    "doctor_id": row["doctor_id"],
                    "department_id": row["department_id"],
                    "department_name": row["department_name"],
                }
            )

        logger.info(
            f"Prepared {len(processed_data)} appointment records."
        )

        return processed_data

    except Exception as e:
        logger.error(
            f"Appointment data preprocessing failed: {e}"
        )
        raise CustomException(e, sys)