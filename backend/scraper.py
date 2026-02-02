"""HackerNews scraper with RSS feed support for major AI labs"""
import requests
import feedparser
from typing import List, Dict
from datetime import datetime
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Import configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from config import AI_KEYWORDS, HACKERNEWS_STORY_LIMIT, RSS_FEEDS, RSS_STORIES_PER_FEED
except ImportError:
    AI_KEYWORDS = ['ai', 'llm', 'machine learning', 'deep learning']
    HACKERNEWS_STORY_LIMIT = 30
    RSS_FEEDS = {'arxiv': 'http://arxiv.org/rss/cs.AI'}
    RSS_STORIES_PER_FEED = 5

class ImageFetcher:
    """Fetch potential images from URLs for AI review"""
    
    @staticmethod
    def get_candidate_images(url: str) -> List[str]:
        """Extract all potential raster cover images from URL (SEO, OpenGraph, Thumbnails)"""
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
            
            # Helper to check if URL is a valid raster image
            def is_valid(img_url):
                img_url = img_url.lower()
                # Must be one of our extensions
                if not any(img_url.endswith(ext) for ext in valid_exts):
                    # Also check if it's a dynamic URL that might be an image but lacks extension
                    if '?' not in img_url and not any(ext in img_url for ext in valid_exts):
                        return False
                # Filter out obvious small icons/logos even if they are PNG
                if any(x in img_url for x in ['icon', 'logo', 'avatar', 'sprite', 'pixel', 'tracker', 'ad', 'btn', 'nav']):
                    return False
                return True

            # 1. OpenGraph Image
            for og in soup.find_all('meta', property=re.compile(r'^og:image', re.I)):
                c = og.get('content')
                if c and is_valid(c):
                    candidates.append(urljoin(url, c))
            
            # 2. Twitter Image
            for tw in soup.find_all('meta', name=re.compile(r'^twitter:image', re.I)):
                c = tw.get('content')
                if c and is_valid(c):
                    candidates.append(urljoin(url, c))
            
            # 3. Schema.org Image
            for schema in soup.find_all('meta', itemprop='image'):
                c = schema.get('content')
                if c and is_valid(c):
                    candidates.append(urljoin(url, c))

            # 4. Article Thumbnails
            for link in soup.find_all('link', rel=re.compile(r'image_src|thumbnail', re.I)):
                c = link.get('href')
                if c and is_valid(c):
                    candidates.append(urljoin(url, c))

            # 5. Large images in article body
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original-src')
                if not src: continue
                
                full_url = urljoin(url, src)
                if is_valid(full_url):
                    candidates.append(full_url)
            
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
            cutoff_time = time.time() - (24 * 3600)
            
            stories = []
            # We check up to 400 unique candidates to find the best AI content
            for story_id in unique_ids[:400]:
                story = self._get_story(story_id)
                
                # Strict 24h filter
                if story and story.get('time', 0) > cutoff_time:
                    # We only keep stories with a URL (actual content)
                    if story.get('url'):
                        stories.append(story)
                
                # If we have a massive pool, stop early to keep the LLM phase fast
                if len(stories) >= 100: 
                    break
            
            return stories
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
            }
        except Exception as e:
            print(f"Error fetching story {story_id}: {e}")
            return None


class RSSFeedScraper:
    """Fetch RSS feeds from major AI labs and publishers"""
    
    # RSS feeds from config.py
    AI_LAB_FEEDS = RSS_FEEDS
    
    def __init__(self):
        self.timeout = 10
        
    def fetch_feed(self, feed_url: str, limit: int = None) -> List[Dict]:
        """Fetch entries from a single RSS feed"""
        if limit is None:
            limit = RSS_STORIES_PER_FEED
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                print(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            entries = []
            for entry in feed.entries[:limit]:
                entries.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:200],  # Truncate
                    'source': feed.feed.get('title', 'Unknown'),
                })
            
            return entries
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
            return []
    
    def fetch_all_feeds(self, limit_per_feed: int = 5) -> Dict[str, List[Dict]]:
        """Fetch from all AI lab feeds"""
        results = {}
        
        for lab_name, feed_url in self.AI_LAB_FEEDS.items():
            print(f"Fetching {lab_name}...")
            results[lab_name] = self.fetch_feed(feed_url, limit_per_feed)
        
        return results


class GenericWebScraper:
    """Fallback scraper for sites without RSS feeds"""
    
    @staticmethod
    def scrape_blog(name: str, url: str, limit: int = 3) -> List[Dict]:
        """Simple heuristic scraper to find article links on a blog page"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stories = []
            
            # Find all links that look like articles
            # We look for links within h1, h2, h3 or with 'article' in class
            links = []
            for tag in soup.find_all(['a']):
                href = tag.get('href')
                if not href or href.startswith('#') or len(href) < 5:
                    continue
                
                full_url = urljoin(url, href)
                title = tag.get_text().strip()
                
                # Title must be reasonably long to be a headline
                if len(title) < 15:
                    # Try finding title in parent or sibling
                    parent_text = tag.parent.get_text().strip()
                    if 15 < len(parent_text) < 200:
                        title = parent_text
                
                if len(title) > 15 and full_url not in [s['link'] for s in stories]:
                    # Filter for relevance to the lab name or generic AI terms
                    if any(x in title.lower() or x in full_url.lower() for x in ['news', 'blog', '2024', '2025', '2026', name.lower()]):
                        stories.append({
                            'title': title,
                            'link': full_url,
                            'published': 'Recently',
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
    
    def aggregate_all(self) -> Dict:
        """Aggregate HackerNews + RSS feeds + Scraped Blogs"""
        print("Aggregating news...")
        
        # Get HackerNews stories
        hn_stories = self.hn_scraper.get_top_stories()
        hn_filtered = self.filter_ai_stories(hn_stories)
        
        # Get RSS feeds
        rss_results = self.rss_scraper.fetch_all_feeds(RSS_STORIES_PER_FEED)
        
        # Get Scraped Blogs
        scraped_results = {}
        if self.labs_to_scrape:
            print(f"Scraping {len(self.labs_to_scrape)} blogs without RSS...")
            for name, url in self.labs_to_scrape.items():
                scraped_results[name] = GenericWebScraper.scrape_blog(name, url, limit=3)
        
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
