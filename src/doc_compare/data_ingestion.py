import sys
from pathlib import Path
import fitz

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class DocumentIngestion:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def delete_existing_files(self):
        """
        Delete existing files at the specified paths
        """
        try:
            pass

        except Exception as e:
            logger.error(f"Error deleting existing files: {e}")
            raise CustomException(f"Error deleting existing files: {e}", sys)

    def save_uploaded_file(self):
        """
        Saves the uploaded file to the specified path
        """
        try:
            pass

        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise CustomException(f"Error saving uploaded file: {e}", sys)

    def read_pdf(self, pdf_path: Path) -> str:
        """
        Reads the PDF file and extracts text content
        """
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    logger.error(f"PDF is encrypted and cannot be read. PDF path: {pdf_path}")
                    raise ValueError(f"PDF is encrypted and cannot be read. PDF path: {pdf_path}")

                all_text = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():
                        all_text.append(f"\n --- Page {page_num + 1} ---\n{text}")

                logger.info(f"Successfully read PDF: {pdf_path} with {len(all_text)} pages containing text.")
                return "\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise CustomException(f"Error reading PDF: {e}", sys)
