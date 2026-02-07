"""
Configuration file for The Daily Token newspaper.

This is the single source of truth for all customizable settings.
Edit this file to customize your newspaper without touching core code.
"""

# ============================================================================
# PAGE & SECTION CATEGORIES
# ============================================================================
PAGE_CATEGORIES = {
    1: "Breaking Vectors",
    2: "Model Architectures",
    3: "Neural Horizons",
    4: "Lab Outputs",
    5: "Inference Corner",
    6: "AI & LLM Overview",
    7: "Model Release History",
    8: "Top Insights & Advice",
    9: "Lab Updates & Dark Side"
}

PAGES_CONFIG = {
    1: {"title": "The Front Page", "categories": [1, 2, 3, 4, 5]},
    2: {"title": "AI & LLM Overview", "categories": [6]},
    3: {"title": "Model Release History", "categories": [7]},
    4: {"title": "Top Insights & Advice", "categories": [8]},
    5: {"title": "Lab Updates & Dark Side", "categories": [9]}
}

# Alternative theme examples (uncomment to use):
# PAGE_CATEGORIES = {
#     1: "Hot Takes",
#     2: "Papers & Research",
#     3: "Robot World",
#     4: "Who's Hiring",
#     5: "Tea Leaves"
# }

# PAGE_CATEGORIES = {
#     1: "Breaking News",
#     2: "Model Releases",
#     3: "Vision Systems",
#     4: "Company Moves",
#     5: "Analysis & Opinion"
# }


# ============================================================================
# AI KEYWORDS - Stories matching these will be included
# ============================================================================
AI_KEYWORDS = [
    'ai', 'llm', 'language model', 'transformer', 'neural', 'machine learning',
    'deep learning', 'gpt', 'claude', 'gemini', 'llama', 'ml', 'nlp',
    'vision', 'robotics', 'world model', 'diffusion', 'generative',
    'training', 'inference', 'gpu', 'tpu', 'quantization', 'alignment',
    'prompt', 'embeddings', 'attention', 'multimodal', 'agent', 'reasoning'
]


# ============================================================================
# SCRAPER CONFIGURATION
# ============================================================================
RSS_FEEDS = {
    # AI Hubs
    "openai": "https://openai.com/news/rss.xml",
    "anthropic": "https://www.anthropic.com/feed.xml",
    "deepmind": "https://deepmind.google/blog/feed/",
    "huggingface": "https://huggingface.co/blog/feed.xml",
    
    # Tech News AI Sections
    "techcrunch_ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "venturebeat_ai": "https://venturebeat.com/category/ai/feed/",
    "verge_ai": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "wired_ai": "https://www.wired.com/feed/category/ai/latest/rss",
    "zdnet_ai": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    
    # Research
    "arxiv_ai": "https://arxiv.org/rss/cs.AI",
    "bair": "https://bair.berkeley.edu/blog/feed.xml",
}

# Specific keywords to force Model Release categorization (Page 3)
RELEASE_KEYWORDS = [
    "release", "launch", "unveils", "announces", "weights", "v3", "v4", "v5", 
    "checkpoint", "available now", "open source", "opus", "sonnet", "haiku", "gemma"
]


# ============================================================================
# PROCESSOR CONFIGURATION
# ============================================================================
PROCESSOR_CONFIG = {
    'llm': {
        'primary': 'openrouter',
        'fallback': 'meta-ai',
        'openrouter_model': 'openrouter/free',
        'timeout': 30,
        'categorization_confidence_threshold': 0.7,
    },
    'processing': {
        'batch_size': 10,
        'max_workers': 1,  # Set to higher for parallel processing
    }
}


# ============================================================================
# EXPORTER CONFIGURATION
# ============================================================================
EXPORTER_CONFIG = {
    'formats': ['html', 'json', 'markdown', 'rss'],
    'output_directory': './output/current',
    'image_directory': './output/images',
    'include_images': True,
    'include_metadata': True,
    'stories_per_page': 5,  # How many stories per page in newspaper
}


# ============================================================================
# FRONTEND CONFIGURATION
# ============================================================================
FRONTEND_CONFIG = {
    'title': 'Daily Tokens',
    'description': 'The AI world\'s daily news. Breaking vectors. Model architectures. Neural horizons.',
    'theme': 'dark',
    'colors': {
        'primary': '#00d4ff',
        'dark': '#1a1a2e',
        'darker': '#0f0f1e',
        'accent': '#533483',
        'light': '#f8f9fa'
    },
    'animations': {
        'page_flip_duration': 0.6,
        'page_flip_easing': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
    }
}


# ============================================================================
# DEPLOYMENT CONFIGURATION
# ============================================================================
DEPLOYMENT_CONFIG = {
    'github_actions': {
        'enabled': True,
        'schedule': '0 8 * * *',  # 8 AM UTC daily
        'auto_commit': True,
        'auto_push': True
    },
    'netlify': {
        'enabled': False,
        'publish_directory': 'output/current'
    },
    'github_pages': {
        'enabled': False,
        'branch': 'main'
    }
}


# ============================================================================
# Helper functions to access config
# ============================================================================

def get_page_categories():
    """Get page categories dictionary."""
    return PAGE_CATEGORIES


def get_page_name(page_num):
    """Get name of a specific page."""
    return PAGE_CATEGORIES.get(page_num, f"Page {page_num}")


def get_all_page_names():
    """Get list of all page names in order."""
    return [PAGE_CATEGORIES[i] for i in range(1, 6)]


def validate_config():
    """Validate configuration."""
    assert len(PAGE_CATEGORIES) == 5, "Must have exactly 5 pages"
    assert all(isinstance(k, int) and k in range(1, 6) for k in PAGE_CATEGORIES.keys()), \
        "Page numbers must be 1-5"
    assert all(isinstance(v, str) and len(v) > 0 for v in PAGE_CATEGORIES.values()), \
        "All page names must be non-empty strings"
    return True
