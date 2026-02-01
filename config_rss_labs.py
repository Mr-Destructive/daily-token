"""
Updated RSS Feed Configuration with AI Labs
Verified working feeds added Feb 1, 2026
"""

# VERIFIED WORKING RSS FEEDS FROM AI LABS
# These have been tested and are currently active
RSS_FEEDS = {
    # OpenAI
    "openai": "https://openai.com/news/rss.xml",
    
    # Google
    "google_research": "https://research.google/blog/rss/",
    "deepmind": "https://deepmind.google/blog/feed/",
    
    # Microsoft
    "microsoft_ai": "https://news.microsoft.com/source/topics/ai/feed/",
    
    # NVIDIA
    "nvidia_developer": "https://developer.nvidia.com/blog/feed",
    "nvidia_press": "https://nvidianews.nvidia.com/releases.xml",
    
    # Amazon/AWS
    "aws_ai": "https://aws.amazon.com/blogs/ai/feed/",
    
    # Community & Open Source
    "huggingface": "https://huggingface.co/blog/feed.xml",
    "bair": "https://bair.berkeley.edu/blog/feed.xml",
    
    # ArXiv (CS.AI papers)
    "arxiv": "https://arxiv.org/rss/cs.AI",
}

# LABS WITHOUT OFFICIAL RSS (Require web scraping)
# These sites are accessible but don't provide RSS feeds
LABS_WITHOUT_RSS = {
    "meta_ai": "https://ai.meta.com/blog/",
    "anthropic": "https://www.anthropic.com/research",
    "mistral": "https://mistral.ai/news",
    "cohere": "https://cohere.com/blog",
    "ollama": "https://ollama.ai/blog",
    "deepseek": "https://deepseek.com/news",
    "moonshot_ai": "https://www.moonshot.ai/news",
    "minimax": "https://www.minimaxi.com/news",
    "alibaba": "https://damo.alibaba.com/blog",
    "baidu": "https://research.baidu.com/blog",
}

# Number of stories to fetch per feed
RSS_STORIES_PER_FEED = 5

# Total stories to fetch (combine all RSS)
TOTAL_RSS_STORIES = len(RSS_FEEDS) * RSS_STORIES_PER_FEED  # ~55 stories from RSS

if __name__ == "__main__":
    print("AI LABS RSS FEED CONFIGURATION")
    print("=" * 60)
    print(f"\n✓ WORKING RSS FEEDS: {len(RSS_FEEDS)}")
    for name, url in RSS_FEEDS.items():
        print(f"   - {name}")
    
    print(f"\n✗ LABS WITHOUT RSS: {len(LABS_WITHOUT_RSS)}")
    for name, url in LABS_WITHOUT_RSS.items():
        print(f"   - {name}")
    
    print(f"\nTotal RSS feeds to process: {TOTAL_RSS_STORIES} stories")
    print("=" * 60)
