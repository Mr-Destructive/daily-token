import requests
import json
import uuid

class Proton:
    """Proton Mail AI (Lumo) API client."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://lumo.proton.me"
        self.api_url = "https://lumo-api.proton.me"
        self.timeout = timeout
        self.session = self._create_session()
        self.token = None
        self.uid = None
        self._init_session()
    
    def _create_session(self) -> requests.Session:
        """Create configured session."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "application/vnd.protonmail.v1+json",
            "x-pm-appversion": "web-lumo@1.3.0.8",
            "x-pm-locale": "en_US",
            "x-enforce-unauthsession": "true",
            "Origin": "https://lumo.proton.me",
            "Referer": "https://lumo.proton.me/guest",
        })
        return session
    
    def _init_session(self):
        """Initialize session and get tokens."""
        try:
            r = self.session.post(f"{self.base_url}/api/auth/v4/sessions")
            if r.status_code == 200:
                data = r.json()
                self.token = data.get("AccessToken")
                self.uid = data.get("UID")
            else:
                # Fallback to discovered token if init fails
                self.token = "4s6rjent6lwr5dt6t5zkgkttnxigbtun"
                self.uid = "lz63j6xihxtjn2bfsepsfh3aajik32mn"
            
            # Update headers
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "x-pm-uid": self.uid,
                "x-pm-appversion": "web-lumo@1.3.0.8",
            })
        except Exception as e:
            print(f"[Proton] Init failed: {e}")

    def chat(self, prompt: str) -> str:
        """Send prompt to Proton AI."""
        if not self.token:
            self._init_session()
            
        try:
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "model": "models/lpm"
            }
            
            # Try common versioned path
            r = self.session.post(
                f"{self.base_url}/api/lumo/v1/chat",
                json=payload,
                timeout=self.timeout
            )
            
            if r.status_code != 200:
                return f"Error: HTTP {r.status_code}"
            
            # Parse response (assuming Mistral-like format based on context)
            response_parts = []
            for line in r.text.split('\n'):
                if not line: continue
                try:
                    data = json.loads(line)
                    if "content" in data:
                        response_parts.append(data["content"])
                except:
                    continue
            
            return "".join(response_parts).strip() if response_parts else "No response"
            
        except Exception as e:
            raise Exception(f"Proton: {e}")

if __name__ == "__main__":
    client = Proton()
    print(f"\nResponse: {client.chat('What is 2+2?')}")