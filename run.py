import os
import sys
import threading
import webbrowser
import multiprocessing
from config import WEB_HOST, WEB_PORT
from core.state import state
from core.obs_engine import engine
from web.app import create_app

def main():
    multiprocessing.freeze_support()

    print("=" * 65)
    print("🚀 KHỞI ĐỘNG HỆ THỐNG: HLC CLOUD - DYNAMIC OBS LIVE AUTOMATION")
    print("=" * 65)
    print("⏸️  Hệ thống ở chế độ CHỜ (Standby Mode) - Không can thiệp vào OBS.")
    print("👉 Hãy mở Web Dashboard và chọn Scene OBS bạn muốn live để bắt đầu.")

    # 1. Khởi tạo Flask App
    app = create_app()

    # 2. Chạy Web Server Flask trên Daemon Thread
    def run_server():
        try:
            app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
        except Exception as e:
            print(f"❌ Lỗi khởi chạy Web Server: {e}")
            sys.exit(1)

    web_thread = threading.Thread(target=run_server, daemon=True)
    web_thread.start()
    print(f"🌐 Web Dashboard đang chạy tại: http://localhost:{WEB_PORT}")

    # 3. Tự động mở trình duyệt sau 1.5s
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{WEB_PORT}")).start()

    # 4. Khởi chạy vòng lặp điều khiển OBS Engine trên Main Thread
    print("🎬 Sẵn sàng kết nối OBS. Đang chờ người dùng chọn Scene...")
    try:
        engine.start_loop()
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Đang dừng hệ thống HLC Engine...")
        engine.running = False
        sys.exit(0)

if __name__ == "__main__":
    main()
