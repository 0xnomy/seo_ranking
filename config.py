import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Groq Models - model names with provider prefixes for LiteLLM
    LLM_MODEL = 'groq/meta-llama/llama-4-maverick-17b-128e-instruct'  # For general LLM tasks - reliable model
    SEARCH_MODEL = 'groq/compound-beta'  # For search engine analysis - using same model
    VISION_MODEL = 'groq/meta-llama/llama-4-maverick-17b-128e-instruct'  # For image analysis tasks - using same model as LLM

    # Rate limiting settings
    RATE_LIMIT_DELAY = 30  # seconds to wait when rate limited
    MAX_RETRIES = 3  # maximum retries for rate limited requests
    API_CALL_DELAY = 25  # seconds to wait between API calls to prevent rate limiting

    # File paths
    OUTPUT_DIR = "seo_output"
    IMAGES_DIR = "seo_output/images"
    
    # Scraping settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
    
    # Playwright settings
    HEADLESS = True  # Set to True for headless mode
    BROWSER_TYPE = "chromium"  # chromium, firefox, webkit
    
    # Browser headers
    BROWSER_HEADERS = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://www.seoreviewtools.com/seo-api/"
    } 