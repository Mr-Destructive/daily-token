"""Export newspaper in multiple formats."""
import html
import json
import os
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from meta_ai_api_tool_call import MetaAI
    HAS_META_AI = True
except ImportError:
    HAS_META_AI = False

try:
    from config import PAGE_CATEGORIES, PAGES_CONFIG
except ImportError:
    PAGE_CATEGORIES = {
        1: "Breaking Vectors",
        2: "Model Architectures",
        3: "Neural Horizons",
        4: "Lab Outputs",
        5: "Inference Corner",
        6: "AI & LLM Overview",
        7: "Model Release History",
        8: "Top Insights & Advice",
        9: "Lab Updates & Dark Side",
        10: "Benchmarks & Claims Audit",
        11: "Infra & Cost Watch",
        12: "Policy & Safety Moves",
        13: "Corrections & Revisions",
    }
    PAGES_CONFIG = {
        1: {"title": "The Front Page", "categories": [1, 2, 3, 4, 5]},
        2: {"title": "AI & LLM Overview", "categories": [6, 10]},
        3: {"title": "Model Release History", "categories": [7]},
        4: {"title": "Top Insights & Advice", "categories": [8, 11]},
        5: {"title": "Lab Updates & Dark Side", "categories": [9, 12, 13]},
    }


def _site_url() -> str:
    try:
        from config import SITE_URL
        return SITE_URL
    except ImportError:
        return os.environ.get("SITE_URL", "https://daily-tokens.netlify.app")


def _is_http_url(value: Optional[str]) -> bool:
    if not value:
        return False
    v = str(value).strip()
    return v.startswith("http://") or v.startswith("https://")


def _safe_url(value: Optional[str], fallback: str = "#") -> str:
    return value.strip() if _is_http_url(value) else fallback


def _get_llm_location_from_vibes(stories_summary: str) -> str:
    """Get LLM world location based on newspaper vibes using Meta AI."""
    available_locations = [
        "TENSOR CITY",
        "GRADIENT VALLEY",
        "MODEL SQUARE",
        "PROMPT BAY",
        "VECTOR STATION",
        "ATTENTION HEIGHTS",
        "TRANSFORMER TOWER",
        "NEURAL NEXUS",
        "EMBEDDING ESTATES",
        "INFERENCE ISLAND",
    ]

    if not HAS_META_AI:
        return random.choice(available_locations)

    try:
        meta_ai = MetaAI()
        prompt = (
            "Which of these LLM-themed cities best captures the vibe of today's news: "
            f"{', '.join(available_locations)}? News: {stories_summary}. "
            "Respond with ONLY the city name."
        )
        response = meta_ai.prompt(message=prompt)
        location = response.strip().upper()
        return location if location in available_locations else random.choice(available_locations)
    except Exception:
        return random.choice(available_locations)


