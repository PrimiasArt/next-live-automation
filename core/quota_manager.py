import hashlib
import requests
from config import SUPABASE_URL, SUPABASE_ANON_KEY

class QuotaManager:
    def __init__(self, supabase_url: str = SUPABASE_URL, anon_key: str = SUPABASE_ANON_KEY):
        self.supabase_url = supabase_url
        self.anon_key = anon_key
        self.headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
            "Content-Type": "application/json"
        }

    def validate_api_key(self, api_key: str) -> dict:
        api_key = api_key.strip()
        if not api_key:
            return {"success": False, "message": "Vui lòng nhập API Key"}
            
        key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
        url = f"{self.supabase_url}/rest/v1/api_keys?key_hash=eq.{key_hash}&select=*"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            if res.status_code == 200 and len(res.json()) > 0:
                key_data = res.json()[0]
                if key_data.get('status') != 'active':
                    return {"success": False, "message": "API Key đã bị khóa!"}
                
                quota = key_data.get('quota_remaining', 0)
                if quota <= 0:
                    return {"success": False, "message": "Hết Quota/Credits hạn mức!"}
                
                return {
                    "success": True,
                    "key_id": key_data.get('id'),
                    "quota_remaining": quota
                }
            return {"success": False, "message": "Khóa API Key không chính xác!"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi kết nối Supabase Cloud: {str(e)}"}

    def deduct_quota(self, api_key_id, new_quota: int) -> bool:
        if not api_key_id:
            return False
            
        url = f"{self.supabase_url}/rest/v1/api_keys?id=eq.{api_key_id}"
        try:
            res = requests.patch(url, headers=self.headers, json={"quota_remaining": max(0, new_quota)}, timeout=5)
            return res.status_code in [200, 204]
        except Exception as e:
            print(f"Lỗi cập nhật quota Supabase: {e}")
            return False

quota_manager = QuotaManager()
