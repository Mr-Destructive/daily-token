"""Main orchestrator - runs daily newspaper generation."""
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional

# Load .env from repo root and backend/ so vars are available.
try:
    from dotenv import load_dotenv

    _backend_dir = Path(__file__).resolve().parent
    _repo_root = _backend_dir.parent
    load_dotenv(_repo_root / ".env")
    load_dotenv(_backend_dir / ".env")
except ImportError:
    pass

from exporter import NewsExporter
from processor_with_router import NewsProcessorWithRouter as NewsProcessor
from scraper import NewsAggregator

MODEL_PROVIDER_HINTS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "deepmind": "Google DeepMind",
    "meta": "Meta",
    "llama": "Meta",
    "mistral": "Mistral",
    "huggingface": "Hugging Face",
    "cohere": "Cohere",
    "xai": "xAI",
    "grok": "xAI",
    "alibaba": "Alibaba",
    "qwen": "Alibaba",
    "deepseek": "DeepSeek",
    "moonshot": "Moonshot",
    "baidu": "Baidu",
    "gemini": "Google",
    "claude": "Anthropic",
    "gpt": "OpenAI",
}

MODEL_NAME_RE = re.compile(
    r"\b("
    r"GPT[-\s]?\d(?:\.\d+)?(?:[-\w]+)?|"
    r"Claude\s?[\w\.-]*|"
    r"Gemini\s?[\w\.-]*|"
    r"Llama\s?[\w\.-]*|"
    r"Mistral\s?[\w\.-]*|"
    r"Qwen\s?[\w\.-]*|"
    r"DeepSeek\s?[\w\.-]*|"
    r"Grok\s?[\w\.-]*|"
    r"Command\s?[\w\.-]*|"
    r"Veo\s?[\w\.-]*"
    r")\b",
    re.IGNORECASE,
)


def _parse_story_datetime(story: Dict) -> Optional[datetime]:
    if story.get("time"):
        try:
            return datetime.fromtimestamp(int(story["time"]), tz=timezone.utc)
        except Exception:
            pass

    published = story.get("published")
    if isinstance(published, (int, float)):
        try:
            return datetime.fromtimestamp(int(published), tz=timezone.utc)
        except Exception:
            pass

    if isinstance(published, str) and published.strip():
        text = published.strip()
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            pass
        try:
            return parsedate_to_datetime(text)
        except Exception:
            pass
    return None


def _extract_model_releases(stories: List[Dict], edition_day: datetime) -> List[Dict]:
    release_terms = (
        "release",
        "released",
        "launch",
        "launched",
        "announce",
        "announced",
        "introducing",
        "unveil",
        "debut",
    )

    seen = set()
    releases: List[Dict] = []

    for story in stories:
        title = (story.get("title") or "").strip()
        if not title:
            continue

        lower = title.lower()
        if not any(term in lower for term in release_terms):
            continue

        match = MODEL_NAME_RE.search(title)
        if not match:
            continue

        story_dt = _parse_story_datetime(story)
        if story_dt:
            if story_dt.date() != edition_day.date():
                continue

        url = story.get("url") or story.get("link") or ""
        source = str(story.get("source", "")).lower()
        provider = "Unknown"

        for hint, provider_name in MODEL_PROVIDER_HINTS.items():
            if hint in lower or hint in source or hint in url.lower():
                provider = provider_name
                break

        model_name = match.group(1).strip()
        key = (model_name.lower(), url)
        if key in seen:
            continue
        seen.add(key)

        release_type = "Model Release"
        if any(word in lower for word in ["api", "sdk", "preview", "beta"]):
            release_type = "Model/API Update"

        releases.append(
            {
                "model_name": model_name,
                "provider": provider,
                "release_type": release_type,
                "title": title,
                "summary": (story.get("summary") or "")[:320],
                "source": story.get("source", "Unknown"),
                "source_url": url,
                "hn_url": story.get("hn_url", ""),
                "published": story_dt.isoformat() if story_dt else str(story.get("published", "")),
            }
        )

    releases.sort(key=lambda r: (r.get("provider") or "", r.get("model_name") or ""))
    return releases


