"""
RSS Feed Validator
Tests all AI lab feeds to validate they work
"""
import feedparser
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config_ai_labs_rss import VALIDATED_RSS_FEEDS, FEEDS_TO_VALIDATE, NO_RSS_FEEDS


class RSSValidator:
    """Validate and test RSS feeds"""
    
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.results = {
            "valid": [],
            "invalid": [],
            "timeout": [],
            "not_found": []
        }
    
    def validate_feed(self, name: str, url: str) -> dict:
        """
        Validate a single RSS feed
        
        Returns:
            {name, url, status, entries, valid}
        """
        try:
            # First try direct HTTP
            response = requests.head(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 404:
                return {
                    "name": name,
                    "url": url,
                    "status": 404,
                    "valid": False,
                    "error": "Not found"
                }
            
            # Try parsing as RSS
            feed = feedparser.parse(url)
            
            if feed.status == 200 or (hasattr(feed, 'entries') and len(feed.entries) > 0):
                num_entries = len(feed.get('entries', []))
                return {
                    "name": name,
                    "url": url,
                    "status": 200,
                    "valid": True,
                    "entries": num_entries,
                    "title": feed.feed.get('title', 'Unknown')
                }
            else:
                return {
                    "name": name,
                    "url": url,
                    "status": feed.status or "unknown",
                    "valid": False,
                    "error": f"Feed status: {feed.status}"
                }
        
        except requests.Timeout:
            return {
                "name": name,
                "url": url,
                "status": "timeout",
                "valid": False,
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "name": name,
                "url": url,
                "status": "error",
                "valid": False,
                "error": str(e)
            }
    
    def validate_all(self, feeds_dict: dict, category: str = "Unknown") -> list:
        """
        Validate multiple feeds in parallel
        
        Args:
            feeds_dict: {name: url, ...}
            category: Label for categorizing results
        
        Returns:
            List of validation results
        """
        results = []
        
        print(f"\n[{category}] Validating {len(feeds_dict)} feeds...")
        print("-" * 70)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.validate_feed, name, url): name 
                for name, url in feeds_dict.items()
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                status_symbol = "✓" if result["valid"] else "✗"
                print(f"  {status_symbol} {result['name']:.<30} ", end="")
                
                if result["valid"]:
                    print(f"OK ({result.get('entries', 0)} entries)")
                    self.results["valid"].append(result)
                else:
                    print(f"{result.get('error', 'Unknown error')}")
                    if result["status"] == 404:
                        self.results["not_found"].append(result)
                    elif result["status"] == "timeout":
                        self.results["timeout"].append(result)
                    else:
                        self.results["invalid"].append(result)
        
        return results
    
    def test_all(self):
        """Test all feeds and generate report"""
        print("\n" + "=" * 70)
        print("RSS FEED VALIDATION REPORT")
        print("=" * 70)
        
        # Test validated feeds
        self.validate_all(VALIDATED_RSS_FEEDS, "VALIDATED FEEDS")
        
        # Test feeds to validate
        self.validate_all(FEEDS_TO_VALIDATE, "FEEDS TO TEST")
        
        # Test feeds without RSS (just check if URLs exist)
        print("\n[NO OFFICIAL RSS] Checking if fallback URLs exist...")
        print("-" * 70)
        for name, url in NO_RSS_FEEDS.items():
            try:
                response = requests.head(url, timeout=self.timeout, allow_redirects=True)
                if response.status_code < 400:
                    print(f"  ✓ {name:.<30} Accessible (status: {response.status_code})")
                else:
                    print(f"  ✗ {name:.<30} Not accessible (status: {response.status_code})")
            except:
                print(f"  ✗ {name:.<30} Error accessing URL")
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        total = sum(len(v) for v in self.results.values())
        
        print(f"\n✓ VALID FEEDS: {len(self.results['valid'])}/{total}")
        for result in self.results["valid"]:
            print(f"   {result['name']:.<40} {result.get('entries', 0)} entries")
        
        if self.results["invalid"]:
            print(f"\n⚠ INVALID/ERROR: {len(self.results['invalid'])}/{total}")
            for result in self.results["invalid"]:
                print(f"   {result['name']:.<40} {result.get('error', 'Unknown')}")
        
        if self.results["not_found"]:
            print(f"\n✗ NOT FOUND: {len(self.results['not_found'])}/{total}")
            for result in self.results["not_found"]:
                print(f"   {result['name']:.<40} (404)")
        
        if self.results["timeout"]:
            print(f"\n⏱ TIMEOUT: {len(self.results['timeout'])}/{total}")
            for result in self.results["timeout"]:
                print(f"   {result['name']:.<40}")
        
        print("\n" + "=" * 70)
        print(f"TOTAL WORKING: {len(self.results['valid'])}/{total}")
        print("=" * 70)
    
    def export_config(self, output_file: str = "validated_feeds.py"):
        """Export validated feeds to Python config"""
        
        valid_feeds = {r["name"]: r["url"] for r in self.results["valid"]}
        
        config_content = f'''"""Auto-generated from RSS feed validation"""

WORKING_RSS_FEEDS = {{
'''
        
        for name, url in valid_feeds.items():
            config_content += f'    "{name}": "{url}",\n'
        
        config_content += '''}\n'''
        
        with open(output_file, 'w') as f:
            f.write(config_content)
        
        print(f"\n✓ Exported {len(valid_feeds)} working feeds to {output_file}")


if __name__ == "__main__":
    validator = RSSValidator(timeout=10)
    
    # Run validation
    validator.test_all()
    validator.print_summary()
    
    # Export working feeds
    validator.export_config("/tmp/working_feeds.py")
    
    print("\nNext: Add working feeds to your scraper config!")
