# SEO Analyzer

A modular, agentic SEO audit tool. Scrapes any blog/article, downloads images, analyzes content and images with LLMs, and generates actionable SEO reports. Web UI via Streamlit.

Demo: https://drive.google.com/file/d/1qvpSAekJHvYKBZ-UvsduCyktYkvlB3op/view?usp=sharing

## Features
- Scrapes text, images, meta, URLs, backlinks
- Downloads and renames images
- Sends image and metadata to LLM for description
- Fact-based, referenced, numerical SEO analysis
- Actionable report output
- Streamlit web frontend
- Docker support

## Quick Start

### 1. Clone and Install
```
git clone https://github.com/0xnomy/seo_ranking
cd seo_ranking
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Set Environment
Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key
```

### 3. Run (Local)
```
python run_streamlit.py
```

### 4. Run (Docker)
```
docker build -t seo-analyzer .
docker run -p 8501:8501 --env-file .env seo-analyzer
```

## Usage
- Open http://localhost:8501
- Enter a blog/article URL
- View/download the SEO report

## Requirements
- Python 3.8+
- GROQ_API_KEY
- Internet access

## Output
- Results in `seo_output/` as JSON and TXT

## System
- Python, Playwright, Streamlit, CrewAI, Groq LLM 