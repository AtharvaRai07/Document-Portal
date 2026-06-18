import os
import sys
import fitz
import uuid
from datetime import datetime
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__file__)

class DocumentHandler:
    """
    Handles PDF saving and reading operations.
    Automatically logs all the action and supports section-based organization.
    """

    def __init__(self, data_dir=None, session_id=None):
        try:
            self.data_dir = data_dir or os.getenv(
                "DATA_STORAGE_PATH",
                os.path.join(os.getcwd(), "data", "document_analysis")
            )
            self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            self.session_path = os.path.join(self.data_dir, self.session_id)
            os.makedirs(self.session_path, exist_ok=True)

            logger.info(f"DocumentHandler initialized with session ID: {self.session_id} and session path: {self.session_path}")

        except Exception as e:
            logger.error(f"Error initializing DocumentHandler: {e}")
            raise CustomException(f"Error initializing DocumentHandler: {e}", sys)

    def save_pdf(self, uploaded_file):
        try:
            filename = os.path.basename(uploaded_file.name)

            if not filename.lower().endswith('.pdf'):
                raise CustomException("Uploaded file is not a PDF.")

            save_path = os.path.join(self.session_path, filename)

            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            logger.info(f"PDF saved successfully at: {save_path}, filename: {filename}, session ID: {self.session_id}")
            return save_path

        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            raise CustomException(f"Error saving PDF: {e}", sys)

    def read_pdf(self, pdf_path:str) -> str:
        try:
            text_chunks = []
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc, start=1):
                    text_chunks.append(f"\n--- Page {page_num} ---\n{page.get_text()}")

                text = "\n".join(text_chunks)

                logger.info(f"PDF read successfully, total pages: {len(doc)}, session ID: {self.session_id}")
                return text

        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise CustomException(f"Error reading PDF: {e}", sys)

if __name__ == "__main__":
    from pathlib import Path
    from io import BytesIO

    pdf_path = r"D:\\Document Protal\\D Portal\\data\\document_analysis\\Attention_is_all_you_need.pdf"

    class DummyFile:
        def __init__(self, file_path):
            self.name = Path(file_path).name
            self._file_path = file_path

        def getbuffer(self):
            return open(self._file_path, 'rb').read()


    dummy_pdf = DummyFile(pdf_path)

    handler = DocumentHandler()

    try:
        saved_path = handler.save_pdf(dummy_pdf)
        print(f"PDF saved at: {saved_path}")

        content = handler.read_pdf(saved_path)
        print(f"PDF content:\n{content[:500]}...")

    except Exception as e:
        print(f"Error: {e}")
