"""
Updated NewsProcessor with LLM Router
Routes requests across Qwen, GPT-OSS-120B, DeepSeek with intelligent fallback
"""
import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from pathlib import Path

# Import router
from llm_router import LLMRouter

# Load config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import (
        PAGE_CATEGORIES,
        CATEGORIZATION_PROMPT,
        SUMMARIZATION_PROMPT,
        LLM_TIMEOUT,
        PROCESSING_MAX_WORKERS,
    )
except ImportError:
    PAGE_CATEGORIES = {
        1: "Breaking Vectors",
        2: "Model Architectures",
        3: "Neural Horizons",
        4: "Lab Outputs",
        5: "Inference Corner"
    }
    CATEGORIZATION_PROMPT = """Categorize this news story into one of these categories:

{categories}

Story:
Title: {title}
URL: {url}
Summary: {summary}

Respond with ONLY: "CATEGORY | CONFIDENCE"
Where CATEGORY is 1-5, and CONFIDENCE is 0.0-1.0
Example: "2 | 0.95"

If the story is not about AI/ML, respond with "0 | 0.5"
"""
    
    SUMMARIZATION_PROMPT = """You are a professional tech news editor for a high-end AI newspaper. 

ARTICLE TITLE: {title}
CATEGORY: {category}
SUMMARY: {summary}

TASK:
1. Write a professional, emoji-free newspaper headline.
2. Write a 1-2 sentence summary.
3. Select the best cover image URL from the candidates list at the bottom.
   - Look for high-resolution photos or technical diagrams.
   - Ignore logos, icons, or small graphics.
   - If no good image exists, you MUST write "SELECTED_IMAGE_URL: NONE".

RESPONSE FORMAT (EXACT):
HEADLINE: [Your Headline]
SUMMARY: [Your Summary]
SIGNIFICANCE_SCORE: [1-100]
SELECTED_IMAGE_URL: [The full http URL from the list below, or NONE]
IMAGE_LAYOUT: [WIDE, TALL, or SQUARE]

IMAGE CANDIDATES (PICK ONE):
{image_urls}
"""
    
    LLM_TIMEOUT = 30
    PROCESSING_MAX_WORKERS = 5


