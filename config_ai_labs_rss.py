"""
AI Labs RSS Feeds Configuration
Curated and validated RSS feeds from major AI organizations

Status codes:
✓ VERIFIED - Feed works and is valid XML
? UNVERIFIED - Found but need manual testing
✗ NO_FEED - Organization doesn't provide RSS
"""

# AI LABS RSS FEEDS
AI_LAB_RSS_FEEDS = {
    # Major AI Organizations - VERIFIED
    "OpenAI News": {
        "url": "https://openai.com/news/rss.xml",
        "status": "✓ VERIFIED",
        "category": "LLM Labs",
        "notes": "Official OpenAI news RSS feed"
    },
    
    "Meta AI": {
        "url": "https://ai.meta.com/blog/feed/",  # Note: Need to verify actual RSS endpoint
        "status": "? UNVERIFIED",
        "category": "LLM Labs",
        "notes": "Meta AI research blog - May need to check for RSS"
    },
    
    "Google DeepMind": {
        "url": "https://deepmind.google/blog/feed/",  # Note: Need to verify
        "status": "? UNVERIFIED",
        "category": "LLM Labs",
        "notes": "DeepMind research blog - format needs verification"
    },
    
    "Google Research": {
        "url": "https://research.google/blog/rss/",
        "status": "✓ VERIFIED",
        "category": "LLM Labs",
        "notes": "Google Research official RSS feed"
    },
    
    "Anthropic Research": {
        "url": "https://www.anthropic.com/research/feed",  # Note: Needs verification
        "status": "? UNVERIFIED",
        "category": "LLM Labs",
        "notes": "Anthropic research page - may not have RSS"
    },
    
    "Mistral AI": {
        "url": "https://mistral.ai/news/feed/",  # Note: Not found - site has no RSS visible
        "status": "✗ NO_FEED",
        "category": "LLM Labs",
        "notes": "Mistral has news page but no official RSS feed found"
    },
    
    "Microsoft AI": {
        "url": "https://news.microsoft.com/source/topics/ai/feed/",
        "status": "? NEEDS_TEST",
        "category": "LLM Labs",
        "notes": "Microsoft AI news - needs validation"
    },
    
    "xAI (Grok)": {
        "url": "https://x.ai/news/feed",  # Note: Site has news but RSS not visible
        "status": "✗ NO_FEED",
        "category": "LLM Labs",
        "notes": "xAI has news page but no official RSS found"
    },
    
    "NVIDIA AI": {
        "url": "https://developer.nvidia.com/blog/feed",
        "status": "✓ VERIFIED",
        "category": "AI Infrastructure",
        "notes": "NVIDIA Developer blog RSS feed"
    },
    
    "NVIDIA Press": {
        "url": "https://nvidianews.nvidia.com/releases.xml",
        "status": "✓ VERIFIED",
        "category": "AI Infrastructure",
        "notes": "NVIDIA press releases RSS"
    },
    
    # Open Source & Community
    "Hugging Face Blog": {
        "url": "https://huggingface.co/blog/feed.xml",  # Note: Check if exists
        "status": "? UNVERIFIED",
        "category": "Open Source",
        "notes": "HuggingFace blog - need to verify RSS endpoint"
    },
    
    "Ollama": {
        "url": "https://ollama.ai/blog/feed",  # Note: May not have RSS
        "status": "? UNVERIFIED",
        "category": "Open Source",
        "notes": "Ollama blog - needs verification"
    },
    
    # China-based AI Labs
    "DeepSeek": {
        "url": "https://deepseek.com/news/feed",  # Note: Check actual endpoint
        "status": "? UNVERIFIED",
        "category": "LLM Labs",
        "notes": "Chinese LLM company - needs verification"
    },
    
    "Moonshot AI (Kimi)": {
        "url": "https://www.moonshot.ai/blog/feed",  # Note: Check if exists
        "status": "? UNVERIFIED",
        "category": "LLM Labs",
        "notes": "Kimi developer - needs RSS verification"
    },
    
    "MiniMax": {
        "url": "https://www.minimaxi.com/news/feed",  # Note: Check
        "status": "? UNVERIFIED",
        "category": "LLM Labs",
        "notes": "Chinese AI company - needs verification"
    },
    
    "Alibaba DAMO": {
        "url": "https://damo.alibaba.com/blog/feed",  # Note: Check if exists
        "status": "✗ NO_FEED",
        "category": "LLM Labs",
        "notes": "Alibaba Research - may not provide RSS"
    },
    
    "Baidu": {
        "url": "https://research.baidu.com/blog/feed",  # Note: Check
        "status": "✗ NO_FEED",
        "category": "LLM Labs",
        "notes": "Baidu Research - no RSS found"
    },
    
    # Commercial AI Services
    "Cohere": {
        "url": "https://cohere.com/blog/feed",  # Note: Check
        "status": "? UNVERIFIED",
        "category": "LLM Services",
        "notes": "Cohere blog - needs verification"
    },
    
    "Amazon AWS AI": {
        "url": "https://aws.amazon.com/blogs/ai/feed/",
        "status": "? NEEDS_TEST",
        "category": "AI Infrastructure",
        "notes": "AWS AI and Machine Learning blog"
    },
    
    # Academic & Research
    "BAIR (UC Berkeley)": {
        "url": "https://bair.berkeley.edu/blog/feed.xml",
        "status": "✓ VERIFIED",
        "category": "Academic",
        "notes": "Berkeley AI Research Lab"
    },
    
    "Stanford HAI": {
        "url": "https://hai.stanford.edu/news/feed",  # Note: Check
        "status": "? UNVERIFIED",
        "category": "Academic",
        "notes": "Stanford Human-Centered AI - needs verification"
    },
    
    "MIT CSAIL": {
        "url": "https://csail.mit.edu/news/feed",  # Note: Check
        "status": "? UNVERIFIED",
        "category": "Academic",
        "notes": "MIT Computer Science and AI Lab"
    },
}


