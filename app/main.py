import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import DOWNLOADS_DIR, BASE_DIR
from app.downloader import (
    get_media_info,
    start_download_task,
    TASKS,
    format_bytes
)

app = FastAPI(title="Video & Audio Downloader", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
STATIC_DIR = BASE_DIR / "app" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    quality: str = "medium"  # 'medium', 'full', 'mp3'

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = BASE_DIR / "app" / "templates" / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>UI Sedang Dimuat...</h1>", status_code=200)
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

@app.post("/api/info")
async def fetch_info(req: InfoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL tidak boleh kosong.")
    info = get_media_info(url)
    if not info.get("success"):
        raise HTTPException(status_code=400, detail=info.get("error", "Gagal memproses URL"))
    return info

@app.post("/api/download")
async def trigger_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL tidak boleh kosong.")
    if req.quality not in ["medium", "full", "mp3"]:
        raise HTTPException(status_code=400, detail="Opsi kualitas tidak valid.")

    task_id = str(uuid.uuid4())
    background_tasks.add_task(start_download_task, task_id, url, req.quality)
    return {"success": True, "task_id": task_id}

@app.get("/api/status/{task_id}")
async def check_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task tidak ditemukan.")
    return task

@app.get("/api/download-file/{filename}")
async def download_file(filename: str):
    # Sanitize path to prevent directory traversal
    clean_name = os.path.basename(filename)
    file_path = DOWNLOADS_DIR / clean_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")

    media_type = "audio/mpeg" if clean_name.lower().endswith(".mp3") else "video/mp4"
    return FileResponse(
        path=str(file_path),
        filename=clean_name,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{clean_name}"'}
    )

@app.get("/api/history")
async def get_history():
    files = []
    if DOWNLOADS_DIR.exists():
        for f in sorted(DOWNLOADS_DIR.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.is_file() and f.suffix.lower() in [".mp4", ".mp3"]:
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "size": format_bytes(stat.st_size),
                    "ext": f.suffix.lower().replace(".", ""),
                    "download_url": f"/api/download-file/{f.name}",
                    "created_at": stat.st_mtime
                })
    return {"files": files}

@app.delete("/api/delete/{filename}")
async def delete_file(filename: str):
    clean_name = os.path.basename(filename)
    file_path = DOWNLOADS_DIR / clean_name
    if file_path.exists():
        file_path.unlink()
        return {"success": True, "message": f"{clean_name} berhasil dihapus"}
    raise HTTPException(status_code=404, detail="File tidak ditemukan")