def archive_previous_current_edition(repo_root: Path) -> Optional[Path]:
    """Copy the current edition to its dated archive folder before regeneration."""
    current_dir = repo_root / "output" / "current"
    newspaper_html = current_dir / "newspaper.html"

    if not newspaper_html.exists():
        return None

    metadata_file = current_dir / "metadata.json"
    edition_dt = datetime.now()
    if metadata_file.exists():
        try:
            with open(metadata_file, "r") as f:
                meta = json.load(f)
            edition_dt = datetime.fromisoformat(meta.get("timestamp"))
        except Exception:
            edition_dt = datetime.fromtimestamp(newspaper_html.stat().st_mtime)
    else:
        edition_dt = datetime.fromtimestamp(newspaper_html.stat().st_mtime)

    archive_dir = repo_root / "output" / "archive" / edition_dt.strftime("%Y") / edition_dt.strftime("%m") / edition_dt.strftime("%d")
    archive_dir.mkdir(parents=True, exist_ok=True)

    copy_files = [
        "newspaper.html",
        "newspaper.json",
        "newspaper.md",
        "newspaper.txt",
        "feed.xml",
        "metadata.json",
        "model_releases.json",
        "model-releases.html",
    ]
    copied = 0
    for name in copy_files:
        src = current_dir / name
        if src.exists():
            shutil.copy2(src, archive_dir / name)
            copied += 1

    redirect_html = (
        "<!DOCTYPE html><html><head><meta http-equiv=\"refresh\" content=\"0; url=newspaper.html\"></head>"
        "<body><p>Redirecting to <a href=\"newspaper.html\">newspaper.html</a>...</p></body></html>"
    )
    with open(archive_dir / "index.html", "w") as f:
        f.write(redirect_html)

    if copied:
        print(f"   ✓ Archived previous edition to {archive_dir}")
    return archive_dir


def get_archive_dir_for_date(repo_root: Path, dt: datetime) -> Path:
    archive_dir = repo_root / "output" / "archive" / dt.strftime("%Y") / dt.strftime("%m") / dt.strftime("%d")
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def fetch_raw_news(repo_root: Path) -> List[Dict]:
    """Step 1: Aggregate news and save to raw file."""
    print("\n[1/5] Aggregating news from HackerNews and RSS feeds...")
    aggregator = NewsAggregator()
    raw_news = aggregator.aggregate_all()

    all_stories: List[Dict] = []
    for s in raw_news["hackernews"]:
        s = dict(s)
        if s.get("id"):
            s["hn_url"] = f"https://news.ycombinator.com/item?id={s['id']}"
        all_stories.append(s)

    for feed_name, entries in raw_news["rss_feeds"].items():
        for entry in entries:
            normalized = dict(entry)
            normalized["source"] = feed_name
            normalized["url"] = normalized.get("link", normalized.get("url", ""))
            all_stories.append(normalized)

    print(f"   ✓ Found {len(all_stories)} stories")

    raw_path = repo_root / "output" / "raw_news.json"
    with open(raw_path, "w") as f:
        json.dump(all_stories, f, indent=2)
    print(f"   ✓ Raw news saved to {raw_path}")

    return all_stories


