import requests
import json
import uuid
import time
import re

class Mistral:
    """Mistral AI client - reverse-engineered from network traffic."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://chat.mistral.ai"
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create properly configured session."""
        session = requests.Session()
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Origin": "https://chat.mistral.ai",
            "Referer": "https://chat.mistral.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "x-trpc-source": "nextjs-react",
        })
        
        return session
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Mistral."""
        try:
            print("[Mistral] Creating new chat...")
            chat_id = self._create_new_chat(prompt)
            print("[Mistral] Chat created: " + str(chat_id))
            
            print("[Mistral] Starting chat stream...")
            response = self._get_chat_response(chat_id)
            return response
            
        except Exception as e:
            raise Exception("Mistral: " + str(e))

    def _create_new_chat(self, prompt: str) -> str:
        """Initialize a new chat via tRPC."""
        url = self.base_url + "/api/trpc/message.newChat?batch=1"
        
        payload = {
            "0": {
                "json": {
                    "content": [{"type": "text", "text": prompt}],
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
                    "incognito": False
                }
            }
        }
        
        r = self.session.post(url, json=payload, timeout=self.timeout)
        
        if r.status_code != 200:
            raise Exception("newChat failed: HTTP " + str(r.status_code) + "\n" + str(r.text[:200]))
            
        try:
            for line in r.text.split('\n'):
                if not line: continue
                data = json.loads(line)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "result" in item:
                            res = item["result"].get("data", {}).get("json", {})
                            if "chatId" in res: return res["chatId"]
                elif isinstance(data, dict):
                    if "json" in data:
                        res = data["json"].get("0", {}).get("result", {}).get("data", {}).get("json", {})
                        if "chatId" in res: return res["chatId"]
                        if isinstance(data["json"], list):
                            for inner in data["json"]:
                                if isinstance(inner, dict) and "chatId" in inner: return inner["chatId"]
        except:
            pass
            
        match = re.search(r'"chatId":"([^"]+)"', r.text)
        if match:
            return match.group(1)
            
        raise Exception("Could not find chatId in response: " + str(r.text[:200]))

    def _get_chat_response(self, chat_id: str) -> str:
        """Get the actual chat response via /api/chat."""
        url = self.base_url + "/api/chat"
        
        payload = {
            "chatId": chat_id,
            "mode": "start",
            "disabledFeatures": ["memory-inference"],
            "clientPromptData": {
                "currentDate": time.strftime("%Y-%m-%d"),
                "userTimezone": "T+05:30 (Asia/Calcutta)"
            },
            "stableAnonymousIdentifier": str(uuid.uuid4())[:8],
            "shouldAwaitStreamBackgroundTasks": True,
            "shouldUseMessagePatch": True
        }
        
        r = self.session.post(url, json=payload, timeout=self.timeout, stream=True)
        
        if r.status_code != 200:
            raise Exception("chat stream failed: HTTP " + str(r.status_code) + "\n" + str(r.text[:200]))
            
        response_parts = []
        
        for line in r.iter_lines():
            if not line: continue
            
            line_str = line.decode('utf-8')
            
            if ':' in line_str:
                parts = line_str.split(':', 1)
                if len(parts) == 2:
                    try:
                        data = json.loads(parts[1])
                        if "json" in data and "patches" in data["json"]:
                            for patch in data["json"]["patches"]:
                                if patch.get("op") == "append" and "text" in patch.get("path", ""):
                                    val = patch.get("value", "")
                                    if val: response_parts.append(val)
                    except:
                        continue
                        
        return "".join(response_parts).strip()

if __name__ == "__main__":
    client = Mistral()
    try:
        resp = client.chat("What is 2+2?")
        print("\nSUCCESS!")
        print("Response: " + str(resp))
    except Exception as e:
        print("\nERROR: " + str(e))
