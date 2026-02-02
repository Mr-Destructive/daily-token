"Main orchestrator - runs daily newspaper generation"
import os
import json
import sys
import shutil
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
from processor_with_router import NewsProcessorWithRouter as NewsProcessor
from exporter import NewsExporter

def archive_current_edition(repo_root: Path):
    """Move files from output/current to output/archive/YYYY/MM/DD"""
    current_dir = repo_root / "output" / "current"
    metadata_file = current_dir / "metadata.json"
    
    if not metadata_file.exists():
        return
        
    try:
        with open(metadata_file, 'r') as f:
            meta = json.load(f)
            dt = datetime.fromisoformat(meta['timestamp'])
    except Exception:
        dt = datetime.now()
        
    archive_base = repo_root / "output" / "archive"
    archive_dir = archive_base / dt.strftime('%Y') / dt.strftime('%m') / dt.strftime('%d')
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[0/5] Archiving previous edition to {archive_dir.relative_to(repo_root)}...")
    
    # Move all files from current to archive
    for item in current_dir.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            shutil.copy2(item, archive_dir / item.name)

    # Create a simple redirect index.html for the archive folder
    redirect_html = f"""<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=newspaper.html"></head>
    <body><p>Redirecting to <a href="newspaper.html">newspaper.html</a>...</p></body></html>"""
    
    with open(archive_dir / "index.html", 'w') as f:
        f.write(redirect_html)
            
    print(f"   ✓ Archived previous edition with redirect index")

def generate_daily_newspaper() -> Dict:
    """Main pipeline: scrape → process → export"""
    
    repo_root = Path(__file__).resolve().parent.parent
    
    # Pre-step: Archive previous run
    archive_current_edition(repo_root)
    
    print("=" * 60)
    print(f"The Daily Token - AI Newspaper Generator - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Step 1: Aggregate news
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
    
    # Step 2: Process with LLM
    print("\n[2/5] Processing stories with LLM (HuggingFace + Fallbacks)...")
    processor = NewsProcessor()
    processed_stories = processor.process_stories(all_stories)
    
    print(f"   ✓ Processed {len(processed_stories)} stories")
    
    # Step 3: Organize by category
    print("\n[3/5] Organizing into 5-page newspaper...")
    organized = processor.organize_by_category(processed_stories)
    
    for page_num in range(1, 6):
        print(f"   - Page {page_num}: {len(organized[page_num])} stories")
    
    # Step 4: Download AI-selected images
    print("\n[4/5] Downloading AI-selected images (SEO & Preview URLs)...")
    images_dir = repo_root / "output" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    import requests
    img_count = 0
    for page_num in range(1, 6):
        for story_idx, story in enumerate(organized[page_num]):
            image_url = story.get('selected_image_url')
            
            if image_url and image_url.startswith('http'):
                safe_title = "".join([c if c.isalnum() else "_" for c in story['original_title'][:30]])
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': story.get('url', '')
                    }
                    img_response = requests.get(image_url, timeout=10, stream=True, headers=headers)
                    if img_response.status_code == 200:
                        content_type = img_response.headers.get("Content-Type", "").lower()
                        
                        # Only handle raster formats
                        if "image/png" in content_type: ext = ".png"
                        elif "image/webp" in content_type: ext = ".webp"
                        elif "image/jpeg" in content_type or "image/jpg" in content_type: ext = ".jpg"
                        else:
                            # Skip SVGs or other types
                            continue
                        
                        image_filename = f"story_{page_num}_{story_idx}_{safe_title}{ext}"
                        img_path = images_dir / image_filename
                        
                        with open(img_path, 'wb') as f:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        story['generated_image_path'] = f"../images/{image_filename}"
                        img_count += 1
                except Exception: pass
            else:
                story['generated_image_path'] = None
    
    print(f"   ✓ Downloaded {img_count} images from source SEO/Previews")
    
    # Step 5: Export
    print("\n[5/5] Exporting newspaper...")
    exporter = NewsExporter(organized)
    
    output_dir = repo_root / "output" / "current"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    html_file = exporter.export_html(str(output_dir / "newspaper.html"))
    json_file = exporter.export_json(str(output_dir / "newspaper.json"))
    md_file = exporter.export_markdown(str(output_dir / "newspaper.md"))
    txt_file = exporter.export_text(str(output_dir / "newspaper.txt"))
    rss_file = exporter.export_rss_feed(str(output_dir / "feed.xml"))
    
    import shutil
    landing_src = repo_root / "frontend" / "index.html"
    if landing_src.exists():
        shutil.copy2(landing_src, output_dir / "index.html")
    
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_stories': len(all_stories),
        'processed_stories': len(processed_stories),
        'pages': {str(k): len(v) for k, v in organized.items()}
    }
    
    with open(output_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ Daily newspaper generated successfully!")
    print("=" * 60)
    
    return {'status': 'success'}


if __name__ == "__main__":
    try:
        generate_daily_newspaper()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)