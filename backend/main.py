"Main orchestrator - runs daily newspaper generation"
import os
import json
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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
from processor_with_router import NewsProcessorWithRouter as NewsProcessor
from exporter import NewsExporter

def archive_current_edition(repo_root: Path) -> Path:
    """Prepare archive directory for YYYY/MM/DD"""
    current_dir = repo_root / "output" / "current"
    metadata_file = current_dir / "metadata.json"
    
    dt = datetime.now()
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                meta = json.load(f)
                dt = datetime.fromisoformat(meta['timestamp'])
        except Exception: pass
        
    archive_base = repo_root / "output" / "archive"
    archive_dir = archive_base / dt.strftime('%Y') / dt.strftime('%m') / dt.strftime('%d')
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir

def fetch_raw_news(repo_root: Path) -> List[Dict]:
    """Step 1: Aggregate news and save to raw file"""
    print("\n[1/5] Aggregating news from HackerNews and RSS feeds...")
    aggregator = NewsAggregator()
    raw_news = aggregator.aggregate_all()
    
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
    
    # Save raw news for debugging/separation
    raw_path = repo_root / "output" / "raw_news.json"
    with open(raw_path, 'w') as f:
        json.dump(all_stories, f, indent=2)
    print(f"   ✓ Raw news saved to {raw_path}")
    
    return all_stories

