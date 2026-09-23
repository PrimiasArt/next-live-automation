import obsws_python as obs
import time, random, sys, threading, datetime, webbrowser, os, signal, hashlib
import requests  # Thư viện gọi API lên Supabase Cloud
from collections import deque
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS

# --- CẤU HÌNH HỆ THỐNG OBS ---
OBS_HOST, OBS_PORT = '127.0.0.1', 4455
TARGET_SCENE = "WiPro"
OVERLAP_TIME = 1.0  # Đồng bộ chuẩn mượt phân cảnh

# --- CẤU HÌNH SUPABASE CLOUD --
SUPABASE_URL = "https://frredpdjfmafluafkrmr.supabase.co" 
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZycmVkcGRqZm1hZmx1YWZrcm1yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg3Mzk1NTAsImV4cCI6MjA5NDMxNTU1MH0.Rxd8dz_hZxZjqn6uyoStofhMtA2tEKFVxpsQa3e59Xo" 

# =========================================================================
# KHU VỰC 1: KHO KỊCH BẢN TƯƠNG TÁC (ĐÃ LƯỢC BỎ)
# =========================================================================
SCENARIOS = {}

# =========================================================================
# KHU VỰC 2: TẬP DỮ LIỆU CHẠY NỀN AUTO-LOOP (28 VIDEO BASE)
# =========================================================================

DURATIONS = [
    56.87, 43.47, 39.03, 55.63, 31.67,
    45.30, 46.87, 44.83, 61.63, 52.83,
    56.00, 51.07, 48.20, 20.93, 60.20,
    66.83, 54.77, 50.77, 37.50, 75.90,
    47.93, 27.90, 27.43, 22.40, 24.50,
    32.47, 33.23, 39.87
]

TOTAL_VIDEOS = 28 
BASE_LIST = [{"name": f"base_{i+1}wp", "duration": DURATIONS[i]} for i in range(TOTAL_VIDEOS)]
ALL_DURATIONS_MAP = {f"base_{i+1}wp": DURATIONS[i] for i in range(TOTAL_VIDEOS)}

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["POST", "GET", "OPTIONS"], "allow_headers": ["Content-Type"]}})

web_logs = deque(maxlen=30)
state = {
    "is_authorized": False, 
    "current_video": "System Locked", 
    "remaining": 0.0,
    "task_queue": deque(maxlen=15),  
    "api_key_id": None,
    "quota_remaining": 0
}

global_engine = None  

