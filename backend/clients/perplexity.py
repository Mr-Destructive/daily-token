"""Perplexity AI free API client."""
import requests
import json
import uuid


class Perplexity:
    """Perplexity AI free API client."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://api.perplexity.ai"
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create properly configured session."""
        session = requests.Session()
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        
        return session
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Perplexity."""
        try:
            payload = {
                "model": "mistral-7b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
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
            raise Exception(f"Perplexity: {e}")
