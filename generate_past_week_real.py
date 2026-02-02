import os
import json
import sys
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

# Setup paths
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.append(str(backend_dir))

from scraper import NewsAggregator
from processor_with_router import NewsProcessorWithRouter as NewsProcessor
from exporter import NewsExporter

def get_historical_stories(all_stories, day_offset):
    """Slice or shuffle stories differently for each day to simulate history"""
    import random
    temp = list(all_stories)
    random.seed(day_offset) # Consistent shuffle for the same offset
    random.shuffle(temp)
    return temp[:25]

def generate_backfill():
    repo_root = Path(__file__).resolve().parent
    
    print("=" * 60)
    print("BACKFILLING PAST WEEK WITH UNIQUE CONTENT (3 WORKERS)")
    print("=" * 60)
    
    # 1. Aggregate fresh news once
    print("\n[1] Aggregating news...")
    aggregator = NewsAggregator()
    raw_news = aggregator.aggregate_all()
    
    all_raw = []
    for s in raw_news['hackernews']:
        s = dict(s)
        if s.get('id'):
            s['hn_url'] = f"https://news.ycombinator.com/item?id={s['id']}"
        all_raw.append(s)
    
    for feed_name, entries in raw_news['rss_feeds'].items():
        for entry in entries:
            entry = dict(entry)
            entry['source'] = feed_name
            entry['url'] = entry.get('link', entry.get('url', ''))
            all_raw.append(entry)
            
    # 2. Loop through last 7 days
    processor = NewsProcessor()
    locations = ["SILICON VALLEY", "TENSOR CITY", "PARAMETER PARK", "NEURAL NODES", "VECTOR VALLEY", "LATENT LAKE", "TRANSFORMER TOWN"]

    for i in range(7):
        target_date = datetime.now() - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"\n>>> PROCESSING FOR DATE: {date_str} (Workers=3)")
        
        # Get unique story set for this date
        stories_for_day = get_historical_stories(all_raw, i)
        
        # Process stories with 3 workers
        processed = processor.process_stories(stories_for_day, max_workers=3)
        organized = processor.organize_by_category(processed)
        
        # Setup Dated Archive Path
        archive_base = repo_root / "output" / "archive"
        archive_dir = archive_base / target_date.strftime('%Y') / target_date.strftime('%m') / target_date.strftime('%d')
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Export with unique location
        exporter = NewsExporter(organized, location=locations[i % len(locations)])
        # archive/2026/02/02/newspaper.html -> 4 levels up to images/
        exporter.export_html(str(archive_dir / "newspaper.html"), image_prefix="../../../../images/")
        exporter.export_json(str(archive_dir / "newspaper.json"))
        exporter.export_markdown(str(archive_dir / "newspaper.md"))
        exporter.export_text(str(archive_dir / "newspaper.txt"))
        
        # Metadata for that specific day
        metadata = {
            'timestamp': target_date.isoformat(),
            'total_stories': len(stories_for_day),
            'processed_stories': len(processed),
            'pages': {str(k): len(v) for k, v in organized.items()}
        }
        with open(archive_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create redirect
        redirect_html = f"""<!DOCTYPE html><html><head><meta http-equiv=\"refresh\" content=\"0; url=newspaper.html\"></head>
        <body><p>Redirecting to <a href=\"newspaper.html\">newspaper.html</a>...</p></body></html>"""
        with open(archive_dir / "index.html", 'w') as f:
            f.write(redirect_html)
            
        print(f"   ✓ Generated unique archive for {date_str}")
        if i < 6: time.sleep(1)

    # 3. Finalize Archive Index
    print("\n[3] Regenerating Archive Index...")
    exporter = NewsExporter({}, location="THE ARCHIVES")
    exporter.export_archive_index(
        str(repo_root / "output" / "archive"),
        str(repo_root / "output" / "archive" / "index.html")
    )
    
    print("\n" + "=" * 60)
    print("✓ Unique backfill complete!")
    print("=" * 60)

if __name__ == "__main__":
    generate_backfill()
