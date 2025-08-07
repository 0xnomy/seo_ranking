import json
import os
import base64
from config import Config
from crewai import Agent, Task
from langchain.tools import tool
from groq import Groq
from urllib.parse import urlparse
from utils import log_error, handle_rate_limit, is_rate_limit_error, delay_between_calls

class ImageAnalyzerAgent:
    def __init__(self):
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
    
    def analyze_images(self, seo_data: dict) -> dict:
        """Analyze all images in the SEO data using the full JSON for fact-based, referenced, and numerical outputs. Only process .jpeg, .jpg, .png, .webp files. Output only markdown tables, lists, and referenced facts. No generic advice. Only processes first 2 images for vision analysis."""
        try:
            # Use the dict directly
            seo_data_dict = seo_data
            
            # Add delay before API call to prevent rate limiting
            delay_between_calls(Config.API_CALL_DELAY)
            
            # Only keep allowed image extensions and limit to first 2 images
            allowed_exts = {'.jpeg', '.jpg', '.png', '.webp'}
            filtered_images = [img_data for img_data in seo_data_dict.get('images', []) if img_data.get('local_path') and os.path.splitext(img_data['local_path'])[1].lower() in allowed_exts]
            
            # Limit to first 2 images for vision analysis
            filtered_images = filtered_images[:2]
            print(f"Debug: Limiting to first 2 images for vision analysis: {len(filtered_images)} images")
            
            # Convert images to base64
            images_with_base64 = []
            print(f"Debug: Processing {len(filtered_images)} images for vision analysis")
            
            for i, img_data in enumerate(filtered_images):
                local_path = img_data.get('local_path')
                print(f"Debug: Processing image {i+1}: {local_path}")
                
                if local_path and os.path.exists(local_path):
                    try:
                        with open(local_path, 'rb') as img_file:
                            img_bytes = img_file.read()
                            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                            
                            # Determine MIME type based on file extension
                            ext = os.path.splitext(local_path)[1].lower()
                            mime_type = {
                                '.jpg': 'image/jpeg',
                                '.jpeg': 'image/jpeg',
                                '.png': 'image/png',
                                '.webp': 'image/webp'
                            }.get(ext, 'image/jpeg')
                            
                            # Create data URL
                            data_url = f"data:{mime_type};base64,{img_base64}"
                            
                            # Add base64 data to image info
                            img_data_with_base64 = img_data.copy()
                            img_data_with_base64['base64_data'] = data_url
                            img_data_with_base64['mime_type'] = mime_type
                            images_with_base64.append(img_data_with_base64)
                            print(f"Debug: Successfully converted image {i+1} to base64 ({len(img_base64)} chars)")
                    except Exception as e:
                        log_error(f"Failed to convert image to base64: {local_path}, error: {str(e)}", agent="ImageAnalyzerAgent")
                        print(f"Debug: Failed to convert image {i+1} to base64: {str(e)}")
                        # Add image without base64 if conversion fails
                        images_with_base64.append(img_data)
                else:
                    # Add image without base64 if file doesn't exist
                    print(f"Debug: Image file not found: {local_path}")
                    images_with_base64.append(img_data)
            
            print(f"Debug: Successfully processed {len([img for img in images_with_base64 if 'base64_data' in img])} images with base64 data")
            
            # Replace the images list in the JSON with the filtered list including base64
            seo_data_dict['images'] = images_with_base64
            
            # For each image, get a one-line description from the LLM
            image_descriptions = []
            for img_data in images_with_base64:
                if 'base64_data' in img_data:
                    # Prepare prompt for a single image
                    single_image_prompt = f"""
                    Given the following image and its metadata, provide a single, concise, factual one-line description of the image content for SEO purposes. Do not include generic advice. Only output the description, nothing else.
                    
                    Metadata:
                    - URL: {img_data.get('url', '')}
                    - Alt: {img_data.get('alt', '')}
                    - Title: {img_data.get('title', '')}
                    - File Type: {img_data.get('mime_type', '')}
                    """
                    messages = [
                        {"role": "system", "content": "You are an expert image SEO analyst."},
                        {"role": "user", "content": single_image_prompt},
                        {"role": "user", "content": {"type": "image_url", "image_url": {"url": img_data['base64_data'], "detail": "high"}}}
                    ]
                    try:
                        response = self.groq_client.chat.completions.create(
                            model=Config.LLM_MODEL,
                            messages=messages,
                            max_tokens=50
                        )
                        desc = response.choices[0].message.content.strip()
                        image_descriptions.append({
                            "url": img_data.get('url', ''),
                            "description": desc
                        })
                    except Exception as e:
                        log_error(f"Failed to get image description: {str(e)}", agent="ImageAnalyzerAgent")
                        image_descriptions.append({
                            "url": img_data.get('url', ''),
                            "description": "Error generating description"
                        })
            # Save the descriptions in the JSON
            seo_data_dict['image_descriptions'] = image_descriptions
            
            retry_count = 0
            while retry_count < Config.MAX_RETRIES:
                try:
                    # Use regular model for image analysis (vision model has context length issues)
                    analysis_prompt = f"""
                    Analyze the image metadata for SEO optimization. Output ONLY:
                    - A markdown table: | Image | Alt Text Present? | File Type | SEO Score |
                    - A count of images missing alt text.
                    - Basic SEO recommendations based on file types and metadata.
                    - No generic advice. Only reference the data provided.
                    
                    Image Data: {json.dumps([{'url': img.get('url', ''), 'alt': img.get('alt', ''), 'title': img.get('title', ''), 'local_path': img.get('local_path', '')} for img in images_with_base64], indent=2)}
                    """
                    
                    response = self.groq_client.chat.completions.create(
                        model=Config.LLM_MODEL,
                        messages=[
                            {"role": "system", "content": "You are an expert image SEO analyst."},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        max_tokens=100
                    )
                    
                    analysis = response.choices[0].message.content.strip()
                    seo_data_dict['image_analysis'] = analysis
                    domain = urlparse(seo_data_dict.get('url', 'unknown')).netloc
                    filename = f"{domain.replace('.', '_')}_analysis.json"
                    filepath = os.path.join(Config.OUTPUT_DIR, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(seo_data_dict, f, indent=2, ensure_ascii=False)
                    return {"image_analysis_complete": True, "file": filepath}
                    
                except Exception as e:
                    if is_rate_limit_error(e):
                        retry_count = handle_rate_limit(retry_count, Config.MAX_RETRIES, Config.RATE_LIMIT_DELAY)
                        continue
                    else:
                        raise e
            
            # If we get here, we've exhausted retries
            raise Exception(f"Rate limit exceeded after {Config.MAX_RETRIES} retries")
            
        except Exception as e:
            log_error(f"analyze_images error: {str(e)}", agent="ImageAnalyzerAgent")
            return {"error": str(e)} 