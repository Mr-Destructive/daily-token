"""HackerNews scraper with RSS feed support for major AI labs"""
import requests
import feedparser
import re
from typing import List, Dict
from datetime import datetime
from email.utils import parsedate_to_datetime
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Import configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    import config as _cfg
except Exception:
    _cfg = None

AI_KEYWORDS = getattr(_cfg, "AI_KEYWORDS", ['ai', 'llm', 'machine learning', 'deep learning'])
HACKERNEWS_STORY_LIMIT = int(getattr(_cfg, "HACKERNEWS_STORY_LIMIT", 30))
RSS_FEEDS = getattr(_cfg, "RSS_FEEDS", {'arxiv': 'http://arxiv.org/rss/cs.AI'})
RSS_STORIES_PER_FEED = int(getattr(_cfg, "RSS_STORIES_PER_FEED", 5))

class ImageFetcher:
    """Fetch potential images from URLs for AI review"""
    
    @staticmethod
    def get_candidate_images(url: str) -> List[str]:
        """Extract potential raster cover images from URL (SEO, OpenGraph, Thumbnails)"""
        if not url or not url.startswith('http'):
            return []
            
        candidates = []
        valid_exts = ['.jpg', '.jpeg', '.png', '.webp']
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # print(f"      - Successfully fetched HTML for {url[:40]}")
            
            # Helper to check if URL is a valid raster image
            def is_valid(img_url):
                img_url_lower = img_url.lower()
                # 1. Reject SVGs, Icons, and Common Logos/UI elements
                exclusions = [
                    '.svg', '.ico', 'sprite', 'pixel', 'tracker', 'ad', 'btn', 'nav', 
                    'logo', 'banner', 'header', 'footer', 'avatar', 'profile', 
                    'menu', 'icon', 'button', 'search', 'social', 'sharing',
                    'placeholder', 'transparent', 'spacer'
                ]
                if any(x in img_url_lower for x in exclusions):
                    return False
                
                # 2. Check for standard image extensions using regex (handles width-800.format-jpg etc)
                # Look for extension followed by either nothing, a dot, a slash, or a question mark
                if re.search(r'\.(jpg|jpeg|png|webp)($|\.|\/|\?)', img_url_lower):
                    return True
                
                # 3. If it's from a known image CDN, it's likely an image
                if any(cdn in img_url_lower for cdn in ['gstatic.com', 'githubusercontent.com', 'medium.com', 'substack-post-media', 'sanity.io']):
                    return True
                return False

            # 1. Meta Tag extraction (OG, Twitter, Schema)
            for meta in soup.find_all('meta'):
                # Check ALL attributes for 'image' related content in keys/values
                meta_str = str(meta).lower()
                if 'image' not in meta_str: continue
                
                content = meta.get('content')
                if not content: continue
                
                prop = meta.get('property', '').lower()
                name = meta.get('name', '').lower()
                itemprop = meta.get('itemprop', '').lower()
                
                if any(x in prop or x in name for x in ['og:image', 'twitter:image']) or itemprop == 'image' or 'og:image' in prop:
                    full_url = urljoin(url, content)
                    if is_valid(full_url):
                        candidates.append(full_url)

            # 2. Article Thumbnails & Icons
            for link in soup.find_all('link', rel=re.compile(r'image_src|thumbnail|icon', re.I)):
                c = link.get('href')
                if c:
                    full_url = urljoin(url, c)
                    if is_valid(full_url):
                        candidates.append(full_url)

            # 3. Large images in article body
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original-src')
                if not src: continue
                
                full_url = urljoin(url, src)
                if is_valid(full_url):
                    candidates.append(full_url)
            
            # if candidates:
            #     print(f"      - Found {len(candidates)} image candidates")
            
            # Deduplicate while preserving order
            unique_candidates = []
            for c in candidates:
                if c not in unique_candidates:
                    unique_candidates.append(c)
                    
            return unique_candidates[:15]
        except Exception:
            return []

    @staticmethod
    def get_main_image(url: str) -> str | None:
        """Legacy helper - just returns first candidate"""
        candidates = ImageFetcher.get_candidate_images(url)
        return candidates[0] if candidates else None