class NewsExporter:
    """Export processed news to various formats."""

    PAGE_NAMES = PAGE_CATEGORIES

    def __init__(
        self,
        organized_stories: Dict[int, List[Dict]],
        location: str = None,
        timestamp: str = None,
        model_releases: Optional[List[Dict]] = None,
        archive_root: Optional[Path] = None,
    ):
        self.organized = organized_stories
        self.timestamp = timestamp if timestamp else datetime.now().isoformat()
        self.location = location if location else self._determine_location()
        self.editorial: Dict = {}
        self.top_candidates: List[Dict] = []
        self.model_releases: List[Dict] = model_releases or []
        self.archive_root = Path(archive_root) if archive_root else None

    def _determine_location(self) -> str:
        if not self.organized:
            return "THE CLOUD"
        headlines = []
        for cat in sorted(PAGE_CATEGORIES.keys()):
            for story in (self.organized.get(cat, []) or self.organized.get(str(cat), []))[:2]:
                headlines.append(story.get("generated_headline", ""))
        return _get_llm_location_from_vibes(" | ".join(headlines[:10]))

    def _edition_link(self, day: datetime, base_rel: str, label: str) -> str:
        rel = f"archive/{day.strftime('%Y/%m/%d')}/newspaper.html"
        href = f"{base_rel}{rel}"
        if self.archive_root and (self.archive_root / day.strftime("%Y/%m/%d") / "newspaper.html").exists():
            return f'<a href="{href}" class="edition-link">{label}</a>'
        return f'<span class="edition-link disabled" aria-disabled="true">{label}</span>'

    def _list_archive_dates(self) -> List[datetime]:
        if not self.archive_root or not self.archive_root.exists():
            return []
        dates: List[datetime] = []
        for year_dir in self.archive_root.iterdir():
            if not year_dir.is_dir() or not year_dir.name.isdigit():
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir() or not month_dir.name.isdigit():
                    continue
                for day_dir in month_dir.iterdir():
                    if (
                        day_dir.is_dir()
                        and day_dir.name.isdigit()
                        and (day_dir / "newspaper.html").exists()
                    ):
                        try:
                            dates.append(
                                datetime(
                                    int(year_dir.name),
                                    int(month_dir.name),
                                    int(day_dir.name),
                                )
                            )
                        except Exception:
                            pass
        dates.sort()
        return dates

    def _adjacent_edition_days(self, current_day: datetime) -> tuple[Optional[datetime], Optional[datetime]]:
        dates = self._list_archive_dates()
        if not dates:
            return None, None
        current_date = current_day.date()
        prev_day = None
        next_day = None
        for d in dates:
            if d.date() < current_date:
                prev_day = d
            elif d.date() > current_date:
                next_day = d
                break
        return prev_day, next_day

    def _render_source_line(self, story: Dict, article_url: str) -> str:
        source_name = html.escape(str(story.get("source", "Source")).upper())
        source_link = article_url if _is_http_url(article_url) else "#"
        source_html = (
            f'SOURCE: <a href="{source_link}" target="_blank" rel="noopener" class="source-link">{source_name}</a>'
            if source_link != "#"
            else f"SOURCE: {source_name}"
        )

        hn_url = _safe_url(story.get("hn_url"), "")
        if hn_url:
            return f'{source_html} | <a href="{hn_url}" target="_blank" rel="noopener" class="hn-link">HN DISCUSSION</a>'
        return source_html

    def _render_article(self, story: Dict, layout_class: str, headline_class: str, image_prefix: str) -> str:
        headline = html.escape(story.get("generated_headline", story.get("original_title", "Untitled")))
        summary = html.escape(story.get("summary", ""))
        img_path = story.get("generated_image_path", "")
        final_img_src = f"{image_prefix}{os.path.basename(img_path)}" if img_path else ""

        url = _safe_url(story.get("url"), _safe_url(story.get("hn_url"), "#"))
        image_html = (
            f'<a href="{url}" target="_blank" rel="noopener"><img src="{final_img_src}" class="news-img" alt=""></a>'
            if final_img_src
            else ""
        )

        metadata = self._render_source_line(story, url)
        return (
            f'<article class="article {layout_class}">'
            f'<div class="article-body">{image_html}'
            f'<h3 class="{headline_class}"><a href="{url}" target="_blank" rel="noopener">{headline}</a></h3>'
            f'<div class="metadata">{metadata}</div>'
            f'<p class="summary-sm">{summary}</p>'
            f"</div></article>"
        )

    def _render_release_cards(self) -> str:
        if not self.model_releases:
            return '<p class="empty-note">No confirmed model releases were detected for this edition date.</p>'

        cards = []
        for release in self.model_releases:
            model = html.escape(release.get("model_name") or release.get("title") or "Unnamed model")
            provider = html.escape(release.get("provider", "Unknown"))
            kind = html.escape(release.get("release_type", "Release"))
            desc = html.escape(release.get("summary", "")).strip()
            source_url = _safe_url(release.get("source_url"), "#")
            hn_url = _safe_url(release.get("hn_url"), "")

            links = [f'<a href="{source_url}" target="_blank" rel="noopener">Official / Blog</a>' if source_url != "#" else ""]
            if hn_url:
                links.append(f'<a href="{hn_url}" target="_blank" rel="noopener">HN Thread</a>')

            cards.append(
                "<article class='release-card'>"
                f"<div class='release-kicker'>{provider} | {kind}</div>"
                f"<h3>{model}</h3>"
                f"<p>{desc}</p>"
                f"<div class='release-links'>{' | '.join([l for l in links if l])}</div>"
                "</article>"
            )
        return "".join(cards)

    def export_json(self, output_path: str) -> str:
        data = {
            "metadata": {
                "generated": self.timestamp,
                "format_version": "1.2",
                "location": self.location,
                "editorial": self.editorial,
                "top_candidates": self.top_candidates,
                "model_releases": self.model_releases,
            },
            "pages": {
                str(page_id): {
                    "title": self.PAGE_NAMES.get(int(page_id), "Page"),
                    "stories": stories,
                }
                for page_id, stories in self.organized.items()
            },
        }
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        return output_path

    def export_model_releases_json(self, output_path: str) -> str:
        payload = {
            "generated": self.timestamp,
            "count": len(self.model_releases),
            "releases": self.model_releases,
        }
        with open(output_path, "w") as f:
            json.dump(payload, f, indent=2)
        return output_path

    def export_model_releases_html(self, output_path: str, base_rel: str = "") -> str:
        date_label = datetime.fromisoformat(self.timestamp).strftime("%B %d, %Y")
        rows = []
        for r in self.model_releases:
            model = html.escape(r.get("model_name") or r.get("title") or "-")
            provider = html.escape(r.get("provider", "-"))
            release_type = html.escape(r.get("release_type", "Release"))
            source = _safe_url(r.get("source_url"), "")
            hn = _safe_url(r.get("hn_url"), "")
            published = html.escape(str(r.get("published", "-")))
            row_links = []
            if source:
                row_links.append(f'<a href="{source}" target="_blank" rel="noopener">Official</a>')
            if hn:
                row_links.append(f'<a href="{hn}" target="_blank" rel="noopener">HN</a>')
            rows.append(
                f"<tr><td>{model}</td><td>{provider}</td><td>{release_type}</td><td>{published}</td>"
                f"<td>{' | '.join(row_links) if row_links else '-'}</td></tr>"
            )

        if not rows:
            rows.append("<tr><td colspan='5'>No confirmed model releases detected for this date.</td></tr>")

        html_doc = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Model Releases | The Daily Token</title>
  <link href=\"https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@400;600;700&family=Oswald:wght@500;700&display=swap\" rel=\"stylesheet\">
  <style>
    body {{ margin:0; background:#f7f3eb; color:#1d1a16; font-family:'Source Serif 4',serif; }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:28px; }}
    h1 {{ font-family:'Playfair Display',serif; font-size:3rem; margin:0; }}
    .k {{ font-family:'Oswald',sans-serif; letter-spacing:.06em; text-transform:uppercase; color:#7a2b1f; }}
    table {{ width:100%; border-collapse:collapse; background:#fffdf8; margin-top:18px; }}
    th,td {{ border:1px solid #d7cdc0; padding:10px; text-align:left; }}
    th {{ font-family:'Oswald',sans-serif; letter-spacing:.04em; background:#f0e6d6; }}
    a {{ color:#7a2b1f; text-decoration:none; font-weight:700; }}
  </style>
</head>
<body>
<div class=\"wrap\">
  <a href=\"{base_rel}newspaper.html\">Back to newspaper</a>
  <div class=\"k\">Model Release Desk</div>
  <h1>Daily Model Releases</h1>
  <p>Edition date: {date_label}</p>
  <table>
    <thead><tr><th>Model</th><th>Provider</th><th>Type</th><th>Published</th><th>Links</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>
</body>
</html>"""
        with open(output_path, "w") as f:
            f.write(html_doc)
        return output_path

    def export_html(self, output_path: str, image_prefix: str = "images/") -> str:
        html_content = self._generate_html(image_prefix=image_prefix)
        with open(output_path, "w") as f:
            f.write(html_content)
        return output_path

    @staticmethod
    def reconstruct_from_json(json_path: str, output_html_path: str, image_prefix: str = "images/"):
        with open(json_path, "r") as f:
            data = json.load(f)
        organized = {int(k): v["stories"] for k, v in data.get("pages", {}).items()}
        gen_ts = data.get("metadata", {}).get("generated")
        exporter = NewsExporter(
            organized,
            location=data.get("metadata", {}).get("location"),
            timestamp=gen_ts,
            model_releases=data.get("metadata", {}).get("model_releases", []),
        )
        exporter.editorial = data.get("metadata", {}).get("editorial", {})
        exporter.top_candidates = data.get("metadata", {}).get("top_candidates", [])
        exporter.export_html(output_html_path, image_prefix=image_prefix)
        return output_html_path

    def export_archive_index(self, archive_root: str, output_path: str) -> str:
        root_path = Path(archive_root)
        if not root_path.exists():
            return ""

        archive_data: Dict[str, Dict[str, List[str]]] = {}
        years = sorted([d for d in root_path.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
        for year_dir in years:
            year = year_dir.name
            archive_data[year] = {}
            months = sorted([d for d in year_dir.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
            for month_dir in months:
                month = month_dir.name
                days = sorted([d.name for d in month_dir.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
                archive_data[year][month] = days

        lines: List[str] = []
        for year, months in archive_data.items():
            lines.append('<div class="archive-year" style="margin-bottom:40px;">')
            lines.append(f'<h2 style="font-family:\'Oswald\'; border-bottom:4px solid #111; padding-bottom:10px;">{year}</h2>')
            for month, days in months.items():
                month_name = datetime.strptime(month, "%m").strftime("%B").upper()
                lines.append('<div class="archive-month" style="margin-left:20px; margin-bottom:20px;">')
                lines.append(f'<h3 style="font-family:\'Oswald\'; color:#7a2b1f;">{month_name}</h3>')
                lines.append('<ul style="list-style:none; padding:0; display:grid; grid-template-columns:repeat(auto-fill, minmax(120px, 1fr)); gap:10px;">')
                for day in days:
                    display_date = f"{month_name[:3]} {day}"
                    lines.append(
                        f'<li><a href="{year}/{month}/{day}/newspaper.html" '
                        'style="text-decoration:none; color:#111; border:1px solid #ccc; padding:8px; display:block; text-align:center; font-family:\'Oswald\'; font-size:0.8rem;">'
                        f"{display_date}</a></li>"
                    )
                lines.append("</ul></div>")
            lines.append("</div>")

        full_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Historical Archives | The Daily Token</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Source+Serif+4:wght@400;700&display=swap\" rel=\"stylesheet\">
    <style>
        body {{ background-color: #fdfdfb; font-family: 'Source Serif 4', serif; padding: 40px; max-width: 900px; margin: 0 auto; }}
        a:hover {{ background: #111; color: #fff !important; border-color: #111 !important; }}
    </style>
</head>
<body>
    <a href=\"../index.html\" style=\"display:block; margin-bottom:40px; text-decoration:none; color:#7a2b1f; font-family:'Oswald'; font-weight:700; letter-spacing:1px;\">← BACK TO LATEST EDITION</a>
    <h1 style=\"font-family:'Oswald'; font-size:3rem; text-transform:uppercase; text-align:center; margin-bottom:60px; border-bottom:8px double #111; padding-bottom:20px;\">The Daily Token Archives</h1>
    {''.join(lines)}
</body>
</html>"""
        with open(output_path, "w") as f:
            f.write(full_html)
        return output_path

    def export_model_releases_index(self, archive_root: str, output_path: str) -> str:
        """Build an archive-wide model release ledger from dated archive files."""
        root_path = Path(archive_root)
        rows: List[Dict] = []

        if root_path.exists():
            year_dirs = sorted([d for d in root_path.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
            for year_dir in year_dirs:
                month_dirs = sorted([d for d in year_dir.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
                for month_dir in month_dirs:
                    day_dirs = sorted([d for d in month_dir.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
                    for day_dir in day_dirs:
                        rel_path = day_dir / "model_releases.json"
                        if not rel_path.exists():
                            continue
                        try:
                            with open(rel_path, "r") as f:
                                payload = json.load(f)
                            for rel in payload.get("releases", []):
                                entry = dict(rel)
                                entry["edition_date"] = f"{year_dir.name}-{month_dir.name}-{day_dir.name}"
                                rows.append(entry)
                        except Exception:
                            continue

        rows.sort(
            key=lambda r: (
                str(r.get("edition_date", "")),
                str(r.get("provider", "")),
                str(r.get("model_name", "")),
            ),
            reverse=True,
        )

        table_rows: List[str] = []
        for rel in rows:
            edition_date = html.escape(str(rel.get("edition_date", "-")))
            model = html.escape(rel.get("model_name") or rel.get("title") or "-")
            provider = html.escape(str(rel.get("provider", "-")))
            rel_type = html.escape(str(rel.get("release_type", "Release")))
            source = _safe_url(rel.get("source_url"), "")
            hn = _safe_url(rel.get("hn_url"), "")
            edition_link = (
                f'archive/{edition_date[:4]}/{edition_date[5:7]}/{edition_date[8:10]}/newspaper.html'
                if len(edition_date) >= 10
                else "archive/index.html"
            )
            links = [f'<a href="{edition_link}">Edition</a>']
            if source:
                links.append(f'<a href="{source}" target="_blank" rel="noopener">Official</a>')
            if hn:
                links.append(f'<a href="{hn}" target="_blank" rel="noopener">HN</a>')
            table_rows.append(
                f"<tr><td>{edition_date}</td><td>{model}</td><td>{provider}</td><td>{rel_type}</td>"
                f"<td>{' | '.join(links)}</td></tr>"
            )

        if not table_rows:
            table_rows.append("<tr><td colspan='5'>No model releases found in archive yet.</td></tr>")

        full_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Model Release Ledger | The Daily Token</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@400;600;700&family=Oswald:wght@500;700&display=swap\" rel=\"stylesheet\">
    <style>
        body {{ margin:0; background:#f7f3eb; color:#1d1a16; font-family:'Source Serif 4',serif; }}
        .wrap {{ max-width:1200px; margin:0 auto; padding:28px; }}
        h1 {{ font-family:'Playfair Display',serif; font-size:2.8rem; margin:0; }}
        .k {{ font-family:'Oswald',sans-serif; letter-spacing:.06em; text-transform:uppercase; color:#7a2b1f; }}
        table {{ width:100%; border-collapse:collapse; background:#fffdf8; margin-top:18px; }}
        th,td {{ border:1px solid #d7cdc0; padding:10px; text-align:left; vertical-align:top; }}
        th {{ font-family:'Oswald',sans-serif; letter-spacing:.04em; background:#f0e6d6; }}
        a {{ color:#7a2b1f; text-decoration:none; font-weight:700; }}
    </style>
</head>
<body>
<div class=\"wrap\">
    <a href=\"index.html\">Back to front page</a>
    <div class=\"k\">Model Release Desk</div>
    <h1>Archive Model Release Ledger</h1>
    <p>Total entries: {len(rows)}</p>
    <table>
        <thead><tr><th>Edition Date</th><th>Model</th><th>Provider</th><th>Type</th><th>Links</th></tr></thead>
        <tbody>{''.join(table_rows)}</tbody>
    </table>
</div>
</body>
</html>"""
        with open(output_path, "w") as f:
            f.write(full_html)
        return output_path

    def _generate_html(self, image_prefix: str = "images/") -> str:
        is_archive = "../" in image_prefix
        base_rel = "../../../../" if is_archive else ""

        nav_links = "".join(
            [
                f'<a href="javascript:void(0)" onclick="goToPage({p})" class="nav-item" id="nav-{p}">{PAGES_CONFIG[p]["title"].upper()}</a>'
                for p in sorted(PAGES_CONFIG.keys())
            ]
        )

        pages_html = ""
        for page_num in sorted(PAGES_CONFIG.keys()):
            config = PAGES_CONFIG[page_num]
            is_first = page_num == 1
            pages_html += f'<div id="page-content-{page_num}" class="newspaper-page" style="display: {"block" if is_first else "none"}">'
            pages_html += f'<div class="page-title"><span>{config["title"].upper()}</span></div>'

            if is_first:
                if self.editorial.get("editors_note"):
                    note = html.escape(self.editorial["editors_note"])
                    emphasis = html.escape(self.editorial.get("emphasis", "Judgment and craft"))
                    pages_html += f"<div class='editors-note'><strong>EDITOR'S NOTE:</strong> {note} <span class='emphasis'>#{emphasis}</span></div>"

                for cat_id in config["categories"]:
                    stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                    if not stories:
                        continue
                    pages_html += f'<div class="section-sub-header"><span>{PAGE_CATEGORIES[cat_id].upper()}</span></div><div class="columns-3">'
                    for story in stories[:3]:
                        pages_html += self._render_article(story, "span-1", "headline-sm", image_prefix)
                    pages_html += "</div>"

            elif page_num == 3:
                pages_html += '<div class="section-sub-header"><span>DAILY MODEL RELEASE LEDGER</span></div>'
                pages_html += f'<div class="release-grid">{self._render_release_cards()}</div>'

                cat_id = config["categories"][0]
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                if stories:
                    pages_html += '<div class="section-sub-header"><span>RELATED COVERAGE</span></div><div class="columns-3">'
                    for story in stories[:6]:
                        pages_html += self._render_article(story, "span-1", "headline-sm", image_prefix)
                    pages_html += "</div>"

                pages_html += f'<div class="model-ledger-link"><a href="{base_rel}model-releases.html">OPEN FULL MODEL RELEASE PAGE →</a></div>'

            elif page_num == 4:
                cat_id = config["categories"][0]
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                pages_html += '<div class="insights-grid">'
                for story in stories:
                    hn_url = _safe_url(story.get("hn_url"), "#")
                    headline = html.escape(story.get("generated_headline", "Community insight"))
                    summary = html.escape(story.get("summary", ""))
                    author = html.escape(story.get("source_author", "The Community"))
                    pages_html += (
                        '<div class="insight-card">'
                        f'<div class="insight-author">PERSPECTIVE: {author}</div>'
                        f'<h3 class="insight-headline">{headline}</h3>'
                        f'<p class="insight-summary">"{summary}"</p>'
                        f'<div class="insight-footer"><a href="{hn_url}" target="_blank" rel="noopener">READ FULL DISCUSSION →</a></div>'
                        "</div>"
                    )
                pages_html += "</div>"
            else:
                cat_id = config["categories"][0]
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                pages_html += '<div class="columns-3">'
                for story in stories:
                    pages_html += self._render_article(story, "span-1", "headline-sm", image_prefix)
                pages_html += "</div>"

            prev_btn = f'<a href="javascript:void(0)" onclick="goToPage({page_num - 1})" class="nav-btn">← PREVIOUS</a>' if page_num > 1 else "<span></span>"
            next_btn = f'<a href="javascript:void(0)" onclick="goToPage({page_num + 1})" class="nav-btn">NEXT →</a>' if page_num < 5 else "<span></span>"
            pages_html += f'<div class="page-footer-nav">{prev_btn}{next_btn}</div></div>'

        dt = datetime.fromisoformat(self.timestamp)
        prev_day, next_day = self._adjacent_edition_days(dt)
        if prev_day is None:
            prev_link = '<span class="edition-link disabled" aria-disabled="true">← PREVIOUS EDITION</span>'
        else:
            prev_link = self._edition_link(prev_day, base_rel, "← PREVIOUS EDITION")
        if next_day is None:
            next_link = '<span class="edition-link disabled" aria-disabled="true">NEXT EDITION →</span>'
        else:
            next_link = self._edition_link(next_day, base_rel, "NEXT EDITION →")

        return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>The Daily Token</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@400;600;700&family=Oswald:wght@500;700&display=swap\" rel=\"stylesheet\">
    <style>
        :root {{ --ink:#181512; --paper:#f8f3ea; --sep:#c4b8a4; --highlight:#7a2b1f; --muted:#756b5e; --box:#fffaf0; }}
        * {{ box-sizing:border-box; }}
        body {{ background:#c8c1b5; margin:0; font-family:'Source Serif 4',serif; color:var(--ink); line-height:1.35; }}
        .newspaper-container {{ background:var(--paper); max-width:1280px; margin:0 auto; padding:32px; box-shadow:0 18px 80px rgba(0,0,0,.22); min-height:100vh; transition:opacity .22s ease; }}
        .page-turn-out {{ opacity:0; }}
        header {{ text-align:center; border-bottom:6px double var(--ink); padding-bottom:18px; }}
        .masthead-title {{ font-family:'Playfair Display',serif; font-weight:900; font-size:5.4rem; letter-spacing:-2px; margin:0; text-transform:uppercase; }}
        .sub-masthead {{ border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); margin-top:12px; padding:6px 0; font-family:'Oswald',sans-serif; text-transform:uppercase; font-size:.86rem; display:flex; justify-content:center; gap:28px; flex-wrap:wrap; }}
        nav.sticky-nav {{ position:sticky; top:0; background:var(--paper); z-index:100; text-align:center; padding:12px 0; border-bottom:1px solid var(--ink); margin-bottom:30px; }}
        .nav-item {{ text-decoration:none; color:var(--ink); font-family:'Oswald',sans-serif; font-size:.82rem; margin:0 10px; border-bottom:2px solid transparent; }}
        .nav-item.active {{ color:var(--highlight); border-color:var(--highlight); }}
        .page-title {{ text-align:center; border-bottom:3px solid var(--ink); line-height:.1em; margin:40px 0 26px; font-family:'Oswald',sans-serif; font-size:1.32rem; }}
        .page-title span {{ background:var(--paper); padding:0 22px; }}
        .section-sub-header {{ text-align:left; border-bottom:1px solid var(--sep); line-height:.1em; margin:28px 0 18px; font-family:'Oswald',sans-serif; font-size:.86rem; color:var(--highlight); letter-spacing:.06em; }}
        .section-sub-header span {{ background:var(--paper); padding-right:12px; }}
        .columns-3 {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:26px; margin-bottom:24px; }}
        .headline-sm {{ font-family:'Playfair Display',serif; font-size:1.42rem; line-height:1.14; margin:0 0 10px; }}
        .article a {{ color:inherit; text-decoration:none; }}
        .article a:hover {{ color:var(--highlight); }}
        .metadata {{ font-family:'Oswald',sans-serif; font-size:.72rem; color:var(--muted); margin-bottom:10px; letter-spacing:.04em; text-transform:uppercase; }}
        .metadata .source-link, .hn-link {{ color:var(--highlight); font-weight:700; }}
        .summary-sm {{ margin:0; font-size:.98rem; }}
        .news-img {{ width:100%; display:block; margin-bottom:14px; filter:grayscale(100%); border:1px solid #d7c9b2; transition:.25s; box-shadow:4px 4px 0 rgba(0,0,0,.05); }}
        .news-img:hover {{ filter:none; transform:translateY(-1px); }}
        .page-footer-nav {{ display:flex; justify-content:space-between; align-items:center; margin-top:36px; padding-top:14px; border-top:1px solid var(--ink); }}
        .nav-btn {{ font-family:'Oswald',sans-serif; color:var(--ink); text-decoration:none; border:1px solid var(--ink); padding:8px 14px; font-size:.82rem; }}
        .nav-btn:hover {{ background:var(--ink); color:#fff; }}
        .edition-nav {{ display:flex; justify-content:center; align-items:center; gap:20px; background:#e9e1d3; padding:10px; font-family:'Oswald',sans-serif; font-size:.78rem; border-bottom:1px solid #cdbfa8; flex-wrap:wrap; }}
        .edition-link {{ color:#574f46; text-decoration:none; }}
        .edition-link.disabled {{ color:#a69e93; }}
        .editors-note {{ margin-bottom:20px; padding:16px; border:1px solid #d6c8b0; font-style:italic; background:var(--box); border-left:4px solid var(--highlight); }}
        .editors-note .emphasis {{ color:var(--highlight); font-weight:700; }}
        .insights-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:20px; }}
        .insight-card {{ padding:18px; border:1px solid #ded1bb; background:var(--box); }}
        .insight-author {{ font-family:'Oswald',sans-serif; font-size:.68rem; color:var(--highlight); margin-bottom:8px; border-bottom:1px solid #e3d8c7; padding-bottom:4px; text-transform:uppercase; }}
        .insight-headline {{ font-family:'Playfair Display',serif; font-size:1.34rem; margin:0 0 10px; }}
        .insight-summary {{ margin:0; }}
        .insight-footer {{ margin-top:12px; font-family:'Oswald',sans-serif; font-size:.78rem; }}
        .release-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }}
        .release-card {{ border:1px solid #ded1bb; background:var(--box); padding:14px; }}
        .release-kicker {{ font-family:'Oswald',sans-serif; font-size:.68rem; letter-spacing:.08em; color:var(--highlight); text-transform:uppercase; }}
        .release-card h3 {{ font-family:'Playfair Display',serif; margin:6px 0 8px; }}
        .release-card p {{ margin:0; font-size:.95rem; }}
        .release-links {{ margin-top:10px; font-family:'Oswald',sans-serif; font-size:.75rem; }}
        .model-ledger-link {{ margin-top:14px; text-align:right; font-family:'Oswald',sans-serif; font-size:.84rem; }}
        .model-ledger-link a {{ color:var(--highlight); text-decoration:none; }}
        .empty-note {{ border:1px dashed #cab99f; padding:14px; background:#fff8ea; }}
        @media (max-width:1000px) {{
            .masthead-title {{ font-size:3rem; }}
            .columns-3, .insights-grid, .release-grid {{ grid-template-columns:1fr; }}
        }}
    </style>
</head>
<body>
    <div class=\"edition-nav\">
        {prev_link}
        <span style=\"font-weight:700; color:#111;\">EDITION: {dt.strftime('%b %d, %Y').upper()}</span>
        {next_link}
        <span style=\"color:#9b8f82\">|</span>
        <a href=\"{base_rel}archive/index.html\" class=\"edition-link\">FULL ARCHIVES</a>
        <span style=\"color:#9b8f82\">|</span>
        <a href=\"{base_rel}model-releases.html\" class=\"edition-link\">MODEL RELEASES</a>
    </div>
    <div class=\"newspaper-container\" id=\"newspaper-main\">
        <header>
            <h1 class=\"masthead-title\">The Daily Token</h1>
            <div class=\"sub-masthead\">
                <span>{self.location}</span>
                <span>{dt.strftime('%A, %B %d, %Y').upper()}</span>
                <span>GLOBAL AI TECHNOLOGY REPORT</span>
                <span>VOL. {dt.strftime('%Y')}.{dt.strftime('%j')}</span>
            </div>
        </header>
        <nav class=\"sticky-nav\">{nav_links}</nav>
        <main id=\"pages-wrapper\">{pages_html}</main>
        <footer style=\"text-align:center; padding:40px 0; font-family:'Oswald',sans-serif; border-top:4px double var(--ink); margin-top:70px;\">THE DAILY TOKEN // REPORTING IN PUBLIC // &copy; 2026</footer>
    </div>
    <script>
        let currentPage = 1;
        function goToPage(pageNum) {{
            if (pageNum < 1 || pageNum > 5 || pageNum === currentPage) return;
            const container = document.getElementById('newspaper-main');
            container.classList.add('page-turn-out');
            setTimeout(() => {{
                document.querySelectorAll('.newspaper-page').forEach(p => p.style.display = 'none');
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                document.getElementById(`page-content-${{pageNum}}`).style.display = 'block';
                document.getElementById(`nav-${{pageNum}}`).classList.add('active');
                currentPage = pageNum;
                window.scrollTo(0, 0);
                const url = new URL(window.location);
                url.searchParams.set('page', pageNum);
                window.history.pushState({{}}, '', url);
                container.classList.remove('page-turn-out');
            }}, 220);
        }}
        window.addEventListener('load', () => {{
            const params = new URLSearchParams(window.location.search);
            const page = parseInt(params.get('page'));
            if (page >= 1 && page <= 5) goToPage(page);
            else document.getElementById('nav-1').classList.add('active');
        }});
    </script>
</body>
</html>
"""

    def export_markdown(self, output_path: str) -> str:
        dt = datetime.fromisoformat(self.timestamp)
        lines = [
            "# The Daily Token",
            "",
            f"Edition: {dt.strftime('%Y-%m-%d')}",
            "",
        ]
        if self.editorial.get("editors_note"):
            lines.extend(["## Editor's Note", self.editorial["editors_note"], ""])

        for page_num in sorted(PAGES_CONFIG.keys()):
            page_title = PAGES_CONFIG[page_num]["title"]
            lines.extend([f"## {page_title}", ""])
            for cat_id in PAGES_CONFIG[page_num]["categories"]:
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                for story in stories:
                    headline = story.get("generated_headline", story.get("original_title", "Untitled"))
                    url = story.get("url") or story.get("hn_url", "")
                    lines.append(f"### {headline}")
                    if _is_http_url(url):
                        lines.append(f"Source: {url}")
                    if _is_http_url(story.get("hn_url")):
                        lines.append(f"HN: {story['hn_url']}")
                    lines.append(story.get("summary", ""))
                    lines.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(lines))
        return output_path

    def export_text(self, output_path: str) -> str:
        dt = datetime.fromisoformat(self.timestamp)
        lines = [
            "THE DAILY TOKEN",
            f"Edition: {dt.strftime('%Y-%m-%d')}",
            "=" * 48,
            "",
        ]

        if self.editorial.get("editors_note"):
            lines.extend([f"EDITOR'S NOTE: {self.editorial['editors_note']}", ""])

        for page_num in sorted(PAGES_CONFIG.keys()):
            lines.extend([PAGES_CONFIG[page_num]["title"].upper(), "-" * 48])
            for cat_id in PAGES_CONFIG[page_num]["categories"]:
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                for story in stories:
                    headline = story.get("generated_headline", story.get("original_title", "Untitled"))
                    url = story.get("url") or story.get("hn_url", "")
                    lines.append(f"* {headline}")
                    if _is_http_url(url):
                        lines.append(f"  {url}")
                    lines.append(f"  {story.get('summary', '')}")
                    lines.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(lines))
        return output_path

    def export_rss_feed(self, output_path: str) -> str:
        root = ET.Element("rss")
        root.set("version", "2.0")
        root.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")

        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = "The Daily Token"
        ET.SubElement(channel, "link").text = _site_url()
        ET.SubElement(channel, "description").text = "The AI world's daily news."
        ET.SubElement(channel, "pubDate").text = self.timestamp

        for page_num in sorted(PAGES_CONFIG.keys()):
            for cat_id in PAGES_CONFIG[page_num]["categories"]:
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                for story in stories:
                    item = ET.SubElement(channel, "item")
                    ET.SubElement(item, "title").text = story.get("generated_headline", story.get("original_title", ""))
                    ET.SubElement(item, "link").text = story.get("url") or story.get("hn_url", "")
                    ET.SubElement(item, "description").text = story.get("summary", "")

        ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
        return output_path
