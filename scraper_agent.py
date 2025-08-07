import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import Image
import io
import asyncio
from playwright.async_api import async_playwright
from config import Config
import requests
from utils import log_error

class ScraperAgent:
    def __init__(self):
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.IMAGES_DIR, exist_ok=True)

    def scrape_website(self, url: str) -> dict:
        """
        """
        try:
            # Use a new event loop for Windows compatibility
            import asyncio
            import nest_asyncio
            
            # Apply nest_asyncio to allow nested event loops
            try:
                nest_asyncio.apply()
            except:
                pass
            
            # Create new event loop if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in a running event loop (like Streamlit), use asyncio.create_task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._scrape_website_async(url))
                        result = future.result()
                else:
                    result = asyncio.run(self._scrape_website_async(url))
            except RuntimeError:
                # Fallback to synchronous approach
                result = self._scrape_website_sync(url)
            
            return result
        except Exception as e:
            log_error(f"scrape_website error: {str(e)} for URL: {url}", agent="ScraperAgent")
            return {"error": str(e)}

    def _scrape_website_sync(self, url: str) -> dict:
        """
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Make request with headers
            headers = {
                'User-Agent': Config.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else "No title found"
            
            # Extract meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            
            # Extract headings
            headings = {
                'h1': [h.get_text(strip=True) for h in soup.find_all('h1')[:10]],
                'h2': [h.get_text(strip=True) for h in soup.find_all('h2')[:10]],
                'h3': [h.get_text(strip=True) for h in soup.find_all('h3')[:10]],
                'h4': [h.get_text(strip=True) for h in soup.find_all('h4')[:10]],
                'h5': [h.get_text(strip=True) for h in soup.find_all('h5')[:10]],
                'h6': [h.get_text(strip=True) for h in soup.find_all('h6')[:10]]
            }
            
            # Extract paragraphs
            paragraphs = []
            for p in soup.find_all('p')[:20]:
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    paragraphs.append(text[:200])  # Limit to 200 chars
            
            # Extract images
            images = []
            for i, img in enumerate(soup.find_all('img')[:10]):
                src = img.get('src')
                if src:
                    # Make URL absolute if relative
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = url.rstrip('/') + src
                    elif not src.startswith('http'):
                        src = url.rstrip('/') + '/' + src.lstrip('/')
                    
                    images.append({
                        'url': src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
            
            # Download images
            local_image_paths = []
            for i, img in enumerate(images):
                try:
                    img_url = img['url']
                    parsed_url = urlparse(img_url)
                    path_parts = parsed_url.path.split('/')
                    original_filename = path_parts[-1] if path_parts[-1] else f"image_{i}"
                    
                    # Remove invalid characters from filename
                    sanitized_filename = re.sub(r'[<>:"/\\|?*]', '_', original_filename)
                    
                    # Ensure it has an extension
                    if not os.path.splitext(sanitized_filename)[1]:
                        sanitized_filename += '.jpg'
                    
                    img_name = f"{urlparse(url).netloc.replace('.', '_')}_{sanitized_filename}"
                    img_path = os.path.join(Config.IMAGES_DIR, img_name)
                    
                    img_response = requests.get(img_url, timeout=10)
                    img_response.raise_for_status()
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    local_image_paths.append({
                        "url": img_url,
                        "local_path": img_path,
                        "alt": img.get('alt', ''),
                        "title": img.get('title', '')
                    })
                except Exception as e:
                    log_error(f"Image download error: {str(e)} for image {i}", agent="ScraperAgent")
                    local_image_paths.append({
                        "url": img.get('url', f"image_{i}"),
                        "local_path": None,
                        "error": str(e)
                    })
            
            result = {
                "url": url,
                "title": title,
                "meta_tags": meta_tags,
                "headings": headings,
                "paragraphs": paragraphs,
                "images": local_image_paths,
                "scraped_at": str(datetime.now())
            }
            
            # Save to JSON
            domain = urlparse(url).netloc
            filename = f"{domain.replace('.', '_')}_simple_scrape.json"
            filepath = os.path.join(Config.OUTPUT_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            return result
            
        except Exception as e:
            log_error(f"Sync scraping error: {str(e)} for URL: {url}", agent="ScraperAgent")
            return {"error": str(e)}

    async def _scrape_website_async(self, url: str) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=Config.HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Set longer timeout for navigation
            page.set_default_timeout(60000)  # 60 seconds timeout
            
            try:
                # Navigate with longer timeout
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for page to load completely
                await page.wait_for_load_state('networkidle', timeout=30000)
                
                # Additional wait for dynamic content
                await page.wait_for_timeout(5000)
                
            except Exception as e:
                log_error(f"Navigation timeout for {url}: {str(e)}", agent="ScraperAgent")
                # Try to continue with whatever content we have
                pass

            # Extract essential SEO content only
            title = await page.title()
            
            # Get meta tags for SEO
            meta_tags = await self._extract_meta_tags(page)
            
            # Get headings (limit to first 10 of each type)
            headings = await self._extract_headings(page)
            
            # Get paragraphs (limit to first 20, max 200 chars each)
            paragraphs = await self._extract_paragraphs(page)
            
            # Get images (limit to first 10) - DO THIS BEFORE CLOSING BROWSER
            try:
                img_elements = await page.locator('img').all()
                img_elements = img_elements[:10]  # Limit to first 10 images
                
                # Extract image URLs before closing browser
                image_urls = []
                for img_element in img_elements:
                    try:
                        img_url = await img_element.get_attribute('src')
                        if img_url:
                            image_urls.append(img_url)
                    except Exception as e:
                        log_error(f"Error getting image URL: {str(e)}", agent="ScraperAgent")
                        continue
                        
            except Exception as e:
                log_error(f"Error getting images: {str(e)}", agent="ScraperAgent")
                image_urls = []

            # NOW close the browser
            await browser.close()

            # Download images after browser is closed
            local_image_paths = []
            for i, img_url in enumerate(image_urls):
                try:
                    # Sanitize filename
                    parsed_url = urlparse(img_url)
                    path_parts = parsed_url.path.split('/')
                    original_filename = path_parts[-1] if path_parts[-1] else f"image_{i}"
                    
                    # Remove invalid characters from filename
                    sanitized_filename = re.sub(r'[<>:"/\\|?*]', '_', original_filename)
                    
                    # Ensure it has an extension
                    if not os.path.splitext(sanitized_filename)[1]:
                        try:
                            response_head = requests.head(img_url, timeout=10)
                            content_type = response_head.headers.get('Content-Type')
                            if content_type and 'image/' in content_type:
                                ext = '.' + content_type.split('/')[-1]
                                sanitized_filename += ext
                            else:
                                sanitized_filename += '.png'
                        except:
                            sanitized_filename += '.png'

                    img_name = f"{urlparse(url).netloc.replace('.', '_')}_{sanitized_filename}"
                    img_path = os.path.join(Config.IMAGES_DIR, img_name)
                    
                    response = requests.get(img_url, timeout=10)
                    response.raise_for_status()
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    local_image_paths.append({"url": img_url, "local_path": img_path})
                except Exception as e:
                    log_error(f"Image download error: {str(e)} for image {i}", agent="ScraperAgent")
                    local_image_paths.append({"url": f"image_{i}", "local_path": None, "error": str(e)})

            # Create optimized result with only essential SEO data
            result = {
                "url": url,
                "title": title,
                "meta_tags": meta_tags,
                "headings": headings,
                "paragraphs": paragraphs,
                "images": local_image_paths,
                "scraped_at": str(datetime.now())
            }

            domain = urlparse(url).netloc
            filename = f"{domain.replace('.', '_')}_simple_scrape.json"
            filepath = os.path.join(Config.OUTPUT_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            return result

    async def _extract_meta_tags(self, page):
        """
        """
        meta_tags = {}
        
        try:
            # Get meta description
            meta_desc = await page.locator('meta[name="description"]').get_attribute('content')
            if meta_desc:
                meta_tags['description'] = meta_desc[:200]  # Limit to 200 chars
            
            # Get meta keywords
            meta_keywords = await page.locator('meta[name="keywords"]').get_attribute('content')
            if meta_keywords:
                meta_tags['keywords'] = meta_keywords[:200]  # Limit to 200 chars
            
            # Get Open Graph tags
            og_title = await page.locator('meta[property="og:title"]').get_attribute('content')
            if og_title:
                meta_tags['og_title'] = og_title[:100]
            
            og_desc = await page.locator('meta[property="og:description"]').get_attribute('content')
            if og_desc:
                meta_tags['og_description'] = og_desc[:200]
        except Exception as e:
            log_error(f"Error extracting meta tags: {str(e)}", agent="ScraperAgent")
        
        return meta_tags

    async def _extract_headings(self, page):
        """
        """
        headings = {}
        
        try:
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                heading_elements = await page.locator(tag).all()
                # Limit to first 10 headings of each type
                heading_elements = heading_elements[:10]
                
                heading_texts = []
                for element in heading_elements:
                    try:
                        text = await element.text_content()
                        if text and text.strip():
                            # Limit each heading to 100 characters
                            heading_texts.append(text.strip()[:100])
                    except Exception as e:
                        log_error(f"Error extracting heading {tag}: {str(e)}", agent="ScraperAgent")
                        continue
                
                if heading_texts:
                    headings[tag] = heading_texts
        except Exception as e:
            log_error(f"Error extracting headings: {str(e)}", agent="ScraperAgent")
        
        return headings

    async def _extract_paragraphs(self, page):
        """
        """
        paragraphs = []
        
        try:
            paragraph_elements = await page.locator("p").all()
            # Limit to first 20 paragraphs
            paragraph_elements = paragraph_elements[:20]
            
            for element in paragraph_elements:
                try:
                    text = await element.text_content()
                    if text and text.strip():
                        # Limit each paragraph to 200 characters
                        clean_text = text.strip()[:200]
                        if len(clean_text) > 50:  # Only include paragraphs with substantial content
                            paragraphs.append(clean_text)
                except Exception as e:
                    log_error(f"Error extracting paragraph: {str(e)}", agent="ScraperAgent")
                    continue
        except Exception as e:
            log_error(f"Error extracting paragraphs: {str(e)}", agent="ScraperAgent")
        
        return paragraphs 