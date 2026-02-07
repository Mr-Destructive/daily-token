"""
LLM Router - Intelligently route requests across multiple providers
Supports: HuggingFace Inference, with fallbacks
"""
import os
import random
import json
from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass
import httpx
from datetime import datetime

# Load .env
from pathlib import Path
from dotenv import load_dotenv
_repo_root = Path(__file__).resolve().parent.parent
load_dotenv(_repo_root / ".env")


@dataclass
class LLMModel:
    """Model configuration"""
    name: str
    provider: str  # 'huggingface', 'openrouter'
    model_id: str
    input_cost: float  # per 1M tokens
    output_cost: float  # per 1M tokens
    context_window: int
    quality_score: int  # 1-5
    timeout: int = 30


class ModelProvider(Enum):
    """Supported providers"""
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"


class BasicFallbackModel:
    """Zero-cost emergency fallback that requires no API keys"""
    def generate(self, prompt: str) -> str:
        # Check if this is a categorization prompt
        if "Categorize this news story" in prompt or "Respond with ONLY: \"CATEGORY | CONFIDENCE\"" in prompt:
            # Try to guess category from content
            prompt_lower = prompt.lower()
            if any(word in prompt_lower for word in ["overview", "summary", "general"]): return "2 | 0.8"
            if any(word in prompt_lower for word in ["release", "model", "new version"]): return "3 | 0.8"
            if any(word in prompt_lower for word in ["insight", "advice", "tweet", "opinion"]): return "4 | 0.8"
            if any(word in prompt_lower for word in ["lab", "accident", "dark", "failure"]): return "5 | 0.8"
            return "1 | 0.8" # Default to all articles

        # Extract title/summary from prompt to build a crude response
        lines = prompt.split('\n')
        title = "AI Breakthrough"
        summary = "New developments in artificial intelligence."
        
        for line in lines:
            if "ARTICLE TITLE:" in line: title = line.replace("ARTICLE TITLE:", "").strip()
            if "SUMMARY:" in line: summary = line.replace("SUMMARY:", "").strip()
            
        return f"""HEADLINE: {title[:60]}
SUMMARY: {summary[:150]}
SIGNIFICANCE_SCORE: 50
SELECTED_IMAGE_URL: NONE
IMAGE_LAYOUT: SQUARE"""

