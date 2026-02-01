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


class LLMRouter:
    """Route LLM requests across multiple models with fallback"""
    
    # Available models (HuggingFace Inference API)
    MODELS: List[LLMModel] = [
        # Tier 1: Best value
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
        # Tier 2: Fast & cheap
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
        # Tier 3: Best reasoning
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
        # Tier 4: Budget fallback
        LLMModel(
            name="Llama-3.1-70B",
            provider="huggingface",
            model_id="meta-llama/Llama-3.1-70B-Instruct",
            input_cost=0.14,
            output_cost=0.40,
            context_window=131072,
            quality_score=4,
            timeout=30
        ),
        # Tier 5: OpenRouter High-Reasoning Free Fallback
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
        0.35,  # Qwen3-235B
        0.30,  # GPT-OSS-120B
        0.15,  # DeepSeek HF
        0.10,  # Llama HF
        0.10,  # OpenRouter Free
    ]
    
    def __init__(self):
        """Initialize router with API keys"""
        self.hf_token = os.getenv("HF_TOKEN", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        
        if not self.hf_token:
            raise ValueError("HF_TOKEN not found in .env. Get one from https://huggingface.co/settings/tokens")
        
        self.usage_log: List[Dict] = []
        print("✓ LLM Router initialized")
        print(f"  Models: {len(self.MODELS)}")
        print(f"  HF Token: {'✓' if self.hf_token else '✗'}")
    
    def pick_model(self, prefer_cheap: bool = True) -> LLMModel:
        """
        Pick a random model from available pool.
        
        Args:
            prefer_cheap: If True, favor cheaper models (default True)
        
        Returns:
            Selected LLMModel
        """
        if prefer_cheap:
            return random.choices(self.MODELS, weights=self.WEIGHTS)[0]
        else:
            return random.choice(self.MODELS)
    
    def _call_huggingface(self, model: LLMModel, prompt: str) -> Optional[str]:
        """Call HuggingFace Inference API"""
        try:
            with httpx.Client() as client:
                # HuggingFace uses OpenAI-compatible chat endpoint
                response = client.post(
                    "https://api-inference.huggingface.co/models/openai-community/gpt2",  # Placeholder
                    # Actually use direct model endpoint
                    headers={
                        "Authorization": f"Bearer {self.hf_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 200,
                            "temperature": 0.7,
                        }
                    },
                    timeout=model.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0].get("generated_text", "").strip()
                    elif isinstance(data, dict):
                        return data.get("generated_text", "").strip()
                
                return None
        except Exception as e:
            print(f"    ⚠ HF call failed: {e}")
            return None
    
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
                    "X-Title": "Daily Tokens",
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
                        "max_tokens": 300,
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
        
        Args:
            prompt: The prompt to send
            prefer_cheap: Favor cheaper models
            fallback_chain: Try other models if first fails
        
        Returns:
            Dict with 'response', 'model', 'provider', 'cost'
        """
        if not prompt or len(prompt.strip()) == 0:
            return {"response": None, "error": "Empty prompt"}
        
        # Pick primary model
        selected_model = self.pick_model(prefer_cheap=prefer_cheap)
        models_to_try = [selected_model]
        
        # Add fallbacks
        if fallback_chain:
            other_models = [m for m in self.MODELS if m != selected_model]
            models_to_try.extend(random.sample(other_models, min(2, len(other_models))))
        
        # Try models in order
        for model in models_to_try:
            print(f"  → Trying {model.name}...", end=" ")
            
            # Estimate tokens (rough: ~4 chars per token)
            input_tokens = len(prompt) / 4
            output_tokens = 150  # Average response
            
            estimated_cost = (input_tokens / 1_000_000 * model.input_cost) + \
                           (output_tokens / 1_000_000 * model.output_cost)
            
            # Call LLM
            response = self._call_inference_endpoint(model, prompt)
            
            if response:
                # Log usage
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "model": model.name,
                    "provider": model.provider,
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "cost": estimated_cost,
                    "success": True,
                }
                self.usage_log.append(log_entry)
                
                print(f"✓ ({estimated_cost:.6f})")
                
                return {
                    "response": response,
                    "model": model.name,
                    "provider": model.provider,
                    "cost": estimated_cost,
                    "quality_score": model.quality_score,
                }
            else:
                print("✗")
        
        # 3. Final Emergency Fallback: Meta-AI (No API Key)
        print("  → Trying Meta-AI (Emergency Fallback)...", end=" ")
        try:
            from meta_ai_api_tool_call import MetaAI
            ai = MetaAI()
            response = ai.prompt(message=prompt)
            if response and response.get("message"):
                print("✓ (Free)")
                return {
                    "response": response["message"].strip(),
                    "model": "Meta-AI",
                    "provider": "meta",
                    "cost": 0,
                    "quality_score": 3,
                }
        except Exception as e:
            print(f"✗ ({e})")

        # All failed
        return {
            "response": None,
            "error": f"All {len(models_to_try)} models + Meta-AI failed",
            "models_tried": [m.name for m in models_to_try] + ["Meta-AI"]
        }
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        if not self.usage_log:
            return {"total_calls": 0, "total_cost": 0}
        
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
            "avg_cost_per_call": total_cost / len(self.usage_log) if self.usage_log else 0
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
