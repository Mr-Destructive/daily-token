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
    
    def __init__(self, organized_stories: Dict[int, List[Dict]]):
        self.organized = organized_stories
        self.timestamp = datetime.now().isoformat()
        self.location = self._determine_location()
    
    def _determine_location(self) -> str:
        """Get newspaper location based on today's news vibes"""
        # Build a summary of today's stories
        headlines = []
        for page_num in range(1, 6):
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
            f"DAILY TOKENS - {self.timestamp}",
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

    def export_html(self, output_path: str) -> str:
        """Export as interactive HTML newspaper"""
        
        html_content = self._generate_html()
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def export_rss_feed(self, output_path: str) -> str:
        """Export as RSS feed for subscriptions"""
        
        root = ET.Element("rss")
        root.set("version", "2.0")
        root.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
        
        channel = ET.SubElement(root, "channel")
        
        ET.SubElement(channel, "title").text = "Daily Tokens"
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
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        return output_path
    
    def _generate_html(self) -> str:
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
            img_path = story.get('generated_image_path', '')
            image_html = f'<img src="{img_path}" class="news-img" alt="">' if img_path else ""
            
            front_page_html += f'''
                <article class="article {layout}">
                    <div class="article-body">
                        {image_html if idx == 0 else ""}
                        <h2 class={"{'headline-xl' if idx == 0 else 'headline-lg'}"}><a href="{story.get('url', '#')}">{story.get('generated_headline', story['original_title'])}</a></h2>
                        <div class="metadata">SOURCE: {story['source'].upper()} // {str(story.get('published', ''))[:10]}</div>
                        {image_html if idx != 0 else ""}
                        <p class="summary">{" ".join(story['summary'].split()[:60]) + "..." if idx == 0 else story['summary']}</p>
                        <div class="footer-links"><a href="{story.get('url', '#')}">READ ARTICLE</a> | <a href="{story.get('hn_url', '#')}">HN</a></div>
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
                img_path = story.get('generated_image_path', '')
                image_html = f'<img src="{img_path}" class="news-img" alt="">' if img_path else ""
                
                layout_pref = story.get('image_layout', 'SQUARE')
                col_span = "span-2" if layout_pref == "WIDE" else "span-1"
                
                sections_html += f'''
                    <article class="article {col_span}">
                        <div class="article-body">
                            {image_html if idx % 4 == 0 or layout_pref == "WIDE" else ""}
                            <h3 class="headline-sm"><a href="{story.get('url', '#')}">{story.get('generated_headline', story['original_title'])}</a></h3>
                            <div class="metadata">{story['source'].upper()}</div>
                            <p class="summary-sm">{story['summary']}</p>
                            <div class="footer-links-sm"><a href="{story.get('url', '#')}">LINK</a> // <a href="{story.get('hn_url', '#')}">HN</a></div>
                        </div>
                    </article>
                '''
            sections_html += '</div></section>'

        # Archives Section (Last 7 days)
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
    <title>Daily Tokens AI Newspaper</title>
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
            <h1 class="masthead">Daily Tokens</h1>
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
            </div>
        </div>

        <footer style="text-align: center; border-top: 4px double var(--ink); margin-top: 60px; padding-top: 20px; font-family: 'Oswald'; font-size: 0.8rem;">
            VERIFIED BY NEURAL CONSENSUS // AGGREGATED FROM HACKERNEWS & GLOBAL AI FEEDS
        </footer>
    </div>
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