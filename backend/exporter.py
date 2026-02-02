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

# Import page categories from processor for consistency
from processor import PAGE_CATEGORIES

def _site_url():
    try:
        from config import SITE_URL
        return SITE_URL
    except ImportError:
        return os.environ.get("SITE_URL", "https://daily-tokens.netlify.app")


def _get_llm_location_from_vibes(stories_summary: str) -> str:
    """Get LLM world location based on newspaper vibes using Meta AI"""
    
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
        "QUANTIZATION QUARTER",
        "TOKENVILLE",
        "PARAMETER PARK",
        "LAYER LAND",
        "CONVERGENCE CENTRAL",
        "BIAS BOROUGH",
        "WEIGHT WARD",
        "BACKPROP BAY",
        "SOFTMAX SECTOR",
        "ACTIVATION AVENUE"
    ]
    
    if not HAS_META_AI:
        return random.choice(available_locations)
    
    try:
        meta_ai = MetaAI()
        prompt = f"""You are a creative news editor in an AI-themed world. Based on these today's AI news themes:

{stories_summary}

Which of these LLM-themed cities best captures the "vibe" of today's news edition?

Locations: {', '.join(available_locations)}

Respond with ONLY the city name. Examples:
- If news is about new models: MODEL SQUARE or TRANSFORMER TOWER
- If about optimization: QUANTIZATION QUARTER or CONVERGENCE CENTRAL  
- If about inference/deployment: INFERENCE ISLAND or NEURAL NEXUS
- If creative/vision work: PROMPT BAY or VECTOR STATION
- If about training: GRADIENT VALLEY or PARAMETER PARK

Choose one that fits the day's AI news vibe:"""
        
        response = meta_ai.prompt(message=prompt)
        location = response.strip().upper()
        
        # Validate response is one of our locations
        if location in available_locations:
            return location
        
        # Fallback if Meta AI returns something else
        return random.choice(available_locations)
    except Exception as e:
        print(f"⚠ Error getting location from Meta AI: {e}")
        return random.choice(available_locations)


