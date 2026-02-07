"""Google Gemini client - fresh approach using captured network flow."""
import requests
import json
import urllib.parse
import re
import uuid
import time


class Gemini:
    """Google Gemini API client - reverse-engineered HTTP implementation."""
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://gemini.google.com"
        self.timeout = timeout
        self.session = self._create_session()
        self.sid = None
        self.sid_ts = None
        self._init_session()
    
    def _create_session(self) -> requests.Session:
        """Create session with proper headers and cookies."""
        session = requests.Session()
        
        # Headers from captured request
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.6 Safari/537.36",
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
            # Chrome version headers
            "Sec-CH-UA": '"Chromium";v="145", "Not:A-Brand";v="99"',
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Full-Version": '"145.0.7632.6"',
        })
        
        return session
    
    def _init_session(self):
        """Initialize session by visiting the main page."""
        try:
            print("[Gemini] Initializing session...")
            r = self.session.get(self.base_url, timeout=self.timeout)
            
            if r.status_code == 200:
                print("[Gemini] Session initialized")
                # Extract any available tokens from the response
                self._extract_tokens_from_page(r.text)
            else:
                print(f"[Gemini] Init got {r.status_code}")
        except Exception as e:
            print(f"[Gemini] Init failed: {e}")
    
    def _extract_tokens_from_page(self, html: str):
        """Extract SID and other tokens from page."""
        # Try to find SID
        match = re.search(r'"SNlM0e":"([^"]+)"', html)
        if match:
            self.sid = match.group(1)
            print(f"[Gemini] Found SID")
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Gemini and get response."""
        try:
            response = self._stream_generate(prompt)
            return response
        except Exception as e:
            raise Exception(f"Gemini: {e}")
    
    def _stream_generate(self, prompt: str) -> str:
        """Call the StreamGenerate endpoint."""
        
        # Build the payload structure based on captured requests
        # Format: [null, "[[prompt, 0, null, null, null, null, 0], [lang], [empty fields], token]"]
        
        # The token is a long string that contains session data
        # Since we can't extract it dynamically, we'll send a request without it first
        # and see if Google's system generates one
        
        # Inner payload structure
        inner_payload = [
            [prompt, 0, None, None, None, None, 0],  # Message with index
            ["en-US"],                                  # Language
            ["", "", "", None, None, None, None, None, None, ""],  # Empty fields
            ""  # Token (will be filled or left empty)
        ]
        
        # Outer payload
        outer_payload = [
            None,
            json.dumps(inner_payload)
        ]
        
        # Encode as form data
        payload = f"f.req={urllib.parse.quote(json.dumps(outer_payload))}&"
        
        # Build URL parameters
        params = {
            "bl": "boq_assistant-bard-web-server_20260204.08_p0",
            "rt": "c"
        }
        
        url = f"{self.base_url}/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
        
        print(f"[Gemini] Sending request to StreamGenerate...")
        
        r = self.session.post(
            url,
            params=params,
            data=payload,
            timeout=self.timeout,
            stream=True
        )
        
        print(f"[Gemini] Response status: {r.status_code}")
        
        if r.status_code != 200:
            # Try to get error message
            error_body = r.text[:500] if hasattr(r, 'text') else str(r.content)[:500]
            raise Exception(f"StreamGenerate failed: HTTP {r.status_code}\n{error_body}")
        
        # Parse streaming response
        response_text = self._parse_stream(r)
        return response_text
    
    def _parse_stream(self, response):
        """Parse the streaming response from Gemini."""
        
        all_candidates = []
        skip_first = True  # Skip the ")]}'" preamble
        
        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                line_str = line if isinstance(line, str) else line.decode('utf-8')
                
                # Skip the first line which is ")]}'"
                if skip_first:
                    skip_first = False
                    continue
                
                # Skip empty lines and length indicators
                if line_str.strip() == "" or line_str.isdigit():
                    continue
                
                # Try to parse as JSON
                if line_str.startswith('['):
                    try:
                        data = json.loads(line_str)
                        
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, list) and len(item) > 2:
                                    # Look for wrb.fr (response wrapper)
                                    if item[0] == "wrb.fr" and item[2] is not None:
                                        # item[2] contains the response data (as string or list)
                                        content = item[2]
                                        
                                        # Find all text snippets in this item
                                        if isinstance(content, str):
                                            try:
                                                # If it's a JSON string, parse it
                                                inner_data = json.loads(content)
                                                self._collect_all_text_with_scores(inner_data, all_candidates)
                                            except:
                                                # Otherwise treat as plain string
                                                score = self._score_text(content)
                                                if score > 0:
                                                    all_candidates.append((content, score))
                                        else:
                                            self._collect_all_text_with_scores(content, all_candidates)
                    
                    except json.JSONDecodeError:
                        pass
            
            except Exception as e:
                continue
        
        if not all_candidates:
            return "No response"
            
        # Sort candidates by score descending
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Take the top candidate as our primary response
        best_text, best_score = all_candidates[0]
        
        # Final cleanup of the best text
        result = self._clean_final_text(best_text)
        
        return result if result else "No response"

    def _collect_all_text_with_scores(self, obj, candidates):
        """Recursively collect all strings and their scores."""
        if isinstance(obj, str):
            score = self._score_text(obj)
            if score > 0:
                candidates.append((obj, score))
        elif isinstance(obj, list):
            for item in obj:
                self._collect_all_text_with_scores(item, candidates)
        elif isinstance(obj, dict):
            for value in obj.values():
                self._collect_all_text_with_scores(value, candidates)

    def _clean_final_text(self, text: str) -> str:
        """Apply final cleanup to the extracted text."""
        import re
        
        result = text
        
        # Remove trailing junk like session IDs/tokens
        result = re.sub(r'[cr]_[a-f0-9]{10,}\s*$', '', result).strip()
        result = re.sub(r'Aw[A-Za-z0-9_\-/=+]{15,}$', '', result).strip()
        
        # Remove code metadata tags
        result = re.sub(r'\?code_reference&code_event_index=\d+', '', result)
        result = re.sub(r'\?code_stdout&code_event_index=\d+', '', result)
        
        # Fix common escaping issues
        result = result.replace('\\n', '\n').replace('\\"', '"')
        
        # If it's a markdown response with multiple blocks, clean them
        if '```' in result:
            # Keep only until the end of the last meaningful code block or text
            result = re.sub(r'```[a-z]*\s*$', '```', result).strip()
        
        return result.strip()
    
    def _extract_text_from_response_item(self, content) -> str:
        """Keep for backward compatibility but use _parse_stream's new logic."""
        return self._find_longest_text(content)
    
    def _find_longest_text(self, obj, min_len=3, max_len=1000):
        """Recursively find the longest meaningful text string in a nested structure."""
        text, score = self._find_longest_text_with_score(obj, min_len, max_len)
        return text
    
    def _find_longest_text_with_score(self, obj, min_len=3, max_len=1000):
        """Find text and return it with a score."""
        if isinstance(obj, str):
            if min_len <= len(obj) <= max_len:
                return obj, self._score_text(obj)
            return "", 0
        
        longest = ""
        longest_score = 0
        
        if isinstance(obj, list):
            for item in obj:
                text, score = self._find_longest_text_with_score(item, min_len, max_len)
                if score > longest_score:
                    longest = text
                    longest_score = score
        
        elif isinstance(obj, dict):
            for value in obj.values():
                text, score = self._find_longest_text_with_score(value, min_len, max_len)
                if score > longest_score:
                    longest = text
                    longest_score = score
        
        return longest, longest_score
    
    def _score_text(self, text: str) -> float:
        """Score how likely text is to be actual chat content."""
        if not isinstance(text, str) or len(text) < 3:
            return 0
        
        # Penalize metadata and markers
        if "data_analysis_tool" in text:
            return 0
            
        # Don't score URLs or data URIs or location info
        if (text.startswith('http') or text.startswith('data:') or text.startswith('//') or
            'maps' in text.lower() or 'coordinates' in text.lower()):
            return -1
            
        # Filter location info
        if ", " in text and ("Mumbai" in text or "Maharashtra" in text or "India" in text):
            return -1
        
        # Strongly prefer text that contains actual responses (code output, etc)
        # These patterns indicate real chat responses
        score = 0
        if '```' in text:
            score += 1000
        if '$' in text:
            score += 500
        if '\n\n' in text:
            score += 200
            
        # Check for readable content
        letter_count = sum(1 for c in text if c.isalpha())
        letter_ratio = letter_count / len(text) if text else 0
        
        # Preference for text with natural language (>30% letters)
        if letter_ratio > 0.3:
            words = text.split()
            # Length bonus
            score += len(text)
            # Word count bonus
            if len(words) >= 10:
                score *= 1.5
            return score
        
        return 0
    
    def _is_readable_text(self, text: str) -> bool:
        """Check if text looks like human-readable content."""
        # Should have mostly printable chars and words
        letter_count = sum(1 for c in text if c.isalpha())
        return letter_count > len(text) * 0.3  # At least 30% letters
