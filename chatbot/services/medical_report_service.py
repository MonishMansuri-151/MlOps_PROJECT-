import os
import sys
from chatbot.database.queries import get_medical_file_by_id
from chatbot.ai.report_analyzer import analyze_medical_report
from pypdf import PdfReader

from src.logger import get_logger
from src.exception import CustomException

logger = get_logger(__name__)


def extract_pdf_text(file_path: str) -> str:
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                "Medical report file not found."
            )

        reader = PdfReader(file_path)

        pages_text = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages_text.append(text)

        extracted_text = "\n\n".join(pages_text).strip()

        if not extracted_text:
            return ""

        logger.info(
            f"PDF text extracted successfully: {file_path}"
        )

        return extracted_text

    except Exception as e:
        logger.error(
            f"PDF text extraction failed: {e}"
        )

        raise CustomException(e, sys)
    
def analyze_patient_report(
    file_id: int,
    patient_id: int,
    user_question: str = ""
):
    try:
        medical_file = get_medical_file_by_id(
            file_id=file_id,
            patient_id=patient_id
        )

        if not medical_file:
            return {
                "success": False,
                "message": "Medical report not found."
            }

        file_path = medical_file["file_path"]

        if not file_path.lower().endswith(".pdf"):
            return {
                "success": False,
                "message": "Only PDF reports can be analyzed currently."
            }

        report_text = extract_pdf_text(file_path)

        if not report_text:
            return {
                "success": False,
                "message": (
                    "No readable text was found in this PDF. "
                    "It may be a scanned report."
                )
            }

        analysis = analyze_medical_report(
            report_text=report_text,
            user_question=user_question
        )

        return {
            "success": True,
            "file_id": file_id,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(
            f"Patient report analysis failed: {e}"
        )
        raise CustomException(e, sys)