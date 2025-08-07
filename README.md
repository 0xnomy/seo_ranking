# SEO Ranking Analysis Tool

A comprehensive SEO analysis tool powered by CrewAI, Groq, and Compound-Beta. This tool automatically scrapes websites, analyzes content, images, keywords, backlinks, and URL structure to provide actionable SEO recommendations.

## Features

- **Web Scraping**: Uses Playwright for JavaScript-heavy sites with realistic browser headers
- **Content Analysis**: Analyzes content structure, readability, and optimization opportunities
- **Image Analysis**: Uses AI vision to generate optimized alt text and filenames
- **Keyword Research**: Uses Compound-Beta for real search engine data and keyword insights
- **Backlink Analysis**: Evaluates backlink quality, relevance, and diversity
- **URL Analysis**: Analyzes URL structure, hierarchy, and optimization
- **Comprehensive Reports**: Generates actionable SEO reports with prioritized recommendations

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd seo_ranking
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browser**:
   ```bash
   playwright install chromium
   ```

4. **Set up environment variables**:
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Usage

### Streamlit Web Interface (Recommended)

The project includes a modern Streamlit web interface with advanced features:

```bash
# Option 1: Use the launcher script (recommended)
python run_streamlit.py

# Option 2: Run directly with Streamlit
streamlit run streamlit_app.py
```

**Features:**
- Modern, responsive web interface
- Real-time analysis progress tracking
- Interactive charts and visualizations (radar charts, gauge charts)
- Tabbed results display for different analysis areas
- Download functionality for reports
- Sidebar with configuration options and system status
- Advanced styling with custom CSS

### Terminal Interface

For command-line usage:

```bash
python main.py
```

The terminal interface provides:

1. **Analyze a website** - Enter a URL to perform comprehensive SEO analysis
2. **View output directory** - See generated analysis files
3. **View last markdown report** - Display the most recent analysis report
4. **View priority action items** - Show prioritized recommendations
5. **Exit** - Close the application

### Example Usage

```
🔍 SEO RANKING ANALYSIS TOOL
============================================================
Comprehensive SEO analysis using AI agents
Powered by CrewAI, Groq, and Compound-Beta
============================================================

📋 OPTIONS:
1. Analyze a website
2. View output directory
3. Exit
============================================================

Enter your choice (1-3): 1

🌐 WEBSITE ANALYSIS
------------------------------
Enter the website URL to analyze: example.com

🚀 Starting comprehensive SEO analysis for: https://example.com
⏳ This may take several minutes...
```

## Output

The tool generates multiple files in the `seo_output/` directory:

- **SEO Data JSON**: Raw scraped data and analysis results
- **Analysis Reports**: Specialized reports for each SEO area
- **Human-Readable Report**: Executive summary and actionable recommendations

## Architecture

The tool uses specialized AI agents for each SEO area:

1. **Web Scraper Agent**: Extracts comprehensive website data using Playwright
2. **Content SEO Specialist**: Analyzes content structure and readability
3. **Image SEO Specialist**: Optimizes images using AI vision
4. **Keyword Research Specialist**: Uses Compound-Beta for search engine insights
5. **Backlink Analysis Specialist**: Evaluates backlink quality and relevance
6. **URL Structure Specialist**: Analyzes URL optimization and hierarchy
7. **SEO Performance Analyst**: Generates comprehensive reports

## Configuration

### Models Used

- **LLM Model**: `meta-llama/llama-4-maverick-17b-128e-instruct` (for general AI tasks)
- **Search Model**: `compound-beta` (for search engine data and insights)

### Browser Settings

- **Browser**: Chromium (headless mode configurable)
- **Headers**: Realistic browser headers to avoid detection
- **Timeout**: 30 seconds for page loading

## Requirements

- Python 3.8+
- Groq API key
- Internet connection for web scraping and API calls

## Dependencies

- `crewai`: Agent orchestration framework
- `playwright`: Browser automation
- `groq`: LLM API client
- `beautifulsoup4`: HTML parsing
- `pillow`: Image processing
- `python-dotenv`: Environment variable management
- `streamlit`: Web application framework
- `plotly`: Interactive charts and visualizations
- `pandas`: Data manipulation and analysis
- `flask`: Alternative web framework (for Flask version)

## Error Handling

The tool includes comprehensive error handling for:
- Network connectivity issues
- Invalid URLs
- API rate limits
- Browser automation failures
- File system errors

## Troubleshooting

1. **API Key Issues**: Ensure your Groq API key is correctly set in the `.env` file
2. **Browser Issues**: Run `playwright install chromium` to install the browser
3. **Network Issues**: Check your internet connection and firewall settings
4. **Permission Issues**: Ensure write permissions for the output directory

## License

This project is licensed under the MIT License. 