"""Mistral AI client - robust HTTP implementation."""
import requests
import json
import uuid
import time
from typing import Optional


class Mistral:
    """Mistral AI API client."""
    
    def __init__(self, timeout: int = 30, retries: int = 3):
        self.base_url = "https://chat.mistral.ai"
        self.timeout = timeout
        self.retries = retries
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create properly configured session."""
        session = requests.Session()
        
        # Chrome headers
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Origin": "https://chat.mistral.ai",
            "Referer": "https://chat.mistral.ai/chat",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-CH-UA": '"Chromium";v="145", "Not:A-Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Linux"',
        })
        
        return session
    
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
        payload = {
            "0": {
                "json": {
                    "content": [{"type": "text", "text": message}],
                    "voiceInput": None,
                    "audioRecording": None,
                    "agentId": None,
                    "agentsApiAgentId": None,
                    "files": [],
                    "isSampleChatForAgentId": None,
                    "model": None,
                    "features": ["beta-websearch"],
                    "integrations": [],
                    "canva": None,
                    "action": None,
                    "libraries": [],
                    "projectId": None,
                    "incognito": False,
                }
            }
        }
        
        r = self.session.post(
            f"{self.base_url}/api/trpc/message.newChat?batch=1",
            json=payload,
            timeout=self.timeout
        )
        
        if r.status_code != 200:
            raise Exception(f"newChat failed: HTTP {r.status_code}")
        
        try:
            resp = r.json()
            if isinstance(resp, list):
                chat_data = resp[0].get("result", {}).get("data", {}).get("json", {})
            else:
                chat_data = resp.get("result", {}).get("data", {}).get("json", {})
            
            chat_id = chat_data.get("id")
            if not chat_id:
                raise Exception("No chat ID in response")
            
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
        
        r = self.session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
            stream=True
        )
        
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
