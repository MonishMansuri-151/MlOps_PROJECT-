import sys
from datetime import date, datetime, timedelta
from fastapi import Request

from chatbot.ai.llm_service import llm_service
from chatbot.auth.session import get_current_user
from chatbot.services.appointment_service import (
    get_available_slots,
    book_appointment,
)
from chatbot.services.doctor_service import (
    find_departments,
    find_doctors,
)
from chatbot.services.chat_history_service import (
    create_session,
    save_message,
)

from src.logger import get_logger
from src.exception import CustomException


logger = get_logger(__name__)


def _get_or_create_chat_session(request: Request, patient_id: int) -> int:
    """
    Get current chatbot session from temporary web session.
    Create one if it does not exist.
    """

    session_id = request.session.get("chat_session_id")

    if session_id:
        return session_id

    session_id = create_session(patient_id)

    request.session["chat_session_id"] = session_id

    logger.info(
        f"Chat session attached to user: "
        f"patient_id={patient_id}, "
        f"session_id={session_id}"
    )

    return session_id


def _extract_time_from_message(user_message: str):
    """
    Extract simple time formats:
    10:30
    10.30
    10 30
    """

    import re

    match = re.search(
        r"\b([01]?\d|2[0-3])(?:[:.]([0-5]\d)|\s([0-5]\d))\b",
        user_message
    )

    if not match:
        return None

    hour = int(match.group(1))

    minute = (
        match.group(2)
        or match.group(3)
        or "00"
    )

    return datetime.strptime(
        f"{hour}:{minute}",
        "%H:%M"
    ).time()