class HackerNewsScraper:
    """Scrape top stories from HackerNews"""
    
    def __init__(self):
        self.hn_api = "https://hacker-news.firebaseio.com/v0"
        self.timeout = 10
        
    def get_historical_stories(self, target_date: datetime, limit: int = 50) -> List[Dict]:
        """Fetch top AI stories for a specific date using Algolia Search API"""
        start_ts = int(target_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end_ts = start_ts + 86400
        queries = [
            # Primary: keep relevance threshold high.
            (
                "https://hn.algolia.com/api/v1/search"
                f"?query=ai&numericFilters=created_at_i>{start_ts},created_at_i<{end_ts},points>20"
                f"&tags=story&hitsPerPage={limit}"
            ),
            # Fallback 1: broader AI terms, no point floor.
            (
                "https://hn.algolia.com/api/v1/search"
                f"?query=llm&numericFilters=created_at_i>{start_ts},created_at_i<{end_ts}"
                f"&tags=story&hitsPerPage={limit}"
            ),
            # Fallback 2: date-sorted slice for the day.
            (
                "https://hn.algolia.com/api/v1/search_by_date"
                f"?query=ai&numericFilters=created_at_i>{start_ts},created_at_i<{end_ts}"
                f"&tags=story&hitsPerPage={limit}"
            ),
        ]

        for idx, url in enumerate(queries, start=1):
            try:
                print(f"      - Querying Algolia for {target_date.date()} (attempt {idx})...")
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                stories = []
                for hit in data.get('hits', []):
                    title = hit.get('title') or hit.get('story_title') or ""
                    link = hit.get('url') or hit.get('story_url') or ""
                    if not title or not link:
                        continue
                    stories.append({
                        'id': int(hit['objectID']),
                        'title': title,
                        'url': link,
                        'score': hit.get('points', 0),
                        'by': hit.get('author', 'unknown'),
                        'time': hit.get('created_at_i', 0),
                        'kids': hit.get('children', []),
                    })

                if stories:
                    return stories
            except Exception as e:
                print(f"      - Algolia attempt {idx} failed: {e}")

        return []

    def get_top_stories(self, limit: int = None) -> List[Dict]:
        """Fetch stories from Top, Best, and New pools to ensure depth and quality"""
        if limit is None:
            limit = HACKERNEWS_STORY_LIMIT
        
        # We'll pull from multiple endpoints to get a broader view
        endpoints = ["topstories", "beststories", "newstories"]
        all_ids = []
        
        try:
            for endpoint in endpoints:
                # Top/New have 500, Best has 200. 
                # We take a subset of each to stay efficient.
                count = 100 if endpoint != "newstories" else 200
                resp = requests.get(f"{self.hn_api}/{endpoint}.json", timeout=self.timeout)
                all_ids.extend(resp.json()[:count])
            
            # Deduplicate IDs while maintaining some order (top/best first)
            unique_ids = []
            seen_ids = set()
            for s_id in all_ids:
                if s_id not in seen_ids:
                    unique_ids.append(s_id)
                    seen_ids.add(s_id)

            import time
            from concurrent.futures import ThreadPoolExecutor
            cutoff_time = time.time() - (24 * 3600)
            
            stories = []
            print(f"      - Fetching details for {min(len(unique_ids), 400)} HN candidates in parallel...")
            
            def fetch_and_filter(s_id):
                story = self._get_story(s_id)
                if story and story.get('time', 0) > cutoff_time and story.get('url'):
                    return story
                return None

            with ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(fetch_and_filter, unique_ids[:400]))
            
            stories = [r for r in results if r is not None]
            return stories[:100]
        except Exception as e:
            print(f"Error fetching HackerNews: {e}")
            return []
    
    def _get_story(self, story_id: int) -> Dict | None:
        """Fetch individual story details"""
        try:
            response = requests.get(
                f"{self.hn_api}/item/{story_id}.json",
                timeout=self.timeout
            )
            data = response.json()
            
            # Filter out dead/deleted stories
            if not data or data.get('deleted') or data.get('dead'):
                return None
            
            return {
                'id': story_id,
                'title': data.get('title', ''),
                'url': data.get('url', ''),
                'score': data.get('score', 0),
                'by': data.get('by', 'unknown'),
                'time': data.get('time', 0),
                'descendants': data.get('descendants', 0),
                'type': data.get('type', 'story'),
                'kids': data.get('kids', [])
            }
        except Exception as e:
            print(f"Error fetching story {story_id}: {e}")
            return None

    def fetch_hn_comments(self, kid_ids: List[int], limit: int = 5) -> List[str]:
        """Fetch top-level comments for an HN item"""
        comments = []
        if not kid_ids: return []
        
        def fetch_comment(c_id):
            try:
                resp = requests.get(f"{self.hn_api}/item/{c_id}.json", timeout=5)
                data = resp.json()
                if data and not data.get('deleted') and not data.get('dead') and data.get('text'):
                    # Clean HTML tags from HN comments
                    text = BeautifulSoup(data['text'], 'html.parser').get_text()
                    return text[:500] # Truncate long comments
                return None
            except: return None

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(fetch_comment, kid_ids[:limit]))
        
        return [r for r in results if r]


