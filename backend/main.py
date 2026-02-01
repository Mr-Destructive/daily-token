"""Main orchestrator - runs daily newspaper generation"""
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Load .env from repo root and backend/ so vars are available (local: .env at root; CI: backend/.env)
try:
    from dotenv import load_dotenv
    _backend_dir = Path(__file__).resolve().parent
    _repo_root = _backend_dir.parent
    load_dotenv(_repo_root / ".env")
    load_dotenv(_backend_dir / ".env")  # CI writes here
except ImportError:
    pass

from scraper import NewsAggregator
from processor import NewsProcessor
from exporter import NewsExporter


def generate_daily_newspaper() -> Dict:
    """Main pipeline: scrape → process → export"""
    
    repo_root = Path(__file__).resolve().parent.parent
    
    print("=" * 60)
    print(f"Daily AI Newspaper Generator - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Step 1: Aggregate news
    print("\n[1/5] Aggregating news from HackerNews and RSS feeds...")
    aggregator = NewsAggregator()
    raw_news = aggregator.aggregate_all()
    
    # Combine HackerNews + RSS into single list (add HN discussion link for HN stories)
    all_stories = []
    for s in raw_news['hackernews']:
        s = dict(s)
        if s.get('id'):
            s['hn_url'] = f"https://news.ycombinator.com/item?id={s['id']}"
        all_stories.append(s)
    
    for feed_name, entries in raw_news['rss_feeds'].items():
        for entry in entries:
            entry = dict(entry)
            entry['source'] = feed_name
            entry['url'] = entry.get('link', entry.get('url', ''))
            all_stories.append(entry)
    
    print(f"   ✓ Found {len(all_stories)} stories")
    
    # Step 2: Process with LLM
    print("\n[2/5] Processing stories with LLM...")
    processor = NewsProcessor()
    processed_stories = processor.process_stories(all_stories)
    
    print(f"   ✓ Processed {len(processed_stories)} stories")
    
    # Step 3: Organize by category
    print("\n[3/5] Organizing into 5-page newspaper...")
    organized = processor.organize_by_category(processed_stories)
    
    for page_num in range(1, 6):
        print(f"   - Page {page_num}: {len(organized[page_num])} stories")
    
    # Step 4: Skip image processing (not used)
    print("\n[4/5] Skipping image processing...")
    
    # Step 5: Export
    print("\n[5/5] Exporting newspaper...")
    exporter = NewsExporter(organized)
    
    output_dir = repo_root / "output" / "current"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export in multiple formats
    html_file = exporter.export_html(str(output_dir / "newspaper.html"))
    json_file = exporter.export_json(str(output_dir / "newspaper.json"))
    md_file = exporter.export_markdown(str(output_dir / "newspaper.md"))
    rss_file = exporter.export_rss_feed(str(output_dir / "feed.xml"))
    
    print(f"   ✓ HTML: {html_file}")
    print(f"   ✓ JSON: {json_file}")
    print(f"   ✓ Markdown: {md_file}")
    print(f"   ✓ RSS Feed: {rss_file}")
    
    # Copy landing page into output so Netlify/GitHub Pages serve it at /
    import shutil
    landing_src = repo_root / "frontend" / "index.html"
    if landing_src.exists():
        shutil.copy2(landing_src, output_dir / "index.html")
        print(f"   ✓ Landing: {output_dir / 'index.html'}")
    
    # Save metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_stories': len(all_stories),
        'processed_stories': len(processed_stories),
        'pages': {}
    }
    
    for page_num in range(1, 6):
        metadata['pages'][page_num] = len(organized[page_num])
    
    with open(output_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ Daily newspaper generated successfully!")
    print("=" * 60)
    
    return {
        'status': 'success',
        'files': {
            'html': html_file,
            'json': json_file,
            'markdown': md_file,
            'rss': rss_file,
            'metadata': str(output_dir / "metadata.json")
        },
        'metadata': metadata
    }


if __name__ == "__main__":
    try:
        result = generate_daily_newspaper()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
