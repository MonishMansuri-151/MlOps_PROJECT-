from datetime import date, datetime, time, timedelta

from database.connection import get_db
from src.logger import get_logger 
logger = get_logger(__name__)

def get_available_slots(doctor_id: int, appointment_date: date):
    """
    Get available appointment slots for a doctor on a specific date.

    Checks:
    - Doctor must be active.
    - Doctor must have an active schedule.
    - Already booked/confirmed appointments are excluded.
    """

    if not doctor_id or doctor_id <= 0:
        logger.warning(
            "Invalid doctor ID for availability",
            extra={
                "event": "INVALID_DOCTOR_ID",
                "doctor_id": doctor_id,
            },
        )
        return []

    if not appointment_date:
        return []

    day_name = appointment_date.strftime("%A")

    with get_db() as connection:
        with connection.cursor() as cursor:

            # Check doctor status
            cursor.execute(
                """
                SELECT id
                FROM doctors
                WHERE id = %s
                  AND status = 'active'
                LIMIT 1
                """,
                (doctor_id,),
            )

            doctor = cursor.fetchone()

            if not doctor:
                return []

            # Get active schedules for that day
            cursor.execute(
                """
                SELECT
                    start_time,
                    end_time,
                    slot_duration
                FROM doctor_schedules
                WHERE doctor_id = %s
                  AND day_of_week = %s
                  AND status = 'active'
                ORDER BY start_time
                """,
                (doctor_id, day_name),
            )

            schedules = cursor.fetchall()

            if not schedules:
                return []

            # Get already occupied appointments
            cursor.execute(
                """
                SELECT
                    start_time,
                    end_time
                FROM appointments
                WHERE doctor_id = %s
                  AND appointment_date = %s
                  AND status IN ('booked', 'confirmed')
                ORDER BY start_time
                """,
                (doctor_id, appointment_date),
            )

            booked_appointments = cursor.fetchall()

    available_slots = []

    for schedule in schedules:
        schedule_start = schedule["start_time"]
        schedule_end = schedule["end_time"]
        slot_duration = schedule["slot_duration"]

        if not slot_duration or slot_duration <= 0:
            continue

        current_start = schedule_start

        while True:
            current_end = (
                datetime.combine(date.today(), current_start)
                + timedelta(minutes=slot_duration)
            ).time()

            if current_end > schedule_end:
                break

            slot_available = True

            for appointment in booked_appointments:
                booked_start = appointment["start_time"]
                booked_end = appointment["end_time"]

                # Overlap condition
                if (
                    current_start < booked_end
                    and current_end > booked_start
                ):
                    slot_available = False
                    break

            if slot_available:
                available_slots.append(
                    {
                        "start_time": current_start.strftime("%H:%M:%S"),
                        "end_time": current_end.strftime("%H:%M:%S"),
                    }
                )

            current_start = current_end

    logger.info(
        "Doctor availability retrieved",
        extra={
            "event": "DOCTOR_AVAILABILITY_RETRIEVED",
            "doctor_id": doctor_id,
            "appointment_date": str(appointment_date),
            "count": len(available_slots),
        },
    )

    return available_slots


