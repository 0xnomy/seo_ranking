import os
import time
import random
from datetime import datetime

def log_error(message, agent=None):
    """Centralized error logging utility"""
    os.makedirs('seo_output', exist_ok=True)
    log_path = os.path.join('seo_output', 'error.log')
    with open(log_path, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        agent_str = f'[{agent}]' if agent else ''
        f.write(f"[{timestamp}] {agent_str} {message}\n")

def delay_between_calls(seconds=3):
    """Add delay between API calls to prevent rate limiting"""
    log_error(f"Waiting {seconds} seconds before next API call to prevent rate limiting")
    time.sleep(seconds)

def handle_rate_limit(retry_count=0, max_retries=3, base_delay=20):
    """Handle rate limiting with exponential backoff"""
    if retry_count >= max_retries:
        raise Exception(f"Rate limit exceeded after {max_retries} retries")
    
    delay = base_delay * (2 ** retry_count) + random.uniform(0, 1)
    log_error(f"Rate limit hit, waiting {delay:.1f} seconds (retry {retry_count + 1}/{max_retries})")
    time.sleep(delay)
    return retry_count + 1

def is_rate_limit_error(error):
    """Check if error is a rate limit error"""
    error_str = str(error).lower()
    return any(phrase in error_str for phrase in [
        'rate limit', 'rate_limit', 'tpm', 'tokens per minute', 'limit exceeded'
    ]) 