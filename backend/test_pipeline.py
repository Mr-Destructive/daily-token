"""Test the full pipeline with sample data (no API keys needed)"""
import json
from datetime import datetime
from pathlib import Path

# Import with fallbacks
try:
    from scraper import NewsAggregator
except ImportError:
    print("Warning: Can't import scraper, will use sample data")

from exporter import NewsExporter
from image_generator import PlaceholderImageGenerator


def create_sample_stories():
    """Generate realistic sample stories for testing"""
    
    return {
        1: [
            {
                'original_title': 'OpenAI announces GPT-5 with breakthrough reasoning capabilities',
                'url': 'https://openai.com/research/gpt5',
                'source': 'HackerNews',
                'score': 2140,
                'category': 'Front Page Headlines',
                'category_id': 1,
                'confidence': 0.98,
                'summary': """HEADLINE: GPT-5 Arrives with Unprecedented Reasoning
SUMMARY: OpenAI released GPT-5, showcasing 10x improvements in complex reasoning 
tasks. The model demonstrates breakthrough performance on mathematical proofs, 
code generation, and scientific research.""",
                'published': datetime.now().isoformat()
            },
            {
                'original_title': 'DeepMind releases Gemini 2.0 Ultra - multimodal AI breakthrough',
                'url': 'https://deepmind.google/gemini2',
                'source': 'HackerNews',
                'score': 1890,
                'category': 'Front Page Headlines',
                'category_id': 1,
                'confidence': 0.97,
                'summary': """HEADLINE: Gemini 2.0 Ultra Achieves New Multimodal Milestone
SUMMARY: Google DeepMind unveiled Gemini 2.0 Ultra, demonstrating state-of-the-art
performance across text, images, video, and audio. Model outperforms specialized
systems across benchmarks.""",
                'published': datetime.now().isoformat()
            }
        ],
        2: [
            {
                'original_title': 'Mistral releases new 200B parameter open-source model',
                'url': 'https://mistral.ai/200b',
                'source': 'HackerNews',
                'score': 1420,
                'category': 'LLMs & Foundation Models',
                'category_id': 2,
                'confidence': 0.95,
                'summary': """HEADLINE: Mistral Launches 200B Parameter Open Model
SUMMARY: Mistral released a 200 billion parameter model rivaling proprietary LLMs,
emphasizing efficiency and speed. Available for research and commercial use.""",
                'published': datetime.now().isoformat()
            },
            {
                'original_title': 'Researchers achieve breakthrough in model compression',
                'url': 'https://arxiv.org/compression',
                'source': 'arxiv_lg',
                'score': 980,
                'category': 'LLMs & Foundation Models',
                'category_id': 2,
                'confidence': 0.93,
                'summary': """HEADLINE: New Compression Technique Halves Model Sizes
SUMMARY: MIT researchers published novel quantization approach reducing model sizes
by 50% while maintaining 99% performance. Implications for edge deployment.""",
                'published': datetime.now().isoformat()
            }
        ],
        3: [
            {
                'original_title': 'Boston Dynamics releases humanoid robot with expanded capabilities',
                'url': 'https://bostondynamics.com/robot',
                'source': 'HackerNews',
                'score': 1650,
                'category': 'World Models & Vision',
                'category_id': 3,
                'confidence': 0.94,
                'summary': """HEADLINE: New Humanoid Robot Demonstrates Complex Manipulation
SUMMARY: Boston Dynamics unveiled updated Atlas with improved dexterity, capable
of complex assembly tasks. Represents major step toward practical robotics.""",
                'published': datetime.now().isoformat()
            }
        ],
        4: [
            {
                'original_title': 'Anthropic announces $5B funding round, valuation reaches $20B',
                'url': 'https://anthropic.com/funding',
                'source': 'HackerNews',
                'score': 2300,
                'category': 'AI Labs & Companies',
                'category_id': 4,
                'confidence': 0.96,
                'summary': """HEADLINE: Anthropic Secures $5B in Funding
SUMMARY: Anthropic raised $5 billion Series D, bringing valuation to $20B.
Funds support Claude model development and AI safety research initiatives.""",
                'published': datetime.now().isoformat()
            },
            {
                'original_title': 'Meta releases Llama 3.5 with improved reasoning',
                'url': 'https://meta.com/llama3.5',
                'source': 'metaai',
                'score': 1750,
                'category': 'AI Labs & Companies',
                'category_id': 4,
                'confidence': 0.94,
                'summary': """HEADLINE: Meta Releases Llama 3.5 with Enhanced Reasoning
SUMMARY: Meta released Llama 3.5, featuring improved instruction following and
complex reasoning. Available under open license for research and production.""",
                'published': datetime.now().isoformat()
            }
        ],
        5: [
            {
                'original_title': 'Opinion: Why scaling laws might plateau and what comes next',
                'url': 'https://example.com/scaling-analysis',
                'source': 'HackerNews',
                'score': 890,
                'category': 'Speculations & Deep Tech',
                'category_id': 5,
                'confidence': 0.92,
                'summary': """HEADLINE: Analysts Question Future of Scaling Laws
SUMMARY: Researchers debate whether traditional scaling approaches hit diminishing
returns. New architecture paradigms may drive next generation of AI advances.""",
                'published': datetime.now().isoformat()
            }
        ]
    }


def test_full_pipeline():
    """Test the complete export pipeline"""
    
    print("=" * 70)
    print("Daily AI Newspaper - Full Pipeline Test")
    print("=" * 70)
    print()
    
    # Step 1: Create sample data
    print("[1/4] Loading sample stories...")
    organized = create_sample_stories()
    total_stories = sum(len(stories) for stories in organized.values())
    print(f"   ✓ Loaded {total_stories} sample stories")
    for page_num in range(1, 6):
        print(f"      Page {page_num}: {len(organized[page_num])} stories")
    print()
    
    # Step 2: Generate images
    print("[2/4] Generating placeholder images...")
    # Use absolute paths relative to script location
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    image_dir = repo_root / "output" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    
    for page_num in range(1, 6):
        if organized[page_num]:
            top_story = organized[page_num][0]
            svg_path = image_dir / f"page_{page_num}_header.svg"
            PlaceholderImageGenerator.save_placeholder(
                top_story['original_title'],
                top_story['category'],
                str(svg_path)
            )
            print(f"   ✓ Page {page_num}: {svg_path.name}")
    print()
    
    # Step 3: Export
    print("[3/4] Exporting in multiple formats...")
    exporter = NewsExporter(organized)
    
    output_dir = repo_root / "output" / "current"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    html_file = exporter.export_html(str(output_dir / "newspaper.html"))
    json_file = exporter.export_json(str(output_dir / "newspaper.json"))
    md_file = exporter.export_markdown(str(output_dir / "newspaper.md"))
    rss_file = exporter.export_rss_feed(str(output_dir / "feed.xml"))
    
    print(f"   ✓ HTML: {Path(html_file).name}")
    print(f"   ✓ JSON: {Path(json_file).name}")
    print(f"   ✓ Markdown: {Path(md_file).name}")
    print(f"   ✓ RSS Feed: {Path(rss_file).name}")
    print()
    
    # Step 4: Summary
    print("[4/4] Pipeline Summary")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Stories: {total_stories}")
    print()
    print("Output Files:")
    for f in sorted(output_dir.glob("*")):
        size = f.stat().st_size / 1024
        print(f"  {f.name:<25} {size:>8.1f} KB")
    print()
    print("Open newspaper.html in a browser to view the interactive newspaper!")
    print("=" * 70)


if __name__ == "__main__":
    test_full_pipeline()
