import os
import sys
import threading
import webbrowser
import multiprocessing
from config import WEB_HOST, WEB_PORT
from core.state import state
from core.obs_engine import engine
from core.tunnel_manager import tunnel_manager
from web.app import create_app

def on_tunnel_ready(public_url):
    print("\n" + "=" * 70)
    print("🎉 HỆ THỐNG LIVE AUTOMATION ĐÃ ONLINE TOÀN CẦU!")
    print("=" * 70)
    print(f"📱 LINK WEB ĐIỀU KHIỂN TỪ XA (MỞ TRÊN ĐIỆN THOẠI/4G Ở BẤT CỨ ĐÂU):")
    print(f"👉 {public_url}")
    print("=" * 70)
    print(f"💻 HOẶC TRUY CẬP TRỰC TIẾP TRÊN MÁY NÀY:")
    print(f"👉 http://localhost:{WEB_PORT}")
    print("=" * 70 + "\n")
    # Tự động mở trình duyệt vào link web online
    webbrowser.open(public_url)

def main():
    multiprocessing.freeze_support()

    print("=" * 70)
    print("🚀 KHỞI ĐỘNG HỆ THỐNG: HLC CLOUD - DYNAMIC OBS LIVE AUTOMATION")
    print("=" * 70)
    print("⏸️  Hệ thống ở chế độ CHỜ (Standby Mode) - Sẵn sàng kết nối OBS nội bộ.")
    print("🌐 Đang tự động kích hoạt đường truyền Web Online (Cloudflare Tunnel)...")

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

    # 3. Kích hoạt Tunnel tự động lấy Public Link
    tunnel_manager.start_tunnel(local_port=WEB_PORT, on_url_ready=on_tunnel_ready)

    # 4. Khởi chạy vòng lặp điều khiển OBS Engine trên Main Thread
    try:
        engine.start_loop()
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Đang dừng hệ thống HLC Engine...")
        engine.running = False
        tunnel_manager.stop_tunnel()
        sys.exit(0)

if __name__ == "__main__":
    main()
