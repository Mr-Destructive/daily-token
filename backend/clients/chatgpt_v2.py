"""ChatGPT free web client - reverse-engineered."""
import requests
import json
import uuid
import time
from typing import Optional


class ChatGPT:
    """ChatGPT free web API client."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://chat.openai.com"
        self.api_base = "https://chat.openai.com/backend-api"
        self.timeout = timeout
        self.session = self._create_session()
        self.conversation_id = None
        self.parent_message_id = str(uuid.uuid4())
    
    def _create_session(self) -> requests.Session:
        """Create properly configured session."""
        session = requests.Session()
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "text/event-stream",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Origin": "https://chat.openai.com",
            "Referer": "https://chat.openai.com/chat",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
        
        return session
    
    def chat(self, prompt: str) -> str:
        """Send prompt to ChatGPT."""
        try:
            payload = {
                "action": "next",
                "messages": [
                    {
                        "id": str(uuid.uuid4()),
                        "role": "user",
                        "content": {
                            "content_type": "text",
                            "parts": [prompt]
                        }
                    }
                ],
                "conversation_id": self.conversation_id,
                "parent_message_id": self.parent_message_id,
                "model": "text-davinci-002-render-sha",
                "timezone_offset_min": -300,
                "suggestions": [],
                "history_and_training_disabled": False,
                "arkose_token": None,
            }
            
            r = self.session.post(
                f"{self.api_base}/conversation",
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            
            response_parts = []
            
            for line in r.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8') if isinstance(line, bytes) else line
                
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        
                        if data.get('message'):
                            msg = data['message']
                            
                            # Store IDs for next request
                            if msg.get('id'):
                                self.parent_message_id = msg['id']
                            
                            if data.get('conversation_id'):
                                self.conversation_id = data['conversation_id']
                            
                            # Extract text
                            if 'content' in msg and 'parts' in msg['content']:
                                parts = msg['content']['parts']
                                if parts:
                                    response_parts.append(parts[0])
                    except:
                        continue
            
            result = "".join(response_parts).strip()
            return result if result else "No response"
        
        except Exception as e:
            raise Exception(f"ChatGPT: {e}")
