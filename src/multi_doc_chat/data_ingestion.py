import uuid
from pathlib import Path
import sys
from datetime import datetime, timezone
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from utils.models_loader import ModelLoader
from utils.config_loader import load_config
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class DocumentIngestor:
    def __init__(self, base_dir: str, faiss_dir: str, session_id: str | None = None):
        try:
            self.base_dir = Path(base_dir)
            self.faiss_dir = Path(faiss_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            self.config = load_config()
            self.session_id = session_id or f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            self.session_dir = self.base_dir / self.session_id
            self.session_faiss_dir = self.faiss_dir / self.session_id
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self.session_faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()
            logger.info(f"DocumentIngestor initialized with base_dir: {self.base_dir}, faiss_dir: {self.faiss_dir}, session_id: {self.session_id}")

        except Exception as e:
            logger.error(f"Error initializing DocumentIngestor: {e}")
            raise CustomException(f"Error initializing DocumentIngestor: {e}", sys)


    def ingest_files(self, uploaded_files):
        try:
            documents = []

            for uploaded_file in uploaded_files:
                ext = Path(uploaded_file.name).suffix.lower()
                if ext not in self.config['supported_extensions']:
                    logger.warning(f"Unsupported file extension: {ext}. Skipping file: {uploaded_file.name}")
                    continue

                unique_filename = f"{uuid.uuid4().hex[:8]}.{ext}"
                temp_file = self.session_dir / unique_filename

                with open(temp_file, 'wb') as f:
                    f.write(uploaded_file.read())

                logger.info(f"File {uploaded_file.name} saved as {temp_file}")

                if ext == ".pdf":
                    loader = PyPDFLoader(str(temp_file))
                elif ext == ".docx":
                    loader = Docx2txtLoader(str(temp_file))
                elif ext == ".txt":
                    loader = TextLoader(str(temp_file), encoding="utf-8")
                else:
                    logger.warning(f"No loader available for extension: {ext}. Skipping file: {uploaded_file.name}")
                    continue

                docs = loader.load()
                documents.extend(docs)

            if not documents:
                raise CustomException("No valid documents were loaded. Please check the uploaded files.", sys)

            logger.info(f"Total documents loaded: {len(documents)}")
            return self._create_retriever(documents)

        except Exception as e:
            logger.error(f"Error ingesting files: {e}")
            raise CustomException(f"Error ingesting files: {e}", sys)

    def _create_retriever(self, documents):
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300)
            chunks = splitter.split_documents(documents)
            logger.info(f"Total chunks created: {len(chunks)}")

            embeddings = self.model_loader.load_embedding_model()
            vectorstore = FAISS.from_documents(chunks, embeddings)
 
            vectorstore.save_local(str(self.session_faiss_dir))
            logger.info(f"Vectorstore saved at: {self.session_faiss_dir}")

            retriever = vectorstore.as_retriever(search_type=self.config['retriever']['search_type'], search_kwargs={"k": self.config['retriever']['top_k']})
            return retriever

        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            raise CustomException(f"Error creating retriever: {e}", sys)
