import sys
import socket
import webbrowser
import threading
import time
import uvicorn
from app.config import HOST, PORT

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    lan_ip = get_lan_ip()
    print("=" * 64)
    print("⚡ Universal Media Downloader (YouTube & TikTok)")
    print(f"🖥️  Akses di PC ini       : http://localhost:{PORT}")
    print(f"📱 Akses dari HP (Wi-Fi) : http://{lan_ip}:{PORT}")
    print("🌍 Kompatibel semua perangkat & platform (H.264 / AAC / MP3)")
    print("=" * 64)
    
    # Buka browser otomatis di PC
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Jalankan server FastAPI
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
