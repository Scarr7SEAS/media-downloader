import os
import re
import json
import uuid
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

import yt_dlp
from app.config import DOWNLOADS_DIR, NODE_PATH

logger = logging.getLogger("downloader")
logging.basicConfig(level=logging.INFO)

# In-memory task tracking
TASKS: Dict[str, Dict[str, Any]] = {}

def get_base_ydl_opts() -> dict:
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'restrictfilenames': True,
        'windowsfilenames': True,
    }
    if NODE_PATH and os.path.exists(NODE_PATH):
        opts['js_runtimes'] = {'node': {}}
    return opts

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "Live / N/A"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_bytes(size: Optional[int]) -> str:
    if not size:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def get_media_info(url: str) -> dict:
    opts = get_base_ydl_opts()
    opts['skip_download'] = True
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                # In case of playlist, pick the first video
                info = info['entries'][0]
                
            formats = info.get("formats", [])
            max_height = 0
            max_fps = 0
            for f in formats:
                h = f.get("height") or 0
                fps = f.get("fps") or 0
                if h > max_height:
                    max_height = h
                if fps > max_fps:
                    max_fps = fps

            if max_height >= 2160:
                res_label = f"4K Ultra HD {max_height}p"
            elif max_height >= 1440:
                res_label = f"2K Quad HD {max_height}p"
            elif max_height >= 1080:
                res_label = f"Full HD {max_height}p"
            elif max_height >= 720:
                res_label = f"HD {max_height}p"
            elif max_height > 0:
                res_label = f"{max_height}p"
            else:
                res_label = "Maksimal"

            if max_fps and max_fps >= 50:
                res_label += f" {int(max_fps)}fps"

            return {
                "success": True,
                "title": info.get("title", "Unknown Title"),
                "thumbnail": info.get("thumbnail"),
                "duration": format_duration(info.get("duration")),
                "duration_raw": info.get("duration"),
                "uploader": info.get("uploader") or info.get("creator") or info.get("channel") or "Unknown",
                "extractor": info.get("extractor_key") or info.get("extractor") or "Web",
                "view_count": info.get("view_count"),
                "max_resolution": res_label,
                "max_height": max_height,
                "max_fps": int(max_fps) if max_fps else None,
                "url": url
            }
        except Exception as e:
            logger.error(f"Error fetching info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def probe_media(file_path: Path) -> dict:
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate:format=format_name',
        '-of', 'json', str(file_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        v_codec = None
        a_codec = None
        pix_fmt = None
        width = None
        height = None
        fps = None
        for s in data.get('streams', []):
            if s.get('codec_type') == 'video' and not v_codec:
                v_codec = s.get('codec_name')
                pix_fmt = s.get('pix_fmt')
                width = s.get('width')
                height = s.get('height')
                fps = s.get('r_frame_rate')
            elif s.get('codec_type') == 'audio' and not a_codec:
                a_codec = s.get('codec_name')
        return {
            "v_codec": v_codec,
            "a_codec": a_codec,
            "pix_fmt": pix_fmt,
            "width": width,
            "height": height,
            "fps": fps,
            "is_h264": v_codec == 'h264',
            "is_yuv420p": pix_fmt == 'yuv420p',
            "is_aac": a_codec == 'aac'
        }
    except Exception as e:
        logger.warning(f"ffprobe probe failed: {e}")
        return {
            "v_codec": None, "a_codec": None, "pix_fmt": None,
            "width": None, "height": None, "fps": None,
            "is_h264": False, "is_yuv420p": False, "is_aac": False
        }

def make_cross_platform_compatible(input_path: Path, quality: str = "full") -> Path:
    """
    Handles media processing:
    - 'full': 100% PURE ORIGINAL MASTER.
      If already H.264 (like TikTok or YouTube MP4), copies streams bit-for-bit with ZERO re-encoding,
      ZERO compression, and instant execution.
      If VP9/AV1, transcodes cleanly at CRF 16 (visually lossless) preserving full 4K/fps.
    - 'medium': WHATSAPP & CHAT OPTIMIZED.
      Scales video down to max 720p (720x1280 or 1280x720) with lightweight file size (~3-8 MB),
      clean monotonic timestamps, and Main profile 4.0 so WhatsApp forwarding & Status NEVER hang.
    """
    if not input_path.exists() or input_path.suffix.lower() != '.mp4':
        return input_path

    temp_output = input_path.parent / f"opt_{uuid.uuid4().hex[:8]}_{input_path.name}"
    probe = probe_media(input_path)

    if quality == "full":
        # PURE UNTOUCHED ORIGINAL MASTER
        if probe["is_h264"] and (probe["is_aac"] or probe["a_codec"] is None):
            logger.info(f"Full quality: preserving 100% original untouched bitstream (-c copy): {input_path.name}")
            cmd = [
                'ffmpeg', '-y', '-i', str(input_path),
                '-c', 'copy',
                '-movflags', '+faststart',
                str(temp_output)
            ]
        elif probe["is_h264"] and not probe["is_aac"]:
            logger.info(f"Full quality: keeping video stream untouched (-c:v copy), normalizing audio: {input_path.name}")
            cmd = [
                'ffmpeg', '-y', '-i', str(input_path),
                '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '320k',
                '-movflags', '+faststart',
                str(temp_output)
            ]
        else:
            logger.info(f"Full quality: transcoding VP9/AV1 to H.264 master quality (CRF 16): {input_path.name}")
            cmd = [
                'ffmpeg', '-y',
                '-max_error_rate', '1.0',
                '-err_detect', 'ignore_err',
                '-fflags', '+genpts+discardcorrupt',
                '-i', str(input_path),
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-crf', '16',
                '-pix_fmt', 'yuv420p',
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                '-fps_mode', 'cfr',
                '-c:a', 'aac',
                '-b:a', '320k',
                '-movflags', '+faststart',
                str(temp_output)
            ]
    else:
        # MEDIUM: WhatsApp HD Chat & Status Preset (720p, 30fps CFR, crisp CRF 20, zero PTS jitter)
        # Bypasses WhatsApp's aggressive internal re-compression engine so Status remains sharp and crisp.
        logger.info(f"Medium quality: downscaling to 720p 30fps & optimizing for WhatsApp Status/Chat HD: {input_path.name}")
        cmd = [
            'ffmpeg', '-y',
            '-max_error_rate', '1.0',
            '-err_detect', 'ignore_err',
            '-fflags', '+genpts+discardcorrupt',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '20',
            '-profile:v', 'main',
            '-level', '4.0',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            '-fps_mode', 'cfr',
            '-vf', "setpts=PTS-STARTPTS,scale=w='if(gt(iw,ih),1280,720)':h='if(gt(iw,ih),720,1280)':force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2",
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-ac', '2',
            '-af', 'asetpts=PTS-STARTPTS',
            '-movflags', '+faststart',
            str(temp_output)
        ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        # Replace original file with processed one
        input_path.unlink(missing_ok=True)
        temp_output.rename(input_path)
        logger.info(f"Processing complete for: {input_path.name}")
        return input_path
    except Exception as e:
        logger.error(f"FFmpeg processing error: {e}")
        if temp_output.exists():
            temp_output.unlink(missing_ok=True)
        return input_path

def start_download_task(task_id: str, url: str, quality: str):
    """
    Background worker for downloading and processing media.
    quality: 'medium' (720p MP4), 'full' (Max MP4), 'mp3' (Audio MP3)
    """
    TASKS[task_id] = {
        "task_id": task_id,
        "status": "starting",
        "progress": 0,
        "speed": "0 KB/s",
        "eta": "--",
        "title": "Mempersiapkan...",
        "filename": None,
        "file_size": None,
        "quality": quality,
        "error": None
    }

    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            percent = (downloaded / total * 100) if total > 0 else 0
            
            speed = d.get('speed')
            speed_str = f"{format_bytes(speed)}/s" if speed else "Menghitung..."
            
            eta = d.get('eta')
            eta_str = f"{eta}s" if eta else "--"

            TASKS[task_id]["status"] = "downloading"
            TASKS[task_id]["progress"] = round(percent, 1)
            TASKS[task_id]["speed"] = speed_str
            TASKS[task_id]["eta"] = eta_str
            
        elif d['status'] == 'finished':
            TASKS[task_id]["status"] = "processing"
            TASKS[task_id]["progress"] = 95
            TASKS[task_id]["speed"] = "--"
            TASKS[task_id]["eta"] = "Sedikit lagi..."

    out_template = str(DOWNLOADS_DIR / f"%(title).80s_%(id)s_{task_id[:6]}.%(ext)s")
    ydl_opts = get_base_ydl_opts()
    ydl_opts['progress_hooks'] = [progress_hook]
    ydl_opts['outtmpl'] = out_template

    if quality == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif quality == 'medium':
        # Max 720p, preferred compatible video format
        ydl_opts['format'] = (
            'bestvideo[height<=720][vcodec^=avc]+bestaudio[acodec^=mp4a]/'
            'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/'
            'bestvideo[height<=720]+bestaudio/'
            'best[height<=720]/best'
        )
        ydl_opts['merge_output_format'] = 'mp4'
    else:  # 'full'
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            TASKS[task_id]["status"] = "fetching_info"
            info = ydl.extract_info(url, download=True)
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get("title", "Media")
            TASKS[task_id]["title"] = title

            # Locate downloaded file
            final_ext = "mp3" if quality == "mp3" else "mp4"
            # Search by task_id in filename
            matched_files = list(DOWNLOADS_DIR.glob(f"*{task_id[:6]}.*"))
            if not matched_files:
                # Fallback to info['_filename']
                fn = info.get('_filename')
                if fn:
                    p = Path(fn).with_suffix(f".{final_ext}")
                    if p.exists():
                        matched_files = [p]

            if not matched_files:
                raise RuntimeError("File hasil unduhan tidak ditemukan di direktori downloads.")

            file_path = matched_files[0]

            # If video, ensure full cross-platform compatibility
            if quality in ['medium', 'full'] and file_path.suffix.lower() == '.mp4':
                TASKS[task_id]["status"] = "optimizing"
                file_path = make_cross_platform_compatible(file_path, quality=quality)

            file_size_bytes = file_path.stat().st_size
            TASKS[task_id]["status"] = "completed"
            TASKS[task_id]["progress"] = 100
            TASKS[task_id]["filename"] = file_path.name
            TASKS[task_id]["file_size"] = format_bytes(file_size_bytes)
            TASKS[task_id]["download_url"] = f"/api/download-file/{file_path.name}"
            logger.info(f"Task {task_id} completed: {file_path.name}")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        TASKS[task_id]["status"] = "error"
        TASKS[task_id]["error"] = str(e)
