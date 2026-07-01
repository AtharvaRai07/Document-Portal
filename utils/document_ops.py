from __future__ import annotations
from pathlib import Path
from typing import Iterable, List
from fastapi import UploadFile
from langchain_classic.schema import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from utils.config_loader import load_config
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

def load_documents(paths: Iterable[Path]) -> List[Document]:
    """
    Load documents from given file paths using appropriate loaders.
    """
    try:
        config = load_config()
        docs : List[Document] = []

        for p in paths:
            ext = p.suffix.lower()

            if ext == ".pdf":
                loader = PyPDFLoader(str(p))
            elif ext == ".docx":
                loader = Docx2txtLoader(str(p))
            elif ext == ".txt":
                loader = TextLoader(str(p))
            else:
                logger.warning(f"Unsupported file extension: {ext}")
                continue

            docs.extend(loader.load())

        logger.info(f"Loaded {len(docs)} documents from {len(paths)} files.")
        return docs

    except Exception as e:
        logger.error(f"Error loading documents: {e}")
        raise CustomException(f"Error loading documents: {e}")

def concat_for_analysis(docs: List[Document]) -> str:
    parts = []
    for d in docs:
        src = d.metadata.get("source") or d.metadata.get("file_path") or "unknown"
        parts.append(f"Source: {src}\nContent:\n{d.page_content}\n{'-'*40}\n")
        return "\n".join(parts)

def concat_for_comparison(ref_docs: List[Document], actual_docs: List[Document]):
    left = concat_for_analysis(ref_docs)
    right = concat_for_analysis(actual_docs)
    return f"<<REFERENCE DOCUMENTS>>\n{left}\n{'='*80}\n<<ACTUAL DOCUMENTS>>\n{right}"

class FastAPIFileAdapter:
    """
    Adapter to convert FastAPI UploadFile to a Path object for processing.
    """
    def __init__(self, uf: UploadFile):
        self._uf = uf
        self.name = uf.filename

    def getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()


def read_pdf_via_handler(handler, path:str) -> str:
    """
    Read PDF content using a given handler.
    """
    if hasattr(handler, "read_pdf"):
        return handler.read_pdf(path)

    if hasattr(handler, 'read_'):
        return handler.read_(path)

    raise RuntimeError("Document Handler has neither read_pdf not read_ method. Please check the handler implementation.    ")

