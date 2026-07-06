"""
DocMind FastAPI Backend Server

Exposes REST APIs for document intelligence features, allowing web clients
to upload files, view document lists, run searches, query chatbot insights,
and inspect statistics.
"""
from __future__ import annotations

import dataclasses
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Ensure root import path is set
import sys
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from services.document_service import DocumentService
from services.search_service import SearchService
from services.chat_service import ChatService
from utils.app_paths import BUNDLE_DIR, DATA_DIR, ensure_data_dirs, DB_PATH
from utils.logger import setup_logging, get_logger

# ── Initialization ────────────────────────────────────────────────────────
setup_logging()
log = get_logger("backend")

# Try to initialize writable directories
try:
    ensure_data_dirs()
    log.info("App paths and data directories initialized successfully.")
except Exception as exc:
    log.critical("Fatal error: Could not initialize data directories: %s", exc)

app = FastAPI(
    title="DocMind API",
    description="Local Document Intelligence REST APIs",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS Middleware ────────────────────────────────────────────────────────
# Allow all origins for dev flexibility, can be locked down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Service Accessors ──────────────────────────────────────────────────────
db_manager = DatabaseManager()
doc_service = DocumentService(db_manager)
search_service = SearchService(db_manager)
chat_service = ChatService(db_manager)

# ── Request / Response Schema models ───────────────────────────────────────
class IndexFolderRequest(BaseModel):
    path: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    api_key: Optional[str] = None
    model: Optional[str] = "gpt-4o-mini"

# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/health")
def get_health():
    """Health check endpoint to verify API server is running."""
    return {
        "status": "healthy",
        "app": "DocMind Backend",
        "version": "1.0.0",
        "database": str(DB_PATH),
        "data_dir": str(DATA_DIR),
    }

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a file and index it into the database."""
    log.info("Receive upload request for file: %s", file.filename)
    
    # Save the upload to a temp directory
    temp_dir = DATA_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / f"upload_{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        # Import file using standard document service
        doc = doc_service.import_file(temp_file_path)
        
        # Clean up temp file
        if temp_file_path.exists():
            temp_file_path.unlink()
            
        if doc is None:
            log.warning("File %s was skipped (duplicate)", file.filename)
            return JSONResponse(
                status_code=200,
                content={"status": "skipped", "message": "File already indexed", "filename": file.filename}
            )
            
        log.info("File %s indexed successfully as doc_id=%s", file.filename, doc.id)
        return {"status": "success", "document": dataclasses.asdict(doc)}
        
    except Exception as exc:
        log.error("Failed to upload/index file %s: %s", file.filename, exc, exc_info=True)
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/upload/multiple")
async def upload_multiple_documents(files: List[UploadFile] = File(...)):
    """Upload multiple files and index them into the database."""
    log.info("Received batch upload request for %d files", len(files))
    
    results = {
        "successful": [],
        "failed": [],
        "skipped": []
    }
    
    temp_dir = DATA_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        temp_file_path = temp_dir / f"upload_{file.filename}"
        try:
            with open(temp_file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            doc = doc_service.import_file(temp_file_path)
            
            if temp_file_path.exists():
                temp_file_path.unlink()
                
            if doc is None:
                results["skipped"].append({"filename": file.filename, "reason": "Already indexed"})
            else:
                results["successful"].append({"filename": file.filename, "id": doc.id})
                
        except Exception as exc:
            log.error("Failed to process %s in batch: %s", file.filename, exc)
            if temp_file_path.exists():
                temp_file_path.unlink()
            results["failed"].append({"filename": file.filename, "error": str(exc)})
            
    return {"status": "completed", "summary": results}

@app.get("/api/documents")
def get_documents():
    """List all indexed documents, ordered by creation date."""
    try:
        docs = doc_service.get_all_documents()
        return [dataclasses.asdict(d) for d in docs]
    except Exception as exc:
        log.error("Failed to fetch documents: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/document/{doc_id}")
def get_document(doc_id: str):
    """Retrieve metadata of a single document by its UUID."""
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return dataclasses.asdict(doc)

@app.get("/api/document/{doc_id}/download")
def download_document(doc_id: str):
    """Download or stream the original raw document file."""
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    file_path = Path(doc.stored_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found on server storage disk: {file_path}")
        
    return FileResponse(
        path=file_path,
        filename=doc.filename,
        media_type="application/octet-stream"
    )

@app.get("/api/document/{doc_id}/view")
def view_document(doc_id: str):
    """Stream the document file inline so the browser can render it directly."""
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc.stored_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")

    ext = file_path.suffix.lower()
    media_type_map = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc":  "application/msword",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls":  "application/vnd.ms-excel",
        ".txt":  "text/plain",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    from fastapi.responses import Response
    import io
    with open(file_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{doc.filename}"',
            "Content-Length": str(len(content)),
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )

@app.get("/api/document/{doc_id}/text")
def get_document_text(doc_id: str):
    """Retrieve full plain text extracted from a document."""
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    text = doc_service.get_extracted_text(doc_id)
    return {"doc_id": doc_id, "filename": doc.filename, "text": text}

@app.delete("/api/document/{doc_id}")
def delete_document(doc_id: str):
    """Delete a document, its database record, and its storage cache files."""
    log.info("Request to delete document doc_id=%s", doc_id)
    success = doc_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or could not be deleted")
    return {"status": "success", "message": "Document deleted successfully"}

@app.post("/api/index")
def index_folder(req: IndexFolderRequest, background_tasks: BackgroundTasks):
    """
    Trigger indexing of a local directory on the server.
    Recursively scans the directory and imports all supported files.
    """
    folder_path = Path(req.path)
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path '{req.path}' is not a valid directory.")
        
    # Gather supported files
    supported_exts = {".pdf", ".xls", ".xlsx", ".docx", ".txt", ".text", ".md", ".csv", ".log", ".json", ".xml", ".html"}
    file_paths = []
    try:
        for path in folder_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in supported_exts:
                file_paths.append(path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to scan folder: {exc}")

    if not file_paths:
        return {"status": "success", "message": "No supported files found", "indexed_count": 0}

    # Process immediately and return count
    success_count = 0
    skipped_count = 0
    error_count = 0
    
    for path in file_paths:
        try:
            doc = doc_service.import_file(path)
            if doc is None:
                skipped_count += 1
            else:
                success_count += 1
        except Exception as exc:
            log.warning("Index error on %s: %s", path.name, exc)
            error_count += 1
            
    return {
        "status": "success",
        "message": "Folder indexing complete",
        "total_scanned": len(file_paths),
        "success_count": success_count,
        "skipped_count": skipped_count,
        "error_count": error_count
    }

@app.get("/api/search")
def search_documents(
    q: str = Query(..., description="Query keyword or exact phrase"),
    case_sensitive: bool = Query(False),
    whole_word: bool = Query(False),
    exact_phrase: bool = Query(True)
):
    """Search for query occurrences across all document files."""
    if not q.strip():
        return []
        
    try:
        # Record search query in database
        db_manager.add_search_history(q)
        
        results = search_service.search(
            query=q,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            exact_phrase=exact_phrase
        )
        return [dataclasses.asdict(r) for r in results]
    except Exception as exc:
        log.error("Search failed for query '%s': %s", q, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/chat")
def run_chat_query(req: ChatRequest):
    """
    RAG chat interface. Gathers document context matched by query,
    passes context prompt to OpenAI API, and returns cited summary response.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message not allowed")
        
    try:
        # Format chat history list of dicts
        history = [{"role": turn.role, "content": turn.content} for turn in req.history]
        
        response = chat_service.ask(
            message=req.message,
            chat_history=history,
            api_key=req.api_key,
            model=req.model
        )
        return response
    except Exception as exc:
        log.error("Chat engine failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/stats")
def get_stats():
    """Retrieve aggregate storage size and word-count stats across all indexed docs."""
    try:
        return doc_service.get_library_statistics()
    except Exception as exc:
        log.error("Failed to calculate library statistics: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/recent")
def get_recent():
    """Retrieve the 10 most recently added documents."""
    try:
        docs = doc_service.get_recent_documents(limit=10)
        return [dataclasses.asdict(d) for d in docs]
    except Exception as exc:
        log.error("Failed to retrieve recent documents: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/history")
def get_history():
    """Retrieve search query history logs and past chat session turns."""
    try:
        return {
            "search": db_manager.get_search_history(limit=30),
            "chat": db_manager.get_chat_history(limit=50)
        }
    except Exception as exc:
        log.error("Failed to retrieve history logs: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.delete("/api/history")
def delete_history():
    """Clear all past search and chat history logs."""
    try:
        db_manager.clear_all_history()
        return {"status": "success", "message": "History cleared successfully"}
    except Exception as exc:
        log.error("Failed to delete history: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

# ── Main Entry ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    # Read port from env, default to 8000
    port = int(os.environ.get("PORT", 8000))
    log.info("Launching DocMind API Server on port %d", port)
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
