# HLC Cloud - Multi-Brand Live Automation System

Hệ thống tự động hóa chuyển cảnh, phát video livestream và quản lý phát sóng đa thương hiệu thông qua **OBS WebSocket v5**, giao diện Web Dashboard Cyberpunk điều khiển thời gian thực và xác thực bản quyền Cloud.

---

## 🌟 Tính Năng Nổi Bật

1. **Khởi động Chế độ Chờ (Standby Mode)**:
   - Khi mở app, hệ thống giữ trạng thái chờ an toàn, hoàn toàn không can thiệp hay thay đổi bất kỳ cài đặt nào trên OBS.
   - Quét danh sách Scene trực tiếp từ OBS Studio để người dùng lựa chọn.

2. **Tự động chuyển Scene & Bảo toàn Layer**:
   - Khi chọn một Scene trên Web Dashboard, OBS sẽ tự động chuyển Program Scene sang Scene đó.
   - **Chỉ tắt mắt các source video có tên dạng `base_xxx`**, bảo vệ nguyên vẹn 100% các layer khác (Khung Camera, Logo thương hiệu, Chữ chạy, Mic/Audio, Khung viền).

3. **Cấu hình RTMP Server & Stream Key Trực Tiếp**:
   - Bảng cài đặt RTMP chuyên nghiệp ngay trên Web Dashboard.
   - Nhập Server URL & Stream Key và bấm "Áp Dụng" $\rightarrow$ Hệ thống tự đẩy trực tiếp vào OBS Settings mà không cần mở cài đặt OBS.
   - Tích hợp sẵn mẫu nhanh cho **TikTok Live**, **Shopee Live**, **Facebook Live**, **YouTube Live**.
   - Cụm nút **Bắt Đầu Live / Dừng Live** trực tiếp trên Web Dashboard kèm đèn báo trạng thái thời gian thực.

4. **Đo thời lượng video chuẩn xác 100% bằng OpenCV**:
   - Tự động trích xuất file video gốc từ OBS Input Settings và đọc chính xác FPS cùng Frame Count bằng thư viện OpenCV.
   - Độ dài video chính xác đến phần trăm giây cho mọi Brand mới mà không cần OBS phải phát video trước.

5. **Fast Switch (Cắt ngang tức thì)**:
   - Khi chuyển đổi giữa các Scene / Brand, hệ thống ngắt ngay video đang phát dở trong vòng 0.1s và kích hoạt Scene mới ngay lập tức.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### 1. Yêu cầu hệ thống
- Python 3.10 hoặc 3.11
- OBS Studio (phiên bản 28.0 trở lên, đã bật WebSocket server tại cổng `4455`)

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Khởi chạy ứng dụng
```bash
python run.py
```
Hệ thống sẽ tự động mở trình duyệt tại địa chỉ: `http://localhost:5000`

---

## 📁 Cấu Trúc Dự Án

```text
Next Live Automation/
├── config.py                 # File cấu hình trung tâm (OBS, Supabase, Ports)
├── requirements.txt          # Thư viện phụ thuộc
├── run.py                    # Entry point khởi động ứng dụng
├── core/
│   ├── state.py              # Thread-safe State, Standby & Fast Switch Event
│   ├── profile_manager.py    # Quản lý Profiles JSON, lọc base_ & đo OpenCV
│   ├── obs_engine.py         # Bộ điều khiển OBS WebSocket, RTMP Stream & Scene
│   └── quota_manager.py      # Quản lý xác thực bản quyền & Quota Supabase
├── web/
│   ├── app.py                # Khởi tạo Flask App
│   ├── routes/
│   │   ├── auth_routes.py    # Login & kích hoạt Cloud Key
│   │   ├── live_routes.py    # Order, Fast-Track, State Polling, Terminate
│   │   ├── profile_routes.py # Đổi Scene, lưu Brand, quét Scene OBS
│   │   └── stream_routes.py  # Cấu hình RTMP Server/Key & Điều khiển Live
│   └── templates/
│       └── index.html        # Web Dashboard Cyberpunk
└── profiles/                 # Thư mục lưu cấu hình từng phiên live / brand
    ├── wipro.json
    └── demo_brand.json
```

---

## ⚙️ Thiết Lập Môi Trường (Tùy chọn)

Bạn có thể cấu hình các biến môi trường nếu cần:
- `OBS_HOST`: Địa chỉ IP của máy chạy OBS (mặc định `127.0.0.1`)
- `OBS_PORT`: Cổng OBS WebSocket (mặc định `4455`)
- `OBS_PASSWORD`: Mật khẩu OBS WebSocket (nếu có đặt mật khẩu)

---
&copy; 2026 HLC Cloud Automation Team.
