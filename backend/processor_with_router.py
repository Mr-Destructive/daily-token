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
import re

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
        1: "All Articles",
        2: "AI & LLM Overview",
        3: "Model Release History",
        4: "Top Insights & Advice",
        5: "Lab Updates & Dark Side",
        6: "Benchmarks & Claims Audit",
        7: "Infra & Cost Watch",
        8: "Policy & Safety Moves",
        9: "Corrections & Revisions",
    }
    CATEGORIZATION_PROMPT = """[SYSTEM: RESPOND ONLY WITH JSON]
Categorize this AI news story. 
Pick ONE category ID from 1 to 5.

CATEGORIES:
1: Breaking News & Major Breakthroughs
2: AI & LLM Industry Analysis
3: New Model Releases & Benchmarks
4: AI Insights, Tips & Expert Advice
5: AI Safety, Lab Research & Accidents

STORY:
Title: {title}
Summary: {summary}

REQUIRED JSON FORMAT:
{{
  "category_id": 1,
  "confidence": 0.9
}}
"""
    
    SUMMARIZATION_PROMPT = """You are a professional tech news editor. Summarize this AI story.

STORY:
Title: {title}
Category: {category}
Summary: {summary}

IMAGE CANDIDATES:
{image_urls}

RESPOND ONLY WITH A VALID JSON OBJECT:
{{
  "headline": "[Professional Headline]",
  "summary": "[1-2 sentence concise summary]",
  "significance_score": [1-100],
  "selected_image_url": "[Full URL from list or 'NONE']",
  "image_layout": "WIDE|TALL|SQUARE"
}}
"""
    
    LLM_TIMEOUT = 30
    PROCESSING_MAX_WORKERS = 5


