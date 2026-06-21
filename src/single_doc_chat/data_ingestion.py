import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from utils.models_loader import ModelLoader
from utils.config_loader import load_config

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class SingleDocIngestor:
    def __init__(self, data_dir: str, faiss_dir: str = "faiss_index"):
        try:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)

            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()
            self.config = load_config()

            logger.info(f"SingleDocIngestor initialized with data_dir: {self.data_dir} and faiss_dir: {self.faiss_dir}")

        except Exception as e:
            logger.error(f"Error initializing SingleDocIngestor: {e}")
            raise CustomException(f"Error initializing SingleDocIngestor: {e}", sys)

    def ingest_file(self, uploaded_file: str):
        try:
            documents = []

            unique_filename = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
            temp_file = self.data_dir / unique_filename

            with open(temp_file, "wb") as f:
                f.write(uploaded_file.read())

            logger.info("PDF saved for ingestion: {temp_file}")
            loader = PyPDFLoader(str(temp_file))
            docs = loader.load()
            documents.extend(docs)
            logger.info(f"Documents loaded from {temp_file}: {len(documents)}")

            return self._create_retriever(documents)

        except Exception as e:
            logger.error(f"Error ingesting file: {e}")
            raise CustomException(f"Error ingesting file: {e}", sys)

    def _create_retriever(self, documents: list):
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=400)
            chunks = splitter.split_documents(documents)
            logger.info(f"Documents split into chunks: {len(chunks)}")

            embeddings = self.model_loader.load_embedding_model()
            vector_store = FAISS.from_documents(documents=chunks, embedding=embeddings, search_kwargs={"k": self.config['retriever']['k']})

            vector_store.save_local(str(self.faiss_dir))
            logger.info(f"Vector store created with {vector_store.index.ntotal} vectors and saved to {self.faiss_dir}")

            retriever = vector_store.as_retriever(search_type=self.config['retriever']['search_type'])
            logger.info("Retriever created successfully")
            return retriever

        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            raise CustomException(f"Error creating retriever: {e}", sys)
