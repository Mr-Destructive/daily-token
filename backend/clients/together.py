"""Together AI free API client - no auth required."""
import requests
import json


class Together:
    """Together AI free inference API."""
    
    def __init__(self):
        self.base_url = "https://api.together.xyz/v1"
        # Using free tier, no key needed for inference
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Together AI."""
        try:
            payload = {
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
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
                raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")
            
            data = r.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("message", {}).get("content", "No response")
            
            return "No response"
        
        except Exception as e:
            raise Exception(f"Together: {e}")
