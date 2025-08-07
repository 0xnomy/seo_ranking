import json
import os
from config import Config
from crewai import Agent, Task
from langchain.tools import tool
from groq import Groq
from urllib.parse import urlparse
from utils import log_error, handle_rate_limit, is_rate_limit_error, delay_between_calls

class BacklinkAnalyzerAgent:
    def __init__(self):
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
    
    @tool
    def analyze_backlinks(self, seo_data: dict) -> dict:
        """Analyze backlinks for quality, relevance, and SEO impact using only the provided JSON data. Output only markdown tables, lists, and referenced facts. No generic advice."""
        try:
            # Add delay before API call to prevent rate limiting
            delay_between_calls(Config.API_CALL_DELAY)
            
            prompt = f"""
            Analyze all backlinks in the JSON. Output ONLY:
            - A markdown table: | Backlink URL | Domain Authority | Relevance | (reference JSON)
            - A count of low-quality backlinks.
            - No generic advice. Only reference the data provided.
            JSON: {json.dumps(seo_data)}
            """
            
            retry_count = 0
            while retry_count < Config.MAX_RETRIES:
                try:
                    response = self.groq_client.chat.completions.create(
                        model=Config.LLM_MODEL,
                        messages=[
                            {"role": "system", "content": "You are an expert backlink SEO analyst."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000
                    )
                    analysis = response.choices[0].message.content.strip()
                    seo_data['backlink_analysis'] = analysis
                    domain = urlparse(seo_data.get('url', 'unknown')).netloc
                    filename = f"{domain.replace('.', '_')}_analysis.json"
                    filepath = os.path.join(Config.OUTPUT_DIR, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(seo_data, f, indent=2, ensure_ascii=False)
                    return {"backlink_analysis_complete": True, "file": filepath}
                    
                except Exception as e:
                    if is_rate_limit_error(e):
                        retry_count = handle_rate_limit(retry_count, Config.MAX_RETRIES, Config.RATE_LIMIT_DELAY)
                        continue
                    else:
                        raise e
            
            # If we get here, we've exhausted retries
            raise Exception(f"Rate limit exceeded after {Config.MAX_RETRIES} retries")
            
        except Exception as e:
            log_error(f"analyze_backlinks error: {str(e)}", agent="BacklinkAnalyzerAgent")
            return {"error": str(e)} 