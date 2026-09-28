from datetime import date, time, datetime, timedelta
import sys
from chatbot.database.queries import (
    get_patient_appointments,
    get_doctor_schedule_for_date,
    get_booked_slots,
    check_slot_available,
    create_appointment,
)

from chatbot.database.queries import get_doctor_by_id

from src.logger import get_logger 
from src.exception import CustomException
logger = get_logger(__name__)


def get_appointments_for_patient(patient_id):
    try:
        appointments = get_patient_appointments(patient_id)

        logger.info(
            f"Appointments fetched for patient. "
            f"patient_id={patient_id}"
        )

        return appointments

    except Exception as e:
        logger.error(
            f"Error fetching appointments for patient: {str(e)}"
        )
        raise CustomException(e,sys)


def get_available_slots(doctor_id, appointment_date):
    try:
        schedules = get_doctor_schedule_for_date(
            doctor_id,
            appointment_date
        )

        if not schedules:
            logger.info(
                f"No schedule found. "
                f"doctor_id={doctor_id}, "
                f"date={appointment_date}"
            )
            return []

        booked_slots = get_booked_slots(
            doctor_id,
            appointment_date
        )

        available_slots = []

        for schedule in schedules:

            start = schedule["start_time"]
            end = schedule["end_time"]

            # MySQL TIME can be returned as datetime.timedelta
            if isinstance(start, timedelta):
                start = (datetime.min + start).time()

            if isinstance(end, timedelta):
                end = (datetime.min + end).time()

            slot_duration = schedule["slot_duration"]

            current_time = datetime.combine(
                appointment_date,
                start
            )

            end_datetime = datetime.combine(
                appointment_date,
                end
            )

            while current_time + timedelta(
                minutes=slot_duration
            ) <= end_datetime:

                slot_start = current_time.time()

                slot_end = (
                    current_time +
                    timedelta(minutes=slot_duration)
                ).time()

                is_booked = False

                for booked in booked_slots:

                    booked_start = booked["start_time"]
                    booked_end = booked["end_time"]

                    # Booked TIME may also come as timedelta
                    if isinstance(booked_start, timedelta):
                        booked_start = (
                            datetime.min + booked_start
                        ).time()

                    if isinstance(booked_end, timedelta):
                        booked_end = (
                            datetime.min + booked_end
                        ).time()

                    if (
                        slot_start < booked_end
                        and slot_end > booked_start
                    ):
                        is_booked = True
                        break

                if not is_booked:
                    available_slots.append({
                        "start_time": slot_start,
                        "end_time": slot_end
                    })

                current_time += timedelta(
                    minutes=slot_duration
                )

        logger.info(
            f"Available slots generated. "
            f"doctor_id={doctor_id}, "
            f"date={appointment_date}, "
            f"count={len(available_slots)}"
        )

        return available_slots

    except Exception as e:
        logger.error(
            f"Error generating available slots: {str(e)}"
        )
        raise CustomException(e, sys)

def book_appointment(
    patient_id,
    doctor_id,
    appointment_date,
    start_time,
    reason=None
):
    try:

        doctor = get_doctor_by_id(doctor_id)

        if not doctor:
            logger.warning(
                f"Doctor not found. doctor_id={doctor_id}"
            )
            return {
                "success": False,
                "message": "Doctor not found."
            }

        schedules = get_doctor_schedule_for_date(
            doctor_id,
            appointment_date
        )

        if not schedules:
            return {
                "success": False,
                "message": "Doctor is not available on this date."
            }

        selected_schedule = None
        for schedule in schedules:

            schedule_start = schedule["start_time"]
            schedule_end = schedule["end_time"]

            # MySQL TIME may be returned as timedelta
            if isinstance(schedule_start, timedelta):
                schedule_start = (datetime.min + schedule_start).time()

            if isinstance(schedule_end, timedelta):
                schedule_end = (datetime.min + schedule_end).time()

            if schedule_start <= start_time < schedule_end:
                selected_schedule = schedule
                break

        if not selected_schedule:
            return {
                "success": False,
                "message": "Selected time is outside doctor's schedule."
            }

        slot_duration = selected_schedule["slot_duration"]

        start_datetime = datetime.combine(
            appointment_date,
            start_time
        )

        end_datetime = (
            start_datetime +
            timedelta(minutes=slot_duration)
        )

        end_time = end_datetime.time()

        schedule_end = selected_schedule["end_time"]

        # MySQL TIME may be returned as timedelta
        if isinstance(schedule_end, timedelta):
            schedule_end = (datetime.min + schedule_end).time()

        if end_time > schedule_end:
            return {
                "success": False,
                "message": "Selected slot exceeds doctor's working hours."
            }

        available = check_slot_available(
            doctor_id,
            appointment_date,
            start_time,
            end_time
        )

        if not available:
            logger.warning(
                f"Slot already booked. "
                f"doctor_id={doctor_id}, "
                f"date={appointment_date}, "
                f"time={start_time}"
            )

            return {
                "success": False,
                "message": "This slot has already been booked."
            }

        appointment_id = create_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            department_id=doctor["department_id"],
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            reason=reason
        )

        if not appointment_id:
            return {
                "success": False,
                "message": "This slot is no longer available."
            }

        logger.info(
            f"Appointment booking successful. "
            f"appointment_id={appointment_id}"
        )

        return {
            "success": True,
            "appointment_id": appointment_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor["name"],
            "appointment_date": appointment_date,
            "start_time": start_time,
            "end_time": end_time,
            "message": "Appointment booked successfully."
        }

    except Exception as e:
        logger.error(
            f"Error booking appointment: {str(e)}"
        )
        raise CustomException(e,sys)