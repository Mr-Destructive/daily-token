"""
═══════════════════════════════════════════════════════════════════════════════
                          DAILY TOKENS - CONFIGURATION
                    Edit this file to customize everything
═══════════════════════════════════════════════════════════════════════════════

This is the ONLY file you need to edit to customize:
  • Page category names
  • All text/headings/prompts
  • Colors and styling
  • Update schedule
  • RSS feeds
  • Story counts
  • LLM behavior

Everything else works automatically.
"""
import os

# =============================================================================
# PAGE & SECTION CATEGORIES
# =============================================================================
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

# Theme examples to copy/paste:
# CASUAL:     {"Hot Takes", "Papers Worth Reading", "Robot News", "Who's Hiring", "Tea Leaves"}
# ACADEMIC:   {"Papers & Preprints", "Benchmarks", "Systems", "Lab Announcements", "Research Analysis"}
# BUSINESS:   {"Breaking News", "Product Launches", "Acquisitions", "Executive Moves", "Market Analysis"}
# STARTUP:    {"Breaking News", "New Tools", "Vision & Robotics", "Funding & Moves", "What's Next"}


# =============================================================================
# SITE BRANDING - Headlines, titles, descriptions
# =============================================================================

SITE_TITLE = "The Daily Token"
SITE_TAGLINE = "The AI world's daily news. Breaking vectors. Model architectures. Neural horizons."
# Base URL for RSS and links
SITE_URL = os.environ.get("SITE_URL", "https://dev.meetgor.com/daily-token")
SITE_DESCRIPTION = "Your daily digest of AI breakthroughs, model releases, research, and predictions. Curated from HackerNews and major AI labs. Delivered fresh every morning."

# Landing page hero text
HERO_HEADLINE = "The Daily Token"
HERO_SUBHEADING = "The AI world's daily news. Breaking vectors. Model architectures. Neural horizons."
HERO_DESCRIPTION = "Your daily digest of AI breakthroughs, model releases, research, and predictions. Curated from HackerNews and major AI labs. Delivered fresh every morning."

# Newsletter header
NEWSPAPER_HEADER = "THE DAILY TOKEN"
PUBLICATION_TAGLINE = "The AI world's daily news"


# =============================================================================
# LANDING PAGE - Feature titles and descriptions
# =============================================================================

FEATURES = {
    "Newspaper Format": "Experience news the way it was meant to be read—beautifully formatted like a digital newspaper with smooth page-flip animations.",
    "AI-Curated": "Our LLM automatically categorizes and summarizes thousands of stories daily, so you get only the most relevant AI news.",
    "Well-Sourced": "Every story links to HackerNews and original sources. Breaking vectors from OpenAI, Anthropic, Meta, DeepMind, and leading AI labs.",
    "Fully Responsive": "Read on desktop, tablet, or mobile. The newspaper adapts to any screen size while maintaining its elegant design.",
    "Multiple Formats": "Download as HTML, JSON, or Markdown. Perfect for archiving, sharing, or integrating into your workflow.",
    "RSS Feed": "Subscribe to our RSS feed and get daily newspapers delivered straight to your reader."
}

DOWNLOAD_FORMATS = {
    "HTML": "Beautiful webpage with interactive page flip",
    "Markdown": "Clean, readable text format for note-taking",
    "JSON": "Structured data for custom integration",
    "RSS Feed": "Subscribe in your favorite RSS reader"
}


# =============================================================================
# LLM PROMPTS - Customize how AI categorizes and summarizes stories
# =============================================================================

# Categorization prompt - used to assign stories to pages
CATEGORIZATION_PROMPT = """Categorize this news story into ONE of these categories:
0. Irrelevant / Not AI / Generic Tech / Crypto / Politics (FILTER OUT)
{categories}

Story Title: {title}
URL: {url}
Summary: {summary}

RESPOND WITH ONLY THIS FORMAT - NO EXPLANATION:
1|0.95

Where first number is category (0-5) and second is confidence (0.0-1.0).
If the story is not strictly related to AI/ML (e.g. general tech, politics, crypto, or vague science), select 0.
"""

# Summarization prompt - used to create headlines and summaries
SUMMARIZATION_PROMPT = """You are a professional tech news editor for a high-end AI newspaper. 
Write a concise, engaging newspaper headline and a 1-2 sentence summary.

STRICT RULES:
- NO EMOJIS in the headline or summary.
- The headline must be professional and academic yet engaging.

IMAGE SELECTION:
You will be provided with a list of image URLs found in the article. 
Select the ONE URL that best represents the article's core content as a cover image.
If none of the images are relevant or of high quality (e.g., icons, ads, logos), respond with "NONE".

Article Title: {title}
Category: {category}
Summary: {summary}
Available Image URLs: {image_urls}

Format your response exactly like this:
HEADLINE: [Your Headline]
SUMMARY: [Your 1-2 sentence summary]
SIGNIFICANCE_SCORE: [1-100]
SELECTED_IMAGE_URL: [The chosen URL or NONE]
IMAGE_LAYOUT: [WIDE, TALL, or SQUARE]
"""


# =============================================================================
# AI KEYWORDS - Stories must match these to be included
# =============================================================================
# Add/remove keywords that trigger inclusion in the newspaper

