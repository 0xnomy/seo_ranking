from crewai import Agent, Task, Crew
try:
    from langchain_litellm import ChatLiteLLM
except ImportError:
    from langchain_community.chat_models import ChatLiteLLM
from config import Config
from scraper_agent import ScraperAgent
from image_analyzer_agent import ImageAnalyzerAgent
from content_analyzer_agent import ContentAnalyzerAgent
from keyword_analyzer_agent import KeywordAnalyzerAgent
from backlink_analyzer_agent import BacklinkAnalyzerAgent
from url_analyzer_agent import URLAnalyzerAgent
from seo_analyzer_agent import SEOAnalyzerAgent
import os
import sys
import json
from datetime import datetime
import re
from urllib.parse import urlparse
from utils import log_error  # Import from utils instead of defining here
import time

class SEOCrew:
    def __init__(self):
        # Configure LiteLLM directly for CrewAI
        self.llm = ChatLiteLLM(
            model=Config.LLM_MODEL,  # Use config instead of hardcoded model
            api_key=Config.GROQ_API_KEY
        )
        
        # Initialize agent instances
        self.scraper_agent = ScraperAgent()
        self.image_analyzer = ImageAnalyzerAgent()
        self.content_analyzer = ContentAnalyzerAgent()
        self.keyword_analyzer = KeywordAnalyzerAgent()
        self.backlink_analyzer = BacklinkAnalyzerAgent()
        self.url_analyzer = URLAnalyzerAgent()
        self.seo_analyzer = SEOAnalyzerAgent()
        
        # Create CrewAI agents
        self.scraper_crew_agent = Agent(
            llm=self.llm,
            role='Web Scraper',
            goal='Scrape website data including title, headings, paragraphs, and images',
            backstory="""You are an expert web scraper specializing in extracting comprehensive 
            website data for SEO analysis. You use Playwright to handle dynamic content and 
            extract all necessary information for SEO optimization."""
        )
        
        self.content_analyzer_crew_agent = Agent(
            llm=self.llm,
            role='Content SEO Specialist',
            goal='Analyze content structure, readability, and optimization opportunities',
            backstory="""You are an expert content analyst specializing in content structure, 
            readability analysis, and content optimization for SEO. You understand how content 
            organization affects search engine rankings and user engagement."""
        )
        
        self.image_analyzer_crew_agent = Agent(
            llm=self.llm,
            role='Image SEO Specialist',
            goal='Analyze and optimize images for SEO using AI vision',
            backstory="""You are an expert image optimization specialist who uses AI to analyze 
            images and generate SEO-friendly alt text, descriptions, and optimization recommendations."""
        )
        
        self.seo_analyzer_crew_agent = Agent(
            llm=self.llm,
            role='SEO Performance Analyst',
            goal='Generate comprehensive SEO reports and actionable recommendations',
            backstory="""You are a senior SEO analyst who synthesizes all analysis results 
            into comprehensive reports with actionable recommendations and priority action plans."""
        )
    
    def create_tasks(self, scraped_data: dict):
        """Create the task pipeline for SEO analysis using scraped data"""
        # Task 1: Analyze content structure and readability
        content_analysis_task = Task(
            description="""
            Analyze the following scraped content for structure, readability, and optimization. Use only the data provided below. Output must be factual, numerical, and reference the JSON keys.
            
            JSON: {json_data}
            """.format(json_data=json.dumps(scraped_data)),
            agent=self.content_analyzer_crew_agent,
            expected_output="""Content analysis including:
            - structure_analysis: Heading hierarchy and content organization
            - readability_analysis: Readability scores and metrics
            - optimization_analysis: Content gaps and opportunities
            - recommendations: Actionable content improvement suggestions (all referenced to the JSON)"""
        )
        # Task 2: Analyze images for SEO optimization
        image_analysis_task = Task(
            description="""
            Use the analyze_images tool to analyze all images found in the following JSON for SEO optimization. 
            The tool will convert images to base64 and use vision AI to analyze them. Only the first 2 images will be analyzed.
            Output must be factual, numerical, and reference the JSON keys.
            
            JSON: {json_data}
            """.format(json_data=json.dumps(scraped_data)),
            agent=self.image_analyzer_crew_agent,
            expected_output="""Image analysis including:
            - analyzed_images: List of analyzed images with descriptions
            - optimized_alt_text: SEO-friendly alt text for each image
            - seo_filenames: Optimized filename suggestions
            - optimization_suggestions: Image improvement recommendations (all referenced to the JSON)"""
        )
        # Task 3: Generate comprehensive SEO report
        seo_report_task = Task(
            description="""
            Generate a comprehensive SEO analysis report combining all analyses. Use only the factual, referenced, and numerical outputs from previous steps. Do not invent or generalize. Reference the JSON and previous outputs in all sections.
            
            JSON: {json_data}
            """.format(json_data=json.dumps(scraped_data)),
            agent=self.seo_analyzer_crew_agent,
            expected_output="""Comprehensive SEO report including:
            - executive_summary: High-level findings and insights (referenced to the JSON)
            - comprehensive_report: Detailed analysis results (referenced to the JSON)
            - priority_action_plan: Prioritized improvement actions (referenced to the JSON)
            - overall_seo_score: Overall SEO performance score (referenced to the JSON)
            - strategic_recommendations: Long-term SEO strategy (referenced to the JSON)"""
        )
        return [content_analysis_task, image_analysis_task, seo_report_task]

    def run_analysis(self, url: str):
        """Run the complete SEO analysis pipeline"""
        try:
            print(f"🚀 Starting comprehensive SEO analysis for: {url}")
            print("⏳ This may take several minutes...")
            print("📡 Step 1: Scraping website data...")
            scraped_data = self.scraper_agent.scrape_website(url)
            if "error" in scraped_data:
                print(f"❌ Scraping failed: {scraped_data['error']}")
                return scraped_data
            print("✅ Scraping completed successfully!")
            print(f"📄 Found: {len(scraped_data.get('paragraphs', []))} paragraphs, {len(scraped_data.get('images', []))} images")
            tasks = self.create_tasks(scraped_data)
            print("🤖 Step 2: Running AI analysis...")
            # Run tasks with delays between them to prevent rate limiting
            print("📝 Running content analysis...")
            content_result = self.content_analyzer_crew_agent.execute_task(tasks[0])
            time.sleep(Config.API_CALL_DELAY)
            
            print("🖼️ Running image analysis...")
            image_result = self.image_analyzer_crew_agent.execute_task(tasks[1])
            time.sleep(Config.API_CALL_DELAY)
            
            print("📊 Running SEO report generation...")
            seo_result = self.seo_analyzer_crew_agent.execute_task(tasks[2])
            
            # Combine results manually
            result = type('CrewOutput', (), {
                'raw': {
                    'content_analysis': content_result,
                    'image_analysis': image_result,
                    'seo_report': seo_result
                }
            })()
            
            # Add delay after crew analysis to prevent rate limiting
            print(f"⏳ Waiting {Config.API_CALL_DELAY} seconds before image analysis...")
            time.sleep(Config.API_CALL_DELAY)
            
            # Step 3: Run image analysis with vision model
            print("🖼️ Step 3: Running image analysis with vision model...")
            try:
                image_result = self.image_analyzer.analyze_images(scraped_data)
                if isinstance(image_result, dict) and "error" not in image_result:
                    print("✅ Image analysis completed successfully!")
                else:
                    print(f"⚠️ Image analysis had issues: {image_result}")
            except Exception as e:
                print(f"⚠️ Image analysis failed: {str(e)}")
            
            # Add another delay before saving results
            print(f"⏳ Waiting {Config.API_CALL_DELAY} seconds before saving results...")
            time.sleep(Config.API_CALL_DELAY)
            
            # Save the final combined results to JSON
            try:
                domain = urlparse(url).netloc
                final_json_file = os.path.join(Config.OUTPUT_DIR, f"{domain.replace('.', '_')}_analysis.json")
                
                # Combine scraped data with analysis results
                final_data = scraped_data.copy()
                
                # Add analysis results if available
                if hasattr(result, 'raw') and result.raw:
                    # Handle CrewOutput raw data
                    if isinstance(result.raw, dict):
                        final_data.update(result.raw)
                    elif isinstance(result.raw, str):
                        # Try to parse JSON from string
                        try:
                            import json
                            parsed_data = json.loads(result.raw)
                            if isinstance(parsed_data, dict):
                                final_data.update(parsed_data)
                        except:
                            # If it's not JSON, add as text
                            final_data['analysis_report'] = result.raw
                elif isinstance(result, dict):
                    final_data.update(result)
                elif hasattr(result, 'result') and result.result:
                    # Handle CrewOutput result attribute
                    if isinstance(result.result, dict):
                        final_data.update(result.result)
                    elif isinstance(result.result, str):
                        final_data['analysis_report'] = result.result
                
                # Save to JSON
                with open(final_json_file, 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, indent=2, ensure_ascii=False)
                
                print(f"📄 Final results saved to: {final_json_file}")
            except Exception as e:
                print(f"⚠️ Warning: Could not save final results: {str(e)}")
                # Save at least the scraped data
                try:
                    domain = urlparse(url).netloc
                    final_json_file = os.path.join(Config.OUTPUT_DIR, f"{domain.replace('.', '_')}_analysis.json")
                    with open(final_json_file, 'w', encoding='utf-8') as f:
                        json.dump(scraped_data, f, indent=2, ensure_ascii=False)
                    print(f"📄 Scraped data saved to: {final_json_file}")
                except Exception as e2:
                    print(f"❌ Failed to save even scraped data: {str(e2)}")
            
            print("\n✅ Comprehensive SEO analysis completed!")
            print(f"📁 Results saved in: {Config.OUTPUT_DIR}")
            return result
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
            return {"error": str(e)}

