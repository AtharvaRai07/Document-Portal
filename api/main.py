import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.document_ingestion.data_ingestion import(
     DocumentHandler,
     DocumentComparator,
     ChatIngestor,
     FAISSManager
)

from src.doc_analyzer.data_analysis import DocumentAnalyzer
from src.doc_compare.document_comparator import DocumentComparator
from src.document_chat.retrieval import ConversationalRAG

app = FastAPI(title="Document Portal", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="../static"), name="static")
templates = Jinja2Templates(directory="../templates")


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "service": "Document Portal", "version": "1.0.0"}

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)) -> Any:
    try:
        pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/compare')
async def compare_documents(reference: UploadFile = File(...), actual: UploadFile = File(... )) -> Any:
    try:
        pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/index")
async def index_chat() -> Any:
    try:
        pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
