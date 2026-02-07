"""Export newspaper in multiple formats"""
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

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
        6: "AI Industry Overview",
        7: "Model Release History",
        8: "Top Insights & Advice",
        9: "AI Safety & Lab Accidents"
    }
    PAGES_CONFIG = {
        1: {"title": "The Front Page", "categories": [1, 2, 3, 4, 5]},
        2: {"title": "AI Industry Overview", "categories": [6]},
        3: {"title": "Model Release History", "categories": [7]},
        4: {"title": "Top Insights & Advice", "categories": [8]},
        5: {"title": "AI Safety & Lab Accidents", "categories": [9]}
    }

def _site_url():
    try:
        from config import SITE_URL
        return SITE_URL
    except ImportError:
        return os.environ.get("SITE_URL", "https://daily-tokens.netlify.app")


def _get_llm_location_from_vibes(stories_summary: str) -> str:
    """Get LLM world location based on newspaper vibes using Meta AI"""
    available_locations = ["TENSOR CITY", "GRADIENT VALLEY", "MODEL SQUARE", "PROMPT BAY", "VECTOR STATION", "ATTENTION HEIGHTS", "TRANSFORMER TOWER", "NEURAL NEXUS", "EMBEDDING ESTATES", "INFERENCE ISLAND"]
    if not HAS_META_AI: return random.choice(available_locations)
    try:
        meta_ai = MetaAI()
        prompt = f"Which of these LLM-themed cities best captures the vibe of today's news: {', '.join(available_locations)}? News: {stories_summary}. Respond with ONLY the city name."
        response = meta_ai.prompt(message=prompt)
        location = response.strip().upper()
        return location if location in available_locations else random.choice(available_locations)
    except: return random.choice(available_locations)


