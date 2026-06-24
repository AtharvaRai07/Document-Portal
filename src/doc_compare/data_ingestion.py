import sys
from pathlib import Path
import uuid
import fitz
from datetime import datetime, timezone

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class DocumentIngestion:
    def __init__(self, base_dir: str, session_id = None):
        self.base_dir = Path(base_dir)
        self.session_id = session_id or f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_uuid{uuid.uuid4().hex[:8]}"
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"DocumentIngestion initialized with base_dir: {self.base_dir}, session_id: {self.session_id}, session_path: {self.session_path}")

    def save_uploaded_file(self, reference_file, actual_file) -> Path:
        """
        Saves the uploaded file to the specified path
        """
        try:
            logger.info("Existing files deleted successfully.")

            ref_path = self.session_path / reference_file.name
            act_path = self.session_path / actual_file.name

            if not reference_file.name.endswith('.pdf') or not actual_file.name.endswith('.pdf'):
                logger.error("Both files must be PDFs.")
                raise ValueError("Both files must be PDFs.")

            with open(ref_path, 'wb') as f:
                f.write(reference_file.getbuffer())

            with open(act_path, 'wb') as f:
                f.write(actual_file.getbuffer())

            logger.info(f"Files saved successfully at {ref_path} and {act_path}.")
            return ref_path, act_path

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

    def combine_documment(self)-> str:
        try:
            content_dict = {}
            doc_parts = []

            for filename in sorted(self.session_path.iterdir()):
                if filename.is_file() and filename.suffix == '.pdf':
                    content_dict[filename.name] = self.read_pdf(filename)

            for filename, content in content_dict.items():
                doc_parts.append(f"\n --- Document: {filename} ---\n{content}")

            combined_text =  "\n\n".join(doc_parts)
            logger.info(f"Successfully combined the documents with total length: {len(combined_text)} and session_id: {self.session_id}")
            return combined_text

        except Exception as e:
            logger.error(f"Error while combining the document: {e}")
            raise CustomException(f"Error while combining the document: {e}", sys)

    def clean_old_sessions(self, keep_latest: int = 3):
        """
        Method to delete older sessions folders, keeping only the latest N
        """
        try:
            sessoin_folders = sorted(
                [f for f in self.base_dir.iterdir() if f.is_dir()],
                reverse=True
            )

            for folder in sessoin_folders[keep_latest:]:
                for file in folder.iterdir():
                    if file.is_file():
                        file.unlink()
                folder.rmdir()

                logger.info(f"Deleted old session folder: {folder}")

        except Exception as e:
            logger.error(f"Error while cleaning old sessions: {e}")
            raise CustomException(f"Error while cleaning old sessions: {e}", sys)