# VALIDATED FEEDS (Use these now)
VALIDATED_RSS_FEEDS = {
    "openai": "https://openai.com/news/rss.xml",
    "google_research": "https://research.google/blog/rss/",
    "nvidia_developer": "https://developer.nvidia.com/blog/feed",
    "nvidia_press": "https://nvidianews.nvidia.com/releases.xml",
    "bair": "https://bair.berkeley.edu/blog/feed.xml",
    "arxiv": "https://arxiv.org/rss/cs.AI",  # Already in use
}


# FEEDS TO TEST & ADD (Need validation)
FEEDS_TO_VALIDATE = {
    "meta_ai": "https://ai.meta.com/blog/feed/",
    "deepmind": "https://deepmind.google/blog/feed/",
    "microsoft_ai": "https://news.microsoft.com/source/topics/ai/feed/",
    "huggingface": "https://huggingface.co/blog/feed.xml",
    "cohere": "https://cohere.com/blog/feed/",
    "anthropic": "https://www.anthropic.com/news/feed",
    "aws_ai": "https://aws.amazon.com/blogs/ai/feed/",
    "deepseek": "https://deepseek.com/news/feed",
}


# NO OFFICIAL RSS (Use web scraping fallback)
NO_RSS_FEEDS = {
    "mistral": "https://mistral.ai/news",
    "xai": "https://x.ai/news",
    "ollama": "https://ollama.ai/blog",
    "alibaba_damo": "https://damo.alibaba.com",
    "baidu": "https://research.baidu.com",
    "minimax": "https://www.minimaxi.com/news",
    "moonshot": "https://www.moonshot.ai/news",
}


if __name__ == "__main__":
    print("=" * 70)
    print("AI LABS RSS FEED VALIDATION REPORT")
    print("=" * 70)
    
    print("\n✓ VALIDATED FEEDS (Ready to use):")
    print("-" * 70)
    for name, url in VALIDATED_RSS_FEEDS.items():
        print(f"  {name:.<30} {url}")
    
    print("\n? FEEDS TO TEST (Please validate):")
    print("-" * 70)
    for name, url in FEEDS_TO_VALIDATE.items():
        print(f"  {name:.<30} {url}")
    
    print("\n✗ NO OFFICIAL RSS (Require web scraping):")
    print("-" * 70)
    for name, url in NO_RSS_FEEDS.items():
        print(f"  {name:.<30} {url}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("""
1. For VALIDATED feeds: Add directly to scraper config
2. For FEEDS TO TEST: Test RSS validity with feedparser
3. For NO OFFICIAL RSS: Consider web scraping or use RSS generator

Run this to validate a feed:
    import feedparser
    feed = feedparser.parse('https://example.com/feed.xml')
    print(feed.status)  # 200 = valid, 404 = not found
    """)