def generate_daily_newspaper(skip_fetch: bool = False) -> Dict:
    """Main pipeline: fetch -> process -> export."""
    repo_root = Path(__file__).resolve().parent.parent

    print("=" * 60)
    print(f"The Daily Token - AI Newspaper Generator - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    archive_previous_current_edition(repo_root)

    if skip_fetch:
        raw_path = repo_root / "output" / "raw_news.json"
        if raw_path.exists():
            print("\n[1/5] Skipping fetch, loading from raw_news.json...")
            with open(raw_path, "r") as f:
                all_stories = json.load(f)
        else:
            all_stories = fetch_raw_news(repo_root)
    else:
        all_stories = fetch_raw_news(repo_root)

    print("\n[2/5] Processing stories with LLM (Free Chatbots + HF + Fallbacks)...")
    processor = NewsProcessor()
    processed_stories = processor.process_stories(all_stories)

    print("\n[2c] Enriching Insights with HackerNews discussions...")
    aggregator = NewsAggregator()
    for story in processed_stories:
        if story["category_id"] == 8 and story.get("hn_url"):
            try:
                match = re.search(r"id=(\d+)", story["hn_url"])
                if match:
                    item_id = int(match.group(1))
                    details = aggregator.hn_scraper._get_story(item_id)
                    if details and details.get("kids"):
                        comments = aggregator.hn_scraper.fetch_hn_comments(details["kids"])
                        insight_data = processor.process_insight_story(story["original_title"], comments)
                        story["generated_headline"] = insight_data["headline"]
                        story["summary"] = insight_data["summary"]
                        story["source_author"] = insight_data.get("source_author", "The Community")
            except Exception as e:
                print(f"      ⚠ Failed to enrich insight: {e}")

    print("\n[2d] Performing Final Editorial Pass...")
    valid_candidates = [s for s in processed_stories if s.get("significance_score")]
    top_candidates = sorted(valid_candidates, key=lambda x: x.get("significance_score", 0), reverse=True)[:10]
    if not top_candidates:
        editorial = {
            "main_lead_index": 0,
            "supporting_lead_indices": [],
            "editors_note": "A quiet day in AI.",
            "emphasis": "General",
        }
    else:
        editorial = processor.generate_editorial_pass(top_candidates)
    print(f"   ✓ Editor's Note: {editorial.get('editors_note')}")

    edition_dt = datetime.now()
    model_releases = _extract_model_releases(all_stories, edition_dt)
    print(f"   ✓ Model releases detected: {len(model_releases)}")

    print("\n[3/5] Organizing into 5-page newspaper...")
    organized = processor.organize_by_category(processed_stories)
    from config import PAGES_CONFIG

    for page_num in range(1, 6):
        count = sum(len(organized.get(cat, [])) for cat in PAGES_CONFIG[page_num]["categories"])
        print(f"   - Page {page_num} ({PAGES_CONFIG[page_num]['title']}): {count} stories")

    print("\n[4/5] Downloading AI-selected images (SEO & Preview URLs)...")
    images_dir = repo_root / "output" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    import requests

    img_count = 0
    for cat_id in range(1, 10):
        for story_idx, story in enumerate(organized.get(cat_id, [])):
            image_url = story.get("selected_image_url")
            worth_showing = story.get("worth_showing_image", False)
            if story_idx < 3 and cat_id in [1, 2, 3]:
                worth_showing = True

            if worth_showing and image_url and str(image_url).startswith("http"):
                safe_title = "".join([c if c.isalnum() else "_" for c in story.get("original_title", "story")[:30]])
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Referer": story.get("url", ""),
                    }
                    img_response = requests.get(image_url, timeout=10, stream=True, headers=headers)
                    if img_response.status_code == 200:
                        content_type = img_response.headers.get("Content-Type", "").lower()
                        if "image/png" in content_type:
                            ext = ".png"
                        elif "image/webp" in content_type:
                            ext = ".webp"
                        elif "image/jpeg" in content_type or "image/jpg" in content_type:
                            ext = ".jpg"
                        else:
                            continue

                        image_filename = f"story_{cat_id}_{story_idx}_{safe_title}{ext}"
                        img_path = images_dir / image_filename
                        with open(img_path, "wb") as f:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        story["generated_image_path"] = f"../images/{image_filename}"
                        print(f"      ✓ Downloaded: {image_filename}")
                        img_count += 1
                except Exception:
                    pass
            else:
                story["generated_image_path"] = None

    print(f"   ✓ Downloaded {img_count} images")

    print("\n[5/5] Exporting newspaper...")
    archive_root = repo_root / "output" / "archive"
    exporter = NewsExporter(organized, timestamp=edition_dt.isoformat(), model_releases=model_releases, archive_root=archive_root)
    exporter.editorial = editorial
    exporter.top_candidates = top_candidates

    current_dir = repo_root / "output" / "current"
    current_dir.mkdir(parents=True, exist_ok=True)

    exporter.export_html(str(current_dir / "newspaper.html"), image_prefix="images/")
    exporter.export_json(str(current_dir / "newspaper.json"))
    exporter.export_markdown(str(current_dir / "newspaper.md"))
    exporter.export_text(str(current_dir / "newspaper.txt"))
    exporter.export_rss_feed(str(current_dir / "feed.xml"))
    exporter.export_model_releases_json(str(current_dir / "model_releases.json"))
    exporter.export_model_releases_html(str(current_dir / "model-releases.html"), base_rel="")

    archive_dir = get_archive_dir_for_date(repo_root, edition_dt)
    exporter.export_html(str(archive_dir / "newspaper.html"), image_prefix="../../../../images/")
    exporter.export_json(str(archive_dir / "newspaper.json"))
    exporter.export_markdown(str(archive_dir / "newspaper.md"))
    exporter.export_text(str(archive_dir / "newspaper.txt"))
    exporter.export_model_releases_json(str(archive_dir / "model_releases.json"))
    exporter.export_model_releases_html(str(archive_dir / "model-releases.html"), base_rel="")

    redirect_html = (
        "<!DOCTYPE html><html><head><meta http-equiv=\"refresh\" content=\"0; url=newspaper.html\"></head>"
        "<body><p>Redirecting to <a href=\"newspaper.html\">newspaper.html</a>...</p></body></html>"
    )
    with open(archive_dir / "index.html", "w") as f:
        f.write(redirect_html)

    exporter.export_archive_index(str(archive_root), str(archive_root / "index.html"))

    landing_src = repo_root / "frontend" / "index.html"
    if landing_src.exists():
        shutil.copy2(landing_src, current_dir / "index.html")

    metadata = {
        "timestamp": edition_dt.isoformat(),
        "total_stories": len(all_stories),
        "processed_stories": len(processed_stories),
        "model_releases": len(model_releases),
        "pages": {str(p): sum(len(organized.get(c, [])) for c in PAGES_CONFIG[p]["categories"]) for p in range(1, 6)},
    }

    with open(current_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 60)
    print("✓ Daily newspaper generated successfully!")
    print("=" * 60)
    return {"status": "success"}


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
            NewsExporter.reconstruct_from_json(str(json_path), str(html_path))
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
