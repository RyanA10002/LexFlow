"""
FastAPI backend: execute cells, get results, chat (RAG), indexing, export.
"""
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from backend.tasks import run_cell_async, get_task_result
from backend.llm import LLMManager
from backend.vectorstore import VectorManager

app = FastAPI(title="NextGen Notebook API")
llm = LLMManager(api_key=os.getenv("OPENAI_API_KEY"))
vecmgr = VectorManager()

class ExecuteRequest(BaseModel):
    cell_type: str
    source: str
    connection: Optional[str] = None
    result: Optional[str] = None
    dtype: Optional[str] = "pandas"
    session_id: Optional[str] = None

@app.post("/api/execute")
def execute(req: ExecuteRequest):
    task = run_cell_async.delay(req.dict())
    return {"task_id": task.id}

@app.get("/api/result/{task_id}")
def result(task_id: str):
    res = get_task_result(task_id)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res

class IndexRequest(BaseModel):
    target: str  # "notebook" | "dataset" | "text"
    source_id: str
    vector_db: Optional[str] = "chroma"
    embedding_model: Optional[str] = "openai-text-embedding-3-small"

@app.post("/api/index")
def index(req: IndexRequest):
    jobid = vecmgr.enqueue_index(req.dict())
    return {"index_job_id": jobid}

class ChatRequest(BaseModel):
    session_id: Optional[str]
    message: str
    use_rag: Optional[bool] = True
    top_k: Optional[int] = 5

@app.post("/api/chat")
def chat(req: ChatRequest):
    res = llm.chat(req.message, use_rag=req.use_rag, top_k=req.top_k, session_id=req.session_id)
    return res

@app.post("/api/export/static")
def export_static(file: UploadFile = File(...)):
    # Accept .ngnb JSON and return rendered HTML
    import json, backend.exporter as exporter
    data = json.load(file.file)
    html = exporter.render_static_from_object(data)
    return {"html": html}