def book_appointment(
    patient_id: int,
    doctor_id: int,
    department_id: int,
    appointment_date: date,
    start_time: time,
    end_time: time,
    reason: str | None = None,
):
    """
    Book an appointment after validating patient, doctor,
    department, schedule and appointment conflicts.

    The doctor row is locked during booking so that two
    simultaneous booking requests cannot create the same slot.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not doctor_id or doctor_id <= 0:
        return {
            "success": False,
            "message": "Invalid doctor.",
        }

    if not department_id or department_id <= 0:
        return {
            "success": False,
            "message": "Invalid department.",
        }

    if not appointment_date or not start_time or not end_time:
        return {
            "success": False,
            "message": "Appointment date and time are required.",
        }

    if end_time <= start_time:
        return {
            "success": False,
            "message": "Appointment end time must be after start time.",
        }

    day_name = appointment_date.strftime("%A")

    with get_db() as connection:
        with connection.cursor() as cursor:

            # Lock doctor row to serialize bookings for this doctor.
            cursor.execute(
                """
                SELECT
                    id,
                    department_id,
                    status
                FROM doctors
                WHERE id = %s
                FOR UPDATE
                """,
                (doctor_id,),
            )

            doctor = cursor.fetchone()

            if not doctor:
                return {
                    "success": False,
                    "message": "Doctor not found.",
                }

            if doctor["status"] != "active":
                return {
                    "success": False,
                    "message": "Doctor is not available.",
                }

            # Verify doctor belongs to selected department.
            if doctor["department_id"] != department_id:
                return {
                    "success": False,
                    "message": "Doctor does not belong to this department.",
                }

            # Verify department is active.
            cursor.execute(
                """
                SELECT id
                FROM departments
                WHERE id = %s
                  AND status = 'active'
                LIMIT 1
                """,
                (department_id,),
            )

            department = cursor.fetchone()

            if not department:
                return {
                    "success": False,
                    "message": "Department is not available.",
                }

            # Verify patient exists.
            cursor.execute(
                """
                SELECT id
                FROM patients
                WHERE id = %s
                LIMIT 1
                """,
                (patient_id,),
            )

            patient = cursor.fetchone()

            if not patient:
                return {
                    "success": False,
                    "message": "Patient not found.",
                }

            # Find doctor's schedule for the requested day.
            cursor.execute(
                """
                SELECT
                    start_time,
                    end_time,
                    slot_duration
                FROM doctor_schedules
                WHERE doctor_id = %s
                  AND day_of_week = %s
                  AND status = 'active'
                ORDER BY start_time
                """,
                (doctor_id, day_name),
            )

            schedules = cursor.fetchall()

            if not schedules:
                return {
                    "success": False,
                    "message": "Doctor is not scheduled on this day.",
                }

            valid_schedule = None

            for schedule in schedules:

                schedule_start = schedule["start_time"]
                schedule_end = schedule["end_time"]
                slot_duration = schedule["slot_duration"]

                if (
                    start_time >= schedule_start
                    and end_time <= schedule_end
                ):
                    requested_minutes = (
                        datetime.combine(date.today(), end_time)
                        - datetime.combine(date.today(), start_time)
                    ).total_seconds() / 60

                    if requested_minutes == slot_duration:
                        valid_schedule = schedule
                        break

            if not valid_schedule:
                return {
                    "success": False,
                    "message": "Requested time is outside the doctor's schedule.",
                }

            # Make sure the requested start time follows the slot interval.
            schedule_start = valid_schedule["start_time"]
            slot_duration = valid_schedule["slot_duration"]

            minutes_from_start = (
                datetime.combine(date.today(), start_time)
                - datetime.combine(date.today(), schedule_start)
            ).total_seconds() / 60

            if minutes_from_start % slot_duration != 0:
                return {
                    "success": False,
                    "message": "Requested time does not match the doctor's slot timing.",
                }

            # Check conflicting appointments.
            cursor.execute(
                """
                SELECT
                    id
                FROM appointments
                WHERE doctor_id = %s
                  AND appointment_date = %s
                  AND status IN ('booked', 'confirmed')
                  AND start_time < %s
                  AND end_time > %s
                LIMIT 1
                """,
                (
                    doctor_id,
                    appointment_date,
                    end_time,
                    start_time,
                ),
            )

            conflict = cursor.fetchone()

            if conflict:
                return {
                    "success": False,
                    "message": "This appointment slot is already booked.",
                }

            # Create appointment.
            cursor.execute(
                """
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
                """,
                (
                    patient_id,
                    doctor_id,
                    department_id,
                    appointment_date,
                    start_time,
                    end_time,
                    reason,
                ),
            )

            appointment_id = cursor.lastrowid

    logger.info(
        "Appointment booked successfully",
        extra={
            "event": "APPOINTMENT_BOOKED",
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department_id,
        },
    )

    return {
        "success": True,
        "appointment_id": appointment_id,
        "message": "Appointment booked successfully.",
    }


def get_patient_appointments(patient_id: int):
    """
    Get appointments belonging to a specific patient.
    """

    if not patient_id or patient_id <= 0:
        return []

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
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
                """,
                (patient_id,),
            )

            appointments = cursor.fetchall()

    logger.info(
        "Patient appointments retrieved",
        extra={
            "event": "PATIENT_APPOINTMENTS_RETRIEVED",
            "patient_id": patient_id,
            "count": len(appointments),
        },
    )

    return appointments


def cancel_appointment(patient_id: int, appointment_id: int):
    """
    Cancel an appointment belonging to the patient.

    Only booked or confirmed appointments can be cancelled.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not appointment_id or appointment_id <= 0:
        return {
            "success": False,
            "message": "Invalid appointment.",
        }

    with get_db() as connection:
        with connection.cursor() as cursor:

            # Lock appointment row before changing it.
            cursor.execute(
                """
                SELECT
                    id,
                    patient_id,
                    status
                FROM appointments
                WHERE id = %s
                FOR UPDATE
                """,
                (appointment_id,),
            )

            appointment = cursor.fetchone()

            if not appointment:
                return {
                    "success": False,
                    "message": "Appointment not found.",
                }

            # Patient can only cancel their own appointment.
            if appointment["patient_id"] != patient_id:
                logger.warning(
                    "Unauthorized appointment cancellation attempt",
                    extra={
                        "event": "UNAUTHORIZED_APPOINTMENT_CANCEL",
                        "patient_id": patient_id,
                        "appointment_id": appointment_id,
                    },
                )

                return {
                    "success": False,
                    "message": "You are not allowed to cancel this appointment.",
                }

            if appointment["status"] not in ("booked", "confirmed"):
                return {
                    "success": False,
                    "message": "This appointment cannot be cancelled.",
                }

            cursor.execute(
                """
                UPDATE appointments
                SET status = 'cancelled'
                WHERE id = %s
                """,
                (appointment_id,),
            )

    logger.info(
        "Appointment cancelled successfully",
        extra={
            "event": "APPOINTMENT_CANCELLED",
            "appointment_id": appointment_id,
            "patient_id": patient_id,
        },
    )

    return {
        "success": True,
        "message": "Appointment cancelled successfully.",
    }