import sys

from chatbot.database.connection import get_connection
from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)

def load_appointment_analytics_data():
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.id AS appointment_id,
                    a.patient_id,
                    a.doctor_id,
                    a.appointment_date,
                    a.start_time,
                    d.department_id,
                    dep.name AS department_name
                FROM appointments a
                INNER JOIN doctors d
                    ON a.doctor_id = d.id
                INNER JOIN departments dep
                    ON d.department_id = dep.id
                ORDER BY a.appointment_date
                """
            )

            return cursor.fetchall()

    except Exception as e:
        logger.error(
            f"Failed to load appointment analytics data: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()