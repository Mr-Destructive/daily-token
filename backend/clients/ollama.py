"""Ollama local LLM client - requires local Ollama server."""
import requests
import json


class Ollama:
    """Ollama local LLM client."""
    
    def __init__(self, host: str = "http://localhost:11434"):
        self.base_url = host
        self.model = "mistral"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        self._check_health()
    
    def _check_health(self):
        """Check if Ollama server is available."""
        try:
            r = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                print(f"[Ollama] Server is ready")
            else:
                print(f"[Ollama] Warning: Server returned {r.status_code}")
        except Exception as e:
            print(f"[Ollama] Server not available: {e}")
            print(f"[Ollama] Run: ollama serve")
    
    def chat(self, prompt: str) -> str:
        """Send prompt to local Ollama."""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
            
            r = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            
            data = r.json()
            if "message" in data:
                return data["message"].get("content", "No response")
            
            return "No response"
        
        except Exception as e:
            raise Exception(f"Ollama: {e}")
