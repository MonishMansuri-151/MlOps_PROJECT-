import os
import sys

from groq import Groq
from dotenv import load_dotenv

from chatbot.ai.prompts import (
    SYSTEM_PROMPT,
    DEPARTMENT_DETECTION_PROMPT,
)

from src.logger import logging
from src.exception import CustomException

load_dotenv()


class LLMService:

    def __init__(self):
        try:
            api_key = os.getenv("GROQ_API_KEY")
            model = os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-20b"
            )

            if not api_key:
                raise ValueError("GROQ_API_KEY is not configured.")

            self.client = Groq(api_key=api_key)
            self.model = model

            logging.info(
                f"Groq LLM service initialized. model={self.model}"
            )

        except Exception as e:
            logging.error(
                f"Failed to initialize LLM service: {e}"
            )
            raise CustomException(e, sys)

    def generate_response(self, user_message: str) -> str:
        try:
            if not user_message or not user_message.strip():
                return "Please describe your health concern."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_message.strip(),
                    },
                ],
                temperature=0.2,
                max_tokens=800,
            )

            answer = response.choices[0].message.content

            logging.info("LLM response generated successfully.")

            return answer.strip()

        except Exception as e:
            logging.error(
                f"LLM response generation failed: {e}"
            )
            raise CustomException(e, sys)

    def detect_department(self, user_message: str) -> str:
        try:
            if not user_message or not user_message.strip():
                return "General Medicine"

            text = user_message.lower().strip()

            # Strong keyword-based routing
            department_keywords = {
                "Dermatology": [
                    "skin",
                    "rash",
                    "itching",
                    "itch",
                    "acne",
                    "pimple",
                    "pimples",
                    "skin allergy",
                    "hair problem",
                    "hair fall",
                    "dandruff",
                    "खुजली",
                    "रैश",
                    "त्वचा",
                    "मुंहासे",
                    "बाल झड़ना",
                ],

                "Cardiology": [
                    "heart",
                    "chest pain",
                    "palpitation",
                    "heartbeat",
                    "blood pressure",
                    "दिल",
                    "सीने में दर्द",
                ],

                "Orthopedics": [
                    "bone",
                    "joint",
                    "fracture",
                    "knee pain",
                    "back pain",
                    "shoulder pain",
                    "हड्डी",
                    "जोड़",
                    "घुटने",
                    "कमर दर्द",
                ],

                "Neurology": [
                    "migraine",
                    "seizure",
                    "nerve",
                    "numbness",
                    "tingling",
                    "brain",
                    "दौरा",
                    "नस",
                    "सुन्न",
                ],

                "ENT": [
                    "ear pain",
                    "ear",
                    "throat",
                    "sore throat",
                    "sinus",
                    "hearing",
                    "कान",
                    "गला",
                    "साइनस",
                ],

                "Ophthalmology": [
                    "eye",
                    "eyes",
                    "vision",
                    "blurred vision",
                    "eye pain",
                    "आंख",
                    "दृष्टि",
                ],

                "Gynecology": [
                    "period",
                    "menstrual",
                    "pregnancy",
                    "pregnant",
                    "pcos",
                    "uterus",
                    "पीरियड",
                    "गर्भावस्था",
                ],

                "Pediatrics": [
                    "child",
                    "baby",
                    "kid",
                    "infant",
                    "बच्चा",
                    "बच्चे",
                    "शिशु",
                ],
            }

            for department, keywords in department_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        logging.info(
                            f"Department detected by keyword: {department}"
                        )
                        return department

            # If no strong keyword matches, use LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": DEPARTMENT_DETECTION_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_message.strip(),
                    },
                ],
                temperature=0,
                max_tokens=30,
            )

            raw_department = (
                response.choices[0].message.content or ""
            ).strip()

            logging.info(
                f"Raw department response from LLM: {raw_department}"
            )

            allowed_departments = [
                "General Medicine",
                "Dermatology",
                "Cardiology",
                "Orthopedics",
                "Neurology",
                "Pediatrics",
                "Gynecology",
                "ENT",
                "Ophthalmology",
            ]

            for department in allowed_departments:
                if department.lower() in raw_department.lower():
                    return department

            logging.warning(
                f"Invalid department returned by LLM: {raw_department}"
            )

            return "General Medicine"

        except Exception as e:
            logging.error(
                f"Department detection failed: {e}"
            )
            raise CustomException(e, sys)
llm_service = LLMService()