AI_KEYWORDS = [
    # Core AI/ML terms
    'ai', 'artificial intelligence', 'machine learning', 'deep learning', 'ml', 'dl',
    
    # Models and architectures
    'llm', 'language model', 'foundation model', 'transformer', 'neural network', 
    'gpt', 'claude', 'gemini', 'llama', 'mistral', 'qwen', 'deepseek',
    
    # AI techniques
    'training', 'inference', 'fine-tuning', 'prompting', 'rag',
    'embeddings', 'attention', 'quantization', 'distillation',
    
    # Vision and multimodal
    'vision', 'computer vision', 'multimodal', 'diffusion',
    'generative', 'generative ai', 'stable diffusion', 'dalle',
    
    # Robotics and embodied AI
    'robotics', 'robot', 'embodied', 'world model',
    
    # AI research areas
    'nlp', 'natural language', 'reasoning', 'agent', 'alignment', 'interpretability',
    'safety', 'ethics', 'bias', 'hallucination',
    
    # Hardware (only if AI specific)
    'gpu', 'tpu', 'cuda', 'h100', 'b200', 'npu',
    
    # Companies/labs
    'openai', 'anthropic', 'deepmind', 'mistral ai', 'hugging face', 'cohere'
]


# =============================================================================
# NEWS SOURCES - Where to fetch from
# =============================================================================

# HackerNews scraping
HACKERNEWS_STORY_LIMIT = 100  # Expand candidate pool significantly

# RSS feeds - only working ones (many lab feeds have broken XML)
RSS_FEEDS = {
    "openai": "https://openai.com/news/rss.xml",
    "anthropic": "https://www.anthropic.com/feed.xml",
    "deepmind": "https://deepmind.google/blog/feed/",
    "huggingface": "https://huggingface.co/blog/feed.xml",
    "techcrunch_ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "venturebeat_ai": "https://venturebeat.com/category/ai/feed/",
    "verge_ai": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "wired_ai": "https://www.wired.com/feed/category/ai/latest/rss",
    "zdnet_ai": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    "arxiv_ai": "https://arxiv.org/rss/cs.AI",
    "bair": "https://bair.berkeley.edu/blog/feed.xml",
}

# LABS TO SCRAPE (If RSS fails)
LABS_TO_SCRAPE = {
    "anthropic": "https://www.anthropic.com/news",
    "mistral": "https://mistral.ai/news",
    "cohere": "https://cohere.com/blog",
    "deepseek": "https://deepseek.com/news",
    "moonshot": "https://www.moonshot.ai/news",
    "alibaba": "https://damo.alibaba.com/blog",
    "baidu": "https://research.baidu.com/blog",
    "xai": "https://x.ai/blog",
    "ollama": "https://ollama.com/blog"
}

RSS_STORIES_PER_FEED = 5  # Stories per feed


# =============================================================================
# OUTPUT - How to format the newspaper
# =============================================================================

STORIES_PER_PAGE = 5  # How many stories appear on each page

INCLUDE_IMAGES = True  # Generate SVG placeholder images

INCLUDE_METADATA = True  # Include generation info in output

EXPORT_FORMATS = ['html', 'json', 'markdown', 'rss']  # What to generate


# =============================================================================
# STYLING - Colors and design
# =============================================================================

COLORS = {
    'primary': '#00d4ff',        # Main accent color (cyan)
    'dark': '#1a1a2e',           # Dark background
    'darker': '#0f0f1e',         # Darker background
    'accent': '#533483',         # Secondary accent (purple)
    'light': '#f8f9fa'           # Light background
}

# Animation speed (in seconds)
PAGE_FLIP_DURATION = 0.6

# Easing function for page flip
PAGE_FLIP_EASING = 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'


# =============================================================================
# AUTOMATION - GitHub Actions schedule
# =============================================================================

# Cron expression - when to run daily
# Format: "minute hour day month day-of-week"
# Examples:
#   "0 8 * * *"           = 8 AM UTC every day
#   "0 9 * * MON-FRI"     = 9 AM UTC weekdays only
#   "30 6,18 * * *"       = 6:30 AM and 6:30 PM UTC
# Use https://crontab.guru to generate your schedule

DAILY_SCHEDULE = "0 8 * * *"  # 8 AM UTC daily


# =============================================================================
# LLM CONFIGURATION - Which AI models to use
# =============================================================================

# Decision Hierarchy:
# 1. Kimi (Moonshot K2.5) - Primary Decision Maker
# 2. OpenRouter High-Reasoning Free Models (Fallback 1)
# 3. Meta-AI / Gemini (Fallback 2)

PRIMARY_LLM = "kimi"
KIMI_MODEL = "moonshot-v1-8k" # Kimi K2.5 endpoint usually follows this or specific deployment

# OpenRouter Free Models ranked by reasoning capability
OPENROUTER_REASONING_MODELS = [
    "deepseek/deepseek-r1:free",       # Best for reasoning
    "google/gemini-2.0-flash-exp:free", # Fast & Intelligent
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat:free",
    "mistralai/mistral-small-24b-instruct-2501:free"
]

# Gemini model for images/fallback
GEMINI_MODEL = "gemini-2.5-flash-image"

# Parallel processing: number of concurrent LLM calls (categorize + summarize per story)
PROCESSING_MAX_WORKERS = 1  # Set to 1 to avoid rate limits (was 5)

LLM_TIMEOUT = 30  # Seconds before giving up on LLM response

CONFIDENCE_THRESHOLD = 0.8  # Stricter: Only use categorizations above 80% confidence


# =============================================================================
# PATHS - Where to save output
# =============================================================================

OUTPUT_DIRECTORY = "./output/current"
IMAGE_DIRECTORY = "./output/images"


# =============================================================================
# NO EDITS BELOW THIS LINE - Helper functions
# =============================================================================

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
