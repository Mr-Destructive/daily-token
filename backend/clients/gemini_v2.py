"""Google Gemini client - reverse-engineered from network traffic."""
import requests
import json
import urllib.parse
import re
import time
from typing import Optional


class Gemini:
    """Google Gemini API client - pure HTTP implementation."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://gemini.google.com"
        self.timeout = timeout
        self.session = self._create_session()
        self.snlm0e = None
        self._init_session()
    
    def _create_session(self) -> requests.Session:
        """Create properly configured session."""
        session = requests.Session()
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://gemini.google.com",
            "Referer": "https://gemini.google.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "x-same-domain": "1",
        })
        
        return session
    
    def _init_session(self):
        """Initialize session and extract SNLM0e token."""
        try:
            r = self.session.get(self.base_url, timeout=self.timeout)
            
            # Extract SNlM0e token from response
            match = re.search(r'"SNlM0e":"([^"]+)"', r.text)
            if match:
                self.snlm0e = match.group(1)
                print(f"[Gemini] Session initialized, SNlM0e token found")
            else:
                print(f"[Gemini] Warning: Could not find SNlM0e token")
        
        except Exception as e:
            print(f"[Gemini] Init failed: {e}")
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Gemini."""
        if not self.snlm0e:
            raise Exception("SNlM0e token not available")
        
        try:
            response_text = self._call_stream_generate(prompt)
            return response_text
        except Exception as e:
            raise Exception(f"Gemini: {e}")
    
    def _call_stream_generate(self, prompt: str) -> str:
        """Call StreamGenerate endpoint."""
        
        # Build request payload
        # Format: [null, [[prompt, 0, null, null, null, null, 0], [language], [...], token]]
        request_data = [
            None,
            json.dumps([
                [prompt, 0, None, None, None, None, 0],
                ["en-US"],
                ["", "", "", None, None, None, None, None, None, ""],
                self.snlm0e
            ])
        ]
        
        payload = f"f.req={urllib.parse.quote(json.dumps(request_data))}&"
        
        # Build URL with parameters
        params = {
            "bl": "boq_assistant-bard-web-server_20260204.08_p0",
            "_reqid": str(int(time.time() * 1000)),
            "rt": "c"
        }
        
        url = f"{self.base_url}/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
        
        r = self.session.post(
            url,
            params=params,
            data=payload,
            timeout=self.timeout,
            stream=True
        )
        
        if r.status_code != 200:
            raise Exception(f"StreamGenerate failed: HTTP {r.status_code}")
        
        # Parse streaming response
        response_parts = []
        
        for line in r.iter_lines():
            if not line:
                continue
            
            try:
                line_str = line if isinstance(line, str) else line.decode('utf-8')
                
                # Skip first line with )]}' 
                if line_str.startswith(")]}"):
                    continue
                
                # Parse length-prefixed JSON
                # Format: "123\n[["wrb.fr", "rpc_id", data, ...]]"
                if '\n' in line_str:
                    parts = line_str.split('\n', 1)
                    if len(parts) == 2:
                        json_str = parts[1]
                    else:
                        json_str = line_str
                else:
                    json_str = line_str
                
                # Try to parse as JSON
                if json_str.strip().startswith('['):
                    data = json.loads(json_str)
                    
                    # Extract text from response
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, list) and len(item) > 2:
                                # Look for wrb.fr responses
                                if item[0] == "wrb.fr" and item[2]:
                                    content = item[2]
                                    if isinstance(content, str):
                                        # Extract actual text
                                        text = self._extract_text_from_response(content)
                                        if text:
                                            response_parts.append(text)
            
            except json.JSONDecodeError:
                continue
            except Exception as e:
                continue
        
        result = "".join(response_parts).strip()
        return result if result else "No response"
    
    def _extract_text_from_response(self, content: str) -> str:
        """Extract text from Gemini response."""
        try:
            # Response is usually a string containing escaped JSON
            # Try to parse it
            if content.startswith('['):
                data = json.loads(content)
                # Navigate through the nested structure
                if isinstance(data, list) and len(data) > 0:
                    # Usually the first element contains text
                    text = self._find_text_in_nested(data)
                    return text
        except:
            pass
        
        # Fallback: extract any non-escaped text
        text = re.sub(r'\\(.)', r'\1', content)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\{.*?\}', '', text)
        text = text.strip()
        
        if len(text) > 5 and text.isascii():
            return text
        
        return ""
    
    def _find_text_in_nested(self, obj, max_depth=10, depth=0):
        """Recursively find text in nested structure."""
        if depth > max_depth:
            return ""
        
        if isinstance(obj, str) and len(obj) > 5 and len(obj) < 1000:
            # Likely a text response
            if re.search(r'[a-zA-Z]{5,}', obj):
                return obj
        
        if isinstance(obj, list):
            for item in obj:
                result = self._find_text_in_nested(item, max_depth, depth + 1)
                if result:
                    return result
        
        if isinstance(obj, dict):
            for value in obj.values():
                result = self._find_text_in_nested(value, max_depth, depth + 1)
                if result:
                    return result
        
        return ""