class NewsExporter:
    """Export processed news to various formats"""
    
    PAGE_NAMES = PAGE_CATEGORIES
    
    def __init__(self, organized_stories: Dict[int, List[Dict]], location: str = None, timestamp: str = None):
        self.organized = organized_stories
        self.timestamp = timestamp if timestamp else datetime.now().isoformat()
        self.location = location if location else self._determine_location()
        self.editorial = {}
        self.top_candidates = []
    
    def _determine_location(self) -> str:
        if not self.organized: return "THE CLOUD"
        headlines = []
        for cat in range(1, 10):
            for story in (self.organized.get(cat, []) or self.organized.get(str(cat), []))[:2]:
                headlines.append(story.get('generated_headline', ''))
        return _get_llm_location_from_vibes(" | ".join(headlines[:10]))
    
    def _render_article(self, story: Dict, layout_class: str, headline_class: str, image_prefix: str) -> str:
        """Helper to render a standard article block linking directly to source"""
        headline = story.get('generated_headline', story['original_title'])
        summary = story['summary']
        img_path = story.get('generated_image_path', '')
        final_img_src = f"{image_prefix}{os.path.basename(img_path)}" if img_path else ""
        url = story.get('url') or story.get('hn_url', '#')
        hn_url = story.get('hn_url', '#')
        
        # Link images and headlines directly to original article
        image_html = f'<a href="{url}" target="_blank"><img src="{final_img_src}" class="news-img" alt=""></a>' if final_img_src else ""
        
        return f'''
            <article class="article {layout_class}">
                <div class="article-body">
                    {image_html}
                    <h3 class="{headline_class}"><a href="{url}" target="_blank">{headline}</a></h3>
                    <div class="metadata">SOURCE: {story["source"].upper()} | <a href="{hn_url}" target="_blank" class="hn-link">DISCUSS ON HN</a></div>
                    <p class="summary-sm">{summary}</p>
                </div>
            </article>
        '''

    def export_json(self, output_path: str) -> str:
        data = {
            'metadata': {
                'generated': self.timestamp,
                'format_version': '1.1',
                'location': self.location,
                'editorial': self.editorial,
                'top_candidates': self.top_candidates
            },
            'pages': {str(page_id): {'title': self.PAGE_NAMES.get(int(page_id), 'Page'), 'stories': stories} for page_id, stories in self.organized.items()}
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        return output_path

    def export_html(self, output_path: str, image_prefix: str = "images/") -> str:
        html_content = self._generate_html(image_prefix=image_prefix)
        with open(output_path, 'w') as f:
            f.write(html_content)
        return output_path

    @staticmethod
    def reconstruct_from_json(json_path: str, output_html_path: str, image_prefix: str = "images/"):
        with open(json_path, 'r') as f:
            data = json.load(f)
        organized = {int(k): v['stories'] for k, v in data['pages'].items()}
        gen_ts = data['metadata'].get('generated')
        exporter = NewsExporter(organized, location=data['metadata'].get('location'), timestamp=gen_ts)
        exporter.editorial = data['metadata'].get('editorial', {})
        exporter.top_candidates = data['metadata'].get('top_candidates', [])
        exporter.export_html(output_html_path, image_prefix=image_prefix)
        return output_html_path

    def export_archive_index(self, archive_root: str, output_path: str) -> str:
        root_path = Path(archive_root)
        if not root_path.exists(): return ""
        archive_data = {}
        # Scan year/month/day
        years = sorted([d for d in root_path.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
        for year_dir in years:
            year = year_dir.name
            archive_data[year] = {}
            months = sorted([d for d in year_dir.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
            for month_dir in months:
                month = month_dir.name
                days = sorted([d.name for d in month_dir.iterdir() if d.is_dir() and d.name.isdigit()], reverse=True)
                archive_data[year][month] = days
        
        html_lines = []
        for year, months in archive_data.items():
            html_lines.append(f'<div class="archive-year" style="margin-bottom:40px;">')
            html_lines.append(f'<h2 style="font-family:\'Oswald\'; border-bottom:4px solid #111; padding-bottom:10px;">{year}</h2>')
            for month, days in months.items():
                month_name = datetime.strptime(month, "%m").strftime("%B").upper()
                html_lines.append(f'<div class="archive-month" style="margin-left:20px; margin-bottom:20px;">')
                html_lines.append(f'<h3 style="font-family:\'Oswald\'; color:#a00;">{month_name}</h3>')
                html_lines.append('<ul style="list-style:none; padding:0; display:grid; grid-template-columns:repeat(auto-fill, minmax(120px, 1fr)); gap:10px;">')
                for day in days:
                    display_date = f"{month_name[:3]} {day}"
                    html_lines.append(f'<li><a href="{year}/{month}/{day}/newspaper.html" style="text-decoration:none; color:#111; border:1px solid #ccc; padding:8px; display:block; text-align:center; font-family:\'Oswald\'; font-size:0.8rem;">{display_date}</a></li>')
                html_lines.append('</ul></div>')
            html_lines.append('</div>')
        
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Historical Archives | The Daily Token</title>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Lora:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #fdfdfb; font-family: 'Lora', serif; padding: 40px; max-width: 900px; margin: 0 auto; }}
        a:hover {{ background: #111; color: #fff !important; border-color: #111 !important; }}
        li a {{ transition: all 0.2s; }}
        li a:hover {{ background: #111; color: #fff !important; border-color: #111 !important; }}
    </style>
</head>
<body>
    <a href="../index.html" style="display:block; margin-bottom:40px; text-decoration:none; color:#a00; font-family:'Oswald'; font-weight:700; letter-spacing:1px;">← BACK TO LATEST EDITION</a>
    <h1 style="font-family:'Oswald'; font-size:3.5rem; text-transform:uppercase; text-align:center; margin-bottom:60px; border-bottom:8px double #111; padding-bottom:20px;">The Daily Token Archives</h1>
    { "".join(html_lines) }
    <footer style="text-align:center; margin-top:80px; font-family:'Oswald'; font-size:0.8rem; color:#888;">&copy; 2026 THE DAILY TOKEN</footer>
</body>
</html>"""
        with open(output_path, 'w') as f: f.write(full_html)
        return output_path

    def _generate_html(self, image_prefix: str = "images/") -> str:
        # Determine relative depth for navigation
        is_archive = "../" in image_prefix
        base_rel = "../../../../" if is_archive else ""
        
        # Navigation
        nav_links = "".join([f'<a href="javascript:void(0)" onclick="goToPage({p})" class="nav-item" id="nav-{p}">{PAGES_CONFIG[p]["title"].upper()}</a>' for p in sorted(PAGES_CONFIG.keys())])

        # Build Pages
        pages_html = ""
        for page_num in sorted(PAGES_CONFIG.keys()):
            config = PAGES_CONFIG[page_num]
            is_first = (page_num == 1)
            pages_html += f'<div id="page-content-{page_num}" class="newspaper-page" style="display: {"block" if is_first else "none"}">'
            pages_html += f'<div class="page-title"><span>{config["title"].upper()}</span></div>'
            
            if is_first:
                # Editor's Note
                if self.editorial.get('editors_note'):
                    pages_html += f'<div class="editors-note"><strong>EDITOR\'S NOTE:</strong> {self.editorial["editors_note"]} <span class="emphasis" style="color:var(--highlight); font-weight:700;">#{self.editorial.get("emphasis", "AI")}</span></div>'
                
                # Multi-section overview for Front Page
                for cat_id in config["categories"]:
                    stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                    if not stories: continue
                    pages_html += f'<div class="section-sub-header"><span>{PAGE_CATEGORIES[cat_id].upper()}</span></div>'
                    pages_html += '<div class="columns-3">'
                    for story in stories[:3]: # Top 3 per section
                        pages_html += self._render_article(story, "span-1", "headline-sm", image_prefix)
                    pages_html += '</div>'
            elif page_num == 4:
                # Top Insights Page (Community Wisdom Only)
                cat_id = config["categories"][0]
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                pages_html += '<div class="insights-grid">'
                for story in stories:
                    pages_html += f'''<div class="insight-card">
                        <div class="insight-author">PERSPECTIVE: {story.get("source_author", "The Community")}</div>
                        <h3 class="insight-headline">{story.get("generated_headline")}</h3>
                        <p class="insight-summary">"{story["summary"]}"</p>
                        <div class="insight-footer"><a href="{story.get("hn_url", "#")}" target="_blank">READ FULL DISCUSSION →</a></div>
                    </div>'''
                pages_html += '</div>'
            elif page_num == 3:
                # Model Release Page (Only day releases)
                cat_id = config["categories"][0]
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                pages_html += '<div class="columns-3">'
                for story in stories:
                    if story.get('detected_model') or "Release" in story.get('generated_headline', ''):
                        pages_html += self._render_article(story, "span-1", "headline-sm", image_prefix)
                pages_html += '</div>'
            else:
                # Regular specialized pages
                cat_id = config["categories"][0]
                stories = self.organized.get(cat_id, []) or self.organized.get(str(cat_id), [])
                pages_html += '<div class="columns-3">'
                for story in stories:
                    pages_html += self._render_article(story, "span-1", "headline-sm", image_prefix)
                pages_html += '</div>'

            prev_btn = f'<a href="javascript:void(0)" onclick="goToPage({page_num-1})" class="nav-btn">← PREVIOUS</a>' if page_num > 1 else '<span></span>'
            next_btn = f'<a href="javascript:void(0)" onclick="goToPage({page_num+1})" class="nav-btn">NEXT →</a>' if page_num < 5 else '<span></span>'
            pages_html += f'<div class="page-footer-nav">{prev_btn}{next_btn}</div></div>'

        # Edition Nav with relative paths
        import datetime as dt_mod
        dt = datetime.fromisoformat(self.timestamp)
        prev_day = dt - dt_mod.timedelta(days=1)
        next_day = dt + dt_mod.timedelta(days=1)
        
        edition_nav = f'''
            <div class="edition-nav">
                <a href="{base_rel}archive/{prev_day.strftime('%Y/%m/%d')}/newspaper.html" class="edition-link">← PREVIOUS EDITION</a>
                <span class="edition-current">EDITION: {dt.strftime('%b %d, %Y').upper()}</span>
                <a href="{base_rel}archive/{next_day.strftime('%Y/%m/%d')}/newspaper.html" class="edition-link">NEXT EDITION →</a>
                <span style="color:#ccc">|</span>
                <a href="{base_rel}archive/index.html" class="edition-link">FULL ARCHIVES</a>
            </div>
        '''

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Daily Token</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Lora:ital,wght@0,400;0,700;1,400&family=Oswald:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{ --ink: #111; --paper: #fdfdfb; --sep: #ccc; --highlight: #a00; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: #ddd; margin: 0; padding: 0; font-family: 'Lora', serif; color: var(--ink); line-height: 1.2; overflow-x: hidden; }}
        .newspaper-container {{ background-color: var(--paper); max-width: 1300px; margin: 0 auto; padding: 40px; box-shadow: 0 0 100px rgba(0,0,0,0.2); min-height: 100vh; transition: opacity 0.3s ease; }}
        .page-turn-out {{ opacity: 0; }}
        header {{ text-align: center; border-bottom: 6px double var(--ink); padding-bottom: 20px; }}
        .masthead-title {{ font-family: 'Playfair Display'; font-weight: 900; font-size: 6rem; letter-spacing: -3px; margin: 0; text-transform: uppercase; }}
        .sub-masthead {{ border-top: 1px solid var(--ink); border-bottom: 1px solid var(--ink); margin-top: 15px; padding: 6px 0; font-family: 'Oswald'; text-transform: uppercase; font-size: 0.9rem; display: flex; justify-content: center; gap: 40px; }}
        nav.sticky-nav {{ position: sticky; top: 0; background: var(--paper); z-index: 100; text-align: center; padding: 15px 0; border-bottom: 1px solid var(--ink); margin-bottom: 40px; }}
        .nav-item {{ text-decoration: none; color: var(--ink); font-family: 'Oswald'; font-weight: 700; font-size: 0.85rem; margin: 0 15px; transition: 0.2s; border-bottom: 2px solid transparent; }}
        .nav-item.active {{ color: var(--highlight); border-bottom: 2px solid var(--highlight); }}
        .page-title {{ text-align: center; border-bottom: 3px solid var(--ink); line-height: 0.1em; margin: 60px 0 40px; font-family: 'Oswald'; font-size: 1.5rem; }}
        .page-title span {{ background: var(--paper); padding: 0 30px; }}
        .section-sub-header {{ text-align: left; border-bottom: 1px solid var(--sep); line-height: 0.1em; margin: 40px 0 20px; font-family: 'Oswald'; font-size: 0.9rem; color: var(--highlight); }}
        .section-sub-header span {{ background: var(--paper); padding-right: 15px; }}
        .columns-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 35px; margin-bottom: 40px; }}
        .headline-sm {{ font-family: 'Playfair Display'; font-size: 1.5rem; line-height: 1.1; margin: 0 0 10px 0; font-weight: 700; }}
        .article a {{ color: inherit; text-decoration: none; }}
        .article a:hover {{ color: var(--highlight); }}
        .metadata {{ font-family: 'Oswald'; font-size: 0.75rem; color: #666; margin-bottom: 10px; }}
        .news-img {{ width: 100%; height: auto; display: block; margin-bottom: 20px; filter: grayscale(100%); border: 1px solid #ddd; transition: 0.4s; cursor: pointer; box-shadow: 5px 5px 0 rgba(0,0,0,0.05); }}
        .news-img:hover {{ filter: none; transform: translateY(-2px); }}
        .page-footer-nav {{ display: flex; justify-content: space-between; align-items: center; margin-top: 80px; padding-top: 20px; border-top: 1px solid var(--ink); }}
        .nav-btn {{ font-family: 'Oswald'; font-weight: 700; color: var(--ink); text-decoration: none; border: 1px solid var(--ink); padding: 10px 20px; transition: 0.2s; }}
        .nav-btn:hover {{ background: var(--ink); color: #fff; }}
        .edition-nav {{ display: flex; justify-content: center; align-items: center; background: #eee; padding: 10px; font-family: 'Oswald'; font-size: 0.8rem; gap: 30px; border-bottom: 1px solid #ccc; }}
        .edition-link {{ color: #666; text-decoration: none; }}
        .editors-note {{ margin-bottom: 40px; padding: 20px; border: 1px solid #ddd; font-style: italic; background: #f9f9f9; text-align: center; border-left: 5px solid var(--highlight); }}
        .insights-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; }}
        .insight-card {{ padding: 30px; border: 1px solid #eee; background: #fff; box-shadow: 8px 8px 0 rgba(0,0,0,0.05); transition: 0.3s; }}
        .insight-card:hover {{ transform: translateY(-5px); box-shadow: 12px 12px 0 rgba(0,0,0,0.08); }}
        .insight-author {{ font-family: 'Oswald'; font-size: 0.7rem; color: var(--highlight); margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .insight-headline {{ font-family: 'Playfair Display'; font-size: 1.8rem; margin-bottom: 15px; }}
        .insight-summary {{ font-family: 'Lora'; line-height: 1.6; font-size: 1.1rem; font-style: italic; }}
        .insight-footer {{ margin-top: 20px; font-family: 'Oswald'; font-size: 0.8rem; font-weight: 700; }}
        .hn-link {{ color: var(--highlight); text-decoration: none; font-weight: 700; }}
        @media (max-width: 1000px) {{ .masthead-title {{ font-size: 3.5rem; }} .columns-3, .insights-grid {{ grid-template-columns: 1fr !important; }} .sub-masthead {{ flex-direction: column; gap: 5px; }} }}
    </style>
</head>
<body>
    <div class="edition-nav">
        <a href="{base_rel}archive/{prev_day.strftime('%Y/%m/%d')}/newspaper.html" class="edition-link">← PREVIOUS EDITION</a>
        <span style="font-weight:700; color:#111;">EDITION: {dt.strftime('%b %d, %Y').upper()}</span>
        <a href="{base_rel}archive/{next_day.strftime('%Y/%m/%d')}/newspaper.html" class="edition-link">NEXT EDITION →</a>
        <span style="color:#ccc">|</span>
        <a href="{base_rel}archive/index.html" class="edition-link">FULL ARCHIVES</a>
    </div>
    <div class="newspaper-container" id="newspaper-main">
        <header>
            <h1 class="masthead-title">The Daily Token</h1>
            <div class="sub-masthead">
                <span>{self.location}</span>
                <span>{dt.strftime('%A, %B %d, %Y').upper()}</span>
                <span>GLOBAL AI TECHNOLOGY REPORT</span>
                <span>VOL. {dt.strftime('%Y')}.{dt.strftime('%j')}</span>
            </div>
        </header>
        <nav class="sticky-nav">{nav_links}</nav>
        <main id="pages-wrapper">{pages_html}</main>
        <footer style="text-align: center; padding: 60px 0; font-family: 'Oswald'; border-top: 4px double var(--ink); margin-top: 100px;">
            THE DAILY TOKEN // PRODUCED BY NEURAL AGENTS // &copy; 2026
        </footer>
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
            }}, 300);
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

    def export_rss_feed(self, output_path: str) -> str:
        root = ET.Element("rss"); root.set("version", "2.0"); root.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = "The Daily Token"
        ET.SubElement(channel, "link").text = _site_url()
        ET.SubElement(channel, "description").text = "The AI world's daily news."
        ET.SubElement(channel, "pubDate").text = self.timestamp
        for page_num in range(1, 6):
            stories = self.organized.get(page_num, []) or self.organized.get(str(page_num), [])
            for story in stories:
                item = ET.SubElement(channel, "item")
                ET.SubElement(item, "title").text = story.get('generated_headline', story['original_title'])
                ET.SubElement(item, "link").text = story.get('url') or story.get('hn_url', '')
                ET.SubElement(item, "description").text = story['summary']
        ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
        return output_path