from database.connection import get_db
from src.logger import get_logger 
logger = get_logger(__name__)

def get_patient_by_id(patient_id: int):
    """
    Get basic information of one patient.

    Password hash is never selected here.
    """

    if not patient_id or patient_id <= 0:
        logger.warning(
            "Invalid patient ID",
            extra={
                "event": "INVALID_PATIENT_ID",
                "patient_id": patient_id,
            },
        )
        return None

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    phone,
                    email,
                    dob,
                    gender,
                    address,
                    role,
                    created_at,
                    updated_at
                FROM patients
                WHERE id = %s
                LIMIT 1
                """,
                (patient_id,),
            )

            patient = cursor.fetchone()

    if not patient:
        logger.warning(
            "Patient not found",
            extra={
                "event": "PATIENT_NOT_FOUND",
                "patient_id": patient_id,
            },
        )
        return None

    logger.info(
        "Patient retrieved successfully",
        extra={
            "event": "PATIENT_RETRIEVED",
            "patient_id": patient_id,
        },
    )

    return patient


def patient_exists(patient_id: int) -> bool:
    """
    Check whether a patient exists.
    """

    if not patient_id or patient_id <= 0:
        return False

    with get_db() as connection:
        with connection.cursor() as cursor:

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

    return patient is not None
# from datetime import date

# from database.connection import get_db
# from src.logger import get_logger 
# logger = get_logger(__name__)

# ALLOWED_PROFILE_FIELDS = {
#     "name",
#     "phone",
#     "email",
#     "dob",
#     "gender",
#     "address",
# }


# def _sanitize_patient(patient):
#     """
#     Return only fields that are safe for normal application use.

#     Password/hash fields are intentionally never selected from the database.
#     """

#     if not patient:
#         return None

#     return {
#         "id": patient["id"],
#         "name": patient["name"],
#         "phone": patient["phone"],
#         "email": patient["email"],
#         "dob": patient["dob"],
#         "gender": patient["gender"],
#         "address": patient["address"],
#         "role": patient["role"],
#         "created_at": patient["created_at"],
#         "updated_at": patient["updated_at"],
#     }


# def patient_exists(patient_id: int) -> bool:
#     """
#     Check whether a patient exists.
#     """

#     if not isinstance(patient_id, int) or patient_id <= 0:
#         return False

#     with get_db() as connection:
#         with connection.cursor() as cursor:
#             cursor.execute(
#                 """
#                 SELECT id
#                 FROM patients
#                 WHERE id = %s
#                 LIMIT 1
#                 """,
#                 (patient_id,),
#             )

#             result = cursor.fetchone()

#     return result is not None


# def get_patient_by_id(patient_id: int):
#     """
#     Retrieve a patient's basic profile.

#     Authorization must be performed before calling this function
#     when the requested patient belongs to another user.
#     """

#     if not isinstance(patient_id, int) or patient_id <= 0:
#         logger.warning(
#             "Invalid patient ID supplied",
#             extra={
#                 "event": "INVALID_PATIENT_ID",
#             },
#         )
#         return None

#     with get_db() as connection:
#         with connection.cursor() as cursor:
#             cursor.execute(
#                 """
#                 SELECT
#                     id,
#                     name,
#                     phone,
#                     email,
#                     dob,
#                     gender,
#                     address,
#                     role,
#                     created_at,
#                     updated_at
#                 FROM patients
#                 WHERE id = %s
#                 LIMIT 1
#                 """,
#                 (patient_id,),
#             )

#             patient = cursor.fetchone()

#     if not patient:
#         logger.warning(
#             "Patient profile not found",
#             extra={
#                 "event": "PATIENT_PROFILE_NOT_FOUND",
#                 "patient_id": patient_id,
#             },
#         )
#         return None

#     logger.info(
#         "Patient profile retrieved",
#         extra={
#             "event": "PATIENT_PROFILE_RETRIEVED",
#             "patient_id": patient_id,
#         },
#     )

#     return _sanitize_patient(patient)


# def get_patient_profile(patient_id: int):
#     """
#     Public service-level method for retrieving a patient profile.
#     """

#     return get_patient_by_id(patient_id)


# def update_patient_profile(
#     patient_id: int,
#     updates: dict,
# ):
#     """
#     Update allowed patient profile fields.

#     Password changes are intentionally NOT handled here.
#     They belong to the authentication/security layer.
#     """

#     if not isinstance(patient_id, int) or patient_id <= 0:
#         logger.warning(
#             "Invalid patient ID during profile update",
#             extra={
#                 "event": "INVALID_PATIENT_ID_UPDATE",
#             },
#         )
#         return None

#     if not isinstance(updates, dict) or not updates:
#         return None

#     invalid_fields = set(updates.keys()) - ALLOWED_PROFILE_FIELDS

#     if invalid_fields:
#         logger.warning(
#             "Attempt to update restricted patient fields",
#             extra={
#                 "event": "PATIENT_PROFILE_RESTRICTED_FIELD",
#                 "patient_id": patient_id,
#             },
#         )
#         return None

#     cleaned_updates = {}

#     for field, value in updates.items():
#         if value is None:
#             cleaned_updates[field] = None
#             continue

#         if isinstance(value, str):
#             value = value.strip()

#         cleaned_updates[field] = value

#     if "name" in cleaned_updates:
#         name = cleaned_updates["name"]

#         if not isinstance(name, str) or not name:
#             return None

#         if len(name) > 100:
#             return None

#     if "phone" in cleaned_updates:
#         phone = cleaned_updates["phone"]

#         if phone is not None:
#             if not isinstance(phone, str) or not phone:
#                 return None

#             if len(phone) > 20:
#                 return None

#     if "email" in cleaned_updates:
#         email = cleaned_updates["email"]

#         if email is not None:
#             if not isinstance(email, str) or not email:
#                 return None

#             if len(email) > 150:
#                 return None

#     if "gender" in cleaned_updates:
#         gender = cleaned_updates["gender"]

#         if gender is not None and len(str(gender)) > 20:
#             return None

#     if "address" in cleaned_updates:
#         address = cleaned_updates["address"]

#         if address is not None and len(str(address)) > 65535:
#             return None

#     if "dob" in cleaned_updates:
#         dob = cleaned_updates["dob"]

#         if dob is not None and not isinstance(dob, (date, str)):
#             return None

#     if not cleaned_updates:
#         return get_patient_by_id(patient_id)

#     set_parts = []
#     values = []

#     for field, value in cleaned_updates.items():
#         set_parts.append(f"{field} = %s")
#         values.append(value)

#     values.append(patient_id)

#     query = f"""
#         UPDATE patients
#         SET {", ".join(set_parts)}
#         WHERE id = %s
#     """

#     try:
#         with get_db() as connection:
#             with connection.cursor() as cursor:
#                 cursor.execute(query, values)

#                 if cursor.rowcount == 0:
#                     logger.warning(
#                         "Patient profile update affected no records",
#                         extra={
#                             "event": "PATIENT_PROFILE_UPDATE_NO_CHANGE",
#                             "patient_id": patient_id,
#                         },
#                     )
#                     return get_patient_by_id(patient_id)

#         logger.info(
#             "Patient profile updated",
#             extra={
#                 "event": "PATIENT_PROFILE_UPDATED",
#                 "patient_id": patient_id,
#             },
#         )

#         return get_patient_by_id(patient_id)

#     except Exception:
#         logger.exception(
#             "Patient profile update failed",
#             extra={
#                 "event": "PATIENT_PROFILE_UPDATE_ERROR",
#                 "patient_id": patient_id,
#             },
#         )
#         raise