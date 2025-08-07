import json
import os
from config import Config
from crewai import Agent, Task
from langchain.tools import tool
from groq import Groq
from urllib.parse import urlparse
from utils import log_error, handle_rate_limit, is_rate_limit_error, delay_between_calls

class KeywordAnalyzerAgent:
    def __init__(self):
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
    
    @tool
    def analyze_keywords(self, seo_data: dict) -> dict:
        try:
            # Add delay before API call to prevent rate limiting
            delay_between_calls(Config.API_CALL_DELAY)
            
            prompt = f"""
            From the JSON, extract all keywords and their frequencies. Output ONLY:
            - A markdown table: | Keyword | Frequency | (reference JSON)
            - A list of keywords missing compared to the top 5 competitors (if available).
            - No generic advice. Only reference the data provided.
            JSON: {json.dumps(seo_data)}
            """
            
            retry_count = 0
            while retry_count < Config.MAX_RETRIES:
                try:
                    response = self.groq_client.chat.completions.create(
                        model=Config.SEARCH_MODEL,
                        messages=[
                            {"role": "system", "content": "You are an expert keyword analyst."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000
                    )
                    analysis = response.choices[0].message.content.strip()
                    seo_data['keyword_analysis'] = analysis
                    domain = urlparse(seo_data.get('url', 'unknown')).netloc
                    filename = f"{domain.replace('.', '_')}_analysis.json"
                    filepath = os.path.join(Config.OUTPUT_DIR, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(seo_data, f, indent=2, ensure_ascii=False)
                    return {"keyword_analysis_complete": True, "file": filepath}
                    
                except Exception as e:
                    if is_rate_limit_error(e):
                        retry_count = handle_rate_limit(retry_count, Config.MAX_RETRIES, Config.RATE_LIMIT_DELAY)
                        continue
                    else:
                        raise e
            
            # If we get here, we've exhausted retries
            raise Exception(f"Rate limit exceeded after {Config.MAX_RETRIES} retries")
            
        except Exception as e:
            log_error(f"analyze_keywords error: {str(e)}", agent="KeywordAnalyzerAgent")
            return {"error": str(e)} 