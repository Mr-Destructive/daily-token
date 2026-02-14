"""Backfill missing archive editions by fetching historical HN + RSS data."""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from exporter import NewsExporter
from main import (
    _attach_hn_comment_signals,
    _extract_model_releases,
    _load_timeline_releases_for_day,
    _merge_model_releases,
)
from processor_with_router import NewsProcessorWithRouter
from scraper import NewsAggregator


def _iter_dates(start: datetime, end: datetime):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _existing_days(archive_root: Path) -> set:
    days = set()
    if not archive_root.exists():
        return days
    for year_dir in archive_root.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            for day_dir in month_dir.iterdir():
                if day_dir.is_dir() and day_dir.name.isdigit() and (day_dir / "newspaper.html").exists():
                    days.add(f"{year_dir.name}-{month_dir.name}-{day_dir.name}")
    return days


def _normalize_raw(raw: Dict) -> List[Dict]:
    stories: List[Dict] = []
    for s in raw.get("hackernews", []):
        s = dict(s)
        if s.get("id"):
            s["hn_url"] = f"https://news.ycombinator.com/item?id={s['id']}"
        stories.append(s)

    for feed_name, entries in raw.get("rss_feeds", {}).items():
        for entry in entries:
            item = dict(entry)
            item["source"] = feed_name
            item["url"] = item.get("link", item.get("url", ""))
            stories.append(item)
    return stories


def _write_redirect(path: Path):
    html = (
        "<!DOCTYPE html><html><head><meta http-equiv=\"refresh\" content=\"0; url=newspaper.html\"></head>"
        "<body><p>Redirecting to <a href=\"newspaper.html\">newspaper.html</a>...</p></body></html>"
    )
    path.write_text(html)


def backfill(start: datetime, end: datetime, overwrite: bool = False):
    repo_root = Path(__file__).resolve().parent.parent
    archive_root = repo_root / "output" / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)

    aggregator = NewsAggregator()
    processor = NewsProcessorWithRouter(prefer_cheap=True)

    existing = _existing_days(archive_root)

    for day in _iter_dates(start, end):
        day_key = day.strftime("%Y-%m-%d")
        out_dir = archive_root / day.strftime("%Y") / day.strftime("%m") / day.strftime("%d")

        if day_key in existing and not overwrite:
            print(f"[skip] {day_key} already exists")
            continue

        print(f"[fetch] {day_key}")
        try:
            raw = aggregator.aggregate_all(target_date=day)
            stories = _normalize_raw(raw)
            if not stories:
                print(f"  - no stories found for {day_key}, writing placeholder edition")
                organized = {i: [] for i in range(1, 10)}
                organized[6] = [
                    {
                        "original_title": f"Archive Placeholder for {day_key}",
                        "generated_headline": f"Archive Record Pending: {day_key}",
                        "url": "",
                        "hn_url": "",
                        "source": "Daily Token",
                        "score": 0,
                        "significance_score": 1,
                        "category": "AI & LLM Overview",
                        "category_id": 6,
                        "confidence": 1.0,
                        "summary": "Source fetch failed for this date. This placeholder preserves archive continuity until data backfill succeeds.",
                        "selected_image_url": None,
                        "worth_showing_image": False,
                        "image_layout": "SQUARE",
                    }
                ]
                edition_ts = day.replace(hour=0, minute=0, second=0, microsecond=0)
                exporter = NewsExporter(
                    organized,
                    timestamp=edition_ts.isoformat(),
                    model_releases=[],
                    archive_root=archive_root,
                )
                exporter.editorial = {
                    "main_lead_index": 0,
                    "supporting_lead_indices": [],
                    "editors_note": "Signal unavailable today; archive entry retained for continuity.",
                    "emphasis": "Continuity",
                }
                out_dir.mkdir(parents=True, exist_ok=True)
                exporter.export_html(str(out_dir / "newspaper.html"), image_prefix="../../../../images/")
                exporter.export_json(str(out_dir / "newspaper.json"))
                exporter.export_markdown(str(out_dir / "newspaper.md"))
                exporter.export_text(str(out_dir / "newspaper.txt"))
                exporter.export_model_releases_json(str(out_dir / "model_releases.json"))
                exporter.export_model_releases_html(str(out_dir / "model-releases.html"), base_rel="")
                with open(out_dir / "metadata.json", "w") as f:
                    json.dump(
                        {
                            "timestamp": edition_ts.isoformat(),
                            "total_stories": 0,
                            "processed_stories": 1,
                            "placeholder": True,
                        },
                        f,
                        indent=2,
                    )
                _write_redirect(out_dir / "index.html")
                continue

            processed = processor.process_stories(stories[:30])
            organized = processor.organize_by_category(processed)

            top_candidates = sorted(processed, key=lambda s: s.get("significance_score", 0), reverse=True)[:10]
            editorial = processor.generate_editorial_pass(top_candidates) if top_candidates else {
                "main_lead_index": 0,
                "supporting_lead_indices": [],
                "editors_note": "Signal was thin; still worth reading closely.",
                "emphasis": "Continuity",
            }

            edition_ts = day.replace(hour=0, minute=0, second=0, microsecond=0)
            release_scan_stories = list(stories)
            for item in processed:
                release_scan_stories.append(
                    {
                        "title": item.get("original_title") or item.get("generated_headline") or "",
                        "summary": item.get("summary", ""),
                        "url": item.get("url", ""),
                        "hn_url": item.get("hn_url", ""),
                        "source": item.get("source", ""),
                        "published": item.get("published", ""),
                        "category_id": item.get("category_id"),
                        "detected_model": item.get("detected_model"),
                    }
                )

            _attach_hn_comment_signals(release_scan_stories, aggregator)
            model_releases = _extract_model_releases(release_scan_stories, edition_ts)
            timeline_releases = _load_timeline_releases_for_day(edition_ts)
            model_releases = _merge_model_releases(model_releases, timeline_releases)

            exporter = NewsExporter(
                organized,
                timestamp=edition_ts.isoformat(),
                model_releases=model_releases,
                archive_root=archive_root,
            )
            exporter.editorial = editorial
            exporter.top_candidates = top_candidates

            out_dir.mkdir(parents=True, exist_ok=True)
            exporter.export_html(str(out_dir / "newspaper.html"), image_prefix="../../../../images/")
            exporter.export_json(str(out_dir / "newspaper.json"))
            exporter.export_markdown(str(out_dir / "newspaper.md"))
            exporter.export_text(str(out_dir / "newspaper.txt"))
            exporter.export_model_releases_json(str(out_dir / "model_releases.json"))
            exporter.export_model_releases_html(str(out_dir / "model-releases.html"), base_rel="")

            with open(out_dir / "metadata.json", "w") as f:
                json.dump(
                    {
                        "timestamp": edition_ts.isoformat(),
                        "total_stories": len(stories),
                        "processed_stories": len(processed),
                        "model_releases": len(model_releases),
                    },
                    f,
                    indent=2,
                )
            _write_redirect(out_dir / "index.html")
            print(f"  - wrote {out_dir}")
        except Exception as exc:
            print(f"  - failed {day_key}: {exc}")

    index_exporter = NewsExporter({}, archive_root=archive_root)
    index_exporter.export_archive_index(str(archive_root), str(archive_root / "index.html"))
    # Keep root model release page as an archive-wide ledger.
    current_dir = repo_root / "output" / "current"
    current_dir.mkdir(parents=True, exist_ok=True)
    index_exporter.export_model_releases_index(str(archive_root), str(current_dir / "model-releases.html"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    backfill(start, end, overwrite=args.overwrite)
