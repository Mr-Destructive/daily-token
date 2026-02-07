"""Fireworks AI free API client."""
import requests
import json


class Fireworks:
    """Fireworks AI free inference API."""
    
    def __init__(self, timeout: int = 30):
        # Fireworks has a free tier with limited calls
        self.base_url = "https://api.fireworks.ai/inference/v1"
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create properly configured session."""
        session = requests.Session()
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Content-Type": "application/json",
        })
        
        return session
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Fireworks."""
        try:
            payload = {
                "model": "accounts/fireworks/models/llama-v2-7b-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            }
            
            r = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            
            data = r.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("message", {}).get("content", "No response")
            
            return "No response"
        
        except Exception as e:
            raise Exception(f"Fireworks: {e}")
