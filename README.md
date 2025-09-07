# SEO Ranking Tool

A comprehensive SEO analysis tool that scrapes websites, analyzes content structure, readability, images, and generates actionable SEO reports.

## How It Works

The tool uses CrewAI to orchestrate multiple AI agents:
- Scrapes websites using Playwright for dynamic content handling
- Analyzes content structure, readability, and optimization opportunities
- Processes images with AI vision for SEO-friendly alt text and recommendations
- Generates comprehensive SEO reports with priority action plans

## APIs Used

- Groq API for language model analysis
- Playwright for browser automation and scraping

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install Playwright: `python -m playwright install chromium`
4. Set environment variable: `GROQ_API_KEY=your_api_key`

## Usage

Run the Streamlit app: `python run_streamlit.py`

## License

This project is licensed under the MIT License.
