"""LLM-based news categorization and summarization"""
import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from enum import Enum

import requests
import re
import httpx

try:
    from meta_ai_api_tool_call import MetaAI
    HAS_META_AI = True
except ImportError:
    HAS_META_AI = False
    MetaAI = None

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("Warning: google-generativeai not installed")


# Import configuration from root config.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import (
        PAGE_CATEGORIES,
        CATEGORIZATION_PROMPT,
        SUMMARIZATION_PROMPT,
        LLM_TIMEOUT,
        CONFIDENCE_THRESHOLD,
        PROCESSING_MAX_WORKERS,
        GEMINI_MODEL,
        OPENROUTER_REASONING_MODELS,
        KIMI_MODEL,
    )
except ImportError:
    # Fallback to defaults
    PAGE_CATEGORIES = {1: "Breaking Vectors", 2: "Model Architectures", 
                       3: "Neural Horizons", 4: "Lab Outputs", 5: "Inference Corner"}
    CATEGORIZATION_PROMPT = "Categorize this story into 1-5"
    SUMMARIZATION_PROMPT = "Summarize this story"
    LLM_TIMEOUT = 30
    CONFIDENCE_THRESHOLD = 0.8
    PROCESSING_MAX_WORKERS = 5
    GEMINI_MODEL = "gemini-2.5-flash-lite"
    OPENROUTER_REASONING_MODELS = ["google/gemini-2.0-flash-exp:free"]
    KIMI_MODEL = "moonshot-v1-8k"


class PageCategory(Enum):
    """5-page newspaper categories (from config.py)"""
    FRONT_PAGE = PAGE_CATEGORIES[1]
    LLMS_MODELS = PAGE_CATEGORIES[2]
    WORLD_MODELS = PAGE_CATEGORIES[3]
    AI_LABS = PAGE_CATEGORIES[4]
    SPECULATIONS = PAGE_CATEGORIES[5]


