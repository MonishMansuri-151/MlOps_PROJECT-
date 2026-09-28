import base64
import os
import sys

from chatbot.ai.llm_service import llm_service
from src.logger import get_logger
from src.exception import CustomException


logger = get_logger(__name__)


VISION_MODEL = os.getenv(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.8-27b"
)

ALLOWED_DEPARTMENTS = {
    "General Medicine",
    "Dermatology",
    "Cardiology",
    "Orthopedics",
    "Neurology",
    "Pediatrics",
    "Gynecology",
    "ENT",
    "Ophthalmology",
}


def extract_department(analysis: str):
    for department in ALLOWED_DEPARTMENTS:
        if f"DEPARTMENT: {department}" in analysis:
            return department

    return None

def analyze_injury_image(
    image_bytes: bytes,
    content_type: str
) -> str:

    try:
        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        image_url = (
            f"data:{content_type};"
            f"base64,{image_base64}"
        )

        system_prompt = """
You are a medical image guidance assistant for Sanjivni Clinic.

Analyze the uploaded image for general medical guidance.

Rules:
- Do not provide a definitive diagnosis.
- Do not prescribe medicines.
- Do not provide medicine dosage.
- Do not provide treatment duration.
- Describe only visible/general observations.
- Clearly mention that image-based assessment has limitations.
- Do not invent findings.
- If the image is not medically relevant, clearly say so.

Choose ONLY ONE department from this list:

General Medicine
Dermatology
Cardiology
Orthopedics
Neurology
Pediatrics
Gynecology
ENT
Ophthalmology

Return the response in exactly this format:

OBSERVATION: <general visible observation>
CONCERN: <low/moderate/high/unclear>
DEPARTMENT: <one department from the list or None>
DOCTOR_REQUIRED: <yes/no>
URGENT: <yes/no>
ADVICE: <short general guidance>

Do not add any other fields.
"""
        user_prompt = """
Examine the uploaded image and provide general medical guidance.

Do not diagnose the condition.
Keep the response simple and practical.
"""

        response = llm_service.client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            temperature=0.2,
            max_completion_tokens=700
        )

        result = (
            response.choices[0]
            .message.content or ""
        ).strip()

        logger.info(
            "Injury image analysis completed successfully."
        )

        department = extract_department(result)

        return {
            "analysis": result,
            "department": department
        }

    except Exception as e:
        logger.error(
            f"Injury image analysis failed: {e}"
        )
        raise CustomException(e, sys)