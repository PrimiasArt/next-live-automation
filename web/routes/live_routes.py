import os
import signal
from flask import Blueprint, request, jsonify
from core.state import state

live_bp = Blueprint('live', __name__)

@live_bp.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(state.to_dict())

@live_bp.route('/api/order', methods=['POST'])
def order_video():
    data = request.json or {}
    video_name = data.get('video_name')
    is_ft = bool(data.get('ft', False))
    
    # Hỗ trợ cả trường hợp gửi số thứ tự val (1-indexed) để tương thích ngược
    raw_val = data.get('val')
    if not video_name and raw_val is not None:
        try:
            idx = int(raw_val) - 1
            videos = state.current_profile.get("videos", [])
            if 0 <= idx < len(videos):
                video_name = videos[idx]["name"]
        except Exception:
            pass

    if not video_name:
        return jsonify({"success": False, "message": "Tên video không hợp lệ"}), 400

    # Kiểm tra xem video_name có trong profile hiện tại không
    current_videos = [v["name"] for v in state.current_profile.get("videos", [])]
    if video_name not in current_videos:
        return jsonify({"success": False, "message": f"Video '{video_name}' không tồn tại trong Brand hiện tại"}), 400

    state.add_task(video_name, is_fast_track=is_ft)
    return jsonify({"success": True, "target": video_name, "fast_track": is_ft})

@live_bp.route('/api/terminate', methods=['POST'])
def terminate():
    state.add_log("SYSTEM", "🛑 Đã nhận lệnh TERMINATE - Đang đóng tiến trình...")
    os.kill(os.getpid(), signal.SIGTERM)
    return jsonify({"success": True})
