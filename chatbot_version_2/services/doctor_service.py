from database.connection import get_db
from src.logger import get_logger 
logger = get_logger(__name__)

def get_doctor_by_id(doctor_id: int):
    """
    Get basic information about one doctor.
    """

    if not doctor_id or doctor_id <= 0:
        logger.warning(
            "Invalid doctor ID",
            extra={
                "event": "INVALID_DOCTOR_ID",
                "doctor_id": doctor_id,
            },
        )
        return None

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    d.id,
                    d.name,
                    d.phone,
                    d.email,
                    d.specialization,
                    d.department_id,
                    dep.name AS department_name,
                    d.qualification,
                    d.experience_years,
                    d.consultation_fee,
                    d.status
                FROM doctors d
                LEFT JOIN departments dep
                    ON d.department_id = dep.id
                WHERE d.id = %s
                LIMIT 1
                """,
                (doctor_id,),
            )

            doctor = cursor.fetchone()

    if not doctor:
        logger.warning(
            "Doctor not found",
            extra={
                "event": "DOCTOR_NOT_FOUND",
                "doctor_id": doctor_id,
            },
        )
        return None

    logger.info(
        "Doctor retrieved successfully",
        extra={
            "event": "DOCTOR_RETRIEVED",
            "doctor_id": doctor_id,
        },
    )

    return doctor


def get_active_doctors():
    """
    Get all active doctors.

    Only doctors with active status are returned.
    """

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    d.id,
                    d.name,
                    d.specialization,
                    d.department_id,
                    dep.name AS department_name,
                    d.qualification,
                    d.experience_years,
                    d.consultation_fee
                FROM doctors d
                LEFT JOIN departments dep
                    ON d.department_id = dep.id
                WHERE d.status = 'active'
                ORDER BY d.name
                """
            )

            doctors = cursor.fetchall()

    logger.info(
        "Active doctors retrieved",
        extra={
            "event": "ACTIVE_DOCTORS_RETRIEVED",
            "count": len(doctors),
        },
    )

    return doctors


def get_doctors_by_department(department_id: int):
    """
    Get active doctors belonging to a department.
    """

    if not department_id or department_id <= 0:
        return []

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    d.id,
                    d.name,
                    d.specialization,
                    d.department_id,
                    dep.name AS department_name,
                    d.qualification,
                    d.experience_years,
                    d.consultation_fee
                FROM doctors d
                INNER JOIN departments dep
                    ON d.department_id = dep.id
                WHERE d.department_id = %s
                  AND d.status = 'active'
                ORDER BY d.name
                """,
                (department_id,),
            )

            doctors = cursor.fetchall()

    logger.info(
        "Doctors retrieved by department",
        extra={
            "event": "DOCTORS_BY_DEPARTMENT_RETRIEVED",
            "department_id": department_id,
            "count": len(doctors),
        },
    )

    return doctors