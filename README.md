# Daily Tokens

Daily Tokens is an automated news curation engine that transforms the latest developments in artificial intelligence into a beautifully formatted digital newspaper. It bridges the gap between raw data from HackerNews and laboratory RSS feeds, and a readable, curated experience designed for those who want to stay informed about the rapidly evolving AI landscape without being overwhelmed by the noise.

The system intelligently categorizes, summarizes, and organizes stories into a 5-page layout, choosing relevant imagery directly from source articles. Whether you prefer an interactive 3D page-flip experience, a clean Markdown summary, or a plain text digest, Daily Tokens provides a sophisticated way to consume the day's most significant technical breakthroughs and research.

## Technical Setup

Daily Tokens uses a robust backend pipeline powered by a hierarchy of Large Language Models and an intelligent image extraction engine.

### Prerequisites

- Python 3.11 or higher
- API Keys for your preferred providers:
  - HF_TOKEN (Hugging Face Inference API - Primary)
  - OPENROUTER_API_KEY (OpenRouter - Secondary Fallback)
  - GEMINI_API_KEY (Google Gemini - Optional Fallback)

### Installation

1. Clone the repository and navigate to the project directory.
2. Run the setup script to create a virtual environment and install dependencies:
   ```bash
   bash setup.sh
   ```
3. Create a `.env` file in the root directory based on `.env.example`:
   ```bash
   HF_TOKEN=your_huggingface_token
   OPENROUTER_API_KEY=your_openrouter_key
   ```

### Running the Pipeline

To generate the current day's edition:
```bash
source venv/bin/activate
python backend/main.py
```

The script will:
1. Archive the previous day's edition into `output/archive/`.
2. Aggregate stories from HackerNews (Top, Best, and New pools) and configured RSS feeds.
3. Route categorization and summarization through the LLM hierarchy (HF -> OpenRouter -> Meta-AI).
4. Extract and download high-quality preview images from source article SEO metadata.
5. Export the newspaper in HTML, JSON, Markdown, Text, and RSS formats to `output/current/`.

### Configuration

All high-level behavior, including page names, AI keywords for filtering, and RSS sources, can be customized in `config.py` at the root of the project.

### Automated Deployment

The project includes a GitHub Actions workflow in `.github/workflows/generate-newspaper.yml` that runs the pipeline daily. To enable this, add your API keys as Repository Secrets in your GitHub settings.

## System Architecture

The project is structured into modular components:
- Scraper: Handles multi-pool HackerNews fetching and RSS aggregation.
- LLM Router: Dynamically selects and falls back between multiple model providers.
- News Processor: Manages the logic for story relevance, categorization, and summarization.
- Image Fetcher: Uses BeautifulSoup to extract authentic article thumbnails.
- Exporter: Generates multiple output formats and maintains the dated archive.