"""Hugging Face Inference API client - free tier."""
import requests
import json
import os


class HuggingFace:
    """Hugging Face Inference API client."""
    
    def __init__(self, api_key: str = None, timeout: int = 30):
        if not api_key:
            api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"
        self.model = "mistralai/Mistral-7B-Instruct-v0.1"
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create properly configured session."""
        session = requests.Session()
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Content-Type": "application/json",
        })
        
        if self.api_key:
            session.headers["Authorization"] = f"Bearer {self.api_key}"
        
        return session
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Hugging Face."""
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 512,
                    "temperature": 0.7,
                }
            }
            
            r = self.session.post(
                f"{self.base_url}/{self.model}",
                json=payload,
                timeout=self.timeout
            )
            
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            
            data = r.json()
            
            # Hugging Face returns a list of generated sequences
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict) and "generated_text" in data[0]:
                    return data[0]["generated_text"]
            
            return "No response"
        
        except Exception as e:
            raise Exception(f"HuggingFace: {e}")
