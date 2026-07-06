import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.document_ingestion.data_ingestion import (
    ChatIngestor,
    DocComparator,
    DocHandler,
    FAISSManager,
)
from src.doc_analyzer.data_analysis import DocumentAnalyzer
from src.doc_compare.document_comparator import DocumentComparator
from src.document_chat.retrieval import ConversationalRAG

BASE_DIR = Path(__file__).resolve().parent.parent
FAISS_BASE = os.getenv("FAISS_BASE", str(BASE_DIR / "faiss_index"))
UPLOAD_BASE = os.getenv("UPLOAD_BASE", str(BASE_DIR / "data" / "document_chat"))
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index")

app = FastAPI(title="Document Portal API", version="0.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    response = templates.TemplateResponse("index.html", {"request": request})
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "service": "document-portal", "version": "0.1"}


class FastAPIFileAdapter:
    """
    Adapter to convert FastAPI UploadFile to a Path object for processing.
    """
    def __init__(self, uf: UploadFile):
        self._uf = uf
        self.name = uf.filename

    def  getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()

def _read_pdf_via_handler(handler: DocHandler, path: str) -> str:
    """
    Helper function to read PDF content using a given handler.
    """
    try:
        if hasattr(handler, "read_pdf"):
            return handler.read_pdf(path)
        raise RuntimeError("DocHandler has no read_pdf method")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {e}")

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)) -> Any:
    try:
        dh = DocHandler()
        saved_path = dh.save_pdf(FastAPIFileAdapter(file))
        text = _read_pdf_via_handler(dh, saved_path)
        analyzer = DocumentAnalyzer()
        result = analyzer.analyze_document(text)
        return JSONResponse(content={"analysis": result})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/compare')
async def compare_documents(reference: UploadFile = File(...), actual: UploadFile = File(...)) -> Any:
    try:
        dc = DocComparator()
        ref_path, act_path = dc.save_uploaded_files(FastAPIFileAdapter(reference), FastAPIFileAdapter(actual))
        _ = ref_path, act_path
        combined_text = dc.combine_documents()
        comp = DocumentComparator()
        df = comp.compare_documents(combined_text)
        return {"rows": df.to_dict(orient='records'), "session_id": dc.session_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/index")
async def index_chat(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool = Form(True),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(100),
    k: int = Form(10),
) -> Any:
    try:
        wrapped = [FastAPIFileAdapter(f) for f in files]
        ci = ChatIngestor(
            temp_base=UPLOAD_BASE,
            faiss_base=FAISS_BASE,
            use_session_dirs=use_session_dirs,
            session_id=session_id or None,
        )
        ci.build_retriever(wrapped, chunk_overlap=chunk_overlap, chunk_size=chunk_size)
        return {
            "session_id": ci.session_id,
            "use_session_dirs": ci.use_session,
            "message": "Documents indexed successfully",
            "k": k,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/query")
async def chat_query(
    question: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool = Form(True),
    k: int = Form(10),
) -> Any:
    try:
        if use_session_dirs and not session_id:
            raise HTTPException(status_code=400, detail="session_id is required when use_session_dirs=True")

        index_dir = os.path.join(FAISS_BASE, session_id) if use_session_dirs else FAISS_BASE
        if not os.path.isdir(index_dir):
            raise HTTPException(status_code=404, detail=f"FAISS index not found at: {index_dir}")

        rag = ConversationalRAG(session_id=session_id)
        rag.load_retriever_from_faiss(index_dir, index_name=FAISS_INDEX_NAME)

        response = rag.invoke(question, chat_history=[])

        return {
            "answer": response,
            "session_id": session_id,
            "k": k,
            "engine": "LCEL-RAG"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")
