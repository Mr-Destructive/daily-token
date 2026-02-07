"""Mistral AI client - using cloudscraper to bypass Cloudflare."""
import json
import uuid
import time
import cloudscraper


class Mistral:
    """Mistral AI API client - Cloudflare-aware."""
    
    def __init__(self, timeout: int = 30, retries: int = 3):
        self.base_url = "https://chat.mistral.ai"
        self.timeout = timeout
        self.retries = retries
        # Use cloudscraper which automatically handles Cloudflare challenges
        # Initialize with longer delay to give time for challenge solving
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
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://chat.mistral.ai",
            "Referer": "https://chat.mistral.ai/chat",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
        # Remove Accept-Encoding to let the session handle it
        if 'Accept-Encoding' in self.scraper.headers:
            del self.scraper.headers['Accept-Encoding']
    
    def _init_session(self):
        """Initialize session by visiting main page first."""
        try:
            print("[Mistral] Initializing session and solving Cloudflare challenges...")
            r = self.scraper.get(f"{self.base_url}/chat", timeout=self.timeout)
            print(f"[Mistral] Session initialized (status: {r.status_code})")
        except Exception as e:
            print(f"[Mistral] Session init warning: {e}")
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Mistral with retries."""
        for attempt in range(self.retries):
            try:
                return self._do_chat(prompt)
            except Exception as e:
                if attempt < self.retries - 1:
                    wait = 2 ** attempt
                    print(f"[Mistral] Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise Exception(f"Mistral failed after {self.retries} attempts: {e}")
    
    def _do_chat(self, prompt: str) -> str:
        """Execute chat request."""
        # Step 1: Create new chat
        chat_id = self._create_chat(prompt)
        
        # Step 2: Get response stream
        response = self._get_response(chat_id)
        
        return response
    
    def _create_chat(self, message: str) -> str:
        """Create new chat and return chat ID."""
        # Use minimal valid payload based on API requirements
        payload = {
            "0": {
                "json": {
                    "content": [{"type": "text", "text": message}],
                    "files": [],
                    "incognito": False,
                }
            }
        }
        
        print("[Mistral] Creating new chat...")
        r = self.scraper.post(
            f"{self.base_url}/api/trpc/message.newChat?batch=1",
            json=payload,
            timeout=self.timeout
        )
        
        print(f"[Mistral] Chat creation response: {r.status_code}")
        print(f"[Mistral] Response length: {len(r.text)}")
        if len(r.text) > 0:
            print(f"[Mistral] Response preview: {r.text[:200]}")
        
        if r.status_code != 200:
            raise Exception(f"newChat failed: HTTP {r.status_code}\nBody: {r.text[:200]}")
        
        try:
            # requests library auto-decompresses gzip responses
            resp = r.json()
            if isinstance(resp, list):
                chat_data = resp[0].get("result", {}).get("data", {}).get("json", {})
            else:
                chat_data = resp.get("result", {}).get("data", {}).get("json", {})
            
            # Chat ID is in the top level of chat_data
            chat_id = chat_data.get("chatId")
            if not chat_id:
                raise Exception(f"No chatId in response")
            
            print(f"[Mistral] Chat ID obtained: {chat_id[:20]}...")
            return chat_id
        except Exception as e:
            raise Exception(f"Failed to parse chat response: {e}")
    
    def _get_response(self, chat_id: str) -> str:
        """Get response from chat stream."""
        payload = {
            "chatId": chat_id,
            "mode": "start",
            "disabledFeatures": ["memory-inference"],
            "clientPromptData": {
                "currentDate": time.strftime("%Y-%m-%d"),
                "userTimezone": "UTC",
            },
            "stableAnonymousIdentifier": str(uuid.uuid4()),
            "shouldAwaitStreamBackgroundTasks": True,
            "shouldUseMessagePatch": True,
            "shouldUsePersistentStream": True,
        }
        
        print("[Mistral] Getting response stream...")
        r = self.scraper.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
            stream=True
        )
        
        print(f"[Mistral] Stream response: {r.status_code}")
        
        if r.status_code != 200:
            raise Exception(f"Stream failed: HTTP {r.status_code}")
        
        # Parse streaming response
        response_parts = []
        
        for line in r.iter_lines():
            if not line:
                continue
            
            try:
                line_str = line if isinstance(line, str) else line.decode('utf-8')
                
                # Parse format: "15:{"json":{...}}"
                if ':' in line_str:
                    parts = line_str.split(':', 1)
                    if len(parts) == 2:
                        json_str = parts[1]
                        data = json.loads(json_str)
                        
                        # Extract text from patches
                        if 'json' in data and 'patches' in data['json']:
                            patches = data['json']['patches']
                            
                            for patch in patches:
                                if patch.get('op') == 'append':
                                    path = patch.get('path', '')
                                    if 'text' in path or 'contentChunks' in path:
                                        value = patch.get('value', '')
                                        if value:
                                            response_parts.append(value)
            except:
                continue
        
        result = "".join(response_parts).strip()
        return result if result else "No response"
