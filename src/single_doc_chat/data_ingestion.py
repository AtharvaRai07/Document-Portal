import os
import sys
import uuid
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class SingleDocIngestor:
    def __init__(self):
        try:
            pass

        except Exception as e:
            logger.error(f"Error initializing SingleDocIngestor: {e}")
            raise CustomException(f"Error initializing SingleDocIngestor: {e}", sys)

    def ingest_file(self):
        try:
            pass

        except Exception as e:
            logger.error(f"Error ingesting file: {e}")
            raise CustomException(f"Error ingesting file: {e}", sys)

    def _create_retriever(self):
        try:
            pass

        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            raise CustomException(f"Error creating retriever: {e}", sys)
