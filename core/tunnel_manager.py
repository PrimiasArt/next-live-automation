import os
import re
import sys
import atexit
import threading
import subprocess
import urllib.request
from core.state import state

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(BASE_DIR, "bin")
CLOUDFLARED_PATH = os.path.join(BIN_DIR, "cloudflared.exe")

CLOUDFLARED_DOWNLOAD_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

class TunnelManager:
    def __init__(self):
        self.process = None
        self.public_url = None

    def ensure_cloudflared(self) -> str:
        """Đảm bảo file cloudflared.exe đã sẵn sàng, nếu chưa có thì tự tải"""
        os.makedirs(BIN_DIR, exist_ok=True)
        if not os.path.exists(CLOUDFLARED_PATH) or os.path.getsize(CLOUDFLARED_PATH) < 1000000:
            print("📦 Đang tự động tải bộ công cụ Cloudflare Tunnel (chỉ tải 1 lần duy nhất)...")
            try:
                urllib.request.urlretrieve(CLOUDFLARED_DOWNLOAD_URL, CLOUDFLARED_PATH)
                print("✅ Đã tải xong Cloudflare Tunnel!")
            except Exception as e:
                print(f"❌ Lỗi tải cloudflared: {e}")
                return None
        return CLOUDFLARED_PATH

    def start_tunnel(self, local_port: int = 5000, on_url_ready=None):
        """Khởi chạy Cloudflare Tunnel ngầm và tự động lấy Public URL HTTPS"""
        cf_path = self.ensure_cloudflared()
        if not cf_path:
            return

        def _run():
            try:
                cmd = [cf_path, "tunnel", "--url", f"http://127.0.0.1:{local_port}"]
                # Ẩn cửa sổ console con trên Windows
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = subprocess.CREATE_NO_WINDOW

                self.process = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=creationflags
                )

                # Đăng ký tự đóng process khi thoát app
                atexit.register(self.stop_tunnel)

                for line in self.process.stderr:
                    if not line:
                        continue
                    # Tìm link https://*.trycloudflare.com
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if match and not self.public_url:
                        self.public_url = match.group(0)
                        state.public_url = self.public_url
                        state.add_log("TUNNEL", f"🌐 Web Online: {self.public_url}")
                        
                        if on_url_ready:
                            on_url_ready(self.public_url)
                            
            except Exception as e:
                state.add_log("TUNNEL", f"❌ Lỗi khởi động Tunnel: {e}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def stop_tunnel(self):
        if self.process:
            try:
                self.process.terminate()
                self.process = None
            except Exception:
                pass

tunnel_manager = TunnelManager()
