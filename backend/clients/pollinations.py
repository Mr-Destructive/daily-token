
import requests
import urllib.parse

class Pollinations:
    """Pollinations.ai client - simple and free."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://text.pollinations.ai"
        self.timeout = timeout
        self.session = requests.Session()
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Pollinations."""
        try:
            # Simple GET request is the most reliable for Pollinations
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"{self.base_url}/{encoded_prompt}?model=openai&json=true"
            
            r = self.session.get(url, timeout=self.timeout)
            
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            
            # The API returns raw text unless json=true is passed
            # If json=true is passed, it returns a JSON object
            try:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("content", "No response")
                elif isinstance(data, dict):
                    # Check for different possible JSON structures
                    return data.get("choices", [{}])[0].get("message", {}).get("content", r.text)
            except:
                return r.text.strip()
                
            return r.text.strip()
            
        except Exception as e:
            raise Exception(f"Pollinations: {e}")

if __name__ == "__main__":
    client = Pollinations()
    print(client.chat("What is 2+2?"))
