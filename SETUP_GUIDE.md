# Setup Guide - AI Labs RSS Feeds + LLM Router

## What You Got

### 1. LLM Router (Smart Model Selection)
- **Files:** `llm_router.py`, `processor_with_router.py`
- **Purpose:** Randomly select between multiple models
- **Models:** Qwen3-235B, GPT-OSS-120B, DeepSeek-V3.2, Llama-3.1-70B
- **Cost:** ~$0.01-0.02/day for your 25 stories

### 2. AI Labs RSS Feeds (9 Verified Sources)
- **Files:** `config_rss_labs.py`, `validate_rss_feeds.py`
- **Sources:** OpenAI, Google, Microsoft, NVIDIA, AWS, HuggingFace, BAIR
- **Plus:** Identified 10+ labs needing web scraping

### 3. Validation Tools
- **File:** `validate_rss_feeds.py`
- **Function:** Test all feeds, report status, export working configs

---

## Quick Start

### Step 1: Update Your Scraper Config

Edit `config.py` and add the verified feeds:

```python
from config_rss_labs import RSS_FEEDS

# This now includes:
# - OpenAI
# - Google Research + DeepMind  
# - Microsoft AI
# - NVIDIA (2 feeds)
# - AWS AI
# - HuggingFace
# - BAIR (Berkeley)
```

### Step 2: Switch to LLM Router

In `main.py`, replace:

```python
# OLD:
from processor import NewsProcessor
processor = NewsProcessor()

# NEW:
from processor_with_router import NewsProcessorWithRouter
processor = NewsProcessorWithRouter(prefer_cheap=True)
```

### Step 3: Test Everything

```bash
# Test the router alone
python backend/llm_router.py

# Test the processor with router
python backend/processor_with_router.py

# Validate RSS feeds
python validate_rss_feeds.py

# Run full pipeline
python backend/main.py
```

---

## Costs

### With LLM Router
```
Daily:  $0.01 - $0.02 (randomized models)
Monthly: $0.30 - $0.60
```

### With New AI Lab Feeds
```
Additional daily:  +$0.005
Additional monthly: +$0.15
```

### Total Estimated
```
Daily:   $0.015 - $0.025
Monthly: $0.45 - $0.75
Still completely affordable!
```

---

## Files Overview

```
backend/
├── llm_router.py                  # Smart model selector
├── processor_with_router.py       # Updated processor using router
├── scraper.py                     # Existing (no changes needed)
├── main.py                        # Update to use router processor
├── config.py                      # Update RSS feeds list
└── processor.py                   # Keep as fallback

Root/
├── config_rss_labs.py             # Production RSS config
├── config_ai_labs_rss.py          # Detailed documentation
├── validate_rss_feeds.py          # Feed validation script
├── RSS_FEEDS_SUMMARY.md           # Complete reference
└── AI_LABS_RSS_SUMMARY.txt        # This summary
```

---

## Model Selection Strategy

The router uses weighted random selection:

```
Qwen3-235B-A22B:     40% (best accuracy/price)
GPT-OSS-120B:        35% (fast, proven stable)
DeepSeek-V3.2:       15% (best reasoning)
Llama-3.1-70B:       10% (fallback, reliable)
```

This ensures:
- Cheap models run most (save money)
- Expensive models run rarely (high quality checks)
- Balanced accuracy + cost

---

## Monitoring

Check usage stats after each run:

```python
# In processor output
Cost Summary:
- Total calls: 50
- Total cost: $0.012
- Avg per story: $0.00024
```

The router logs all usage to `output/llm_usage.json`.

---

## RSS Feed Status

**Working (9):**
- OpenAI, Google (2), Microsoft, NVIDIA (2), AWS, HuggingFace, BAIR

**Need Scraping (7):**
- Meta, Anthropic, Mistral, Ollama, DeepSeek, MiniMax, Moonshot

**Not Tested (5):**
- Cohere, xAI, Alibaba, Baidu, Qwen

---

## Advanced: Add Web Scraping for Missing Labs

For labs without RSS, implement BeautifulSoup scraping:

```python
# Add to scraper.py

def scrape_meta_blog():
    from bs4 import BeautifulSoup
    url = "https://ai.meta.com/blog/"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    # Parse posts...

def scrape_anthropic_blog():
    url = "https://www.anthropic.com/research"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    # Parse posts...
```

---

## Troubleshooting

**Router not working?**
```
Check: Is HF_TOKEN in .env?
Run: python validate_rss_feeds.py
```

**Some feeds failing?**
```
Run: python validate_rss_feeds.py
Check: RSS_FEEDS_SUMMARY.md for known issues
```

**High costs?**
```
Adjust weights in llm_router.py
Reduce num_workers in processor
Use cheaper models (Llama-3.1-8B)
```

---

## Next Steps

**Phase 1:** ✓ Router + 9 RSS feeds working
**Phase 2:** Add web scraping for Meta, Anthropic, Ollama
**Phase 3:** Monitor costs and optimize model selection

---

**Created:** Feb 1, 2026  
**Tested:** All 9 RSS feeds verified working
**Cost:** ~$0.50/month additional

Enjoy your AI newspaper with more sources and smarter model selection! 🚀
