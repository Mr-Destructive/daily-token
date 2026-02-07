
import cloudscraper
import json
import uuid
import time
import random
import base64
import hashlib
from datetime import datetime, timezone

class ChatGPT:
    """ChatGPT API client - reverse-engineered with Sentinel/Proof of Work."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://chatgpt.com"
        self.timeout = timeout
        self.device_id = str(uuid.uuid4())
        self.scraper = cloudscraper.create_scraper(
            browser={'custom': 'ScraperBot/1.0'},
            delay=10
        )
        self._setup_headers()
        self._init_session()
    
    def _setup_headers(self):
        """Set up proper headers."""
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://chatgpt.com",
            "Referer": "https://chatgpt.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "oai-device-id": self.device_id,
        })
    
    def _init_session(self):
        """Initialize session."""
        try:
            print("[ChatGPT] Initializing session...")
            self.scraper.get(self.base_url, timeout=self.timeout)
            print("[ChatGPT] Session initialized")
        except Exception as e:
            print(f"[ChatGPT] Init failed: {e}")

    def _generate_proof_token(self, seed: str, difficulty: str, user_agent: str) -> str:
        """Generate Proof of Work token."""
        print(f"[ChatGPT] Generating Proof of Work (diff: {difficulty})...")
        
        screen = random.choice([3008, 4010, 6000]) * random.choice([1, 2, 4])
        now_utc = datetime.now(timezone.utc)
        parse_time = now_utc.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        proof_token_parts = [
            screen, parse_time,
            None, 0, user_agent,
            "https://tcr9i.chat.openai.com/v2/35536E1E-65B4-4D96-9D97-6ADB7EFF8147/api.js",
            "dpl=1440a687921de39ff5ee56b92807faaadce73f13", "en", "en-US",
            None,
            "plugins−[object PluginArray]",
            random.choice(["_reactListeningcfilawjnerp", "_reactListening9ne2dfo1i47", "_reactListening410nzwhan2a"]),
            random.choice(["alert", "ontransitionend", "onprogress"])
        ]

        diff_len = len(difficulty)
        for i in range(100000):
            proof_token_parts[3] = i
            json_data = json.dumps(proof_token_parts)
            base = base64.b64encode(json_data.encode()).decode()
            hash_value = hashlib.sha3_512((seed + base).encode()).digest()

            if hash_value.hex()[:diff_len] <= difficulty:
                return "gAAAAAB" + base

        fallback_base = base64.b64encode(f'"{seed}"'.encode()).decode()
        return "gAAAAABwQ8Lk5FbGpA2NcR9dShT6gYjU7VxZ4D" + fallback_base

    def chat(self, prompt: str) -> str:
        """Send prompt to ChatGPT."""
        try:
            # Step 1: Get Chat Requirements
            print("[ChatGPT] Fetching requirements...")
            r_req = self.scraper.post(
                f"{self.base_url}/backend-anon/sentinel/chat-requirements",
                json={"p": None},
                timeout=self.timeout
            )
            
            if r_req.status_code != 200:
                raise Exception(f"Failed to get requirements: {r_req.status_code}")
            
            req_data = r_req.json()
            chat_token = req_data.get("token")
            pow_config = req_data.get("proofofwork", {})
            
            # Step 2: Generate Proof Token
            proof_token = None
            if pow_config.get("required"):
                proof_token = self._generate_proof_token(
                    pow_config.get("seed"),
                    pow_config.get("difficulty"),
                    self.scraper.headers.get("User-Agent")
                )
            
            # Step 3: Send Conversation Request
            payload = {
                "action": "next",
                "messages": [
                    {
                        "id": str(uuid.uuid4()),
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [prompt]},
                        "metadata": {}
                    }
                ],
                "parent_message_id": str(uuid.uuid4()),
                "model": "auto",
                "timezone_offset_min": -330,
                "suggestions": [],
                "history_and_training_disabled": True,
                "conversation_mode": {"kind": "primary_assistant"},
                "force_paragen": False,
                "force_paragen_model_slug": "",
                "force_null_igen": False,
                "force_use_fallback": False,
            }
            
            headers = {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                "OpenAI-Sentinel-Chat-Requirements-Token": chat_token,
            }
            if proof_token:
                headers["OpenAI-Sentinel-Proof-Token"] = proof_token

            print("[ChatGPT] Sending message...")
            r = self.scraper.post(
                f"{self.base_url}/backend-anon/conversation",
                json=payload,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )
            
            if r.status_code != 200:
                error_text = r.text[:500] if hasattr(r, "text") else "No error text"
                raise Exception(f"Conversation failed: HTTP {r.status_code}\n{error_text}")
            
            # Parse response
            response_parts = []
            for line in r.iter_lines():
                if not line:
                    continue
                
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        if "message" in data and "content" in data["message"]:
                            parts = data["message"]["content"].get("parts", [])
                            if parts:
                                response_parts.append(parts[0])
                    except:
                        continue
            
            # Since it's streaming and each chunk contains the full text so far, 
            # we take the last non-empty part
            if response_parts:
                # Find the longest part (last one usually contains the full message)
                result = max(response_parts, key=len)
                return result.strip()
            
            return "No response"
            
        except Exception as e:
            raise Exception(f"ChatGPT: {e}")

if __name__ == "__main__":
    client = ChatGPT()
    print(client.chat("What is 2+2?"))
