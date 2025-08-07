import json
import os
from config import Config
from crewai import Agent, Task
from langchain.tools import tool
from groq import Groq
from urllib.parse import urlparse
from utils import log_error, handle_rate_limit, is_rate_limit_error, delay_between_calls

class SEOAnalyzerAgent:
    def __init__(self):
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
    
    @tool
    def analyze_seo_performance(self, seo_data: dict) -> dict:
        """Generate comprehensive SEO report using only the provided JSON data and previous agent outputs. Output only markdown tables, lists, and referenced facts. No generic advice. Save the report as a .txt file in the output folder."""
        try:
            # Add delay before API call to prevent rate limiting
            delay_between_calls(Config.API_CALL_DELAY)
            
            prompt = f"""
            Generate a brief SEO analysis report using only the provided JSON data. Output ONLY:
            - Executive summary (2-3 sentences)
            - 3 priority action items
            - Overall SEO score (1-10)
            - No generic advice. Only reference the JSON data.
            
            JSON: {json.dumps(seo_data)}
            """
            
            retry_count = 0
            while retry_count < Config.MAX_RETRIES:
                try:
                    response = self.groq_client.chat.completions.create(
                        model=Config.LLM_MODEL,
                        messages=[
                            {"role": "system", "content": "You are an expert SEO report generator."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=200
                    )
                    report = response.choices[0].message.content.strip()
                    domain = urlparse(seo_data.get('url', 'unknown')).netloc
                    filename = f"{domain.replace('.', '_')}_final_report.txt"
                    filepath = os.path.join(Config.OUTPUT_DIR, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(report)
                    return {"seo_analysis_complete": True, "file": filepath}
                    
                except Exception as e:
                    if is_rate_limit_error(e):
                        retry_count = handle_rate_limit(retry_count, Config.MAX_RETRIES, Config.RATE_LIMIT_DELAY)
                        continue
                    else:
                        raise e
            
            # If we get here, we've exhausted retries
            raise Exception(f"Rate limit exceeded after {Config.MAX_RETRIES} retries")
            
        except Exception as e:
            log_error(f"analyze_seo_performance error: {str(e)}", agent="SEOAnalyzerAgent")
            return {"error": str(e)} 