class LLMRouter:
    """Route LLM requests across multiple models with fallback"""
    
    # Available models (HuggingFace Inference API)
    MODELS: List[LLMModel] = [
        # Tier 1: HF Best value
        LLMModel(
            name="Qwen3-235B-A22B",
            provider="huggingface",
            model_id="Qwen/Qwen3-235B-A22B-Instruct-2507",
            input_cost=0.09,
            output_cost=0.58,
            context_window=131072,
            quality_score=5,
            timeout=30
        ),
        # Tier 2: HF Fast & cheap
        LLMModel(
            name="GPT-OSS-120B",
            provider="huggingface",
            model_id="openai/gpt-oss-120b",
            input_cost=0.05,
            output_cost=0.25,
            context_window=131072,
            quality_score=4,
            timeout=30
        ),
        # Tier 3: HF Best reasoning
        LLMModel(
            name="DeepSeek-V3.2",
            provider="huggingface",
            model_id="deepseek-ai/DeepSeek-V3.2-Exp",
            input_cost=0.27,
            output_cost=0.41,
            context_window=163840,
            quality_score=5,
            timeout=30
        ),
        # Tier 4: OpenRouter High-Reasoning Free Fallback
        LLMModel(
            name="OpenRouter-DeepSeek-R1",
            provider="openrouter",
            model_id="deepseek/deepseek-r1:free",
            input_cost=0.0,
            output_cost=0.0,
            context_window=128000,
            quality_score=5,
            timeout=60
        ),
    ]
    
    # Weight distribution
    WEIGHTS = [
        0.40,  # Qwen3-235B
        0.30,  # GPT-OSS-120B
        0.20,  # DeepSeek HF
        0.10,  # OpenRouter Free
    ]
    
    def __init__(self):
        """Initialize router with API keys"""
        self.hf_token = os.getenv("HF_TOKEN", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        
        # Add clients directory to path for imports
        import sys
        clients_path = str(Path(__file__).parent / "clients")
        if clients_path not in sys.path:
            sys.path.append(clients_path)

        if not self.hf_token:
            print("⚠ HF_TOKEN not found in .env. HuggingFace models will be skipped.")
        
        if not self.openrouter_key:
            print("⚠ OPENROUTER_API_KEY not found in .env. OpenRouter models will be skipped.")
        
        self.usage_log: List[Dict] = []
        print("✓ LLM Router initialized with Free Chatbots + HF + OpenRouter Fallback")
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract and parse JSON from model response, handling conversational filler"""
        if not text: return None
        print(f"      [DEBUG] Raw response: {repr(text)[:200]}...")
        try:
            # 1. Try direct parse
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # 2. Try finding JSON block
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # 3. Last ditch: Heuristic extraction for categorization
            if "category_id" in text or "confidence" in text or "|" in text:
                # Try finding "X | Y.Y" or "| Y.Y" (assuming 1 as default for tech)
                pipe_match = re.search(r'([1-9])\s*\|\s*([01]?\.[\d]+)', text)
                if pipe_match:
                    return {
                        "category_id": int(pipe_match.group(1)),
                        "confidence": float(pipe_match.group(2))
                    }
                
                start_pipe = re.search(r'^\s*\|\s*([01]?\.[\d]+)', text)
                if start_pipe:
                    return {"category_id": 1, "confidence": float(start_pipe.group(1))}
                
                # Try finding field names
                cid_match = re.search(r'category_id["\s:]+(\d)', text)
                conf_match = re.search(r'confidence["\s:]+([01]?\.[\d]+)', text)
                if cid_match:
                    return {
                        "category_id": int(cid_match.group(1)),
                        "confidence": float(conf_match.group(1)) if conf_match else 0.8
                    }
                
                # Just find the first digit 1-5 if it's a very short response
                if len(text.strip()) < 10:
                    digit_match = re.search(r'([1-5])', text)
                    if digit_match:
                        return {"category_id": int(digit_match.group(1)), "confidence": 0.8}

            return None

    def _call_free_chatbot(self, prompt: str) -> Optional[str]:
        """Try the reverse-engineered free chatbots from the ported code"""
        providers = ["gemini", "mistral", "chatgpt"]
        random.shuffle(providers)
        
        for provider in providers:
            try:
                print(f"    → Trying Free {provider.capitalize()}...", end=" ")
                if provider == "gemini":
                    from clients.gemini import Gemini
                    client = Gemini()
                    response = client.chat(prompt)
                elif provider == "mistral":
                    from clients.mistral import Mistral
                    client = Mistral()
                    response = client.chat(prompt)
                elif provider == "chatgpt":
                    from clients.chatgpt import ChatGPT
                    client = ChatGPT()
                    response = client.chat(prompt)
                else: continue
                
                if response and not response.startswith("Error:") and response != "No response":
                    # For JSON prompts, we want to keep the raw response for _extract_json to handle
                    print("✓")
                    return response
                print("✗")
            except Exception as e:
                print(f"✗ ({str(e)[:50]})")
        return None

    def pick_model(self, prefer_cheap: bool = True) -> LLMModel:
        """
        Pick a random model from available pool.
        """
        if prefer_cheap:
            return random.choices(self.MODELS, weights=self.WEIGHTS)[0]
        else:
            return random.choice(self.MODELS)

    def _call_inference_endpoint(self, model: LLMModel, prompt: str) -> Optional[str]:
        """
        Call via appropriate provider endpoint
        """
        try:
            url = "https://api-inference.huggingface.co/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            
            if model.provider == "openrouter":
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "HTTP-Referer": "https://daily-tokens.netlify.app",
                    "X-Title": "The Daily Token",
                    "Content-Type": "application/json"
                }

            with httpx.Client() as client:
                response = client.post(
                    url,
                    headers=headers,
                    json={
                        "model": model.model_id,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 800,
                    },
                    timeout=model.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("choices") and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"].strip()
                elif response.status_code == 429:
                    print(f"    ⚠ Rate limited on {model.name}")
                    return None
                
                print(f"    ⚠ {model.provider.upper()} returned {response.status_code}")
                return None
        except Exception as e:
            print(f"    ⚠ {model.provider.upper()} call failed: {e}")
            return None

    def call_llm(self, prompt: str, prefer_cheap: bool = True, fallback_chain: bool = True) -> Dict:
        """
        Call an LLM with smart fallback.
        1. Try Free Chatbots (Gemini, Mistral, etc.)
        2. Try HuggingFace Inference
        3. Try OpenRouter (Final Fallback)
        """
        if not prompt or len(prompt.strip()) == 0:
            return {"response": None, "error": "Empty prompt"}
        
        # 1. Try Free Chatbots First (Tier 0)
        response = self._call_free_chatbot(prompt)
        if response:
            return {
                "response": response,
                "model": "Free-Chatbot",
                "provider": "reverse-engineered",
                "cost": 0,
                "quality_score": 4,
            }

        # 2. Try HuggingFace / OpenRouter (Normal Pool)
        selected_model = self.pick_model(prefer_cheap=prefer_cheap)
        models_to_try = [selected_model]
        
        if fallback_chain:
            other_models = [m for m in self.MODELS if m != selected_model]
            models_to_try.extend(random.sample(other_models, min(len(other_models), 3)))
        
        for model in models_to_try:
            if model.provider == "huggingface" and not self.hf_token: continue
            if model.provider == "openrouter" and not self.openrouter_key: continue

            print(f"  → Trying {model.name}...", end=" ")
            
            # Call LLM
            response = self._call_inference_endpoint(model, prompt)
            
            if response:
                print("✓")
                return {
                    "response": response,
                    "model": model.name,
                    "provider": model.provider,
                    "cost": 0, # Estimates removed for brevity
                    "quality_score": model.quality_score,
                }
            print("✗")
        
        # 3. Final Emergency Fallback: Meta-AI
        print("  → Trying Meta-AI (Emergency Fallback)...", end=" ")
        try:
            from meta_ai_api_tool_call import MetaAI
            ai = MetaAI()
            response = ai.prompt(message=prompt)
            if response and response.get("message"):
                print("✓")
                return {
                    "response": response["message"].strip(),
                    "model": "Meta-AI",
                    "provider": "meta",
                    "cost": 0,
                    "quality_score": 3,
                }
        except Exception: print("✗")

        # 4. Ultimate Guaranteed Fallback
        print("  → Trying Local Basic Fallback...", end=" ")
        try:
            basic_model = BasicFallbackModel()
            response = basic_model.generate(prompt)
            print("✓")
            return {
                "response": response,
                "model": "Local-Fallback",
                "provider": "local",
                "cost": 0,
                "quality_score": 1,
            }
        except Exception: print("✗")

        return {"response": None, "error": "All providers failed"}
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        if not self.usage_log:
            return {
                "total_calls": 0,
                "total_cost": 0.0,
                "by_model": {},
                "avg_cost_per_call": 0.0
            }
        
        total_cost = sum(log["cost"] for log in self.usage_log)
        model_usage = {}
        for log in self.usage_log:
            model = log["model"]
            if model not in model_usage:
                model_usage[model] = {"count": 0, "cost": 0}
            model_usage[model]["count"] += 1
            model_usage[model]["cost"] += log["cost"]
        
        return {
            "total_calls": len(self.usage_log),
            "total_cost": total_cost,
            "by_model": model_usage,
            "avg_cost_per_call": total_cost / len(self.usage_log) if self.usage_log else 0.0
        }
    
    def save_usage_log(self, filepath: str = None):
        """Save usage log to file"""
        if filepath is None:
            filepath = Path(__file__).parent.parent / "output" / "llm_usage.json"
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump({
                "logs": self.usage_log,
                "stats": self.get_usage_stats()
            }, f, indent=2)
        
        print(f"✓ Usage log saved to {filepath}")


# Test script
if __name__ == "__main__":
    print("=" * 60)
    print("LLM Router Test")
    print("=" * 60)
    
    router = LLMRouter()
    
    # Test 1: Simple prompt
    print("\n[Test 1] Basic categorization prompt:")
    result = router.call_llm(
        prompt="Categorize this story: 'New AI model achieves 99% accuracy on reasoning tasks' into one of: [Breaking News, Research, Tools, Speculation]",
        prefer_cheap=True
    )
    
    if result.get("response"):
        print(f"Response: {result['response'][:100]}...")
        print(f"Model: {result['model']}")
        print(f"Cost: ${result['cost']:.6f}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Test 2: Usage stats
    print("\n[Test 2] Usage statistics:")
    stats = router.get_usage_stats()
    print(f"Total calls: {stats['total_calls']}")
    print(f"Total cost: ${stats['total_cost']:.6f}")
    print(f"Avg cost per call: ${stats['avg_cost_per_call']:.6f}")
    
    # Test 3: Save log
    print("\n[Test 3] Saving usage log...")
    router.save_usage_log()
    
    print("\n" + "=" * 60)
    print("✓ Tests complete!")
    print("=" * 60)
