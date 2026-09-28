from chatbot.database.connection import get_connection
from src.logger import get_logger 
from src.exception import CustomException 
import sys
logger = get_logger(__name__)

# ============================================================
# PATIENT QUERIES
# ============================================================

def get_patient_by_id(patient_id):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    name,
                    phone,
                    email,
                    dob,
                    gender,
                    address,
                    created_at
                FROM patients
                WHERE id = %s
            """

            cursor.execute(query, (patient_id,))
            result = cursor.fetchone()

            logger.info(
                f"Patient fetched successfully. patient_id={patient_id}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching patient. patient_id={patient_id}, error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


def get_patient_by_phone(phone):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    name,
                    phone,
                    email,
                    password_hash,
                    role,
                    dob,
                    gender,
                    address,
                    created_at
                FROM patients
                WHERE phone = %s
            """

            cursor.execute(query, (phone,))
            result = cursor.fetchone()

            logger.info(
                f"Patient fetched using phone. phone={phone}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching patient by phone. error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


def get_patient_by_email(email):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    name,
                    phone,
                    email,
                    password_hash,
                    role,
                    dob,
                    gender,
                    address,
                    created_at
                FROM patients
                WHERE email = %s
            """

            cursor.execute(query, (email,))
            result = cursor.fetchone()

            logger.info(
                f"Patient fetched using email. email={email}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching patient by email. error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()

def create_patient(
    name: str,
    phone: str,
    email: str,
    password_hash: str,
    dob=None,
    gender=None,
    address=None,
):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO patients
                (
                    name,
                    phone,
                    email,
                    password_hash,
                    dob,
                    gender,
                    address,
                    role
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'user'
                )
                """,
                (
                    name,
                    phone,
                    email,
                    password_hash,
                    dob,
                    gender,
                    address,
                ),
            )

        connection.commit()

        return {
            "success": True,
            "message": "Patient registered successfully."
        }

    except Exception as e:
        if connection:
            connection.rollback()

        logger.error(f"Failed to create patient: {e}")
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()
# ============================================================
# DEPARTMENT QUERIES
# ============================================================

