from __future__ import annotations
import os
import sys
import json
import uuid
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Dict, Any

import fitz
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import FAISS

from utils.config_loader import load_config
from utils.models_loader import ModelLoader
from utils.file_io import _session_id, save_uploaded_file
from utils.document_ops import load_documents, concat_for_analysis, concat_for_comparison

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class FAISSManager:
    def __init__(self, index_dir: Path, model_loader: Optional[ModelLoader] = None):
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.meta_path = self.index_dir / "ingested_metadata.json"
        self._meta: Dict[str, Any] = {"rows": {}}

        if self.meta_path.exists():
            try:
                self._meta = json.loads(self.meta_path.read_text(encoding='utf-8')) or {"rows":{}}
            except Exception:
                self._meta = {"rows": {}}

        self.model_loader = model_loader or ModelLoader()
        self.embedding_model = self.model_loader.load_embedding_model()
        self.vector_store: Optional[FAISS] = None

    def _exists(self) -> bool:
        return (self.index_dir / "index.faiss").exists() and (self.index_dir / "index.pkl").exists()

    @staticmethod
    def _fingerprint(text: str, md: Dict[str, Any]) -> str:
        src = md.get("source") or md.get("file_path")
        rid = md.get("row_id")
        if src is not None:
            return f"{src}::{'' if rid is None else rid}"
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _save_meta(self):
        self.meta_path.write_text(json.dumps(self._meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_documents(self,docs: List[Document]):
        if self.vector_store is None:
            raise RuntimeError("Call load_or_create() before add_documents_idempotent().")

        new_docs: List[Document] = []

        for d in docs:
            key = self._fingerprint(d.page_content, d.metadata or {})
            if key in self._meta["rows"]:
                continue
            self._meta["rows"][key] = True
            new_docs.append(d)

        if new_docs:
            self.vector_store.add_documents(new_docs)
            self.vector_store.save_local(str(self.index_dir))
            self._save_meta()
        return len(new_docs)

    def load_or_create(self, texts: Optional[List[str]] = None, metadatas: Optional[List[dict]] = None):
        if self._exists():
            self.vector_store = FAISS.load_local(str(self.index_dir), self.embedding_model, allow_dangerous_deserialization=True)

            return self.vector_store

        if not texts:
            raise CustomException("No texts provided for index creation.")

        self.vector_store = FAISS.from_texts(texts=texts, embedding=self.embedding_model, metadatas=metadatas or [])
        self.vector_store.save_local(str(self.index_dir))
        return self.vector_store

class ChatIngestor:
    def __init__(self, temp_base: str = "data", faiss_base: str = "faiss_index", use_session_dirs: bool = True, session_id: Optional[str] = None):
        try:
            self.model_loader = ModelLoader()
            self.config = load_config()

            self.use_session = use_session_dirs
            self.session_id = session_id or _session_id()

            self.temp_base = Path(temp_base); self.temp_base.mkdir(parents=True, exist_ok=True)
            self.faiss_base = Path(faiss_base); self.faiss_base.mkdir(parents=True, exist_ok=True)

            self.temp_dir = self._resolve_dir(self.temp_base)
            self.faiss_dir = self._resolve_dir(self.faiss_base)

            logger.info(f"ChatIngestor initialized with temp_dir: {self.temp_dir}, faiss_dir: {self.faiss_dir}, session_id: {self.session_id}")

        except Exception as e:
            logger.error(f"Error initializing ChatIngestor: {e}")
            raise CustomException(f"Error initializing ChatIngestor: {e}") from e


    def _resolve_dir(self, base_dir: Path):
        if self.use_session:
            d = base_dir / self.session_id
            d.mkdir(parents=True, exist_ok=True)
            return d
        return base_dir

    def _split(self, docs: List[Document], chunk_size=1000, chunk_overlap=200) -> List[Document]:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks =  text_splitter.split_documents(docs)
        logger.info(f"Split {len(docs)} documents into {len(chunks)} chunks with chunk_size={chunk_size} and chunk_overlap={chunk_overlap}.")
        return chunks

    def build_retriever(self, uploaded_files: Iterable, *, chunk_size: int = 1000, chunk_overlap: int = 200):
        try:
            paths = save_uploaded_file(uploaded_files, self.temp_dir)
            docs = load_documents(paths)

            if not docs:
                raise ValueError("No valid documents loaded")

            chunks = self._split(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            fm = FAISSManager(self.faiss_dir, self.model_loader)

            texts = [c.page_content for c in chunks]
            metas = [c.metadata for c in chunks]

            vector_store = fm.load_or_create(texts=texts, metadatas=metas)

            logger.info(f"Built retriever with {len(chunks)} chunks and stored in FAISS index at {self.faiss_dir}.")
            return vector_store.as_retriever(search_type=self.config['retriever']['search_type'], search_kwargs={"k": self.config['retriever']['top_k']})

        except Exception as e:
            logger.error(f"Error building retriever: {e}")
            raise CustomException(f"Error building retriever: {e}") from e


class DocHandler:
    def __init__(self, data_dir: Optional[str] = None, session_id: Optional[str] = None):
        self.data_dir = data_dir or os.getenv("DATA_STORAGE_PATH", os.path.join(os.getcwd(), "data", "document_analysis"))
        self.session_id = session_id or _session_id()
        self.session_path = os.path.join(self.data_dir, self.session_id)
        os.makedirs(self.session_path, exist_ok=True)

        logger.info(f"DocHandler initialized with session_path: {self.session_path}")

    def save_pdf(self, uploaded_file):
        try:
            filename = os.path.basename(uploaded_file.name)
            if not filename.lower().endswith('.pdf'):
                raise ValueError("Uploaded file is not a PDF.")

            save_path = os.path.join(self.session_path, filename)
            with open(save_path, 'wb') as f:
                if hasattr(uploaded_file, 'read'):
                    f.write(uploaded_file.read())
                else:
                    f.write(uploaded_file.getbuffer())

            logger.info(f"PDF saved succesfully at {save_path} for session {self.session_id}")
            return save_path

        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            raise CustomException(f"Error saving PDF: {e}") from e

    def read_pdf(self, pdf_path: str) -> str:
        try:
            text_chunks = []
            with fitz.open(pdf_path) as doc:
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text_chunks.append(f"\n--- Page {page_num + 1} ---\n{page.get_text()}")
            logger.info(f"PDF read successfully from {pdf_path} for session {self.session_id}")
            return "\n".join(text_chunks)

        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise CustomException(f"Error reading PDF: {e}") from e

class DocumentComparator:
    def __init__(self, base_dir: Optional[str] = None, session_id: Optional[str] = None):
        self.base_dir = Path(base_dir)
        self.session_id = session_id or _session_id()
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)

    def save_uploaded_files(self, reference_file, actual_file):
        try:
            ref_path = self.session_path / reference_file.name
            act_path = self.session_path / actual_file.name

            for fobj, out in ((reference_file, ref_path), (actual_file, act_path)):
                if not fobj.name.lower().endswith(('.pdf', '.docx', '.txt')):
                    raise ValueError(f"Unsupported file type: {fobj.name}")
                with open(out, 'wb') as f:
                    if hasattr(fobj, 'read'):
                        f.write(fobj.read())
                    else:
                        f.write(fobj.getbuffer())

            logger.info(f"Uploaded files saved successfully at {self.session_path} for session {self.session_id}")
            return ref_path, act_path

        except Exception as e:
            logger.error(f"Error saving uploaded files: {e}")
            raise CustomException(f"Error saving uploaded files: {e}") from e

    def read_pdf(self, pdf_path: str) -> str:
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError("PDF is encrypted and cannot be read.")
                parts = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():
                        parts.append(f"\n--- Page {page_num + 1} ---\n{text}")

            logger.info(f"PDF read successfully from {pdf_path} for session {self.session_id}")
            return "\n".join(parts)

        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise CustomException(f"Error reading PDF: {e}") from e

    def combine_documents(self) -> str:
        try:
            doc_parts = []
            for file in sorted(self.session_path.iterdir()):
                if file.is_file() and file.suffix.lower() == '.pdf':
                    content = self.read_pdf(str(file))
                    doc_parts.append(f"--- Document: {file.name} ---\n{content}")
            combined_text = "\n\n".join(doc_parts)
            logger.info(f"Combined documents successfully for session {self.session_id}")
            return combined_text

        except Exception as e:
            logger.error(f"Error combining documents: {e}")
            raise CustomException(f"Error combining documents: {e}") from e

    def clean_old_sessions(self, keep_latest: int = 3):
        try:
            sessions = sorted([f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True)
            for folder in sessions[keep_latest:]:
                shutil.rmtree(folder, ignore_errors=True)
                logger.info(f"Deleted old session folder: {folder}")

        except Exception as e:
            logger.error(f"Error cleaning old sessions: {e}")
            raise CustomException(f"Error cleaning old sessions: {e}") from e