class RSSFeedScraper:
    """Fetch RSS feeds from major AI labs and publishers"""
    
    # RSS feeds from config.py
    AI_LAB_FEEDS = RSS_FEEDS
    
    def __init__(self):
        self.timeout = 10

    @staticmethod
    def _entry_datetime(entry) -> datetime | None:
        """Best-effort published datetime extraction for RSS entries."""
        try:
            if getattr(entry, "published_parsed", None):
                return datetime(*entry.published_parsed[:6])
        except Exception:
            pass
        try:
            if getattr(entry, "updated_parsed", None):
                return datetime(*entry.updated_parsed[:6])
        except Exception:
            pass

        for key in ("published", "updated"):
            raw = entry.get(key, "")
            if not raw:
                continue
            try:
                return parsedate_to_datetime(raw).replace(tzinfo=None)
            except Exception:
                continue
        return None
        
    def fetch_feed(self, feed_url: str, limit: int = None, target_date: datetime = None) -> List[Dict]:
        """Fetch entries from a single RSS feed"""
        if limit is None:
            limit = RSS_STORIES_PER_FEED
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                print(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            entries = []
            # For historical backfills, scan more entries and keep only target-day posts.
            feed_entries = feed.entries
            if target_date:
                feed_entries = feed.entries[:150]

            for entry in feed_entries:
                entry_dt = self._entry_datetime(entry)
                if target_date:
                    # Without a trustworthy timestamp we cannot map to a historical day.
                    if not entry_dt or entry_dt.date() != target_date.date():
                        continue

                entries.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:200],  # Truncate
                    'source': feed.feed.get('title', 'Unknown'),
                })

                if limit and len(entries) >= limit:
                    break
            
            return entries
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
            return []
    
    def fetch_all_feeds(self, limit_per_feed: int = 5, target_date: datetime = None) -> Dict[str, List[Dict]]:
        """Fetch from all AI lab feeds"""
        results = {}
        
        for lab_name, feed_url in self.AI_LAB_FEEDS.items():
            print(f"Fetching {lab_name}...")
            results[lab_name] = self.fetch_feed(feed_url, limit_per_feed, target_date=target_date)
        
        return results