def get_departments():
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    name,
                    description
                FROM departments
                WHERE status = 'active'
                ORDER BY name
            """

            cursor.execute(query)
            result = cursor.fetchall()

            logger.info(
                f"Active departments fetched successfully. count={len(result)}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching departments. error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


def search_departments(keyword):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    name,
                    description
                FROM departments
                WHERE status = 'active'
                AND (
                    name LIKE %s
                    OR description LIKE %s
                )
                ORDER BY name
            """

            search_value = f"%{keyword}%"

            cursor.execute(
                query,
                (search_value, search_value)
            )

            result = cursor.fetchall()

            logger.info(
                f"Department search completed. keyword={keyword}, "
                f"count={len(result)}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error searching departments. "
            f"keyword={keyword}, error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


# ============================================================
# DOCTOR QUERIES
# ============================================================

def search_doctors(keyword=None, department_id=None):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            query = """
                SELECT
                    d.id,
                    d.name,
                    d.specialization,
                    d.qualification,
                    d.experience_years,
                    d.consultation_fee,
                    d.phone,
                    d.email,
                    dep.id AS department_id,
                    dep.name AS department_name
                FROM doctors d
                INNER JOIN departments dep
                    ON d.department_id = dep.id
                WHERE d.status = 'active'
                AND dep.status = 'active'
            """

            params = []

            if keyword:
                query += """
                    AND (
                        d.name LIKE %s
                        OR d.specialization LIKE %s
                        OR dep.name LIKE %s
                    )
                """

                search_value = f"%{keyword}%"

                params.extend([
                    search_value,
                    search_value,
                    search_value
                ])

            if department_id:
                query += """
                    AND d.department_id = %s
                """

                params.append(department_id)

            query += """
                ORDER BY d.name
            """

            cursor.execute(query, tuple(params))

            result = cursor.fetchall()

            logger.info(
                f"Doctor search completed. "
                f"keyword={keyword}, "
                f"department_id={department_id}, "
                f"count={len(result)}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error searching doctors. "
            f"keyword={keyword}, "
            f"department_id={department_id}, "
            f"error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


def get_doctor_by_id(doctor_id):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    d.id,
                    d.name,
                    d.specialization,
                    d.qualification,
                    d.experience_years,
                    d.consultation_fee,
                    d.phone,
                    d.email,
                    dep.id AS department_id,
                    dep.name AS department_name
                FROM doctors d
                INNER JOIN departments dep
                    ON d.department_id = dep.id
                WHERE d.id = %s
                AND d.status = 'active'
            """

            cursor.execute(query, (doctor_id,))
            result = cursor.fetchone()

            logger.info(
                f"Doctor fetched successfully. doctor_id={doctor_id}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching doctor. "
            f"doctor_id={doctor_id}, error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


# ============================================================
# DOCTOR SCHEDULE QUERIES
# ============================================================

def get_doctor_schedule(doctor_id, day_of_week=None):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            query = """
                SELECT
                    id,
                    doctor_id,
                    day_of_week,
                    start_time,
                    end_time,
                    slot_duration
                FROM doctor_schedules
                WHERE doctor_id = %s
                AND status = 'active'
            """

            params = [doctor_id]

            if day_of_week:
                query += """
                    AND day_of_week = %s
                """

                params.append(day_of_week)

            query += """
                ORDER BY start_time
            """

            cursor.execute(query, tuple(params))

            result = cursor.fetchall()

            logger.info(
                f"Doctor schedule fetched. "
                f"doctor_id={doctor_id}, "
                f"day={day_of_week}, "
                f"count={len(result)}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching doctor schedule. "
            f"doctor_id={doctor_id}, "
            f"day={day_of_week}, "
            f"error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


# ============================================================
# APPOINTMENT QUERIES
# ============================================================

def get_patient_appointments(patient_id):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    a.id,
                    a.appointment_date,
                    a.start_time,
                    a.end_time,
                    a.status,
                    a.reason,

                    d.id AS doctor_id,
                    d.name AS doctor_name,
                    d.specialization,

                    dep.id AS department_id,
                    dep.name AS department_name

                FROM appointments a

                INNER JOIN doctors d
                    ON a.doctor_id = d.id

                INNER JOIN departments dep
                    ON a.department_id = dep.id

                WHERE a.patient_id = %s

                ORDER BY
                    a.appointment_date DESC,
                    a.start_time DESC
            """

            cursor.execute(query, (patient_id,))
            result = cursor.fetchall()

            logger.info(
                f"Patient appointments fetched. "
                f"patient_id={patient_id}, count={len(result)}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching patient appointments. "
            f"patient_id={patient_id}, error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


# ============================================================
# MEDICAL HISTORY QUERIES
# ============================================================

def get_patient_medical_history(patient_id):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    mh.id,
                    mh.condition_name,
                    mh.notes,
                    mh.record_date,

                    d.id AS doctor_id,
                    d.name AS doctor_name,
                    d.specialization

                FROM medical_history mh

                LEFT JOIN doctors d
                    ON mh.doctor_id = d.id

                WHERE mh.patient_id = %s

                ORDER BY mh.record_date DESC
            """

            cursor.execute(query, (patient_id,))
            result = cursor.fetchall()

            logger.info(
                f"Medical history fetched. "
                f"patient_id={patient_id}, count={len(result)}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching medical history. "
            f"patient_id={patient_id}, error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()
            
            
from datetime import datetime, timedelta


# ============================================================
# APPOINTMENT / SLOT QUERIES
# ============================================================

def get_doctor_schedule_for_date(doctor_id, appointment_date):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    doctor_id,
                    day_of_week,
                    start_time,
                    end_time,
                    slot_duration
                FROM doctor_schedules
                WHERE doctor_id = %s
                AND day_of_week = DAYNAME(%s)
                AND status = 'active'
            """

            cursor.execute(
                query,
                (doctor_id, appointment_date)
            )

            result = cursor.fetchall()

            logger.info(
                f"Doctor schedule fetched for date. "
                f"doctor_id={doctor_id}, "
                f"date={appointment_date}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching schedule for date. "
            f"doctor_id={doctor_id}, "
            f"date={appointment_date}, "
            f"error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


def get_booked_slots(doctor_id, appointment_date):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    start_time,
                    end_time
                FROM appointments
                WHERE doctor_id = %s
                AND appointment_date = %s
                AND status IN ('booked', 'confirmed')
            """

            cursor.execute(
                query,
                (doctor_id, appointment_date)
            )

            result = cursor.fetchall()

            logger.info(
                f"Booked slots fetched. "
                f"doctor_id={doctor_id}, "
                f"date={appointment_date}, "
                f"count={len(result)}"
            )

            return result

    except Exception as e:
        logger.error(
            f"Error fetching booked slots. "
            f"doctor_id={doctor_id}, "
            f"date={appointment_date}, "
            f"error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


def check_slot_available(
    doctor_id,
    appointment_date,
    start_time,
    end_time
):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT id
                FROM appointments
                WHERE doctor_id = %s
                AND appointment_date = %s
                AND status IN ('booked', 'confirmed')
                AND start_time < %s
                AND end_time > %s
                LIMIT 1
            """

            cursor.execute(
                query,
                (
                    doctor_id,
                    appointment_date,
                    end_time,
                    start_time
                )
            )

            result = cursor.fetchone()

            return result is None

    except Exception as e:
        logger.error(
            f"Error checking appointment slot. "
            f"doctor_id={doctor_id}, "
            f"date={appointment_date}, "
            f"error={str(e)}"
        )
        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()


def create_appointment(
    patient_id,
    doctor_id,
    department_id,
    appointment_date,
    start_time,
    end_time,
    reason=None
):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            # Re-check slot inside the same transaction.
            # This is important for preventing double booking.
            check_query = """
                SELECT id
                FROM appointments
                WHERE doctor_id = %s
                AND appointment_date = %s
                AND status IN ('booked', 'confirmed')
                AND start_time < %s
                AND end_time > %s
                LIMIT 1
                FOR UPDATE
            """

            cursor.execute(
                check_query,
                (
                    doctor_id,
                    appointment_date,
                    end_time,
                    start_time
                )
            )

            existing = cursor.fetchone()

            if existing:
                connection.rollback()

                logger.warning(
                    f"Appointment slot already booked. "
                    f"doctor_id={doctor_id}, "
                    f"date={appointment_date}, "
                    f"start={start_time}"
                )

                return None

            insert_query = """
                INSERT INTO appointments (
                    patient_id,
                    doctor_id,
                    department_id,
                    appointment_date,
                    start_time,
                    end_time,
                    status,
                    reason
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'booked',
                    %s
                )
            """

            cursor.execute(
                insert_query,
                (
                    patient_id,
                    doctor_id,
                    department_id,
                    appointment_date,
                    start_time,
                    end_time,
                    reason
                )
            )

            appointment_id = cursor.lastrowid

        connection.commit()

        logger.info(
            f"Appointment created successfully. "
            f"appointment_id={appointment_id}, "
            f"patient_id={patient_id}, "
            f"doctor_id={doctor_id}"
        )

        return appointment_id

    except Exception as e:
        if connection:
            connection.rollback()

        logger.error(
            f"Error creating appointment. "
            f"patient_id={patient_id}, "
            f"doctor_id={doctor_id}, "
            f"error={str(e)}"
        )

        raise CustomException(e,sys)

    finally:
        if connection:
            connection.close()
            
def create_chat_session(patient_id: int) -> int:
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                INSERT INTO chat_sessions (patient_id)
                VALUES (%s)
            """

            cursor.execute(query, (patient_id,))
            session_id = cursor.lastrowid

        connection.commit()

        logger.info(
            f"Chat session created: session_id={session_id}, "
            f"patient_id={patient_id}"
        )

        return session_id

    except Exception as e:
        if connection:
            connection.rollback()

        logger.error(
            f"Failed to create chat session: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()


def add_chat_message(
    session_id: int,
    role: str,
    message: str
) -> bool:
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                INSERT INTO chat_messages (
                    session_id,
                    role,
                    message
                )
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    session_id,
                    role,
                    message
                )
            )

            update_session_query = """
                UPDATE chat_sessions
                SET ended_at = NULL
                WHERE id = %s
            """

            # cursor.execute(
            #     update_session_query,
            #     (session_id,)
            # )
            cursor.execute(
                """
                UPDATE chat_sessions
                SET ended_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (session_id,)
            )

        connection.commit()

        logger.info(
            f"Chat message saved: session_id={session_id}, "
            f"role={role}"
        )

        return True

    except Exception as e:
        if connection:
            connection.rollback()

        logger.error(
            f"Failed to save chat message: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()


def get_chat_sessions(patient_id: int) -> list:
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    patient_id,
                    started_at,
                    ended_at
                FROM chat_sessions
                WHERE patient_id = %s
                ORDER BY started_at DESC
            """

            cursor.execute(query, (patient_id,))
            sessions = cursor.fetchall()

        return sessions

    except Exception as e:
        logger.error(
            f"Failed to fetch chat sessions: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()


def get_chat_messages(
    session_id: int,
    patient_id: int
) -> list:
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    cm.id,
                    cm.session_id,
                    cm.role,
                    cm.message,
                    cm.created_at
                FROM chat_messages cm
                INNER JOIN chat_sessions cs
                    ON cm.session_id = cs.id
                WHERE
                    cm.session_id = %s
                    AND cs.patient_id = %s
                ORDER BY cm.created_at ASC
            """

            cursor.execute(
                query,
                (
                    session_id,
                    patient_id
                )
            )

            messages = cursor.fetchall()

        return messages

    except Exception as e:
        logger.error(
            f"Failed to fetch chat messages: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()


def delete_chat_session(
    session_id: int,
    patient_id: int
) -> bool:
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            # Security check:
            # session must belong to authenticated patient
            check_query = """
                SELECT id
                FROM chat_sessions
                WHERE
                    id = %s
                    AND patient_id = %s
            """

            cursor.execute(
                check_query,
                (
                    session_id,
                    patient_id
                )
            )

            session = cursor.fetchone()

            if not session:
                connection.rollback()

                logger.warning(
                    f"Unauthorized chat deletion attempt: "
                    f"session_id={session_id}, "
                    f"patient_id={patient_id}"
                )

                return False

            delete_messages_query = """
                DELETE FROM chat_messages
                WHERE session_id = %s
            """

            cursor.execute(
                delete_messages_query,
                (session_id,)
            )

            delete_session_query = """
                DELETE FROM chat_sessions
                WHERE
                    id = %s
                    AND patient_id = %s
            """

            cursor.execute(
                delete_session_query,
                (
                    session_id,
                    patient_id
                )
            )

        connection.commit()

        logger.info(
            f"Chat session deleted: session_id={session_id}, "
            f"patient_id={patient_id}"
        )

        return True

    except Exception as e:
        if connection:
            connection.rollback()

        logger.error(
            f"Failed to delete chat session: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()

def delete_expired_chat_sessions(retention_days: int = 20) -> int:
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM chat_sessions
                WHERE COALESCE(ended_at, started_at)
                      < NOW() - INTERVAL %s DAY
                """,
                (retention_days,)
            )

            sessions = cursor.fetchall()

            deleted_count = 0

            for session in sessions:
                session_id = session["id"]

                cursor.execute(
                    """
                    DELETE FROM chat_messages
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )

                cursor.execute(
                    """
                    DELETE FROM chat_sessions
                    WHERE id = %s
                    """,
                    (session_id,)
                )

                deleted_count += 1

            connection.commit()

            logger.info(
                f"Deleted {deleted_count} expired chat sessions."
            )

            return deleted_count

    except Exception as e:
        if connection:
            connection.rollback()

        logger.error(
            f"Failed to delete expired chat sessions: {e}"
        )

        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()
            
def get_medical_file_by_id(
    file_id: int,
    patient_id: int
):
    connection = None

    try:
        connection = get_connection()

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
                """,
                (
                    file_id,
                    patient_id
                )
            )

            return cursor.fetchone()

    except Exception as e:
        logger.error(
            f"Failed to fetch medical file: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()
            
def get_admin_by_email(email: str):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    password,
                    role
                FROM admin_users
                WHERE email = %s
                """,
                (email,)
            )

            return cursor.fetchone()

    except Exception as e:
        logger.error(
            f"Failed to fetch admin by email: {e}"
        )
        raise CustomException(e, sys)

    finally:
        if connection:
            connection.close()