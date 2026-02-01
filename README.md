# Daily Tokens

The AI world's daily newspaper. Breaking vectors. Model architectures. Neural horizons.

Automatically generates a beautiful 5-page digital newspaper with AI news from HackerNews and major AI labs, powered by LLMs, deployed daily via GitHub Actions.

> **Quick tip:** All customization happens in `config.py` at the root. Edit that one file to change page names, colors, prompts, RSS feeds, schedule, and everything else.

## 📰 What You Get

- **5-page daily newspaper** (customizable page names)
- **AI-curated news** from HackerNews API + 7+ RSS feeds
- **LLM-powered** categorization & summaries (Gemini + Meta-AI)
- **Beautiful UI** with 3D page-flip animations
- **Multiple formats**: HTML (interactive), JSON, Markdown, RSS
- **Fully automated** - runs daily at 8 AM UTC via GitHub Actions
- **Deploy anywhere** - Netlify, GitHub Pages, or self-hosted

## ⚡ Quick Start (5 minutes)

```bash
# Setup
bash setup.sh
source venv/bin/activate

# Configure
nano .env
# Add: GEMINI_API_KEY=your_key_here

# Test locally
python backend/test_pipeline.py

# Deploy
git push origin main
# Add GEMINI_API_KEY to GitHub Secrets → done!
```

## 📄 Pages

Default page names (easily customizable):

1. **Breaking Vectors** - Top AI news
2. **Model Architectures** - LLM releases, benchmarks, papers
3. **Neural Horizons** - Vision systems, world models, robotics
4. **Lab Outputs** - Announcements from OpenAI, Anthropic, Meta, etc.
5. **Inference Corner** - Analysis, predictions, infrastructure news

## 🎯 Customize Everything (30 seconds)

**One file to rule them all:** `config.py` at the root

Edit `config.py` to change:

```python
# Page names
PAGE_CATEGORIES = {
    1: "Your Page 1",
    2: "Your Page 2",
    3: "Your Page 3",
    4: "Your Page 4",
    5: "Your Page 5"
}

# Site title and text
SITE_TITLE = "Daily Tokens"
SITE_TAGLINE = "Your custom tagline"

# Colors
COLORS = {
    'primary': '#00d4ff',
    'dark': '#1a1a2e',
}

# Update schedule (cron format)
DAILY_SCHEDULE = "0 8 * * *"  # 8 AM UTC

# RSS feeds
RSS_FEEDS = {
    'openai': 'https://openai.com/feed.xml',
    'your_lab': 'https://your-lab.com/feed.xml',
}

# And much more...
```

Examples:
- `{"Hot Takes", "Papers Worth Reading", "Robot News", "Who's Hiring", "Tea Leaves"}`
- `{"Breaking News", "Product Launches", "Funding", "Executive Moves", "Market Analysis"}`

Changes apply everywhere automatically (HTML, JSON, Markdown, RSS).

## 🔧 All Configuration in One File

Edit `config.py` (at root) for everything:

```python
# Page names (1-5)
PAGE_CATEGORIES = {...}

# Site branding
SITE_TITLE = "..."
SITE_TAGLINE = "..."
SITE_DESCRIPTION = "..."

# Prompts for LLM
CATEGORIZATION_PROMPT = "..."
SUMMARIZATION_PROMPT = "..."

# Stories to include
AI_KEYWORDS = [...]

# News sources
HACKERNEWS_STORY_LIMIT = 30
RSS_FEEDS = {...}
RSS_STORIES_PER_FEED = 5

# Output settings
STORIES_PER_PAGE = 5
INCLUDE_IMAGES = True

# Colors and design
COLORS = {'primary': '#...', ...}

# Update schedule (cron)
DAILY_SCHEDULE = "0 8 * * *"

# LLM settings
PRIMARY_LLM = "meta-ai"
FALLBACK_LLM = "gemini"
LLM_TIMEOUT = 30
```

**That's literally it.** Change what you want, leave the rest alone.

## 📁 Structure

```
ROOT
├── config.py                       # ← EDIT THIS FOR EVERYTHING
├── README.md                       # You are here
├── setup.sh                        # One-command setup
├── requirements.txt                # Python dependencies
├── netlify.toml                    # Netlify config

backend/
  ├── main.py                       # Run to generate newspaper
  ├── scraper.py                    # Fetches news
  ├── processor.py                  # LLM categorization
  ├── exporter.py                   # Generates HTML/JSON/MD/RSS
  ├── image_generator.py            # Optional SVG images
  └── test_pipeline.py              # Test without API keys

frontend/
  └── index.html                    # Landing page

.github/workflows/
  └── generate-newspaper.yml        # Daily automation

output/
  └── current/                      # Generated files (daily)
      ├── newspaper.html
      ├── newspaper.json
      ├── newspaper.md
      └── feed.xml
```

## 🚀 Deploy

### GitHub Actions (Auto Daily)
- Workflow runs automatically at 8 AM UTC
- Generates newspaper
- Commits to `output/current/`
- Can trigger manually: Actions → Generate Newspaper

### Netlify (Recommended)
1. Push to GitHub
2. Connect repo to Netlify
3. Set publish directory: `output/current`
4. Auto-deploys daily

### GitHub Pages (Free)
1. Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: /output/current

### Self-hosted
Copy `output/current/` files to your server daily

## 🔑 API Keys