def validate_url(url: str) -> str:
    """Validate and format URL"""
    if not url:
        return None
    
    # Remove whitespace
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

def check_environment():
    """Check if environment is properly configured"""
    if not Config.GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY not found in environment variables")
        print("Please set your GROQ_API_KEY in a .env file or environment variables")
        return False
    
    # Check if output directory exists
    if not os.path.exists(Config.OUTPUT_DIR):
        os.makedirs(Config.OUTPUT_DIR)
    
    return True

# Utility: View markdown report or priority actions

def view_report(report_path, section=None):
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if section == 'priority':
        # Extract Priority Action Plan section
        match = re.search(r'### Priority Action Plan(.*?)(###|$)', content, re.DOTALL)
        if match:
            print('\n--- PRIORITY ACTION ITEMS ---\n')
            print(match.group(1).strip())
            return
        else:
            print('No Priority Action Plan section found.')
            return
    print(content)

def main():
    """Main function with terminal interface"""
    print("=" * 60)
    print("🔍 SEO RANKING ANALYSIS TOOL")
    print("=" * 60)
    print("Comprehensive SEO analysis using AI agents")
    print("Powered by CrewAI, Groq, and Compound-Beta")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Initialize SEO Crew
    try:
        seo_crew = SEOCrew()
        print("✅ SEO Crew initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing SEO Crew: {str(e)}")
        sys.exit(1)
    
    while True:
        print("=" * 60)
        print("📋 OPTIONS:")
        print("1. Analyze a website")
        print("2. View output directory")
        print("3. View last markdown report")
        print("4. View priority action items")
        print("5. Exit")
        print("=" * 60)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n🌐 WEBSITE ANALYSIS")
            print("-" * 30)
            url = input("Enter the website URL to analyze: ").strip()
            
            if not url:
                print("❌ No URL entered. Please try again.")
                continue
            
            # Validate and format URL
            url = validate_url(url)
            if not url:
                print("❌ Invalid URL format. Please try again.")
                continue
            
            print(f"🔍 Analyzing: {url}")
            
            # Run analysis
            result = seo_crew.run_analysis(url)
            # Save last report path for export/view
            if not hasattr(seo_crew, 'last_report_path'):
                seo_crew.last_report_path = None
            if isinstance(result, dict) and 'file' in result:
                seo_crew.last_report_path = result['file']
            else:
                # Try to find the latest .txt in output
                txts = [f for f in os.listdir(Config.OUTPUT_DIR) if f.endswith('.txt')]
                if txts:
                    txts.sort(key=lambda x: os.path.getmtime(os.path.join(Config.OUTPUT_DIR, x)), reverse=True)
                    seo_crew.last_report_path = os.path.join(Config.OUTPUT_DIR, txts[0])
            # Fix: CrewOutput is not a dict, check for 'error' attribute
            if hasattr(result, 'error') and result.error:
                print("❌ Analysis failed. Please check your internet connection and try again")
            else:
                print("🎉 Analysis completed successfully!")
                print("📊 Check the 'seo_output' directory for detailed results")
                print("📋 ANALYSIS SUMMARY:")
                print(f"• Domain: {url}")
                print(f"• Output Directory: {Config.OUTPUT_DIR}")
                print("• Files generated:")
                print("  - SEO data JSON files")
                print("  - Analysis reports")
                print("  - Human-readable report")
        
        elif choice == "2":
            print(f"\n📁 OUTPUT DIRECTORY: {Config.OUTPUT_DIR}")
            if os.path.exists(Config.OUTPUT_DIR):
                files = os.listdir(Config.OUTPUT_DIR)
                if files:
                    print("📄 Files found:")
                    for file in files:
                        print(f"  - {file}")
                else:
                    print("📭 No files found in output directory")
            else:
                print("❌ Output directory does not exist")
        
        elif choice == "3":
            # View markdown report
            if hasattr(seo_crew, 'last_report_path') and seo_crew.last_report_path:
                view_report(seo_crew.last_report_path)
            else:
                print("❌ No report available. Run an analysis first.")
        elif choice == "4":
            # View priority action items
            if hasattr(seo_crew, 'last_report_path') and seo_crew.last_report_path:
                view_report(seo_crew.last_report_path, section='priority')
            else:
                print("❌ No report available. Run an analysis first.")
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter a number from 1 to 5.")

if __name__ == "__main__":
    main() 