class NewsProcessorWithRouter:
    """Process news using LLM Router for intelligent model selection"""
    
    CATEGORIZATION_PROMPT = """[SYSTEM: RESPOND ONLY WITH JSON]
You are a high-end AI news curator. Categorize this story.

CATEGORIES:
1: Breaking Vectors (Major breakthroughs, high-impact news)
2: Model Architectures (New techniques, layers, methods)
3: Neural Horizons (Robotics, future tech, world models)
4: Lab Outputs (Open source tools, smaller releases)
5: Inference Corner (Optimization, hardware, deployment)
6: AI Industry Overview (Market analysis, business trends)
7: Model Release History (ONLY specific model launches like 'Gemma 3' or 'Opus 4.6')
8: Top Insights & Advice (HackerNews community wisdom, expert advice)
9: AI Safety & Lab Accidents (Safety failures, research lab drama)
10: Benchmarks & Claims Audit (evaluation quality, claims-vs-evidence, reproducibility checks)
11: Infra & Cost Watch (compute economics, GPU supply, cloud/on-prem cost shifts, serving efficiency)
12: Policy & Safety Moves (regulatory actions, governance updates, safety policy changes with practical impact)
13: Corrections & Revisions (retractions, errata, model updates, deprecations, changelog-impacting fixes)

STORY:
Title: {title}
Summary: {summary}

REQUIRED JSON FORMAT:
{{
  "category_id": [1-13],
  "confidence": [0.0-1.0],
  "is_model_release": [true/false],
  "detected_model": "[Name if cat 7, else null]"
}}
"""
    
    SUMMARIZATION_PROMPT = """[SYSTEM: RESPOND ONLY WITH JSON]
You are writing for a serious AI newspaper read by engineers.
Tone: factual, restrained, and unmistakably human.
Voice: intriguing and slightly odd in the way a sharp columnist can be, never theatrical.
Style constraints:
- no hype language, no marketing phrasing, no cliches
- no robotic phrasing, no generic "AI changed everything" lines
- include one concrete tradeoff or risk when relevant
- acknowledge uncertainty only when real
Editorial posture: quietly cynical about the erosion of software craft, but open-ended about where discipline can return.

Summarize this AI story and decide if the cover image is high-quality enough to feature.

STORY:
Title: {title}
Category: {category}
Summary: {summary}

IMAGE CANDIDATES:
{image_urls}

REQUIRED JSON FORMAT:
{{
  "headline": "[Newspaper-style headline, concise and concrete]",
  "summary": "[1-2 sentence distillation with concrete implications and a human newsroom voice]",
  "significance_score": [1-100],
  "selected_image_url": "[Chosen URL or 'NONE']",
  "worth_showing_image": [true/false],
  "image_layout": "WIDE|TALL|SQUARE"
}}
"""

    INSIGHT_PROMPT = """[SYSTEM: RESPOND ONLY WITH JSON]
Convert this HackerNews discussion into a "Community Insight".
DO NOT summarize the article. Extract distilled community wisdom, a powerful quote, or a core lesson.

ARTICLE: {title}
DISCUSSION:
{comments}

REQUIRED JSON FORMAT:
{{
  "headline": "[Insight Title]",
  "summary": "[The core advice or wisdom distilled]",
  "top_quote": "[The most impactful single sentence from comments]",
  "contributor": "[Username or 'The Community']",
  "significance_score": [1-100]
}}
"""

    EDITORIAL_PROMPT = """[SYSTEM: RESPOND ONLY WITH JSON]
You are the Chief Editor of 'The Daily Token'. Review today's top stories and decide the layout.
Editorial voice:
- Serious metropolitan newspaper, not a blog.
- One sentence only for editor note.
- Quietly cynical about the erosion of engineering craft.
- Do not romanticize decline.
- Keep the line distinctive and human, slightly unexpected but still precise.
- End with open-ended agency or possibility.

STORIES FOR REVIEW:
{story_list}

TASK:
1. Select the ABSOLUTE #1 LEAD STORY.
2. Select two supporting leads.
3. Write a 1-sentence 'Editor's Note' setting the tone for today (e.g. bullish, cautious, visionary).

REQUIRED JSON FORMAT:
{{
  "main_lead_index": [index of story],
  "supporting_lead_indices": [idx1, idx2],
  "editors_note": "[One-sentence editor note with skeptical realism and measured hope]",
  "emphasis": "[Which tech trend is dominating today]"
}}
"""

    def __init__(self, prefer_cheap: bool = True):
        """
        Initialize processor with LLM Router
        
        Args:
            prefer_cheap: Favor cheaper models (default True)
        """
        self.router = LLMRouter()
        self.prefer_cheap = prefer_cheap
        print(f"✓ Processor initialized with LLM Router (prefer_cheap={prefer_cheap})")
    def process_insight_story(self, title: str, comments: List[str]) -> Dict:
        """Specialized processor for Page 4 (Insights) using discussion context"""
        comments_text = "\n---\n".join(comments) if comments else "No comments found."
        prompt = self.INSIGHT_PROMPT.format(title=title, comments=comments_text)
        
        result = self.router.call_llm(prompt=prompt)
        data = self.router._extract_json(result.get("response", ""))
        
        if data:
            return {
                'headline': data.get('headline', title),
                'summary': data.get('summary', 'No summary Distilled.') + " Quote: " + data.get('top_quote', ''),
                'source_author': data.get('contributor', 'The Community'),
                'significance_score': data.get('significance_score', 50),
                'is_insight': True
            }
        return {'headline': title, 'summary': 'No insight extracted.', 'significance_score': 10}

    def generate_editorial_pass(self, top_stories: List[Dict]) -> Dict:
        """Final LLM call to decide front page layout and tone"""
        story_briefs = "\n".join([f"[{i}] {s['generated_headline']} (Score: {s['significance_score']})" for i, s in enumerate(top_stories)])
        prompt = self.EDITORIAL_PROMPT.format(story_list=story_briefs)
        
        result = self.router.call_llm(prompt=prompt)
        data = self.router._extract_json(result.get("response", ""))
        
        if data:
            return data
        return {"main_lead_index": 0, "supporting_lead_indices": [1, 2], "editors_note": "A busy day in the latent space."}
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
        prompt = self.CATEGORIZATION_PROMPT.format(
            title=title,
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
        
        # Parse JSON response
        data = self.router._extract_json(result["response"])
        if data:
            raw_category_id = data.get("category_id", 0)
            try:
                category_id = int(raw_category_id)
            except (TypeError, ValueError):
                category_id = 0

            raw_confidence = data.get("confidence", 0.0)
            try:
                confidence = float(raw_confidence)
            except (TypeError, ValueError):
                confidence = 0.0
            
            if category_id == 0:
                return {
                    'category': 'Irrelevant',
                    'category_id': 0,
                    'confidence': confidence,
                    'model_used': result['model'],
                    'cost': result.get('cost', 0)
                }
            
            max_category_id = max(PAGE_CATEGORIES.keys())
            if 1 <= category_id <= max_category_id:
                category_name = PAGE_CATEGORIES.get(category_id)
                if not category_name:
                    category_id = 0
                    category_name = "Irrelevant"
                return {
                    'category': category_name,
                    'category_id': category_id,
                    'confidence': confidence,
                    'detected_model': data.get('detected_model'),
                    'model_used': result['model'],
                    'cost': result.get('cost', 0)
                }
        
        return {
            'category': 'Irrelevant',
            'category_id': 0,
            'confidence': 0.0,
            'model_used': result['model'],
            'cost': result.get('cost', 0)
        }
# ... Summarization parsing ...
    def _normalize_model_output_url(self, value: str) -> str:
        """Extract a clean URL from common LLM wrappers like markdown links."""
        if not value:
            return ""
        text = str(value).strip()
        if text.upper() == "NONE":
            return ""
        markdown_match = re.search(r'\((https?://[^)\s]+)\)', text)
        if markdown_match:
            return markdown_match.group(1)
        raw_match = re.search(r'https?://[^\s\]>)"]+', text)
        if raw_match:
            return raw_match.group(0)
        return ""

    def summarize_story(self, title: str, url: str, summary: str = "", 
                       category: str = "", image_urls: List[str] = None) -> Dict:
        """
        Summarize story using LLM Router
        """
        image_urls_str = "\n".join(image_urls) if image_urls else "NONE FOUND"
        prompt = self.SUMMARIZATION_PROMPT.format(
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
        
        default_res = {
            'headline': title,
            'summary': summary[:100],
            'image_url': None,
            'image_layout': 'SQUARE',
            'significance_score': 50,
            'worth_showing_image': False,
            'model_used': None,
            'cost': 0
        }

        if not result.get("response"):
            return default_res
        
        # Parse JSON response
        data = self.router._extract_json(result["response"])
        if data:
            normalized_image = self._normalize_model_output_url(data.get('selected_image_url', ''))
            return {
                'headline': data.get('headline', title),
                'summary': data.get('summary', summary[:100]),
                'image_url': normalized_image if normalized_image else None,
                'worth_showing_image': data.get('worth_showing_image', False),
                'image_layout': data.get('image_layout', 'SQUARE'),
                'significance_score': data.get('significance_score', 50),
                'model_used': result['model'],
                'cost': result.get('cost', 0)
            }
        
        return default_res
    
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
                'detected_model': cat_result.get('detected_model'),
                'summary': sum_result['summary'],
                'selected_image_url': selected_image_url,
                'worth_showing_image': sum_result.get('worth_showing_image', False),
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
        """Group stories by configured category ids."""
        organized = {i: [] for i in sorted(PAGE_CATEGORIES.keys())}
        
        for story in processed_stories:
            category_id = story['category_id']
            if category_id in organized:
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
