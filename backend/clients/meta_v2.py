
import cloudscraper
import json
import uuid
import re
import time
import random

class Meta:
    """Meta AI API client - reverse-engineered with cloudscraper."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://www.meta.ai"
        self.timeout = timeout
        self.scraper = cloudscraper.create_scraper(
            browser={'custom': 'ScraperBot/1.0'},
            delay=10
        )
        self.lsd = None
        self.dtsg = None
        self.access_token = None
        self._setup_headers()
        self._init_session()
    
    def _setup_headers(self):
        """Set up proper headers."""
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.meta.ai",
            "Referer": "https://www.meta.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "x-asbd-id": "129477",
        })

    def _init_session(self):
        """Initialize session by extracting tokens from the home page."""
        try:
            print("[Meta] Initializing session...")
            r = self.scraper.get(self.base_url, timeout=self.timeout)
            
            if r.status_code == 200:
                text = r.text
                
                # Extract LSD token
                lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', text)
                if lsd_match:
                    self.lsd = lsd_match.group(1)
                    print("[Meta] Found LSD token")
                
                # Extract DTSG token
                dtsg_match = re.search(r'"DTSGInitialData",\[\],{"token":"([^"]+)"}', text)
                if dtsg_match:
                    self.dtsg = dtsg_match.group(1)
                    print("[Meta] Found DTSG token")
                
                # Try to get access token for temporary user
                self._update_access_token()
                
            else:
                print(f"[Meta] Init got {r.status_code}")
        except Exception as e:
            print(f"[Meta] Init failed: {e}")

    def _update_access_token(self):
        """Get access token for temporary user."""
        if not self.lsd:
            return
            
        url = f"{self.base_url}/api/graphql/"
        payload = {
            "lsd": self.lsd,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraAcceptTOSForTempUserMutation",
            "variables": json.dumps({
                "dob": "1999-01-01",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            }),
            "doc_id": "7604648749596940",
        }
        headers = {
            "x-fb-friendly-name": "useAbraAcceptTOSForTempUserMutation",
            "x-fb-lsd": self.lsd,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        try:
            r = self.scraper.post(url, headers=headers, data=payload, timeout=self.timeout)
            if r.status_code == 200:
                data = r.json()
                if "data" in data and "xab_abra_accept_terms_of_service" in data["data"]:
                    tos_data = data["data"]["xab_abra_accept_terms_of_service"]
                    if "new_temp_user_auth" in tos_data:
                        self.access_token = tos_data["new_temp_user_auth"].get("access_token")
                        if self.access_token:
                            print("[Meta] Found temporary access token")
        except Exception as e:
            print(f"[Meta] Failed to get access token: {e}")

    def chat(self, prompt: str) -> str:
        """Send prompt to Meta AI."""
        try:
            if self.access_token:
                url = "https://graph.meta.ai/graphql?locale=user"
                base_payload = {"access_token": self.access_token}
            else:
                url = f"{self.base_url}/api/graphql/"
                base_payload = {"lsd": self.lsd, "fb_dtsg": self.dtsg} if self.lsd else {}

            payload = {
                **base_payload,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useAbraSendMessageMutation",
                "variables": json.dumps({
                    "message": {"sensitive_string_value": prompt},
                    "externalConversationId": str(uuid.uuid4()),
                    "offlineThreadingId": self._generate_offline_threading_id(),
                    "suggestedPromptIndex": None,
                    "flashVideoRecapInput": {"images": []},
                    "flashPreviewInput": None,
                    "promptPrefix": None,
                    "entrypoint": "ABRA__CHAT__TEXT",
                    "icebreaker_type": "TEXT",
                    "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                    "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
                }),
                "server_timestamps": "true",
                "doc_id": "7783822248314888"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "x-fb-friendly-name": "useAbraSendMessageMutation",
            }
            if self.lsd:
                headers["x-fb-lsd"] = self.lsd

            print("[Meta] Sending message...")
            r = self.scraper.post(url, headers=headers, data=payload, timeout=self.timeout, stream=True)
            
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")
            
            last_snippet = ""
            
            for line in r.iter_lines():
                if not line:
                    continue
                
                try:
                    line_str = line.decode('utf-8')
                    data = json.loads(line_str)
                    
                    if "data" in data and "node" in data["data"]:
                        bot_msg = data["data"]["node"].get("bot_response_message", {})
                        if "snippet" in bot_msg:
                            last_snippet = bot_msg["snippet"]
                except:
                    continue
            
            return last_snippet if last_snippet else "No response"
        
        except Exception as e:
            raise Exception(f"Meta: {e}")

    def _generate_offline_threading_id(self) -> str:
        random_value = random.getrandbits(64)
        timestamp = int(time.time() * 1000)
        threading_id = (timestamp << 22) | (random_value & ((1 << 22) - 1))
        return str(threading_id)

if __name__ == "__main__":
    client = Meta()
    resp = client.chat("What is 2+2?")
    print(f"Response: {resp}")