class NewsProcessor:
    """Process and categorize news using a hierarchy of LLMs"""
    
    def __init__(self):
        self.use_kimi = False
        self.use_openrouter = False
        self.use_meta_ai = False
        self.use_gemini = False
        self.dynamic_free_models = []
        
        # Primary: OpenRouter (We will use Kimi K2.5 through OpenRouter if possible)
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if self.openrouter_key:
            self.use_openrouter = True
            print("✓ OpenRouter initialized - Fetching latest free models...")
            self.dynamic_free_models = self._fetch_best_free_models()
            if self.dynamic_free_models:
                print(f"   - Top free models found: {', '.join(self.dynamic_free_models[:3])}")

        # Meta-AI fallback
        if HAS_META_AI:
            try:
                self.meta_ai = MetaAI()
                self.use_meta_ai = True
                print("✓ Meta-AI initialized")
            except Exception: pass

        # Gemini fallback
        if HAS_GEMINI:
            gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel(GEMINI_MODEL)
                self.use_gemini = True
                print("✓ Gemini initialized")

    def _fetch_best_free_models(self) -> List[str]:
        """Fetch and prioritize the best free reasoning models from OpenRouter"""
        try:
            with httpx.Client() as client:
                response = client.get("https://openrouter.ai/api/v1/models")
                if response.status_code == 200:
                    models = response.json().get('data', [])
                    # Filter for free models
                    free_models = [m for m in models if m.get('pricing', {}).get('prompt') == "0"]
                    
                    # Manual prioritization based on known capabilities (Kimi K2.5, DeepSeek R1, Llama 3.3)
                    priorities = ["moonshot/kimi-k2.5", "deepseek/deepseek-r1:free", "google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]
                    
                    sorted_free = []
                    # 1. Add prioritized ones if they exist in free list
                    for p in priorities:
                        for m in free_models:
                            if p in m['id']:
                                sorted_free.append(m['id'])
                    
                    # 2. Add rest of free models
                    for m in free_models:
                        if m['id'] not in sorted_free:
                            sorted_free.append(m['id'])
                    
                    return sorted_free
        except Exception as e:
            print(f"  ⚠ Failed to fetch dynamic models: {e}")
        return ["deepseek/deepseek-r1:free", "google/gemini-2.0-flash-exp:free"]

    def _call_openrouter_hierarchy(self, prompt: str) -> str | None:
        """Try dynamic free models in order of reasoning capability"""
        # Always try to find Kimi K2.5 specifically first
        target_models = self.dynamic_free_models
        
        for model in target_models[:5]: # Try top 5 most capable
            try:
                with httpx.Client() as client:
                    response = client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.openrouter_key}",
                            "HTTP-Referer": "https://daily-tokens.netlify.app",
                            "X-Title": "Daily Tokens",
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                        timeout=LLM_TIMEOUT
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('choices'):
                            print(f"      (Used: {model})")
                            return data['choices'][0]['message']['content'].strip()
                    elif response.status_code == 429:
                        continue # Try next model if rate limited
            except Exception:
                continue
        return None

    def _run_llm_chain(self, prompt: str) -> str | None:
        """Execute the fallback chain prioritizing OpenRouter's best free models"""
        result = None
        
        if self.use_openrouter:
            result = self._call_openrouter_hierarchy(prompt)
            
        if not result and self.use_meta_ai:
            try:
                res = self.meta_ai.prompt(message=prompt)
                result = res.get("message", "").strip()
                if result: print("      (Used Meta-AI)")
            except Exception: pass
            
        if not result and self.use_gemini:
            try:
                res = self.gemini_model.generate_content(prompt)
                result = res.text.strip()
                if result: print("      (Used Gemini)")
            except Exception: pass
            
        return result

    def categorize_story(self, title: str, url: str, summary: str = "") -> Dict:
        """Categorize story to one of 5 pages"""
        categories_text = "\n".join([f"{i}. {PAGE_CATEGORIES[i]}" for i in range(1, 6)])
        prompt = CATEGORIZATION_PROMPT.format(categories=categories_text, title=title, url=url, summary=summary)
        
        result = self._run_llm_chain(prompt)
        
        if result:
            try:
                match = re.search(r'(\d)\s*\|\s*([\d\.]+)', result)
                if match:
                    category_num = int(match.group(1))
                    confidence = float(match.group(2))
                    if category_num == 0:
                        return {'category': 'Irrelevant', 'category_id': 0, 'confidence': confidence}
                    categories = [c for c in PageCategory]
                    return {'category': categories[category_num - 1].value, 'category_id': category_num, 'confidence': confidence}
            except Exception: pass
            
        return {'category': 'Irrelevant', 'category_id': 0, 'confidence': 0.0}

    def summarize_story(self, title: str, url: str, summary: str = "", category: str = "", image_urls: List[str] = None) -> str:
        """Generate a concise summary and select image"""
        image_urls_str = "\n".join(image_urls) if image_urls else "NONE FOUND"
        prompt = SUMMARIZATION_PROMPT.format(title=title, category=category, summary=summary, image_urls=image_urls_str)
        
        result = self._run_llm_chain(prompt)
        
        if result:
            return result
        
        return f"HEADLINE: {title}\nSUMMARY: {summary[:100]}\nSELECTED_IMAGE_URL: NONE"
    
    def _process_one_story(self, index_and_story: Tuple[int, Dict]) -> Tuple[int, Dict]:
        """Process a single story (categorize + summarize). Used for parallel execution."""
        # Add delay to avoid rate limits (especially for Meta AI / Gemini free tier)
        time.sleep(2)
        
        i, story = index_and_story
        try:
            from scraper import ImageFetcher
            image_candidates = ImageFetcher.get_candidate_images(story.get('url', ''))
            
            category_info = self.categorize_story(
                story['title'],
                story.get('url', ''),
                story.get('summary', '')
            )
            
            # FILTER: If LLM says it's irrelevant (Category 0), drop it
            if category_info['category_id'] == 0:
                print(f"  - Filtered out (Irrelevant): {story['title'][:50]}...")
                return (i, None)

            raw_summary = self.summarize_story(
                story['title'],
                story.get('url', ''),
                story.get('summary', ''),
                category_info['category'],
                image_candidates
            )
            
            # Parse HEADLINE and SUMMARY
            generated_headline = story['title']  # Default to original
            clean_summary = raw_summary # Default to raw
            selected_image_url = "NONE"
            image_layout = "SQUARE"
            significance_score = 50 # Default middle
            
            import re
            # Extract headline
            headline_match = re.search(r'HEADLINE:\s*(.*?)(?:\n|SUMMARY:|SELECTED_IMAGE_URL:|SIGNIFICANCE_SCORE:|$)', raw_summary, re.IGNORECASE | re.DOTALL)
            # Extract summary
            summary_match = re.search(r'SUMMARY:\s*(.*?)(?:\n|SELECTED_IMAGE_URL:|IMAGE_LAYOUT:|SIGNIFICANCE_SCORE:|$)', raw_summary, re.IGNORECASE | re.DOTALL)
            # Extract significance
            score_match = re.search(r'SIGNIFICANCE_SCORE:\s*(\d+)', raw_summary, re.IGNORECASE)
            # Extract image info
            # Improved regex to find URLs in case model adds quotes, brackets or other text
            img_sel_match = re.search(r'SELECTED_IMAGE_URL:\s*(https?://\S+)', raw_summary, re.IGNORECASE)
            if not img_sel_match and "SELECTED_IMAGE_URL: NONE" not in raw_summary.upper():
                # Try finding any URL in the response if the explicit field is messy
                all_urls = re.findall(r'https?://\S+', raw_summary)
                if all_urls:
                    selected_image_url = all_urls[0]
            
            img_layout_match = re.search(r'IMAGE_LAYOUT:\s*(WIDE|TALL|SQUARE)', raw_summary, re.IGNORECASE)
            
            if headline_match:
                generated_headline = headline_match.group(1).strip().strip('"').strip("'")
            
            if summary_match:
                clean_summary = summary_match.group(1).strip()
                
            if score_match:
                try:
                    significance_score = int(score_match.group(1).strip())
                except:
                    pass

            if img_sel_match:
                selected_image_url = img_sel_match.group(1).strip().strip('"').strip("'").strip(']').strip('[')
            
            if img_layout_match:
                image_layout = img_layout_match.group(1).upper().strip()
            
            return (i, {
                'original_title': story['title'],
                'generated_headline': generated_headline,
                'url': story.get('url', ''),
                'hn_url': story.get('hn_url', ''),
                'source': story.get('source', 'HackerNews'),
                'score': story.get('score', 0),
                'significance_score': significance_score,
                'category': category_info['category'],
                'category_id': category_info['category_id'],
                'confidence': category_info['confidence'],
                'summary': clean_summary,
                'selected_image_url': selected_image_url if selected_image_url.upper() != "NONE" else None,
                'image_layout': image_layout,
                'published': story.get('published', story.get('time')),
            })
        except Exception as e:
            print(f"  ✗ Story {i+1} failed: {e}")
            return (i, None)
    
    def process_stories(self, stories: List[Dict], max_workers: int = None) -> List[Dict]:
        """Process and categorize all stories in parallel."""
        if max_workers is None:
            max_workers = PROCESSING_MAX_WORKERS
        to_process = list(enumerate(stories[:25]))  # Limit to first 25
        total = len(to_process)
        if not to_process:
            return []
        
        print(f"Processing {total} stories in parallel (workers={max_workers})...")
        results: Dict[int, Dict] = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._process_one_story, item): item[0] for item in to_process}
            done = 0
            for future in as_completed(futures):
                done += 1
                try:
                    idx, processed = future.result()
                    if processed is not None:
                        results[idx] = processed
                except Exception as e:
                    print(f"  ✗ Worker error: {e}")
                if done % 5 == 0 or done == total:
                    print(f"   … {done}/{total} done")
        
        # Return in original order
        processed = [results[i] for i in range(total) if i in results]
        print(f"   ✓ Processed {len(processed)} stories")
        return processed
    
    def organize_by_category(self, processed_stories: List[Dict]) -> Dict[int, List[Dict]]:
        """Group stories by page category"""
        
        organized = {i: [] for i in range(1, 6)}
        
        for story in processed_stories:
            category_id = story['category_id']
            organized[category_id].append(story)
        
        # Sort by score/relevance within each category
        for category_id in organized:
            organized[category_id].sort(
                key=lambda x: (x['confidence'], x['score']),
                reverse=True
            )
        
        return organized


if __name__ == "__main__":
    # Test processor with sample stories
    processor = NewsProcessor()
    
    sample_stories = [
        {
            'title': 'OpenAI releases GPT-5 with breakthrough reasoning',
            'url': 'https://example.com/gpt5',
            'source': 'HackerNews',
            'score': 500,
            'summary': 'New model shows 10x improvement in complex reasoning'
        },
        {
            'title': 'Boston Dynamics releases new humanoid robot',
            'url': 'https://example.com/robot',
            'source': 'HackerNews',
            'score': 300,
            'summary': 'Latest robotics advancement in embodied AI'
        }
    ]
    
    print("Testing story processing...\n")
    processed = processor.process_stories(sample_stories)
    
    print("\nProcessed stories:")
    for story in processed:
        print(f"\n{story['original_title']}")
        print(f"  Category: {story['category']}")
        print(f"  Confidence: {story['confidence']}")
        print(f"  Summary: {story['summary'][:100]}")