class GenericWebScraper:
    """Fallback scraper for sites without RSS feeds"""

    @staticmethod
    def _normalize_published(raw: str) -> str:
        if not raw:
            return ""
        text = str(raw).strip()
        if not text:
            return ""
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
        except Exception:
            pass
        try:
            return parsedate_to_datetime(text).isoformat()
        except Exception:
            return ""

    @staticmethod
    def _extract_article_published(article_url: str, headers: Dict[str, str]) -> str:
        """Try hard to extract article publication date from metadata."""
        try:
            response = requests.get(article_url, timeout=10, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            date_candidates = []
            for meta in soup.find_all("meta"):
                k = (meta.get("property") or meta.get("name") or meta.get("itemprop") or "").lower()
                v = meta.get("content")
                if not v:
                    continue
                if any(token in k for token in ("published", "publish", "date", "modified", "updated", "article:published_time")):
                    date_candidates.append(v)

            for time_tag in soup.find_all("time"):
                if time_tag.get("datetime"):
                    date_candidates.append(time_tag.get("datetime"))
                txt = time_tag.get_text(strip=True)
                if txt:
                    date_candidates.append(txt)

            for candidate in date_candidates:
                normalized = GenericWebScraper._normalize_published(candidate)
                if normalized:
                    return normalized

            # Some sites (e.g., Anthropic news) render date in visible text only.
            page_text = soup.get_text(" ", strip=True)
            text_match = re.search(
                r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),\s*(\d{4})\b",
                page_text,
                re.IGNORECASE,
            )
            if text_match:
                normalized = f"{text_match.group(1).title()} {int(text_match.group(2))}, {text_match.group(3)}"
                return datetime.strptime(normalized, "%b %d, %Y").isoformat()
        except Exception:
            return ""
        return ""

    @staticmethod
    def _extract_date_from_text(text: str) -> str:
        """Fallback for listings embedding dates in link text (e.g., 'Feb 5, 2026')."""
        if not text:
            return ""
        m = re.search(
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),\s*(\d{4})\b",
            text,
            re.IGNORECASE,
        )
        if not m:
            return ""
        try:
            normalized = f"{m.group(1).title()} {int(m.group(2))}, {m.group(3)}"
            return datetime.strptime(normalized, "%b %d, %Y").isoformat()
        except Exception:
            return ""
    
    @staticmethod
    def scrape_blog(name: str, url: str, limit: int = 3) -> List[Dict]:
        """Simple heuristic scraper to find article links on a blog page"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stories = []
            base_host = urlparse(url).netloc.lower().lstrip("www.")
            
            # Find all links that look like articles
            # We look for links within h1, h2, h3 or with 'article' in class
            links = []
            for tag in soup.find_all(['a']):
                href = tag.get('href')
                if not href or href.startswith('#') or len(href) < 5:
                    continue
                
                full_url = urljoin(url, href)
                if not full_url.startswith("http"):
                    continue

                parsed = urlparse(full_url)
                host = parsed.netloc.lower().lstrip("www.")
                path = (parsed.path or "").lower()
                if host and base_host and host != base_host and not host.endswith(f".{base_host}"):
                    continue
                if any(full_url.lower().startswith(s) for s in ("mailto:", "tel:")):
                    continue
                if any(token in full_url.lower() for token in ("twitter.com", "x.com", "linkedin.com", "facebook.com", "instagram.com", "youtube.com")):
                    continue

                title = tag.get_text().strip()
                
                # Title must be reasonably long to be a headline
                if len(title) < 15:
                    # Try finding title in parent or sibling
                    parent_text = tag.parent.get_text().strip()
                    if 15 < len(parent_text) < 200:
                        title = parent_text
                
                if len(title) > 15 and full_url not in [s['link'] for s in stories]:
                    if not any(token in path for token in ("/news", "/blog", "/research", "/index")):
                        continue
                    # Tighten source-specific paths for better precision.
                    if "anthropic.com" in host and "/news/" not in path:
                        continue

                    # Filter for relevance to the lab name or generic AI terms
                    if any(x in title.lower() or x in full_url.lower() for x in ['news', 'blog', '2024', '2025', '2026', name.lower()]):
                        published = GenericWebScraper._extract_article_published(full_url, headers)
                        if not published:
                            published = GenericWebScraper._extract_date_from_text(title)
                        stories.append({
                            'title': title,
                            'link': full_url,
                            'published': published,
                            'summary': '',
                            'source': name.title()
                        })
                
                if len(stories) >= limit:
                    break
            
            return stories
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []

class NewsAggregator:
    """Combine HackerNews, RSS feeds, and Web Scraping, filter for AI content"""
    
    # Keywords from config.py
    AI_KEYWORDS = AI_KEYWORDS
    
    def __init__(self):
        self.hn_scraper = HackerNewsScraper()
        self.rss_scraper = RSSFeedScraper()
        # Import LABS_TO_SCRAPE if exists
        try:
            from config import LABS_TO_SCRAPE
            self.labs_to_scrape = LABS_TO_SCRAPE
        except ImportError:
            self.labs_to_scrape = {}
    
    def filter_ai_stories(self, stories: List[Dict]) -> List[Dict]:
        """Filter stories by AI relevance - be more permissive"""
        filtered = []
        
        # Expanded keywords for local check
        local_keywords = self.AI_KEYWORDS + ['learning', 'neural', 'robot', 'compute', 'data', 'algorithm', 'model']
        
        for story in stories:
            title = story.get('title', '').lower()
            url = story.get('url', '').lower()
            
            # Check if contains AI keywords - case insensitive
            if any(keyword.lower() in title or keyword.lower() in url for keyword in local_keywords):
                filtered.append(story)
            
        return filtered
    
    def aggregate_all(self, target_date: datetime = None) -> Dict:
        """Aggregate HackerNews + RSS feeds + Scraped Blogs"""
        print(f"Aggregating news for {target_date.date() if target_date else 'Today'}...")
        from concurrent.futures import ThreadPoolExecutor
        
        # Get HackerNews stories
        if target_date and target_date.date() < datetime.now().date():
            hn_stories = self.hn_scraper.get_historical_stories(target_date)
        else:
            hn_stories = self.hn_scraper.get_top_stories()
            
        hn_filtered = self.filter_ai_stories(hn_stories)
        
        # Get RSS feeds
        # In backfills, request more feed entries so the target day is actually discoverable.
        per_feed_limit = RSS_STORIES_PER_FEED if not target_date else 50
        rss_results = self.rss_scraper.fetch_all_feeds(per_feed_limit, target_date=target_date)
        
        # Get Scraped Blogs in parallel
        scraped_results = {}
        if self.labs_to_scrape:
            print(f"Scraping {len(self.labs_to_scrape)} blogs in parallel...")
            
            def scrape_one(item):
                name, url = item
                return name, GenericWebScraper.scrape_blog(name, url, limit=3)

            with ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(scrape_one, self.labs_to_scrape.items()))
            
            for name, stories in results:
                scraped_results[name] = stories
        
        # Combine all RSS + Scraped
        all_rss_combined = rss_results
        for name, stories in scraped_results.items():
            if name in all_rss_combined:
                all_rss_combined[name].extend(stories)
            else:
                all_rss_combined[name] = stories
        
        return {
            'timestamp': datetime.now().isoformat(),
            'hackernews': hn_filtered[:50],
            'rss_feeds': all_rss_combined,
        }


if __name__ == "__main__":
    # Test scraper
    aggregator = NewsAggregator()
    news = aggregator.aggregate_all()
    
    print(f"\nFound {len(news['hackernews'])} AI stories on HackerNews")
    print("\nTop 5 stories:")
    for story in news['hackernews'][:5]:
        print(f"  - {story['title'][:60]}... ({story['score']} points)")
    
    print("\nRSS Feed summary:")
    for feed_name, entries in news['rss_feeds'].items():
        print(f"  {feed_name}: {len(entries)} entries")
    
    # Save test output
    with open('/tmp/aggregated_news.json', 'w') as f:
        json.dump(news, f, indent=2)
    print("\nSaved to /tmp/aggregated_news.json")