def process_chat_message(
    user_message: str,
    request: Request
) -> dict:

    try:
        if not user_message or not user_message.strip():
            return {
                "success": False,
                "message": "Please describe your health concern."
            }

        # -------------------------------------------------
        # 1. Authentication
        # -------------------------------------------------

        user = get_current_user(request)

        if not user:
            return {
                "success": False,
                "message": "Please login before using the chatbot."
            }

        patient_id = user["id"]

        message = user_message.strip()

        # -------------------------------------------------
        # 2. Get/Create chat session
        # -------------------------------------------------

        session_id = _get_or_create_chat_session(
            request=request,
            patient_id=patient_id
        )

        # -------------------------------------------------
        # 3. Save USER message
        # -------------------------------------------------

        save_message(
            session_id=session_id,
            role="user",
            message=message
        )

        # -------------------------------------------------
        # 4. Booking context
        # -------------------------------------------------

        booking_context = request.session.get(
            "booking_context"
        )

        # -------------------------------------------------
        # 5. Handle booking confirmation
        # -------------------------------------------------

        confirmation_words = {
            "yes",
            "yes please",
            "haan",
            "ha",
            "haan ji",
            "confirm",
            "book it",
            "book",
            "kar do",
            "confirm it"
        }

        cancel_words = {
            "no",
            "cancel",
            "nahi",
            "nahin",
            "don't book",
            "dont book"
        }

        normalized_message = message.lower().strip()

        if (
            booking_context
            and booking_context.get("status")
            == "awaiting_confirmation"
        ):

            # -----------------------------
            # Cancel booking
            # -----------------------------

            if normalized_message in cancel_words:

                request.session.pop(
                    "booking_context",
                    None
                )

                response = (
                    "Okay, appointment booking cancelled."
                )

                save_message(
                    session_id=session_id,
                    role="assistant",
                    message=response
                )

                return {
                    "success": True,
                    "session_id": session_id,
                    "message": response
                }

            # -----------------------------
            # Confirm booking
            # -----------------------------

            if normalized_message in confirmation_words:

                appointment_date = datetime.strptime(
                    booking_context["appointment_date"],
                    "%Y-%m-%d"
                ).date()

                start_time = datetime.strptime(
                    booking_context["start_time"],
                    "%H:%M:%S"
                ).time()

                booking_result = book_appointment(
                    patient_id=patient_id,
                    doctor_id=booking_context["doctor_id"],
                    appointment_date=appointment_date,
                    start_time=start_time,
                    reason=booking_context.get("reason")
                )

                if booking_result["success"]:

                    request.session.pop(
                        "booking_context",
                        None
                    )

                    response = (
                        f"Appointment booked successfully with "
                        f"{booking_result['doctor_name']} on "
                        f"{booking_result['appointment_date']} "
                        f"at {booking_result['start_time']}."
                    )

                    save_message(
                        session_id=session_id,
                        role="assistant",
                        message=response
                    )

                    return {
                        "success": True,
                        "session_id": session_id,
                        "message": response,
                        "appointment": booking_result
                    }

                response = booking_result["message"]

                save_message(
                    session_id=session_id,
                    role="assistant",
                    message=response
                )

                return {
                    "success": False,
                    "session_id": session_id,
                    "message": response
                }

        # -------------------------------------------------
        # 6. Handle time selection
        # -------------------------------------------------

        if booking_context:

            selected_time = _extract_time_from_message(
                message
            )

            if selected_time:

                available_slots = get_available_slots(
                    doctor_id=booking_context["doctor_id"],
                    appointment_date=date.today()
                )

                selected_slot = None

                for slot in available_slots:

                    slot_start = slot["start_time"]

                    if isinstance(slot_start, str):
                        slot_start = datetime.strptime(
                            slot_start,
                            "%H:%M:%S"
                        ).time()

                    if slot_start == selected_time:
                        selected_slot = slot
                        break

                if selected_slot:

                    start_time = selected_slot["start_time"]
                    end_time = selected_slot["end_time"]

                    if isinstance(start_time, str):
                        start_time = datetime.strptime(
                            start_time,
                            "%H:%M:%S"
                        ).time()

                    if isinstance(end_time, str):
                        end_time = datetime.strptime(
                            end_time,
                            "%H:%M:%S"
                        ).time()

                    request.session["booking_context"] = {
                        "doctor_id": booking_context["doctor_id"],
                        "doctor_name": booking_context["doctor_name"],
                        "appointment_date": date.today().isoformat(),
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "reason": booking_context.get("reason"),
                        "status": "awaiting_confirmation"
                    }

                    response = (
                        f"Dr. {booking_context['doctor_name']} "
                        f"is available at "
                        f"{start_time.strftime('%I:%M %p')}. "
                        f"Would you like me to confirm this appointment?"
                    )

                    save_message(
                        session_id=session_id,
                        role="assistant",
                        message=response
                    )

                    return {
                        "success": True,
                        "session_id": session_id,
                        "message": response,
                        "booking_context": request.session[
                            "booking_context"
                        ]
                    }

        # -------------------------------------------------
        # 7. Normal medical conversation
        # -------------------------------------------------

        response = llm_service.generate_response(
            message
        )

        department_name = (
            llm_service.detect_department(
                message
            )
        )

        departments = find_departments(
            department_name
        )

        doctors = []

        if departments:

            department_id = departments[0]["id"]

            doctors = find_doctors(
                department_id=department_id
            )

        slots = []

        if doctors:

            doctor_id = doctors[0]["id"]

            slots = get_available_slots(
                doctor_id=doctor_id,
                appointment_date=date.today()
            )

        # -------------------------------------------------
        # 8. Save ASSISTANT message
        # -------------------------------------------------

        save_message(
            session_id=session_id,
            role="assistant",
            message=response
        )

        # -------------------------------------------------
        # 9. Store temporary booking context
        # -------------------------------------------------

        if doctors:

            request.session["booking_context"] = {
                "doctor_id": doctors[0]["id"],
                "doctor_name": doctors[0]["name"],
                "appointment_date": date.today().isoformat(),
                "reason": message,
                "status": "selecting_slot"
            }

        logger.info(
            f"Chat processed and saved: "
            f"patient_id={patient_id}, "
            f"session_id={session_id}, "
            f"department={department_name}"
        )

        return {
            "success": True,
            "session_id": session_id,
            "message": response,
            "detected_department": department_name,
            "departments": departments,
            "doctors": doctors,
            "slots": slots
        }

    except Exception as e:

        logger.error(
            f"Error processing chat message: {e}"
        )

        raise CustomException(e, sys)
