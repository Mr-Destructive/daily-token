"""Groq free API client - fast inference."""
import requests
import json
import os


class Groq:
    """Groq free inference API."""
    
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv("GROQ_API_KEY")
        
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
        else:
            self.session.headers.update({
                "Content-Type": "application/json",
            })
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Groq."""
        try:
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 512,
            }
            
            r = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=30
            )
            
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            
            data = r.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("message", {}).get("content", "No response")
            
            return "No response"
        
        except Exception as e:
            raise Exception(f"Groq: {e}")
