from flask import Blueprint, request, jsonify
from core.state import state
from core.quota_manager import quota_manager
from core.obs_engine import engine

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    api_key = data.get('api_key', '').strip()
    
    if not api_key:
        return jsonify({"success": False, "message": "Vui lòng nhập Cloud API Key"}), 400
        
    res = quota_manager.validate_api_key(api_key)
    if res.get("success"):
        state.set_authorized(True, key_id=res.get("key_id"), quota=res.get("quota_remaining", 0))
        # Không tự đổi scene, không ẩn source gì cả, giữ nguyên OBS và chờ người dùng chọn Scene trên web
        state.add_log("AUTH", "🔑 Đăng nhập thành công! Hệ thống ở chế độ CHỜ. Vui lòng chọn Scene OBS để bắt đầu.")
        return jsonify({"success": True, "quota": state.quota_remaining})
    else:
        return jsonify({"success": False, "message": res.get("message", "API Key không hợp lệ")}), 401
