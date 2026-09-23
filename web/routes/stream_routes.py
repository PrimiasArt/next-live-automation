from flask import Blueprint, request, jsonify
from core.obs_engine import engine

stream_bp = Blueprint('stream', __name__)

@stream_bp.route('/api/stream/settings', methods=['GET'])
def get_stream_settings():
    res = engine.get_stream_settings()
    return jsonify(res)

@stream_bp.route('/api/stream/settings', methods=['POST'])
def set_stream_settings():
    data = request.json or {}
    server = data.get('server', '').strip()
    key = data.get('key', '').strip()
    service_type = data.get('service_type', 'rtmp_custom')

    if not server:
        return jsonify({"success": False, "message": "Vui lòng nhập RTMP Server URL"}), 400

    res = engine.set_stream_settings(server=server, key=key, service_type=service_type)
    status_code = 200 if res.get("success") else 500
    return jsonify(res), status_code

@stream_bp.route('/api/stream/status', methods=['GET'])
def get_stream_status():
    status = engine.get_stream_status()
    return jsonify({"success": True, **status})

@stream_bp.route('/api/stream/start', methods=['POST'])
def start_stream():
    res = engine.start_streaming()
    status_code = 200 if res.get("success") else 500
    return jsonify(res), status_code

@stream_bp.route('/api/stream/stop', methods=['POST'])
def stop_stream():
    res = engine.stop_streaming()
    status_code = 200 if res.get("success") else 500
    return jsonify(res), status_code
