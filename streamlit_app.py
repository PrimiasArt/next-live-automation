import streamlit as st
import time
import os
import sys
import re

# Đảm bảo đường dẫn import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OBS_HOST, OBS_PORT, OBS_PASSWORD
from core.profile_manager import profile_manager
from core.quota_manager import quota_manager
import obsws_python as obs

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="HLC Cloud | Live Automation Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách Cyberpunk Dark Theme
st.markdown("""
<style>
    .stApp {
        background-color: #07090e;
        color: #e2e8f0;
    }
    .neon-title {
        color: #38bdf8;
        font-weight: 800;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
        font-size: 1.8rem;
    }
    .auth-card {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-top: 4px solid #0284c7;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stSidebar"] {
        background-color: #0d121d;
        border-right: 1px solid #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if "is_authorized" not in st.session_state:
    st.session_state.is_authorized = False
if "api_key_id" not in st.session_state:
    st.session_state.api_key_id = None
if "quota_remaining" not in st.session_state:
    st.session_state.quota_remaining = 0
if "obs_host" not in st.session_state:
    st.session_state.obs_host = OBS_HOST
if "obs_port" not in st.session_state:
    st.session_state.obs_port = OBS_PORT
if "obs_password" not in st.session_state:
    st.session_state.obs_password = OBS_PASSWORD
if "active_scene" not in st.session_state:
    st.session_state.active_scene = None
if "current_video" not in st.session_state:
    st.session_state.current_video = "Chế độ chờ (Vui lòng chọn Scene)"

# =========================================================================
# 1. MÀN HÌNH KHÓA XÁC THỰC CLOUD API KEY (SUPABASE AUTH)
# =========================================================================
if not st.session_state.is_authorized:
    st.write("")
    st.write("")
    col_left, col_center, col_right = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown("""
        <div class="auth-card text-center">
            <h2 style="color:#38bdf8; font-weight:900; margin-bottom:4px;">🔑 HLC CLOUD</h2>
            <p style="color:#94a3b8; font-size:12px; margin-bottom:20px; text-transform:uppercase; letter-spacing:1px;">
                HỆ THỐNG ĐIỀU KHIỂN THỜI GIAN LIVE STREAM
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        input_key = st.text_input("Nhập Cloud API Key:", type="password", placeholder="NHẬP CLOUD API KEY ĐỂ KÍCH HOẠT", label_visibility="collapsed")
        
        if st.button("KÍCH HOẠT HỆ THỐNG ⚡", type="primary", use_container_width=True):
            if not input_key.strip():
                st.error("Vui lòng nhập Cloud API Key!")
            else:
                with st.spinner("Đang xác thực khóa qua Supabase Cloud..."):
                    res = quota_manager.validate_api_key(input_key)
                    if res.get("success"):
                        st.session_state.is_authorized = True
                        st.session_state.api_key_id = res.get("key_id")
                        st.session_state.quota_remaining = res.get("quota_remaining", 0)
                        st.success(f"Kích hoạt thành công! Hạn mức: {st.session_state.quota_remaining} Credits")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(res.get("message", "API Key không hợp lệ!"))
                        
        st.caption("🔒 Bản quyền được quản lý và bảo vệ bởi Supabase Cloud Authentication.")
    st.stop()  # Dừng ở đây nếu chưa xác thực, không hiển thị Dashboard

# =========================================================================
# 2. HÀM KẾT NỐI OBS CLIENT (TỰ ĐỘNG TÁCH HOST & PORT NẾU DÙNG NGROK)
# =========================================================================
def parse_host_port(raw_host, raw_port):
    """Hỗ trợ tự tách host và port nếu người dùng paste nguyên link tcp://0.tcp.ap.ngrok.io:12345"""
    clean_host = raw_host.strip().replace("tcp://", "")
    if ":" in clean_host:
        parts = clean_host.split(":")
        return parts[0], int(parts[1])
    try:
        return clean_host, int(raw_port)
    except Exception:
        return clean_host, 4455

@st.cache_resource
def get_obs_client(host, port, password):
    try:
        h, p = parse_host_port(str(host), str(port))
        kwargs = {"host": h, "port": p, "timeout": 4}
        if password:
            kwargs["password"] = password
        client = obs.ReqClient(**kwargs)
        return client, None
    except Exception as e:
        return None, str(e)

client, conn_err = get_obs_client(st.session_state.obs_host, st.session_state.obs_port, st.session_state.obs_password)

# =========================================================================
# 3. SIDEBAR: KẾT NỐI OBS & RTMP STREAM
# =========================================================================
with st.sidebar:
    # Hiển thị Quota & Đăng xuất
    st.markdown(f"**Credits Hạn Mức:** 🟡 `{st.session_state.quota_remaining} Credits`")
    if st.button("🔒 Khóa hệ thống / Đăng xuất", use_container_width=True):
        st.session_state.is_authorized = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔌 Kết Nối OBS Studio")
    
    col_h, col_p = st.columns([2, 1])
    with col_h:
        new_host = st.text_input("OBS Host", value=st.session_state.obs_host, placeholder="127.0.0.1 hoặc ngrok")
    with col_p:
        new_port = st.text_input("Port", value=str(st.session_state.obs_port))
    new_pass = st.text_input("Mật khẩu OBS", value=st.session_state.obs_password, type="password")

    if st.button("🔄 Kết nối lại OBS", use_container_width=True):
        st.session_state.obs_host = new_host
        st.session_state.obs_port = new_port
        st.session_state.obs_password = new_pass
        st.cache_resource.clear()
        st.rerun()

    if client:
        st.success("🟢 OBS: Đã kết nối WebSocket v5")
    else:
        st.error(f"🔴 OBS: Chưa kết nối ({conn_err})")
        # Hướng dẫn kết nối khi chạy trên Streamlit Cloud
        st.info("""
        💡 **Bạn đang mở web trên Streamlit Cloud:**
        Server Cloud không thể truy cập trực tiếp `127.0.0.1` của máy bạn.
        
        👉 **Để kết nối OBS trên máy tính:**
        1. Mở PowerShell trên máy tính gõ:
           `ngrok tcp 4455`
        2. Copy link (ví dụ: `0.tcp.ap.ngrok.io:14231`) dán vào ô **OBS Host** ở trên rồi bấm **Kết nối lại OBS**.
        """)

    st.markdown("---")
    st.markdown("### 📡 Cấu Hình RTMP Stream")
    
    # Template chọn nhanh
    tmpl = st.selectbox("Chọn nhanh nền tảng:", ["-- Tùy chỉnh --", "TikTok Live", "Shopee Live", "Facebook Live", "YouTube Live"])
    default_server = ""
    if tmpl == "TikTok Live":
        default_server = "rtmp://live-upload.tiktok.com/live/"
    elif tmpl == "Shopee Live":
        default_server = "rtmp://live.shopee.vn/live/"
    elif tmpl == "Facebook Live":
        default_server = "rtmps://live-api-s.facebook.com:443/rtmp/"
    elif tmpl == "YouTube Live":
        default_server = "rtmp://a.rtmp.youtube.com/live2"

    rtmp_server = st.text_input("Server URL (RTMP)", value=default_server, placeholder="rtmp://...")
    rtmp_key = st.text_input("Stream Key", type="password", placeholder="Nhập khóa luồng")

    if st.button("⚡ Đẩy Cấu Hình Sang OBS", use_container_width=True):
        if not client:
            st.error("Chưa kết nối tới OBS Studio!")
        elif not rtmp_server:
            st.warning("Vui lòng nhập Server URL!")
        else:
            try:
                client.set_stream_service_settings("rtmp_custom", {"server": rtmp_server.strip(), "key": rtmp_key.strip()})
                st.success("✅ Đã cập nhật RTMP Server & Key sang OBS thành công!")
            except Exception as e:
                st.error(f"Lỗi: {e}")

    # Cụm điều khiển Live Stream
    st.markdown("---")
    st.markdown("### 🔴 Điều Khiển Live Stream")
    if client:
        try:
            stream_status = client.get_stream_status()
            is_live = getattr(stream_status, "output_active", False)
            timecode = getattr(stream_status, "output_timecode", "00:00:00")
            
            if is_live:
                st.markdown(f"**Trạng thái:** 🔴 <span style='color:#ef4444;font-weight:bold;'>ĐANG LIVE ({timecode})</span>", unsafe_allow_html=True)
                if st.button("⏹ DỪNG LIVE STREAM", type="primary", use_container_width=True):
                    client.stop_stream()
                    st.rerun()
            else:
                st.markdown("**Trạng thái:** ⚪ OFFLINE (Chưa phát live)")
                if st.button("🔴 BẮT ĐẦU PHÁT LIVE", use_container_width=True):
                    client.start_stream()
                    st.rerun()
        except Exception:
            st.warning("Không lấy được trạng thái stream từ OBS")

# =========================================================================
# 4. MAIN PANEL: ĐIỀU KHIỂN SCENE & VIDEO MATRIX
# =========================================================================
st.markdown("<div class='neon-title'>🎬 HLC CLOUD | LIVE AUTOMATION DASHBOARD</div>", unsafe_allow_html=True)
st.caption("Quản lý chuyển cảnh đa thương hiệu, tự động nhận diện video base_xxx và điều khiển OBS từ xa.")

# Lấy danh sách Scene từ OBS
scene_list = []
if client:
    try:
        scenes_res = client.get_scene_list()
        scene_list = [s['sceneName'] for s in scenes_res.scenes]
    except Exception as e:
        st.error(f"Lỗi quét danh sách Scene: {e}")

col_scene, col_btn, col_standby = st.columns([3, 1, 1])

with col_scene:
    selected_scene = st.selectbox("🎯 Chọn Scene OBS để Live:", ["-- Chọn một Scene --"] + scene_list)

with col_btn:
    st.write("")
    st.write("")
    if st.button("▶ KÍCH HOẠT SCENE", type="primary", use_container_width=True):
        if selected_scene and selected_scene != "-- Chọn một Scene --" and client:
            try:
                # 1. Chuyển scene trong OBS
                client.set_current_program_scene(selected_scene)
                # 2. Tắt mắt các source base_xxx
                items_res = client.get_scene_item_list(selected_scene)
                for item in items_res.scene_items:
                    s_name = item.get('sourceName', '')
                    if s_name.lower().startswith("base_"):
                        client.set_scene_item_enabled(selected_scene, item['sceneItemId'], False)
                
                st.session_state.active_scene = selected_scene
                st.success(f"Đã chuyển OBS sang Scene '{selected_scene}' và chỉ ẩn các source base_*!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")

with col_standby:
    st.write("")
    st.write("")
    if st.button("⏸ CHẾ ĐỘ CHỜ", use_container_width=True):
        st.session_state.active_scene = None
        st.session_state.current_video = "Chế độ chờ (Vui lòng chọn Scene)"
        st.info("Hệ thống đã về Chế độ Chờ (Standby)")
        st.rerun()

# Hiển thị thông tin Scene đang Active
if st.session_state.active_scene and client:
    st.markdown("---")
    st.markdown(f"#### 📺 Scene Đang Hoạt Động: `{st.session_state.active_scene}`")

    # Lấy danh sách các video base_
    try:
        scan_data = profile_manager.scan_scene_items(client, st.session_state.active_scene)
        videos = scan_data.get("videos", [])
        
        st.caption(f"Tìm thấy **{len(videos)}** video chuẩn `base_*` (Đã tự động loại bỏ các layer camera, logo, text).")

        if videos:
            st.markdown("##### 🎛️ Ma Trận Video Matrix Grid (Bấm để phát hoặc chọn):")
            cols = st.columns(5)
            for idx, v in enumerate(videos):
                c = cols[idx % 5]
                with c:
                    v_title = v.get("title", v["name"])
                    v_dur = f"{v.get('duration', 30.0)}s"
                    btn_label = f"#{idx+1} {v_title}\n({v_dur})"
                    
                    if st.button(btn_label, key=f"vid_{idx}", use_container_width=True):
                        try:
                            items = client.get_scene_item_list(st.session_state.active_scene).scene_items
                            for it in items:
                                s_name = it.get('sourceName', '')
                                if s_name.lower().startswith("base_"):
                                    client.set_scene_item_enabled(st.session_state.active_scene, it['sceneItemId'], (s_name == v["name"]))
                            st.session_state.current_video = v["name"]
                            st.toast(f"🎬 Đang phát: {v['name']}")
                        except Exception as e:
                            st.error(f"Lỗi: {e}")
        else:
            st.warning("⚠️ Scene này chưa có video nào có tên dạng 'base_xxx'. Hãy đặt tên video dạng base_1, base_2 trong OBS!")
    except Exception as e:
        st.error(f"Lỗi quét source trong scene: {e}")
else:
    st.markdown("---")
    st.info("💡 **Hệ thống đang ở chế độ CHỜ (STANDBY)**. Hãy chọn một Scene trong OBS từ dropdown bên trên và bấm **▶ KÍCH HOẠT SCENE** để bắt đầu!")

# Footer
st.markdown("---")
st.caption("HLC Cloud Hybrid Live Automation © 2026 | Built with Streamlit & OBS WebSocket v5")