**Essential:**
- [Gemini API Key](https://makersuite.google.com/app/apikey) - Free tier available (60 calls/min)

**Optional:**
- Meta-AI cookie - Falls back to Gemini if unavailable
- Netlify Auth Token - For auto-deployment

## 🛠 Local Testing

```bash
# Test without API keys (sample data)
python backend/test_pipeline.py

# Test with real API
python backend/main.py

# Check scraper
python backend/scraper.py

# Check processor
python backend/processor.py
```

Output files: `output/current/newspaper.{html,json,md}` + `feed.xml`

## 📡 Automation

GitHub Actions workflow (`.github/workflows/generate-newspaper.yml`):

```yaml
schedule:
  - cron: '0 8 * * *'  # 8 AM UTC daily
```

Change time: [crontab.guru](https://crontab.guru)

Examples:
- `0 8 * * *` = 8 AM UTC daily
- `0 9 * * MON-FRI` = 9 AM UTC weekdays only
- `30 6,18 * * *` = 6:30 AM and 6:30 PM UTC daily

## 🎨 Customization

### Change Daily Schedule
Edit `.github/workflows/generate-newspaper.yml`:
```yaml
schedule:
  - cron: '0 8 * * *'  # Change here
```

### Add More RSS Feeds
In `backend/config.py`:
```python
SCRAPER_CONFIG['rss_feeds']['feeds']['my_lab'] = 'https://my-lab.com/feed.xml'
```

### Adjust Colors
In `backend/config.py`:
```python
FRONTEND_CONFIG['colors'] = {
    'primary': '#your_color',
    'dark': '#your_color',
    'accent': '#your_color'
}
```

### Change Stories per Page
In `backend/config.py`:
```python
EXPORTER_CONFIG['stories_per_page'] = 3
```

### Disable Images
In `backend/config.py`:
```python
EXPORTER_CONFIG['include_images'] = False
```

## 🏗 How It Works

```
HackerNews API (30 stories)
         +
7+ RSS Feeds (5 stories each)
         ↓
    Scraper (Filter AI keywords)
         ↓
LLM Processor (Categorize + Summarize)
├─ Meta-AI primary
└─ Gemini fallback
         ↓
Organize by 5 Pages
         ↓
Export (HTML/JSON/MD/RSS)
         ↓
GitHub commit → Netlify deploy
         ↓
Live website
```

**Time:** ~3-6 minutes per generation  
**Cost:** Free (Gemini free tier)  
**Frequency:** Daily (configurable)

## 📊 Output Files

Generated in `output/current/`:

- `newspaper.html` (15-20 KB) - Interactive newspaper with page flip
- `newspaper.json` (5-10 KB) - Structured data
- `newspaper.md` (3-5 KB) - Markdown version
- `feed.xml` (5-8 KB) - RSS feed
- `metadata.json` - Generation info

## 🔍 Troubleshooting

**No files generated:**
- Check GitHub Actions logs
- Verify GEMINI_API_KEY in secrets
- Test locally: `python backend/main.py`

**Feed parsing warnings:**
- Normal - some feeds have malformed XML
- Scraper handles gracefully and continues

**Netlify deploy fails:**
- Verify NETLIFY_AUTH_TOKEN is valid
- Check publish directory is `output/current`

**Empty newspaper:**
- HackerNews API might be down
- Check logs for network errors
- Try again in a few minutes

## 📚 Files

```
backend/config.py      - Change page names, RSS feeds, colors, schedule
backend/main.py        - Run to generate newspaper
backend/scraper.py     - Fetch news
backend/processor.py   - LLM categorization
backend/exporter.py    - Generate outputs
requirements.txt       - Python dependencies
setup.sh              - Setup script
.github/workflows/    - GitHub Actions automation
netlify.toml          - Netlify config
frontend/index.html   - Landing page
```

## 🚀 Next Steps

1. Get API key: https://makersuite.google.com/app/apikey
2. Setup: `bash setup.sh`
3. Configure: `nano .env` (add GEMINI_API_KEY)
4. Test: `python backend/test_pipeline.py`
5. Deploy: `git push origin main` + add GitHub secrets
6. Done! Newspaper runs daily automatically

## 💡 Tips

- **Customize pages in 30 seconds:** Edit `backend/config.py`
- **Test without API keys:** `python backend/test_pipeline.py`
- **Check automation:** GitHub repo → Actions tab
- **Monitor deployment:** Netlify dashboard
- **View output:** Open `output/current/newspaper.html` in browser

## 📝 Page Categories (Default)

| Page | Name | Content |
|------|------|---------|
| 1 | Breaking Vectors | Top AI news |
| 2 | Model Architectures | LLM releases & papers |
| 3 | Neural Horizons | Vision, world models, robotics |
| 4 | Lab Outputs | Company announcements |
| 5 | Inference Corner | Analysis & predictions |

All customizable via `backend/config.py`

## 🛠 Stack

- **Backend:** Python 3.11+ (requests, feedparser, google-generativeai, meta-ai-api-tool-call)
- **Frontend:** HTML5, CSS3 (3D transforms), vanilla JavaScript
- **Automation:** GitHub Actions (cron scheduling)
- **Hosting:** Netlify or GitHub Pages
- **APIs:** HackerNews (free), Gemini (free tier), RSS (free)

## 📜 License

MIT - Use, modify, redistribute freely

## 🤝 Contributing

Areas for enhancement:
- Go backend rewrite (faster performance)
- Email digest distribution
- Full-text search across archives
- Custom feed subscriptions
- Image generation (DALL-E/Flux)
- Archive browsing
- Browser extension

---

**Built for the AI community.** Daily news from the world of tokens, vectors, and neural networks.

Get started: `bash setup.sh`