def generate_daily_newspaper(skip_fetch: bool = False) -> Dict:
    """Main pipeline: fetch → process → export"""
    
    repo_root = Path(__file__).resolve().parent.parent
    
    # Pre-step: Archive previous run
    archive_current_edition(repo_root)
    
    print("=" * 60)
    print(f"The Daily Token - AI Newspaper Generator - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Step 1: Aggregation
    if skip_fetch:
        raw_path = repo_root / "output" / "raw_news.json"
        if raw_path.exists():
            print("\n[1/5] Skipping fetch, loading from raw_news.json...")
            with open(raw_path, 'r') as f:
                all_stories = json.load(f)
        else:
            all_stories = fetch_raw_news(repo_root)
    else:
        all_stories = fetch_raw_news(repo_root)
    
    # Step 2: Process with LLM
    print("\n[2/5] Processing stories with LLM (Free Chatbots + HF + Fallbacks)...")
    processor = NewsProcessor()
    
    # 2a. Initial Processing
    processed_stories = processor.process_stories(all_stories)
    
    # 2b. Special Handling for Insights (Page 4)
    print("\n[2c] Enriching Insights with HackerNews discussions...")
    aggregator = NewsAggregator()
    for story in processed_stories:
        if story['category_id'] == 4 and story.get('hn_url'):
            try:
                import re
                match = re.search(r'id=(\d+)', story['hn_url'])
                if match:
                    item_id = int(match.group(1))
                    details = aggregator.hn_scraper._get_story(item_id)
                    if details and details.get('kids'):
                        comments = aggregator.hn_scraper.fetch_hn_comments(details['kids'])
                        insight_data = processor.process_insight_story(story['original_title'], comments)
                        story['generated_headline'] = insight_data['headline']
                        story['summary'] = insight_data['summary']
                        story['source_author'] = insight_data.get('source_author', 'HackerNews')
            except Exception as e:
                print(f"      ⚠ Failed to enrich insight: {e}")

    # 2d. Final Editorial Pass
    print("\n[2d] Performing Final Editorial Pass...")
    valid_candidates = [s for s in processed_stories if s.get('significance_score')]
    top_candidates = sorted(valid_candidates, key=lambda x: x.get('significance_score', 0), reverse=True)[:10]
    
    if not top_candidates:
        editorial = {"main_lead_index": 0, "supporting_lead_indices": [], "editors_note": "A quiet day in AI.", "emphasis": "General"}
    else:
        editorial = processor.generate_editorial_pass(top_candidates)
    
    print(f"   ✓ Editor's Note: {editorial.get('editors_note')}")
    
    # Step 3: Organize by category
    print("\n[3/5] Organizing into 5-page newspaper...")
    organized = processor.organize_by_category(processed_stories)
    
    from config import PAGES_CONFIG, PAGE_CATEGORIES
    for page_num in range(1, 6):
        count = sum(len(organized.get(cat, [])) for cat in PAGES_CONFIG[page_num]["categories"])
        print(f"   - Page {page_num} ({PAGES_CONFIG[page_num]['title']}): {count} stories")
    
    # Step 4: Download AI-selected images
    print("\n[4/5] Downloading AI-selected images (SEO & Preview URLs)...")
    images_dir = repo_root / "output" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    import requests
    img_count = 0
    for cat_id in range(1, 10):
        for story_idx, story in enumerate(organized.get(cat_id, [])):
            image_url = story.get('selected_image_url')
            worth_showing = story.get('worth_showing_image', False)
            
            # Special case: Always try to get images for top leads on front page
            if story_idx < 3 and cat_id in [1, 2, 3]:
                worth_showing = True

            if worth_showing and image_url and image_url.startswith('http'):
                safe_title = "".join([c if c.isalnum() else "_" for c in story['original_title'][:30]])
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': story.get('url', '')
                    }
                    img_response = requests.get(image_url, timeout=10, stream=True, headers=headers)
                    if img_response.status_code == 200:
                        content_type = img_response.headers.get("Content-Type", "").lower()
                        if "image/png" in content_type: ext = ".png"
                        elif "image/webp" in content_type: ext = ".webp"
                        elif "image/jpeg" in content_type or "image/jpg" in content_type: ext = ".jpg"
                        else: continue
                        
                        image_filename = f"story_{cat_id}_{story_idx}_{safe_title}{ext}"
                        img_path = images_dir / image_filename
                        with open(img_path, 'wb') as f:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        story['generated_image_path'] = f"../images/{image_filename}"
                        print(f"      ✓ Downloaded: {image_filename}")
                        img_count += 1
                except Exception: pass
            else:
                story['generated_image_path'] = None
    
    print(f"   ✓ Downloaded {img_count} images")
    
    # Step 5: Export
    print("\n[5/5] Exporting newspaper...")
    exporter = NewsExporter(organized)
    exporter.editorial = editorial
    exporter.top_candidates = top_candidates
    
    # 5a. Export Current Edition
    current_dir = repo_root / "output" / "current"
    current_dir.mkdir(parents=True, exist_ok=True)
    
    html_file = exporter.export_html(str(current_dir / "newspaper.html"), image_prefix="images/")
    json_file = exporter.export_json(str(current_dir / "newspaper.json"))
    md_file = exporter.export_markdown(str(current_dir / "newspaper.md"))
    txt_file = exporter.export_text(str(current_dir / "newspaper.txt"))
    rss_file = exporter.export_rss_feed(str(current_dir / "feed.xml"))
    
    # 5b. Export Dated Archive
    archive_dir = archive_current_edition(repo_root)
    # For archive folders like archive/2026/02/02/, we need 4 levels up to get to images/
    exporter.export_html(str(archive_dir / "newspaper.html"), image_prefix="../../../../images/")
    exporter.export_json(str(archive_dir / "newspaper.json"))
    exporter.export_markdown(str(archive_dir / "newspaper.md"))
    exporter.export_text(str(archive_dir / "newspaper.txt"))
    
    # Create redirect index for archive
    redirect_html = f"""<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=newspaper.html"></head>
    <body><p>Redirecting to <a href="newspaper.html">newspaper.html</a>...</p></body></html>"""
    with open(archive_dir / "index.html", 'w') as f:
        f.write(redirect_html)

    # 5c. Generate Archive Index
    archive_index = exporter.export_archive_index(
        str(repo_root / "output" / "archive"),
        str(repo_root / "output" / "archive" / "index.html")
    )
    
    # Copy landing page
    import shutil
    landing_src = repo_root / "frontend" / "index.html"
    if landing_src.exists():
        shutil.copy2(landing_src, current_dir / "index.html")
    
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_stories': len(all_stories),
        'processed_stories': len(processed_stories),
        'pages': {str(p): sum(len(organized.get(c, [])) for c in PAGES_CONFIG[p]["categories"]) for p in range(1, 6)}
    }
    
    with open(current_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ Daily newspaper generated successfully!")
    print("=" * 60)
    
    return {'status': 'success'}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetching and use last raw_news.json")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI processing and use last newspaper.json")
    args = parser.parse_args()
    
    try:
        if args.skip_ai:
            print("\n[!] Skipping AI processing, reconstructing from existing newspaper.json...")
            repo_root = Path(__file__).resolve().parent.parent
            json_path = repo_root / "output" / "current" / "newspaper.json"
            html_path = repo_root / "output" / "current" / "newspaper.html"
            from exporter import NewsExporter
            NewsExporter.reconstruct_from_json(str(json_path), str(html_path))
            
            # Copy to docs
            import shutil
            shutil.copy2(html_path, repo_root / "docs" / "index.html")
            print("✓ UI Reconstructed and copied to docs/")
            sys.exit(0)

        generate_daily_newspaper(skip_fetch=args.skip_fetch)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)