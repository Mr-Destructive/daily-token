
from curl_cffi import requests
import json
import uuid
import re
import time
import random

class Meta:
    """Meta AI API client - reverse-engineered with dynamic tokens."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://www.meta.ai"
        self.timeout = timeout
        self.session = requests.Session(impersonate="chrome")
        self.lsd = None
        self.dtsg = None
        self._init_session()
    
    def _init_session(self):
        """Initialize session and extract tokens."""
        try:
            print("[Meta] Initializing session and extracting tokens...")
            r = self.session.get(self.base_url, timeout=self.timeout)
            if r.status_code == 200:
                # Extract LSD token - search multiple patterns
                lsd_pattern = r'"LSD",\[\],{"token":"([^"]+)"}'
                lsd_match = re.search(lsd_pattern, r.text)
                if lsd_match:
                    self.lsd = lsd_match.group(1)
                    print(f"[Meta] Found LSD: {self.lsd[:10]}...")
                else:
                    # Fallback pattern
                    lsd_match = re.search(r'lsd":"([^"]+)"', r.text)
                    if lsd_match:
                        self.lsd = lsd_match.group(1)
                        print(f"[Meta] Found LSD (fallback): {self.lsd[:10]}...")

                # Extract DTSG token
                dtsg_pattern = r'"DTSGInitialData",\[\],{"token":"([^"]+)"}'
                dtsg_match = re.search(dtsg_pattern, r.text)
                if dtsg_match:
                    self.dtsg = dtsg_match.group(1)
                    print(f"[Meta] Found DTSG: {self.dtsg[:10]}...")
                
                if not self.lsd:
                    print("[Meta] Warning: Could not find LSD token")
            else:
                print(f"[Meta] Init got {r.status_code}")
        except Exception as e:
            print(f"[Meta] Init failed: {e}")

    def chat(self, prompt: str) -> str:
        """Send prompt to Meta AI."""
        if not self.lsd:
            self._init_session()
            
        try:
            url = f"{self.base_url}/api/graphql/"
            
            # Variables structure from discovery
            variables = {
                "message": {"sensitive_string_value": prompt},
                "externalConversationId": str(uuid.uuid4()),
                "offlineThreadingId": str(random.getrandbits(64)),
                "suggestedPromptIndex": None,
                "flashVideoRecapInput": {"images": []},
                "flashPreviewInput": None,
                "promptPrefix": None,
                "entrypoint": "ABRA__CHAT__TEXT",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            }
            
            payload = {
                "lsd": self.lsd,
                "fb_dtsg": self.dtsg,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useAbraSendMessageMutation",
                "variables": json.dumps(variables),
                "server_timestamps": "true",
                "doc_id": "7783822248314888" # Verified from discovery
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "x-fb-lsd": self.lsd,
                "x-asbd-id": "129477", # Standard Meta AI ID
                "Origin": "https://www.meta.ai",
                "Referer": "https://www.meta.ai/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }

            print("[Meta] Sending request...")
            r = self.session.post(url, headers=headers, data=payload, timeout=self.timeout)
            
            if r.status_code != 200:
                return f"Error: HTTP {r.status_code}"
            
            # Parse response chunks (Meta sends multiple JSON objects)
            last_snippet = ""
            for line in r.text.split('\n'):
                if not line: continue
                try:
                    data = json.loads(line)
                    # Meta's response structure for snippets
                    if "data" in data and "node" in data["data"]:
                        node = data["data"]["node"]
                        if "bot_response_message" in node:
                            msg = node["bot_response_message"]
                            if "snippet" in msg:
                                last_snippet = msg["snippet"]
                except:
                    continue
            
            return last_snippet if last_snippet else "No response text found"
        
        except Exception as e:
            raise Exception(f"Meta: {e}")

if __name__ == "__main__":
    client = Meta()
    print(f"\nResponse: {client.chat('What is 2+2?')}")