class NewsProcessorWithRouter:
    """Process news using LLM Router for intelligent model selection"""
    
    def __init__(self, prefer_cheap: bool = True):
        """
        Initialize processor with LLM Router
        
        Args:
            prefer_cheap: Favor cheaper models (default True)
        """
        self.router = LLMRouter()
        self.prefer_cheap = prefer_cheap
        print(f"✓ Processor initialized with LLM Router (prefer_cheap={prefer_cheap})")
    
    def categorize_story(self, title: str, url: str, summary: str = "") -> Dict:
        """
        Categorize story using LLM Router
        
        Returns:
            {category, category_id, confidence, model_used, cost}
        """
        categories_text = "\n".join([f"{i}. {PAGE_CATEGORIES[i]}" for i in range(1, 6)])
        prompt = CATEGORIZATION_PROMPT.format(
            categories=categories_text,
            title=title,
            url=url,
            summary=summary
        )
        
        result = self.router.call_llm(
            prompt=prompt,
            prefer_cheap=self.prefer_cheap,
            fallback_chain=True
        )
        
        if not result.get("response"):
            return {
                'category': 'Irrelevant',
                'category_id': 0,
                'confidence': 0.0,
                'model_used': None,
                'cost': 0
            }
        
        # Parse response
        response = result["response"].strip()
        try:
            parts = response.split("|")
            if len(parts) >= 2:
                category_id = int(parts[0].strip())
                confidence = float(parts[1].strip())
                
                if category_id == 0:
                    return {
                        'category': 'Irrelevant',
                        'category_id': 0,
                        'confidence': confidence,
                        'model_used': result['model'],
                        'cost': result.get('cost', 0)
                    }
                
                if 1 <= category_id <= 5:
                    return {
                        'category': PAGE_CATEGORIES[category_id],
                        'category_id': category_id,
                        'confidence': confidence,
                        'model_used': result['model'],
                        'cost': result.get('cost', 0)
                    }
        except Exception as e:
            print(f"    ⚠ Parse error: {e}")
        
        return {
            'category': 'Irrelevant',
            'category_id': 0,
            'confidence': 0.0,
            'model_used': result['model'],
            'cost': result.get('cost', 0)
        }
    
    def summarize_story(self, title: str, url: str, summary: str = "", 
                       category: str = "", image_urls: List[str] = None) -> Dict:
        """
        Summarize story using LLM Router
        
        Returns:
            {headline, summary, image_url, significance_score, model_used, cost}
        """
        image_urls_str = "\n".join(image_urls) if image_urls else "NONE FOUND"
        prompt = SUMMARIZATION_PROMPT.format(
            title=title,
            category=category,
            summary=summary,
            image_urls=image_urls_str
        )
        
        result = self.router.call_llm(
            prompt=prompt,
            prefer_cheap=self.prefer_cheap,
            fallback_chain=True
        )
        
        if not result.get("response"):
            return {
                'headline': title,
                'summary': summary[:100],
                'image_url': None,
                'significance_score': 50,
                'model_used': None,
                'cost': 0
            }
        
        raw_response = result["response"]
        
        # Parse response fields
        import re
        headline = title
        clean_summary = summary[:100]
        image_url = None
        significance_score = 50
        
        # Extract headline
        headline_match = re.search(
            r'HEADLINE:\s*(.*?)(?:\n|SUMMARY:|$)',
            raw_response,
            re.IGNORECASE | re.DOTALL
        )
        if headline_match:
            headline = headline_match.group(1).strip().strip('"').strip("'")
        
        # Extract summary
        summary_match = re.search(
            r'SUMMARY:\s*(.*?)(?:\n|SELECTED_IMAGE_URL:|SIGNIFICANCE_SCORE:|$)',
            raw_response,
            re.IGNORECASE | re.DOTALL
        )
        if summary_match:
            clean_summary = summary_match.group(1).strip()
        
        # Extract significance score
        score_match = re.search(
            r'SIGNIFICANCE_SCORE:\s*(\d+)',
            raw_response,
            re.IGNORECASE
        )
        if score_match:
            try:
                significance_score = int(score_match.group(1).strip())
            except:
                pass
        
        # Extract image URL
        image_match = re.search(
            r'SELECTED_IMAGE_URL:\s*(https?://\S+)',
            raw_response,
            re.IGNORECASE
        )
        image_layout = "SQUARE"
        layout_match = re.search(r'IMAGE_LAYOUT:\s*(WIDE|TALL|SQUARE)', raw_response, re.IGNORECASE)
        if layout_match:
            image_layout = layout_match.group(1).upper().strip()

        if image_match:
            image_url = image_match.group(1).strip().strip('"').strip("'").strip(']').strip('[')
        elif "SELECTED_IMAGE_URL: NONE" not in raw_response.upper():
            # Try finding any URL
            urls = re.findall(r'https?://\S+', raw_response)
            if urls:
                image_url = urls[0]
        
        # FINAL FALLBACK: If still no URL but we had candidates, just take the first one
        if (not image_url or image_url.upper() == "NONE") and image_urls:
            image_url = image_urls[0]
            print(f"      (Auto-selected fallback image candidate)")
        
        return {
            'headline': headline,
            'summary': clean_summary,
            'image_url': image_url,
            'image_layout': image_layout,
            'significance_score': significance_score,
            'model_used': result['model'],
            'cost': result.get('cost', 0)
        }
    
    def _process_one_story(self, index_and_story: Tuple[int, Dict]) -> Tuple[int, Dict]:
        """Process a single story (categorize + summarize)"""
        time.sleep(1)  # Rate limiting
        
        i, story = index_and_story
        try:
            from scraper import ImageFetcher
            image_candidates = ImageFetcher.get_candidate_images(story.get('url', ''))
            
            # Categorize
            cat_result = self.categorize_story(
                story['title'],
                story.get('url', ''),
                story.get('summary', '')
            )
            
            print(f"  [{i+1}] {story['title'][:50]}...")
            print(f"      Category: {cat_result['category']} (model: {cat_result['model_used']})")
            
            # Filter irrelevant
            if cat_result['category_id'] == 0:
                print(f"      → Filtered (irrelevant)")
                return (i, None)
            
            # Summarize
            sum_result = self.summarize_story(
                story['title'],
                story.get('url', ''),
                story.get('summary', ''),
                cat_result['category'],
                image_candidates
            )
            
            selected_image_url = sum_result['image_url']
            # FALLBACK: Auto-select if LLM failed but we have candidates
            if (not selected_image_url or selected_image_url.upper() == "NONE") and image_candidates:
                selected_image_url = image_candidates[0]

            return (i, {
                'original_title': story['title'],
                'generated_headline': sum_result['headline'],
                'url': story.get('url', ''),
                'hn_url': story.get('hn_url', ''),
                'source': story.get('source', 'HackerNews'),
                'score': story.get('score', 0),
                'significance_score': sum_result['significance_score'],
                'category': cat_result['category'],
                'category_id': cat_result['category_id'],
                'confidence': cat_result['confidence'],
                'summary': sum_result['summary'],
                'selected_image_url': selected_image_url,
                'image_layout': sum_result.get('image_layout', 'SQUARE'),
                'published': story.get('published', story.get('time')),
                'model_used': f"Cat: {cat_result.get('model_used', 'Meta-AI')}, Sum: {sum_result.get('model_used', 'Meta-AI')}",
                'cost': cat_result.get('cost', 0) + sum_result.get('cost', 0),
            })
        
        except Exception as e:
            print(f"  ✗ Story {i+1} failed: {e}")
            return (i, None)
    
    def process_stories(self, stories: List[Dict], max_workers: int = None) -> List[Dict]:
        """Process stories in parallel"""
        if max_workers is None:
            max_workers = PROCESSING_MAX_WORKERS
        
        to_process = list(enumerate(stories[:25]))
        total = len(to_process)
        
        if not to_process:
            return []
        
        print(f"Processing {total} stories with LLM Router (workers={max_workers})...")
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
        
        processed = [results[i] for i in range(total) if i in results]
        print(f"   ✓ Processed {len(processed)} stories")
        
        # Print cost summary
        stats = self.router.get_usage_stats()
        print(f"\n   Cost Summary:")
        print(f"   - Total calls: {stats['total_calls']}")
        print(f"   - Total cost: ${stats['total_cost']:.4f}")
        print(f"   - Avg per story: ${stats['avg_cost_per_call']:.6f}")
        
        return processed
    
    def organize_by_category(self, processed_stories: List[Dict]) -> Dict[int, List[Dict]]:
        """Group stories by category"""
        organized = {i: [] for i in range(1, 6)}
        
        for story in processed_stories:
            category_id = story['category_id']
            organized[category_id].append(story)
        
        # Sort by score
        for category_id in organized:
            organized[category_id].sort(
                key=lambda x: (x['confidence'], x['score']),
                reverse=True
            )
        
        return organized
    
    def save_usage_log(self):
        """Save LLM usage statistics"""
        self.router.save_usage_log()


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("NewsProcessor with LLM Router Test")
    print("=" * 60)
    
    processor = NewsProcessorWithRouter(prefer_cheap=True)
    
    # Sample stories
    sample_stories = [
        {
            'title': 'OpenAI releases GPT-5 with breakthrough reasoning',
            'url': 'https://example.com/gpt5',
            'source': 'HackerNews',
            'score': 500,
            'summary': 'New model shows 10x improvement in complex reasoning'
        },
        {
            'title': 'Meta releases new computer vision model',
            'url': 'https://example.com/meta-vision',
            'source': 'HackerNews',
            'score': 400,
            'summary': 'Vision transformer with state-of-the-art performance'
        },
    ]
    
    print("\nProcessing sample stories...\n")
    processed = processor.process_stories(sample_stories)
    
    print("\nResults:")
    for story in processed:
        print(f"\n{story['original_title']}")
        print(f"  Category: {story['category']}")
        print(f"  Model: {story['model_used']}")
        print(f"  Cost: ${story['cost']:.6f}")
        print(f"  Summary: {story['summary'][:80]}...")
    
    print("\n" + "=" * 60)
    processor.save_usage_log()
    print("=" * 60)