class NewsExporter:
    """Export processed news to various formats"""
    
    PAGE_NAMES = PAGE_CATEGORIES
    
    def __init__(self, organized_stories: Dict[int, List[Dict]], location: str = None):
        self.organized = organized_stories
        self.timestamp = datetime.now().isoformat()
        self.location = location if location else self._determine_location()
    
    def _determine_location(self) -> str:
        """Get newspaper location based on today's news vibes"""
        if not self.organized or not self.organized.get(1):
            return "THE CLOUD"
            
        # Build a summary of today's stories
        headlines = []
        for page_num in range(1, 6):
            if page_num in self.organized:
                for story in self.organized[page_num][:2]:  # Top 2 per page
                    headlines.append(story.get('generated_headline', story['original_title']))
        
        summary = " | ".join(headlines[:10])  # Top 10 headlines
        
        print(f"\n[Determining location based on today's vibes...]")
        location = _get_llm_location_from_vibes(summary)
        print(f"   ✓ Today's edition location: {location}")
        return location
    
    def export_json(self, output_path: str) -> str:
        """Export as structured JSON"""
        
        data = {
            'metadata': {
                'generated': self.timestamp,
                'format_version': '1.0'
            },
            'pages': {}
        }
        
        for page_num in range(1, 6):
            stories = self.organized[page_num]
            data['pages'][page_num] = {
                'title': self.PAGE_NAMES[page_num],
                'story_count': len(stories),
                'stories': stories
            }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def export_markdown(self, output_path: str) -> str:
        """Export as readable Markdown"""
        
        lines = [
            "# Daily AI Newspaper",
            f"_Generated: {self.timestamp}_",
            ""
        ]
        
        for page_num in range(1, 6):
            stories = self.organized[page_num]
            
            lines.append(f"## Page {page_num}: {self.PAGE_NAMES[page_num]}")
            lines.append("")
            
            for i, story in enumerate(stories, 1):
                lines.append(f"### {i}. {story.get('generated_headline', story['original_title'])}")
                lines.append("")
                lines.append(f"**Source:** {story['source']}")
                if story.get('url'):
                    lines.append(f"**Link:** {story['url']}")
                if story.get('hn_url'):
                    lines.append(f"**Discuss on HN:** {story['hn_url']}")
                lines.append(f"**Category:** {story['category']}")
                lines.append("")
                lines.append(story['summary'])
                lines.append("")
                lines.append("---")
                lines.append("")
        
        content = "\n".join(lines)
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        return output_path
    
    def export_text(self, output_path: str) -> str:
        """Export as plain text"""
        lines = [
            f"THE DAILY TOKEN - {self.timestamp}",
            f"LOCATION: {self.location}",
            "=" * 60,
            ""
        ]
        
        for page_num in range(1, 6):
            stories = self.organized[page_num]
            lines.append(f"SECTION: {self.PAGE_NAMES[page_num].upper()}")
            lines.append("-" * 60)
            
            for i, story in enumerate(stories, 1):
                lines.append(f"{i}. {story.get('generated_headline', story['original_title']).upper()}")
                lines.append(f"Source: {story['source']} | URL: {story.get('url', 'N/A')}")
                lines.append(f"Summary: {story['summary']}")
                lines.append("")
            lines.append("")
            
        content = "\n".join(lines)
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path

    def export_html(self, output_path: str, image_prefix: str = "images/") -> str:
        """Export as interactive HTML newspaper"""
        
        html_content = self._generate_html(image_prefix=image_prefix)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def export_rss_feed(self, output_path: str) -> str:
        """Export as RSS feed for subscriptions"""
        
        root = ET.Element("rss")
        root.set("version", "2.0")
        root.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
        
        channel = ET.SubElement(root, "channel")
        
        ET.SubElement(channel, "title").text = "The Daily Token"
        ET.SubElement(channel, "link").text = _site_url()
        ET.SubElement(channel, "description").text = "The AI world's daily news."
        ET.SubElement(channel, "language").text = "en-us"
        ET.SubElement(channel, "pubDate").text = self.timestamp
        
        # Add stories from all pages
        for page_num in range(1, 6):
            for story in self.organized[page_num]:
                item = ET.SubElement(channel, "item")
                
                ET.SubElement(item, "title").text = story.get('generated_headline', story['original_title'])
                ET.SubElement(item, "link").text = story.get('url') or story.get('hn_url', '')
                ET.SubElement(item, "source").text = story['source']
                
                description = f"<p><strong>Category:</strong> {story['category']}</p>"
                description += f"<p>{story['summary']}</p>"
                
                ET.SubElement(item, "description").text = description
                ET.SubElement(item, "pubDate").text = str(story.get('published', self.timestamp))
        
    def export_archive_index(self, archive_root: str, output_path: str) -> str:
        """Scan archive folder and generate a historical index page"""
        root_path = Path(archive_root)
        if not root_path.exists():
            return ""

        archive_data = {} # {year: {month: [days]}}
        
        # Scan directories
        for year_dir in sorted(root_path.iterdir(), reverse=True):
            if not year_dir.is_dir() or not year_dir.name.isdigit(): continue
            year = year_dir.name
            archive_data[year] = {}
            
            for month_dir in sorted(year_dir.iterdir(), reverse=True):
                if not month_dir.is_dir() or not month_dir.name.isdigit(): continue
                month = month_dir.name
                archive_data[year][month] = []
                
                for day_dir in sorted(month_dir.iterdir(), reverse=True):
                    if not day_dir.is_dir() or not day_dir.name.isdigit(): continue
                    day = day_dir.name
                    archive_data[year][month].append(day)

        # Generate HTML
        html_lines = []
        for year in archive_data:
            html_lines.append(f'<div class="archive-year"><h2>{year}</h2>')
            for month in archive_data[year]:
                month_name = datetime.strptime(month, "%m").strftime("%B").upper()
                html_lines.append(f'<div class="archive-month"><h3>{month_name}</h3><ul class="archive-days">')
                for day in archive_data[year][month]:
                    date_str = f"{year}-{month}-{day}"
                    display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y").upper()
                    html_lines.append(f'<li><a href="/daily-token/archive/{year}/{month}/{day}/newspaper.html">{display_date}</a></li>')
                html_lines.append('</ul></div>')
            html_lines.append('</div>')

        archive_list_html = "\n".join(html_lines)

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archives | The Daily Token</title>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Lora:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #fdfdfb; font-family: 'Lora', serif; color: #111; padding: 40px 20px; max-width: 800px; margin: 0 auto; }}
        h1 {{ font-family: 'Oswald', sans-serif; font-size: 3rem; text-transform: uppercase; border-bottom: 4px solid #111; padding-bottom: 10px; margin-bottom: 40px; text-align: center; }}
        .archive-year h2 {{ font-family: 'Oswald', sans-serif; font-size: 2rem; background: #111; color: #fff; padding: 5px 15px; }}
        .archive-month {{ margin-left: 20px; margin-bottom: 30px; }}
        .archive-month h3 {{ font-family: 'Oswald', sans-serif; border-bottom: 1px solid #ccc; padding-bottom: 5px; color: #a00; }}
        .archive-days {{ list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }}
        .archive-days li a {{ text-decoration: none; color: #111; border: 1px solid #ccc; padding: 8px; display: block; text-align: center; font-size: 0.85rem; font-family: 'Oswald', sans-serif; transition: all 0.2s; }}
        .archive-days li a:hover {{ background: #111; color: #fff; border-color: #111; }}
        .back-home {{ display: block; text-align: center; margin-bottom: 40px; text-decoration: none; color: #a00; font-family: 'Oswald'; font-weight: 700; letter-spacing: 1px; }}
    </style>
</head>
<body>
    <a href="/daily-token/newspaper.html" class="back-home">← BACK TO LATEST EDITION</a>
    <h1>Historical Archives</h1>
    {archive_list_html}
</body>
</html>"""
        
        with open(output_path, 'w') as f:
            f.write(full_html)
        return output_path
    
    def _generate_html(self, image_prefix: str = "images/") -> str:
        """Generate professional, dense, adaptive newspaper-style HTML"""
        
        # Collect all stories and sort by significance
        all_stories = []
        for page_num in range(1, 6):
            all_stories.extend(self.organized[page_num])
        
        all_stories.sort(key=lambda x: x.get('significance_score', 0), reverse=True)
        
        # Front Page Selection
        front_page_leads = all_stories[:3]
        
        # Navigation
        nav_links = '<a href="#front-page">THE FRONT PAGE</a>'
        for page_num in range(1, 6):
            if self.organized[page_num]:
                nav_links += f' <span class="nav-sep">|</span> <a href="#section-{page_num}">{self.PAGE_NAMES[page_num].upper()}</a>'

        # --- FRONT PAGE ---
        front_page_html = f'''
        <section id="front-page">
            <div class="deck-header"><span>FRONT PAGE // KEY BREAKTHROUGHS</span></div>
            <div class="lead-grid">
        '''
        
        for idx, story in enumerate(front_page_leads):
            layout = "span-8 main-story" if idx == 0 else "span-4 side-story"
            if img_path:
                img_filename = os.path.basename(img_path)
                final_img_src = f"{image_prefix}{img_filename}"
                # We need js_headline etc for the image link too, but they are defined below. 
                # Let's move definitions up.
            
            headline = story.get('generated_headline', story['original_title'])
            summary = story['summary']
            
            # Create a URL-safe slug
            slug = "".join([c.lower() if c.isalnum() else "-" for c in headline[:50]]).strip("-")
            
            # Escape for JavaScript openMap call
            js_headline = headline.replace("'", "\\'").replace('"', '&quot;')
            js_summary = summary.replace("'", "\\'").replace('"', '&quot;')
            
            if img_path:
                image_html = f'<img src="{final_img_src}" class="news-img" alt="" style="cursor:pointer" onclick=\'openMap("{js_headline}", "{js_summary}", "{final_img_src}", "{slug}")\'>'
            else:
                image_html = ""
            
            front_page_html += f'''
                <article class="article {layout}" id="story-{slug}">
                    <div class="article-body">
                        {image_html if idx == 0 else ""}
                        <h2 class={"{'headline-xl' if idx == 0 else 'headline-lg'}"}><a href="javascript:void(0)" onclick='openMap("{js_headline}", "{js_summary}", "{final_img_src}", "{slug}")'>{headline}</a></h2>
                        <div class="metadata">SOURCE: {story['source'].upper()} // {str(story.get('published', ''))[:10]}</div>
                        {image_html if idx != 0 else ""}
                        <p class="summary">{" ".join(summary.split()[:60]) + "..." if idx == 0 else summary}</p>
                        <div class="footer-links">
                            <a href="javascript:void(0)" onclick='openMap("{js_headline}", "{js_summary}", "{final_img_src}", "{slug}")'>READ ARTICLE</a> | 
                            <a href="{story.get('hn_url', '#')}">HN</a>
                        </div>
                    </div>
                </article>
            '''
        front_page_html += '</div>'
        
        # Section Pulse (Compact)
        pulse_html = '<div class="section-pulse-grid">'
        for page_num in range(1, 6):
            stories = self.organized[page_num]
            if stories:
                top = max(stories, key=lambda x: x.get('significance_score', 0))
                pulse_html += f'''
                    <div class="pulse-block">
                        <div class="pulse-tag">{self.PAGE_NAMES[page_num].upper()}</div>
                        <div class="pulse-link"><a href="#section-{page_num}">{top.get('generated_headline', top['original_title'])}</a></div>
                    </div>
                '''
        pulse_html += '</div></section>'

        # --- SECTIONS ---
        sections_html = ""
        for page_num in range(1, 6):
            stories = self.organized[page_num]
            if not stories: continue
                
            sections_html += f'''
            <section id="section-{page_num}">
                <div class="deck-header"><span>{self.PAGE_NAMES[page_num].upper()}</span></div>
                <div class="columns-4">
            '''
            
            for idx, story in enumerate(stories):
                headline = story.get('generated_headline', story['original_title'])
                summary = story['summary']
                img_path = story.get('generated_image_path', '')
                
                # Create a URL-safe slug
                slug = "".join([c.lower() if c.isalnum() else "-" for c in headline[:50]]).strip("-")
                
                # Escape for JavaScript openMap call
                js_headline = headline.replace("'", "\\'").replace('"', '&quot;')
                js_summary = summary.replace("'", "\\'").replace('"', '&quot;')
                
                if img_path:
                    img_filename = os.path.basename(img_path)
                    final_img_src = f"{image_prefix}{img_filename}"
                    image_html = f'<img src="{final_img_src}" class="news-img" alt="" style="cursor:pointer" onclick=\'openMap("{js_headline}", "{js_summary}", "{final_img_src}", "{slug}")\'>'
                else:
                    image_html = ""
                    final_img_src = ""
                
                layout_pref = story.get('image_layout', 'SQUARE')
                col_span = "span-2" if layout_pref == "WIDE" else "span-1"
                
                sections_html += f'''
                    <article class="article {col_span}" id="story-{slug}">
                        <div class="article-body">
                            {image_html if idx % 4 == 0 or layout_pref == "WIDE" else ""}
                            <h3 class="headline-sm"><a href="javascript:void(0)" onclick='openMap("{js_headline}", "{js_summary}", "{final_img_src}", "{slug}")'>{headline}</a></h3>
                            <div class="metadata">{story['source'].upper()}</div>
                            <p class="summary-sm">{summary}</p>
                            <div class="footer-links-sm">
                                <a href="javascript:void(0)" onclick='openMap("{js_headline}", "{js_summary}", "{final_img_src}", "{slug}")'>LINK</a> // 
                                <a href="{story.get('hn_url', '#')}">HN</a>
                            </div>
                        </div>
                    </article>
                '''
            sections_html += '</div></section>'

        archive_links_html = ""
        import datetime as dt_mod
        today = dt_mod.date.today()
        for i in range(1, 8):
            prev_date = today - dt_mod.timedelta(days=i)
            date_path = prev_date.strftime('%Y/%m/%d')
            display_date = prev_date.strftime('%b %d, %Y').upper()
            archive_links_html += f'<a href="/daily-token/archive/{date_path}/newspaper.html" class="archive-link">{display_date}</a>'

        # --- TEMPLATE ---
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Daily Token AI Newspaper</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Lora:ital,wght@0,400;0,700;1,400&family=Oswald:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --ink: #111;
            --paper: #fdfdfb;
            --sep: #ccc;
            --highlight: #a00;
        }}
        
        * {{ box-sizing: border-box; }}
        body {{
            background-color: #ddd;
            margin: 0; padding: 10px;
            font-family: 'Lora', serif;
            color: var(--ink);
            line-height: 1.2;
        }}
        
        .newspaper {{
            background-color: var(--paper);
            max-width: 1300px;
            margin: 0 auto;
            padding: 20px 40px;
            box-shadow: 0 0 50px rgba(0,0,0,0.3);
            border: 1px solid #aaa;
        }}
        
        /* Masthead */
        header {{
            text-align: center;
            border-bottom: 6px double var(--ink);
            padding-bottom: 10px;
            margin-bottom: 10px;
        }}
        
        .masthead {{
            font-family: 'Playfair Display', serif;
            font-weight: 900;
            font-size: 6rem;
            letter-spacing: -3px;
            margin: 0;
            line-height: 0.85;
            text-transform: uppercase;
        }}
        
        .sub-masthead {{
            border-top: 1px solid var(--ink);
            border-bottom: 1px solid var(--ink);
            margin-top: 15px;
            padding: 4px 0;
            font-family: 'Oswald', sans-serif;
            text-transform: uppercase;
            font-size: 0.85rem;
            display: flex;
            justify-content: space-between;
            letter-spacing: 1px;
        }}
        
        nav {{
            text-align: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--ink);
            margin-bottom: 30px;
            font-family: 'Oswald', sans-serif;
            font-size: 0.8rem;
        }}
        nav a {{ text-decoration: none; color: var(--ink); font-weight: 700; }}
        nav a:hover {{ color: var(--highlight); }}
        .nav-sep {{ margin: 0 15px; color: var(--sep); }}
        
        /* Sections */
        .deck-header {{
            text-align: center;
            border-bottom: 2px solid var(--ink);
            line-height: 0.1em;
            margin: 40px 0 25px;
            font-family: 'Oswald', sans-serif;
            font-size: 1rem;
        }}
        .deck-header span {{ background: var(--paper); padding: 0 20px; }}
        
        /* Grid Engine */
        .lead-grid {{
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 30px;
            border-bottom: 3px solid var(--ink);
            padding-bottom: 30px;
        }}
        
        .columns-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        
        .span-8 {{ grid-column: span 8; border-right: 1px solid var(--sep); padding-right: 30px; }}
        .span-4 {{ grid-column: span 4; }}
        .span-2 {{ grid-column: span 2; }}
        .span-1 {{ grid-column: span 1; }}
        
        /* Typography */
        .headline-xl {{ font-family: 'Playfair Display', serif; font-size: 3.5rem; line-height: 0.95; margin: 0 0 15px 0; font-weight: 900; }}
        .headline-lg {{ font-family: 'Playfair Display', serif; font-size: 2rem; line-height: 1; margin: 0 0 10px 0; font-weight: 900; }}
        .headline-sm {{ font-family: 'Playfair Display', serif; font-size: 1.4rem; line-height: 1.1; margin: 0 0 8px 0; font-weight: 700; }}
        .article a {{ color: inherit; text-decoration: none; }}
        .article a:hover {{ text-decoration: underline; }}
        
        .metadata {{
            font-family: 'Oswald', sans-serif;
            font-size: 0.75rem;
            color: #555;
            margin-bottom: 10px;
            letter-spacing: 0.5px;
        }}
        
        .summary {{ font-size: 1.1rem; text-align: justify; margin-bottom: 15px; line-height: 1.3; }}
        .summary-sm {{ font-size: 0.9rem; text-align: justify; margin-bottom: 10px; line-height: 1.3; }}
        
        .footer-links {{ font-family: 'Oswald', sans-serif; font-size: 0.8rem; font-weight: 700; color: var(--highlight); }}
        .footer-links-sm {{ font-family: 'Oswald', sans-serif; font-size: 0.7rem; font-weight: 700; color: var(--highlight); }}

        /* Articles */
        .article {{ margin-bottom: 20px; }}
        .news-img {{
            width: 100%;
            height: auto;
            display: block;
            margin-bottom: 15px;
            filter: grayscale(100%) contrast(1.2);
            border: 1px solid var(--ink);
            transition: filter 0.3s ease;
        }}
        .news-img:hover {{ filter: none; }}

        /* --- MARAUDER'S MAP MODAL --- */
        #marauders-modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0; top: 0;
            width: 100%; height: 100%;
            background-color: rgba(0,0,0,0.8);
            overflow: auto;
            backdrop-filter: blur(5px);
        }}

        .map-content {{
            position: relative;
            background: #e9dcc9; /* Parchment color */
            background-image: url('https://www.transparenttextures.com/patterns/old-map.png');
            margin: 5% auto;
            padding: 50px;
            width: 70%;
            max-width: 900px;
            min-height: 500px;
            border: 20px solid transparent;
            border-image: url('https://www.transparenttextures.com/patterns/pinstripe.png') 30 round;
            box-shadow: 0 0 100px rgba(0,0,0,0.5);
            font-family: 'Playfair Display', serif;
            color: #4a3728;
            transform: scale(0.8);
            opacity: 0;
            transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}

        #marauders-modal.open .map-content {{
            transform: scale(1);
            opacity: 1;
        }}

        .map-header {{
            text-align: center;
            border-bottom: 2px solid #4a3728;
            margin-bottom: 30px;
            padding-bottom: 10px;
        }}

        .map-title {{ font-size: 3rem; font-weight: 900; text-transform: uppercase; margin: 0; letter-spacing: -1px; }}
        .map-subtitle {{ font-family: 'Oswald'; text-transform: uppercase; font-size: 1rem; letter-spacing: 2px; }}

        .map-body {{
            font-size: 1.4rem;
            line-height: 1.6;
            text-align: justify;
            position: relative;
            filter: url('#ink-bleed');
        }}

        /* Footprints Animation */
        .footprint {{
            position: absolute;
            width: 30px;
            height: 15px;
            background: #4a3728;
            opacity: 0;
            border-radius: 50% 50% 40% 40%;
            pointer-events: none;
        }}
        
        @keyframes walk-left {{
            0% {{ opacity: 0; transform: translate(0,0) rotate(-20deg); }}
            20% {{ opacity: 0.6; }}
            80% {{ opacity: 0.6; }}
            100% {{ opacity: 0; transform: translate(40px, -60px) rotate(-20deg); }}
        }}

        @keyframes walk-right {{
            0% {{ opacity: 0; transform: translate(20px,20px) rotate(20deg); }}
            20% {{ opacity: 0.6; }}
            80% {{ opacity: 0.6; }}
            100% {{ opacity: 0; transform: translate(60px, -40px) rotate(20deg); }}
        }}

        .map-close {{
            position: absolute;
            top: 20px; right: 30px;
            font-size: 2rem;
            cursor: pointer;
            font-weight: 900;
        }}

        .ink-spread {{
            animation: inkSpread 2s forwards;
        }}

        @keyframes inkSpread {{
            from {{ opacity: 0; filter: blur(20px); }}
            to {{ opacity: 1; filter: blur(0); }}
        }}
        
        /* Section Pulse */
        .section-pulse-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 15px;
            background: #f4f4f2;
            padding: 15px;
            margin-top: 20px;
            border: 1px solid var(--sep);
        }}
        .pulse-block {{ border-right: 1px solid var(--sep); padding-right: 10px; }}
        .pulse-block:last-child {{ border-right: none; }}
        .pulse-tag {{ font-family: 'Oswald', sans-serif; font-size: 0.65rem; color: var(--highlight); }}
        .pulse-link {{ font-family: 'Playfair Display', serif; font-weight: 700; font-size: 0.85rem; }}
        .pulse-link a {{ color: var(--ink); text-decoration: none; }}

        /* Archive Strip */
        .archive-strip {{
            margin-top: 40px;
            padding: 20px 0;
            border-top: 1px solid var(--sep);
            text-align: center;
        }}
        .archive-title {{ font-family: 'Oswald', sans-serif; font-size: 0.8rem; letter-spacing: 2px; margin-bottom: 15px; color: #777; }}
        .archive-links {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; }}
        .archive-link {{ 
            font-family: 'Oswald', sans-serif; 
            font-size: 0.75rem; 
            color: var(--ink); 
            text-decoration: none; 
            border: 1px solid var(--sep);
            padding: 5px 10px;
            transition: all 0.2s;
        }}
        .archive-link:hover {{ border-color: var(--highlight); color: var(--highlight); }}

        @media (max-width: 900px) {{
            .newspaper {{ padding: 15px 20px; }}
            .masthead {{ font-size: 3rem; letter-spacing: -1px; }}
            .sub-masthead {{ font-size: 0.7rem; flex-direction: column; align-items: center; gap: 5px; }}
            .lead-grid, .columns-4, .section-pulse-grid {{ grid-template-columns: 1fr !important; gap: 20px; }}
            .span-8, .span-4, .span-2 {{ grid-column: span 1 !important; border-right: none; padding-right: 0; }}
            .article {{ border-bottom: 1px solid var(--sep); padding-bottom: 25px; margin-bottom: 25px; }}
            .headline-xl {{ font-size: 2rem; }}
            .headline-lg {{ font-size: 1.6rem; }}
            .headline-sm {{ font-size: 1.2rem; }}
            nav {{ 
                font-size: 0.75rem; 
                display: flex; 
                flex-wrap: wrap; 
                justify-content: center; 
                gap: 10px;
                padding: 10px 0;
            }}
            .nav-sep {{ display: none; }}
            .news-img {{ margin-top: 10px; filter: none; }} /* Real colors on mobile for better visibility */
        }}
    </style>
</head>
<body>
    <div class="newspaper">
        <header>
            <h1 class="masthead">The Daily Token</h1>
            <div class="sub-masthead">
                <span>{self.location}, {datetime.now().strftime('%A, %B %d, %Y').upper()}</span>
                <span>AI TECHNOLOGY & INFRASTRUCTURE</span>
                <span>VOL. {datetime.now().strftime('%Y')}.{datetime.now().strftime('%j')}</span>
            </div>
        </header>

        <nav>
            {nav_links}
        </nav>

        <main>
            {front_page_html}
            {sections_html}
        </main>

        <div class="archive-strip">
            <div class="archive-title">RECENT EDITIONS</div>
            <div class="archive-links">
                {archive_links_html}
                <a href="/daily-token/archive/index.html" class="archive-link" style="background:#111; color:#fff;">ALL ARCHIVES</a>
            </div>
        </div>

        <footer style="text-align: center; border-top: 4px double var(--ink); margin-top: 60px; padding-top: 20px; font-family: 'Oswald'; font-size: 0.8rem;">
            VERIFIED BY NEURAL CONSENSUS // AGGREGATED FROM HACKERNEWS & GLOBAL AI FEEDS
        </footer>
    </div>

    <!-- MARAUDER'S MAP MODAL -->
    <div id="marauders-modal">
        <div class="map-container">
            <div class="map-fold-left"></div>
            <div class="map-content">
                <span class="map-close" onclick="closeMap()">&times;</span>
                <div class="map-header">
                    <div class="map-subtitle">I solemnly swear that I am up to no good</div>
                    <h2 class="map-title" id="modal-title">Article Detail</h2>
                </div>
                <div class="map-inner-content">
                    <div id="modal-image-container"></div>
                    <div class="map-body" id="modal-summary">
                        Summary goes here...
                    </div>
                </div>
                <div class="map-footer">Mischief Managed</div>
            </div>
            <div class="map-fold-right"></div>
        </div>
    </div>

    <style>
        #marauders-modal {{
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0; top: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.9);
            perspective: 2000px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .map-container {{
            position: relative;
            width: 90%;
            max-width: 1000px;
            height: 80vh;
            display: flex;
            transform-style: preserve-3d;
            transition: transform 1s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.5s;
            opacity: 0;
            transform: scale(0.1) rotateX(20deg);
        }}

        #marauders-modal.open .map-container {{
            opacity: 1;
            transform: scale(1) rotateX(0deg);
        }}

        .map-content {{
            flex: 2;
            background: #e9dcc9;
            background-image: url('https://www.transparenttextures.com/patterns/old-map.png');
            box-shadow: 0 0 50px rgba(0,0,0,0.5);
            padding: 40px;
            position: relative;
            overflow-y: auto;
            border: 2px solid #4a3728;
            z-index: 2;
        }}

        .map-fold-left, .map-fold-right {{
            flex: 1;
            background: #d9ccb9;
            background-image: url('https://www.transparenttextures.com/patterns/old-map.png');
            border: 2px solid #4a3728;
            transition: transform 1s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1;
        }}

        .map-fold-left {{ transform-origin: right; transform: rotateY(0deg); border-right: none; }}
        .map-fold-right {{ transform-origin: left; transform: rotateY(0deg); border-left: none; }}

        #marauders-modal:not(.open) .map-fold-left {{ transform: rotateY(-90deg); }}
        #marauders-modal:not(.open) .map-fold-right {{ transform: rotateY(90deg); }}

        .map-header {{ text-align: center; margin-bottom: 30px; border-bottom: 1px double #4a3728; padding-bottom: 20px; }}
        .map-subtitle {{ font-family: 'Oswald'; font-size: 0.8rem; letter-spacing: 3px; color: #842; text-transform: uppercase; }}
        .map-title {{ font-family: 'Playfair Display'; font-size: 2.5rem; color: #4a3728; margin: 10px 0; }}
        
        .map-inner-content {{ display: flex; gap: 30px; flex-direction: column; align-items: center; }}
        #modal-image-container img {{ max-width: 100%; border: 5px solid #4a3728; filter: sepia(0.5) contrast(1.2); box-shadow: 5px 5px 15px rgba(0,0,0,0.3); }}
        
        .map-body {{ 
            font-family: 'Playfair Display', serif; 
            font-size: 1.3rem; 
            line-height: 1.6; 
            color: #4a3728; 
            text-align: justify;
            filter: url('#ink-bleed');
            opacity: 0;
            transition: opacity 2s;
        }}
        
        .map-container.revealed .map-body {{ opacity: 1; }}

        .map-footer {{ text-align: center; margin-top: 40px; font-family: 'Oswald'; color: #842; font-size: 0.9rem; letter-spacing: 5px; }}
        .map-close {{ position: absolute; top: 20px; right: 20px; font-size: 2.5rem; cursor: pointer; color: #4a3728; z-index: 10; }}

        /* Footprints */
        .footprint {{
            position: absolute;
            width: 25px; height: 12px;
            background: #4a3728;
            opacity: 0;
            border-radius: 50% 50% 40% 40%;
            pointer-events: none;
            z-index: 100;
        }}
    </style>

    <!-- SVG Filters for Ink Bleed -->
    <svg style="display:none;">
        <defs>
            <filter id="ink-bleed">
                <feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="3" result="noise" />
                <feDisplacementMap in="SourceGraphic" in2="noise" scale="10" />
            </filter>
        </defs>
    </svg>

    <script>
        function openMap(title, summary, imgUrl, slug) {{
            const modal = document.getElementById('marauders-modal');
            const container = modal.querySelector('.map-container');
            const titleEl = document.getElementById('modal-title');
            const summaryEl = document.getElementById('modal-summary');
            const imgContainer = document.getElementById('modal-image-container');
            
            // Set content
            titleEl.innerText = title;
            summaryEl.innerText = summary;
            imgContainer.innerHTML = imgUrl ? `<img src="${{imgUrl}}" alt="">` : '';
            
            // Show modal
            modal.style.display = 'flex';
            
            // Update URL query param without reload
            const newUrl = new URL(window.location);
            newUrl.searchParams.set('story', slug);
            window.history.pushState({{}}, '', newUrl);

            // Trigger animations
            setTimeout(() => {{
                modal.classList.add('open');
                
                // Walking footprints across the newspaper first
                for(let i=0; i<8; i++) {{
                    setTimeout(() => createFootprint(i), i * 250);
                }}
                
                // Reveal ink after unfold
                setTimeout(() => {{
                    container.classList.add('revealed');
                }}, 1200);
            }}, 10);
        }}

        function closeMap() {{
            const modal = document.getElementById('marauders-modal');
            const container = modal.querySelector('.map-container');
            modal.classList.remove('open');
            container.classList.remove('revealed');
            
            // Remove story from URL
            const newUrl = new URL(window.location);
            newUrl.searchParams.delete('story');
            window.history.pushState({{}}, '', newUrl);

            setTimeout(() => {{
                modal.style.display = 'none';
            }}, 1000);
        }}

        function createFootprint(i) {{
            const body = document.body;
            const fp = document.createElement('div');
            fp.className = 'footprint';
            
            // Start from bottom left and walk towards center
            fp.style.left = (10 + (i * 8)) + '%';
            fp.style.top = (90 - (i * 8)) + '%';
            
            const anim = i % 2 === 0 ? 'walk-left' : 'walk-right';
            fp.style.animation = `${{anim}} 1s forwards`;
            
            body.appendChild(fp);
            setTimeout(() => fp.remove(), 1000);
        }}

        // Check query params on load
        window.onload = function() {{
            const params = new URLSearchParams(window.location.search);
            const storySlug = params.get('story');
            if (storySlug) {{
                const targetArticle = document.getElementById(`story-${{storySlug}}`);
                if (targetArticle) {{
                    // Try to find the trigger link
                    const link = targetArticle.querySelector('a[onclick]');
                    if (link) link.click();
                }}
            }}
        }};

        // Close on outside click
        window.onclick = function(event) {{
            const modal = document.getElementById('marauders-modal');
            if (event.target == modal) {{
                closeMap();
            }}
        }}
    </script>
</body>
</html>
"""
        return html


if __name__ == "__main__":
    # Test exporter
    sample_organized = {
        1: [{
            'original_title': 'OpenAI announces GPT-5',
            'url': 'https://openai.com/gpt5',
            'source': 'HackerNews',
            'score': 500,
            'significance_score': 95,
            'category': 'Breaking Vectors',
            'confidence': 0.95,
            'summary': 'OpenAI releases new model with breakthrough capabilities.',
            'published': datetime.now().isoformat()
        }],
        2: [], 3: [], 4: [], 5: []
    }
    
    exporter = NewsExporter(sample_organized)
    print(exporter.export_html('/tmp/test.html'))