def add_web_log(tag, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    web_logs.append(f"[{timestamp}] [{tag}] {message}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>HLC CLOUD | HYBRID CENTER</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #050505; color: #e0e0e0; font-family: sans-serif; overflow-x: hidden; }
        .neon-text { color: #1fb6ff; text-shadow: 0 0 10px #1fb6ff; }
        .glass { background: rgba(20, 20, 20, 0.9); border: 1px solid #333; }
        .base-node { height: 45px; border-radius: 6px; background: #111; border: 1px solid #222; cursor: pointer; transition: 0.2s; display:flex; align-items:center; justify-content:center; }
        .base-node:hover { border-color: #1fb6ff; color: #1fb6ff; background: #161b22; }
        .base-active { background: #1fb6ff !important; color: #000 !important; box-shadow: 0 0 20px #1fb6ff; border: none; font-weight: bold; }
        .ft-btn-on { border-color: #f59e0b !important; color: #f59e0b; box-shadow: 0 0 10px #f59e0b33; }
        .terminal { font-family: 'Courier New', Courier, monospace; background: #0a0a0a; border: 1px solid #222; }
    </style>
</head>
<body class="p-8">
    <!-- Màn hình khóa xác thực Cloud API Key -->
    <div id="auth" class="fixed inset-0 bg-black flex items-center justify-center z-50 {{ 'hidden' if is_authorized else '' }}">
        <div class="glass p-10 rounded-2xl w-[28rem] text-center border-t-4 border-blue-500">
            <h1 class="text-3xl font-black neon-text mb-2">HLC CLOUD</h1>
            <p class="text-gray-500 text-xs mb-6">HỆ THỐNG ĐIỀU KHIỂN THỜI GIAN LIVE STREAM</p>
            <input type="password" id="key-input" class="w-full p-3 bg-gray-900 border border-gray-700 rounded mb-4 text-center text-white outline-none focus:border-blue-500 tracking-widest font-mono text-sm" placeholder="NHẬP CLOUD API KEY">
            <button onclick="validateCloudKey()" class="w-full p-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded uppercase tracking-wider transition-all">KÍCH HOẠT HỆ THỐNG</button>
            <p id="error-msg" class="text-red-500 mt-4 text-xs hidden"></p>
        </div>
    </div>

    <div class="max-w-7xl mx-auto">
        <header class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-4xl font-black neon-text">HLC <span class="text-white">CLOUD v12.0</span></h1>
                <p class="text-gray-500 text-xs mt-1">STATION: NAKAMURA | SUPABASE API V5 SYNCED</p>
            </div>
            <div class="flex gap-6 items-center">
                <div class="glass px-4 py-2 rounded-lg border border-yellow-600/30">
                    <span class="text-gray-400 text-[10px] uppercase block">Quota Credits Remaining</span>
                    <span id="cloud-quota" class="text-yellow-500 font-bold font-mono text-sm">0 Credits</span>
                </div>
                <button onclick="terminate()" class="bg-red-900/20 hover:bg-red-600 text-red-500 hover:text-white px-4 py-2 rounded-lg text-xs font-bold border border-red-500/40 transition-all">TERMINATE CORE</button>
            </div>
        </header>

        <div class="grid grid-cols-4 gap-6">
            <div class="col-span-3 space-y-6">
                <div class="glass p-8 rounded-2xl border-l-4 border-blue-500">
                    <div class="flex justify-between items-end mb-4">
                        <div>
                            <span class="text-xs text-gray-500 uppercase tracking-wider">Active Output Pipeline</span>
                            <h2 id="vid" class="text-4xl font-bold mt-1">--</h2>
                        </div>
                        <div id="timer" class="text-5xl font-mono text-yellow-500">0.0s</div>
                    </div>
                    <div class="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                        <div id="bar" class="bg-blue-500 h-full transition-all duration-100" style="width:0%"></div>
                    </div>
                </div>

                <div class="glass p-6 rounded-2xl">
                    <div class="flex justify-between mb-4 items-center">
                        <span class="text-xs text-gray-500">VIDEO MATRIX GRID (1-28: AUTO-LOOP)</span>
                        <button id="ft-btn" onclick="toggleFT()" class="px-4 py-1.5 rounded-full border border-gray-600 text-[10px] font-bold uppercase transition-all">⚡ FAST TRACK: <span id="ft-st">OFF</span></button>
                    </div>
                    <div class="grid grid-cols-10 gap-2">
                        {% for i in range(1, 29) %}
                        <div class="base-node text-xs" data-name="base_{{i}}wp" onclick="order('{{i}}')">{{ i }}</div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <div class="col-span-1 flex flex-col gap-6">
                <div class="glass p-5 rounded-2xl flex flex-col h-56 overflow-hidden">
                    <h3 class="neon-text text-xs font-bold mb-3 uppercase tracking-wider">Next Pipeline Queue</h3>
                    <div id="ql" class="flex flex-col gap-2 overflow-y-auto pr-1 flex-grow"></div>
                </div>

                <div class="glass p-5 rounded-2xl flex flex-col h-72 overflow-hidden border-t-2 border-amber-500/50">
                    <h3 class="text-amber-500 text-xs font-bold mb-3 uppercase tracking-wider flex justify-between items-center">
                        <span>📡 Live Reception Logs</span>
                        <span class="animate-pulse text-[9px] bg-amber-500/20 px-2 py-0.5 rounded text-amber-400">CONSOLE OUT</span>
                    </h3>
                    <div id="log-box" class="terminal p-3 rounded-lg text-[10px] text-emerald-400 overflow-y-auto flex-grow space-y-1.5 scrollbar-thin select-text">
                        <div class="text-gray-600 italic">Awaiting connection pipeline...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ft = false;
        async function validateCloudKey() {
            const key = document.getElementById('key-input').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({api_key: key})
            });
            const data = await res.json();
            if(data.success) {
                document.getElementById('auth').classList.add('hidden');
                updateCycle();
            } else {
                const err = document.getElementById('error-msg');
                err.innerText = data.message;
                err.classList.remove('hidden');
            }
        }

        function toggleFT() {
            ft = !ft;
            const b = document.getElementById('ft-btn');
            document.getElementById('ft-st').innerText = ft ? 'ON' : 'OFF';
            ft ? b.classList.add('ft-btn-on', 'border-amber-500') : b.classList.remove('ft-btn-on', 'border-amber-500');
        }
        function order(val) {
            fetch('/api/order', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({val: val, ft: ft})});
            if(ft) toggleFT();
        }
        function terminate() {
            if(confirm("XÁC NHẬN: Tắt hoàn toàn tiến trình ngầm và giải phóng OBS?")) {
                fetch('/api/terminate', {method:'POST'}).then(() => {
                    document.body.innerHTML = "<div class='h-screen flex items-center justify-center'><h1 class='text-red-500 font-bold text-3xl tracking-widest'>CORE TERMINATED.</h1></div>";
                    setTimeout(() => window.close(), 1000);
                });
            }
        }
        
        async function updateCycle() {
            try {
                const res = await fetch('/api/state');
                const d = await res.json();
                
                document.getElementById('vid').innerText = d.current_video;
                document.getElementById('timer').innerText = d.remaining + 's';
                document.getElementById('bar').style.width = d.progress + '%';
                document.getElementById('cloud-quota').innerText = d.quota_remaining + ' Credits';
                
                document.getElementById('ql').innerHTML = d.queue.length > 0 ? d.queue.map((i,idx) => `<div class="bg-blue-900/10 text-blue-300 p-2 rounded border border-blue-800/20 text-[11px] font-bold flex justify-between"><span>Base ${i}</span><span class='opacity-40'>#${idx+1}</span></div>`).join('') : "<div class='text-xs text-gray-600 italic p-1'>Auto-Loop Active (1wp - 28wp)</div>";
                
                const logBox = document.getElementById('log-box');
                if (d.logs.length > 0) {
                    logBox.innerHTML = d.logs.map(log => {
                        let cls = "text-emerald-400";
                        if(log.includes("[QUEUE]")) cls = "text-amber-400";
                        if(log.includes("[OBS]")) cls = "text-fuchsia-400";
                        return `<div class="${cls}">${log}</div>`;
                    }).join('');
                    logBox.scrollTop = logBox.scrollHeight;
                }

                document.querySelectorAll('.base-node').forEach(n => {
                    n.classList.toggle('base-active', n.getAttribute('data-name') === d.current_video);
                });
            } catch(e) {}
        }
        setInterval(updateCycle, 500);
    </script>
</body>
</html>
"""

@app.route('/')
def index(): 
    return render_template_string(HTML_TEMPLATE, is_authorized=state["is_authorized"])

@app.route('/api/login', methods=['POST'])
def login():
    api_key = request.json.get('api_key', '').strip()
    if not api_key: return {"success": False, "message": "Vui lòng nhập API Key"}
    key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    supabase_api_url = f"{SUPABASE_URL}/rest/v1/api_keys?key_hash=eq.{key_hash}&select=*"
    headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {SUPABASE_ANON_KEY}"}
    try:
        response = requests.get(supabase_api_url, headers=headers)
        if response.status_code == 200 and len(response.json()) > 0:
            key_data = response.json()[0]
            if key_data.get('status') != 'active': return {"success": False, "message": "API Key đã bị khoá!"}
            if key_data.get('quota_remaining', 0) <= 0: return {"success": False, "message": "Hết Quota/Credits hạn mức!"}
            state["is_authorized"] = True
            state["api_key_id"] = key_data.get('id')
            state["quota_remaining"] = key_data.get('quota_remaining', 0)
            
            if global_engine:
                global_engine.hide_all_base_sources()
                
            return {"success": True, "quota": state["quota_remaining"]}
        return {"success": False, "message": "Khóa API Key không chính xác!"}
    except Exception as e: return {"success": False, "message": f"Cloud Error: {str(e)}"}

@app.route('/api/order', methods=['POST'])
def order():
    raw_val = request.json.get('val')
    is_ft = request.json.get('ft', False)
    
    if str(raw_val).isdigit():
        idx = int(raw_val)
        if 1 <= idx <= TOTAL_VIDEOS: 
            target_name = f"base_{idx}wp"
            if is_ft: 
                state["task_queue"].appendleft(idx)
                add_web_log("QUEUE", f"⚡ [FAST TRACK] Đẩy gấp kịch bản {target_name} lên đầu hàng đợi")
            else: 
                state["task_queue"].append(idx)
                add_web_log("QUEUE", f"📥 Đã xếp {target_name} vào cuối hàng chờ")
            return {"success": True, "target": target_name}
        
    return {"success": False, "reason": "invalid_id"}

@app.route('/api/state')
def get_state():
    current_dur = ALL_DURATIONS_MAP.get(state['current_video'], 30.0)
    progress = (1 - (float(state['remaining']) / current_dur)) * 100 if current_dur > 0 else 0
    return {
        "authorized": state["is_authorized"],
        "current_video": state["current_video"], 
        "remaining": round(state["remaining"], 1), 
        "progress": min(100, progress),
        "queue": [f"{i}wp" for i in state["task_queue"]],
        "quota_remaining": state["quota_remaining"],
        "logs": list(web_logs)
    }

@app.route('/api/terminate', methods=['POST'])
def terminate(): os.kill(os.getpid(), signal.SIGTERM); return {"success": True}


class HLCEngine:
    def __init__(self):
        try: self.cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT)
        except Exception: print("❌ Lỗi: OBS chưa mở!"); sys.exit()
        
    def play_video(self, v_name):
        try:
            items = self.cl.get_scene_item_list(TARGET_SCENE).scene_items
            nid = next((i['sceneItemId'] for i in items if i['sourceName'] in [v_name, f"{v_name}.mp4"]), None)
            if nid:
                self.cl.set_scene_item_enabled(TARGET_SCENE, nid, True)
                time.sleep(OVERLAP_TIME)
                if self.last_video and self.last_video != v_name:
                    oid = next((i['sceneItemId'] for i in items if i['sourceName'] in [self.last_video, f"{self.last_video}.mp4"]), None)
                    if oid: self.cl.set_scene_item_enabled(TARGET_SCENE, oid, False)
                self.last_video = v_name
                state["current_video"] = v_name
                return True
        except Exception as e:
            add_web_log("OBS", f"Lỗi chuyển video {v_name}: {str(e)}")
        return False

    def hide_all_base_sources(self):
        try:
            items = self.cl.get_scene_item_list(TARGET_SCENE).scene_items
            hidden_count = 0
            for item in items:
                source_name = item['sourceName']
                if source_name.startswith("base_"):
                    self.cl.set_scene_item_enabled(TARGET_SCENE, item['sceneItemId'], False)
                    hidden_count += 1
            add_web_log("OBS", f"👁️ [AUTO-HIDE] Đã ẩn thành công {hidden_count} nguồn video base.")
            return True
        except Exception as e:
            add_web_log("OBS", f"❌ Lỗi ẩn source trên OBS: {str(e)}")
            return False

    def deduct_cloud_quota(self, amount=1):
        if not state["api_key_id"]: return
        new_quota = max(0, state["quota_remaining"] - amount)
        url = f"{SUPABASE_URL}/rest/v1/api_keys?id=eq.{state['api_key_id']}"
        headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {SUPABASE_ANON_KEY}", "Content-Type": "application/json"}
        try:
            # [BẢN VÁ LỖI]: Bổ sung tham số timeout=5 để tránh treo mạng
            res = requests.patch(url, headers=headers, json={"quota_remaining": new_quota}, timeout=5)
            if res.status_code in [200, 204]: state["quota_remaining"] = new_quota
        except Exception: 
            pass

    def start(self):
        self.last_video = None
        accumulated_seconds = 0.0
        
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
        threading.Timer(2.0, lambda: webbrowser.open("http://localhost:5000")).start()
        
        while True:
            if not state["is_authorized"]: 
                time.sleep(1)
                continue
            if state["quota_remaining"] <= 0:
                state["is_authorized"] = False
                state["current_video"] = "System Locked"
                time.sleep(1)
                continue
            
            if state["task_queue"]:
                next_idx = state["task_queue"].popleft()
                current_name = f"base_{next_idx}wp"
            else:
                current_name = random.choice(list(ALL_DURATIONS_MAP.keys()))
            
            if current_name == self.last_video: 
                continue

            if self.play_video(current_name):
                wait_time = max(0.1, ALL_DURATIONS_MAP.get(current_name, 30.0) - OVERLAP_TIME)
                start_p = time.time()
                while (time.time() - start_p) < wait_time:
                    state["remaining"] = max(0, wait_time - (time.time() - start_p))
                    time.sleep(0.1)
                
                accumulated_seconds += ALL_DURATIONS_MAP.get(current_name, 30.0)
                
                # [BẢN VÁ LỖI]: Gọi lệnh mạng trong một luồng riêng biệt (Daemon Thread)
                if accumulated_seconds >= 60.0:
                    mins = int(accumulated_seconds // 60)
                    threading.Thread(target=self.deduct_cloud_quota, args=(mins,), daemon=True).start()
                    accumulated_seconds -= (mins * 60)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    global_engine = HLCEngine()
    global_engine.start()