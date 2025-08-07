import streamlit as st
import os
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
from urllib.parse import urlparse
import base64
from pathlib import Path

# Import our existing modules
from main import SEOCrew, validate_url, check_environment
from config import Config

# Page configuration
st.set_page_config(
    page_title="SEO Analysis Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for advanced styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .metric-card {
        background: #111;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .score-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
        min-width: 80px;
    }
    
    .score-excellent { background-color: #10B981; color: white; }
    .score-good { background-color: #3B82F6; color: white; }
    .score-average { background-color: #F59E0B; color: white; }
    .score-poor { background-color: #EF4444; color: white; }
    
    .progress-container {
        background: #f3f4f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .analysis-step {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
        padding: 0.5rem;
        border-radius: 5px;
        background: white;
    }
    
    .step-icon {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        font-weight: bold;
        color: white;
    }
    
    .step-complete { background-color: #10B981; }
    .step-running { background-color: #3B82F6; animation: pulse 2s infinite; }
    .step-pending { background-color: #9CA3AF; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .tab-content {
        background: #1e1e1e;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-top: 1rem;
        color: white;
    }
    
    .tab-content h1, .tab-content h2, .tab-content h3, .tab-content h4, .tab-content h5, .tab-content h6 {
        color: white;
    }
    
    .tab-content p, .tab-content span, .tab-content div {
        color: white;
    }
    
    .stMarkdown {
        color: white !important;
    }
    
    .stText {
        color: white !important;
    }
    
    .download-button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .download-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'seo_crew' not in st.session_state:
    st.session_state.seo_crew = None
if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False
if 'current_url' not in st.session_state:
    st.session_state.current_url = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

def init_seo_crew():
    """Initialize SEO Crew if not already done"""
    if st.session_state.seo_crew is None:
        try:
            st.session_state.seo_crew = SEOCrew()
            return True
        except Exception as e:
            st.error(f"Failed to initialize SEO Crew: {str(e)}")
            return False
    return True

def get_score_color(score):
    """Get color class for score badge"""
    if score == 'N/A':
        return 'score-poor'
    try:
        score_val = float(score.split('/')[0])
        if score_val >= 8:
            return 'score-excellent'
        elif score_val >= 6:
            return 'score-good'
        elif score_val >= 4:
            return 'score-average'
        else:
            return 'score-poor'
    except:
        return 'score-poor'

def extract_score(analysis_text):
    """Extract score from analysis text"""
    if not analysis_text:
        return 'N/A'
    
    score_patterns = [
        r'(\d+(?:\.\d+)?)/10',
        r'score[:\s]*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)%'
    ]
    
    for pattern in score_patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return 'N/A'

def calculate_overall_score(data):
    """Calculate overall score from individual scores"""
    scores = []
    for key in ['content_analysis', 'image_analysis', 'keyword_analysis', 'backlink_analysis', 'url_analysis']:
        score = extract_score(data.get(key, ''))
        if score != 'N/A':
            try:
                scores.append(float(score))
            except ValueError:
                pass
    
    if scores:
        avg_score = sum(scores) / len(scores)
        return f"{avg_score:.1f}/10"
    
    return 'N/A'

def extract_priority_actions(data):
    """Extract priority actions from analysis data"""
    actions = []
    
    for key, value in data.items():
        if 'analysis' in key and isinstance(value, str):
            action_matches = re.findall(r'[-*]\s*(.+?)(?=\n|$)', value, re.MULTILINE)
            actions.extend(action_matches[:3])
    
    unique_actions = list(dict.fromkeys(actions))[:10]
    return unique_actions if unique_actions else ['No priority actions found']

def load_analysis_results(url):
    """Load analysis results from JSON files"""
    try:
        # Clean the URL to create a proper domain name
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('.', '_')
        
        # Try to find the analysis JSON file
        json_file = os.path.join(Config.OUTPUT_DIR, f"{domain}_analysis.json")
        if not os.path.exists(json_file):
            json_file = os.path.join(Config.OUTPUT_DIR, f"{domain}_simple_scrape.json")
        
        # Debug: List all files in output directory
        if os.path.exists(Config.OUTPUT_DIR):
            all_files = os.listdir(Config.OUTPUT_DIR)
            print(f"Debug: Files in {Config.OUTPUT_DIR}: {all_files}")
        
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    st.error("Analysis results file is empty. Please re-run the analysis.")
                    return None
                data = json.loads(content)
                if 'error' in data:
                    st.error(f"Analysis failed: {data['error']}")
                    return None
        else:
            # If no JSON file found, return basic data
            return {
                'url': url,
                'error': f'No analysis data found. Looked for: {json_file}. Please run the analysis again.'
            }
        
        # Extract analysis data from the JSON
        analysis_report = data.get('analysis_report', '')
        
        # Parse the analysis report to extract individual sections
        content_analysis = ''
        image_analysis = ''
        keyword_analysis = ''
        backlink_analysis = ''
        url_analysis = ''
        
        if analysis_report:
            # Split the report into sections based on headers
            sections = analysis_report.split('###')
            for section in sections:
                if 'Content Analysis' in section or 'Content' in section:
                    content_analysis = section.strip()
                elif 'Image Analysis' in section or 'Images' in section:
                    image_analysis = section.strip()
                elif 'Keyword Analysis' in section or 'Keywords' in section:
                    keyword_analysis = section.strip()
                elif 'Backlink Analysis' in section or 'Backlinks' in section:
                    backlink_analysis = section.strip()
                elif 'URL Analysis' in section or 'URL' in section:
                    url_analysis = section.strip()
        
        # If no sections found, use the entire report for content analysis
        if not content_analysis and analysis_report:
            content_analysis = analysis_report
        
        analysis_data = {
            'url': url,
            'content_score': extract_score(content_analysis),
            'image_score': extract_score(image_analysis),
            'keyword_score': extract_score(keyword_analysis),
            'backlink_score': extract_score(backlink_analysis),
            'url_score': extract_score(url_analysis),
            'overall_score': calculate_overall_score({
                'content_analysis': content_analysis,
                'image_analysis': image_analysis,
                'keyword_analysis': keyword_analysis,
                'backlink_analysis': backlink_analysis,
                'url_analysis': url_analysis
            }),
            'content_analysis': content_analysis,
            'image_analysis': image_analysis,
            'keyword_analysis': keyword_analysis,
            'backlink_analysis': backlink_analysis,
            'url_analysis': url_analysis,
            'priority_actions': extract_priority_actions({
                'content_analysis': content_analysis,
                'image_analysis': image_analysis,
                'keyword_analysis': keyword_analysis,
                'backlink_analysis': backlink_analysis,
                'url_analysis': url_analysis
            }),
            'scraped_data': {
                'title': data.get('title', ''),
                'meta_tags': data.get('meta_tags', {}),
                'headings': data.get('headings', {}),
                'paragraphs': data.get('paragraphs', []),
                'images': data.get('images', [])
            }
        }
        
        # Debug: Print what we found
        print(f"Debug: Found analysis data keys: {list(data.keys())}")
        print(f"Debug: Content analysis length: {len(data.get('content_analysis', ''))}")
        print(f"Debug: Image analysis length: {len(data.get('image_analysis', ''))}")
        print(f"Debug: Keyword analysis length: {len(data.get('keyword_analysis', ''))}")
        print(f"Debug: Backlink analysis length: {len(data.get('backlink_analysis', ''))}")
        print(f"Debug: URL analysis length: {len(data.get('url_analysis', ''))}")
        
        return analysis_data
        
    except Exception as e:
        st.error(f"Failed to load results: {str(e)}")
        return None

def create_radar_chart(scores):
    """Create a radar chart for SEO scores"""
    categories = ['Content', 'Images', 'Keywords', 'Backlinks', 'URLs']
    values = []
    
    for cat in categories:
        score = scores.get(f'{cat.lower()}_score', 'N/A')
        if score != 'N/A':
            try:
                values.append(float(score.split('/')[0]))
            except:
                values.append(0)
        else:
            values.append(0)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='SEO Scores',
        line_color='#667eea'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False,
        title="SEO Performance Radar Chart",
        height=400
    )
    
    return fig

def create_score_gauge(score, title):
    """Create a gauge chart for individual scores"""
    if score == 'N/A':
        value = 0
    else:
        try:
            value = float(score.split('/')[0])
        except:
            value = 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 5},
        gauge = {
            'axis': {'range': [None, 10]},
            'bar': {'color': "#667eea"},
            'steps': [
                {'range': [0, 4], 'color': "#EF4444"},
                {'range': [4, 6], 'color': "#F59E0B"},
                {'range': [6, 8], 'color': "#3B82F6"},
                {'range': [8, 10], 'color': "#10B981"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 8
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def download_file(file_path, filename):
    """Create download link for files"""
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="{filename}" class="download-button">📥 Download {filename}</a>'
        return href
    return None

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 SEO Analysis Tool</h1>
        <p>AI-Powered Website Analysis with CrewAI Agents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Environment check
        if not check_environment():
            st.error("❌ Environment check failed. Please check your GROQ_API_KEY.")
            st.stop()
        else:
            st.success("✅ Environment configured")
        
        # Headless mode toggle
        headless_mode = st.checkbox("Headless Mode", value=False, help="Run browser in headless mode")
        
        # Model selection
        st.subheader("🤖 AI Models")
        st.info(f"LLM: {Config.LLM_MODEL}")
        st.info(f"Search: {Config.SEARCH_MODEL}")
        
        # System status
        st.subheader("📊 System Status")
        if st.session_state.analysis_running:
            st.warning("🔄 Analysis in progress...")
        else:
            st.success("✅ Ready for analysis")
        
        # Recent analyses
        st.subheader("📋 Recent Analyses")
        if os.path.exists(Config.OUTPUT_DIR):
            files = [f for f in os.listdir(Config.OUTPUT_DIR) if f.endswith('.json')]
            if files:
                for file in files[-5:]:  # Show last 5
                    st.text(f"📄 {file}")
            else:
                st.text("No analyses yet")
    
    # Main content area
    st.header("🌐 Website Analysis")
    
    # URL input
    url = st.text_input(
        "Enter website URL",
        placeholder="https://example.com",
        help="Enter the full URL of the website you want to analyze"
    )
    
    # Analysis button
    if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            if not url:
                st.error("Please enter a URL")
            else:
                # Validate URL
                validated_url = validate_url(url)
                if not validated_url:
                    st.error("Invalid URL format")
                else:
                    # Initialize SEO crew
                    if not init_seo_crew():
                        st.error("Failed to initialize analysis system")
                    else:
                        st.session_state.analysis_running = True
                        st.session_state.current_url = validated_url
                        
                        # Run analysis
                        with st.spinner("Initializing analysis..."):
                            try:
                                # Update headless setting
                                Config.HEADLESS = headless_mode
                                
                                # Run the analysis
                                result = st.session_state.seo_crew.run_analysis(validated_url)
                                
                                if hasattr(result, 'error') and result.error:
                                    st.error(f"Analysis failed: {str(result.error)}")
                                else:
                                    st.success("Analysis completed successfully!")
                                    # Store the URL for results loading
                                    st.session_state.current_url = validated_url
                                    # Add a small delay to ensure file is written
                                    time.sleep(2)
                                    # Force reload the page to show results
                                    st.rerun()
                                
                            except Exception as e:
                                st.error(f"Analysis failed: {str(e)}")
                            finally:
                                st.session_state.analysis_running = False
    

    
    # Analysis progress
    if st.session_state.analysis_running:
        st.markdown("""
        <div class="progress-container">
            <h3>🔄 Analysis Progress</h3>
            <div class="analysis-step">
                <div class="step-icon step-running">1</div>
                <span>Scraping website content...</span>
            </div>
            <div class="analysis-step">
                <div class="step-icon step-pending">2</div>
                <span>Analyzing content structure...</span>
            </div>
            <div class="analysis-step">
                <div class="step-icon step-pending">3</div>
                <span>Processing images...</span>
            </div>
            <div class="analysis-step">
                <div class="step-icon step-pending">4</div>
                <span>Keyword analysis...</span>
            </div>
            <div class="analysis-step">
                <div class="step-icon step-pending">5</div>
                <span>Backlink evaluation...</span>
            </div>
            <div class="analysis-step">
                <div class="step-icon step-pending">6</div>
                <span>URL structure analysis...</span>
            </div>
            <div class="analysis-step">
                <div class="step-icon step-pending">7</div>
                <span>Generating final report...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Results display
    if st.session_state.current_url and not st.session_state.analysis_running:
        # Load results for the current URL
        results = load_analysis_results(st.session_state.current_url)
        
        # Debug info
        st.write(f"Debug: Current URL: {st.session_state.current_url}")
        st.write(f"Debug: Results keys: {list(results.keys()) if results else 'No results'}")
        
        if not results: # Check if results is None or empty
            st.info("Analysis completed. No results to display.")
            # Add a button to retry loading
            if st.button("🔄 Retry Loading Results"):
                st.rerun()
        elif 'error' in results:
            st.error(f"Error loading results: {results['error']}")
            # Add a button to retry loading
            if st.button("🔄 Retry Loading Results"):
                st.rerun()
        elif not results or not results.get('url'):
            st.info("Analysis completed. Loading results...")
            st.rerun()
        else:
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📊 Summary", "🕷️ Scraped Data", "📝 Content", "🖼️ Images", 
                "🔑 Keywords", "🔗 Backlinks", "🔗 URLs"
            ])
            
            with tab1:
                st.markdown("""
                <div class="tab-content">
                """, unsafe_allow_html=True)
                
                # Radar chart
                scores = {
                    'content_score': results.get('content_score', 'N/A'),
                    'image_score': results.get('image_score', 'N/A'),
                    'keyword_score': results.get('keyword_score', 'N/A'),
                    'backlink_score': results.get('backlink_score', 'N/A'),
                    'url_score': results.get('url_score', 'N/A')
                }
                
                # Generate default scores if none available
                if all(score == 'N/A' for score in scores.values()):
                    # Create basic scores based on scraped data
                    scraped_data = results.get('scraped_data', {})
                    if scraped_data:
                        # Simple scoring logic
                        title_score = 7 if scraped_data.get('title') else 3
                        headings_score = 6 if scraped_data.get('headings') else 3
                        paragraphs_score = 8 if len(scraped_data.get('paragraphs', [])) > 5 else 4
                        images_score = 6 if scraped_data.get('images') else 3
                        meta_score = 7 if scraped_data.get('meta_tags') else 3
                        
                        scores = {
                            'content_score': f"{((title_score + headings_score + paragraphs_score) / 3):.1f}/10",
                            'image_score': f"{images_score}/10",
                            'keyword_score': f"{meta_score}/10",
                            'backlink_score': '5.0/10',  # Default score
                            'url_score': f"{7 if results.get('url', '').startswith('https://') else 5}/10"
                        }
                
                # Overall score
                overall_score = results.get('overall_score', 'N/A')
                if overall_score == 'N/A':
                    # Calculate from individual scores
                    score_values = []
                    for score in scores.values():
                        if score != 'N/A':
                            try:
                                score_values.append(float(score.split('/')[0]))
                            except:
                                pass
                    if score_values:
                        overall_score = f"{sum(score_values) / len(score_values):.1f}/10"
                    else:
                        overall_score = "5.0/10"
                
                score_color = get_score_color(overall_score)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Overall SEO Score</h3>
                    <div class="score-badge {score_color}">{overall_score}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with tab2:
                st.markdown("""
                <div class="tab-content">
                """, unsafe_allow_html=True)
                
                scraped_data = results.get('scraped_data', {})
                
                # Title
                st.subheader("📄 Page Title")
                st.write(scraped_data.get('title', 'No title found'))
                
                # Meta tags
                st.subheader("🏷️ Meta Tags")
                meta_tags = scraped_data.get('meta_tags', {})
                if meta_tags:
                    meta_df = pd.DataFrame(list(meta_tags.items()), columns=['Tag', 'Content'])
                    st.dataframe(meta_df, use_container_width=True)
                else:
                    st.info("No meta tags found")
                
                # Headings
                st.subheader("📋 Headings")
                headings = scraped_data.get('headings', {})
                if headings:
                    for level, heading_list in headings.items():
                        if heading_list:
                            st.write(f"**{level.upper()}:**")
                            for heading in heading_list:
                                st.write(f"- {heading}")
                else:
                    st.info("No headings found")
                
                # Paragraphs
                st.subheader("📝 Paragraphs")
                paragraphs = scraped_data.get('paragraphs', [])
                if paragraphs:
                    st.write(f"Found {len(paragraphs)} paragraphs")
                    for i, para in enumerate(paragraphs[:5], 1):  # Show first 5
                        st.write(f"**{i}.** {para}")
                    if len(paragraphs) > 5:
                        st.write(f"... and {len(paragraphs) - 5} more")
                else:
                    st.info("No paragraphs found")
                
                # Images
                st.subheader("🖼️ Images")
                images = scraped_data.get('images', [])
                if images:
                    st.write(f"Found {len(images)} images")
                    for i, img in enumerate(images[:5], 1):  # Show first 5
                        st.write(f"**{i}.** {img.get('url', 'No URL')}")
                        if img.get('local_path'):
                            st.write(f"   Saved as: {img['local_path']}")
                    if len(images) > 5:
                        st.write(f"... and {len(images) - 5} more")
                else:
                    st.info("No images found")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with tab3:
                st.markdown("""
                <div class="tab-content">
                """, unsafe_allow_html=True)
                
                content_analysis = results.get('content_analysis', '')
                if content_analysis and content_analysis.strip():
                    st.subheader("📊 Content Analysis")
                    st.markdown(content_analysis)
                else:
                    st.info("No content analysis available")
                    st.write("The content analysis data is not available in the current results.")
                    # Show some basic content analysis based on scraped data
                    scraped_data = results.get('scraped_data', {})
                    if scraped_data:
                        st.subheader("📊 Basic Content Analysis")
                        st.write(f"**Page Title:** {scraped_data.get('title', 'No title')}")
                        st.write(f"**Number of Headings:** {len([h for h in scraped_data.get('headings', {}).values() if h])}")
                        st.write(f"**Number of Paragraphs:** {len(scraped_data.get('paragraphs', []))}")
                        st.write(f"**Number of Images:** {len(scraped_data.get('images', []))}")
                        st.write(f"**Meta Tags:** {len(scraped_data.get('meta_tags', {}))}")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with tab4:
                st.markdown("""
                <div class="tab-content">
                """, unsafe_allow_html=True)
                
                image_analysis = results.get('image_analysis', '')
                if image_analysis and image_analysis.strip():
                    st.subheader("🖼️ Image Analysis")
                    st.markdown(image_analysis)
                else:
                    st.info("No image analysis available")
                    st.write("The image analysis data is not available in the current results.")
                
                # Always show the analyzed images
                scraped_data = results.get('scraped_data', {})
                images = scraped_data.get('images', [])
                if images:
                    st.subheader("🖼️ Analyzed Images")
                    st.write(f"**Total Images Found:** {len(images)}")
                    
                    # Show first 2 images that were analyzed by vision model
                    analyzed_images = []
                    for img in images:
                        if img.get('local_path') and os.path.exists(img.get('local_path')):
                            analyzed_images.append(img)
                            if len(analyzed_images) >= 2:  # Only show first 2
                                break
                    
                    if analyzed_images:
                        st.write("**Images Analyzed by Vision Model:**")
                        for i, img in enumerate(analyzed_images, 1):
                            st.write(f"**Image {i}:**")
                            
                            # Display the actual image
                            try:
                                st.image(img['local_path'], caption=f"Image {i}: {img.get('alt', 'No alt text')}", use_container_width=True)
                            except Exception as e:
                                st.write(f"  - Could not display image: {str(e)}")
                            
                            # Show image details
                            st.write(f"  - **URL:** {img.get('url', 'No URL')}")
                            st.write(f"  - **Alt Text:** {img.get('alt', 'No alt text')}")
                            st.write(f"  - **Local Path:** {img.get('local_path', 'Not downloaded')}")
                            st.write(f"  - **File Type:** {os.path.splitext(img.get('local_path', ''))[1] if img.get('local_path') else 'Unknown'}")
                            
                            # Add separator between images
                            if i < len(analyzed_images):
                                st.divider()
                    else:
                        st.write("No images were successfully analyzed by the vision model.")
                    
                    # Show remaining images (if any)
                    remaining_images = images[2:] if len(images) > 2 else []
                    if remaining_images:
                        st.subheader("📋 Other Images")
                        st.write(f"**Additional Images Found:** {len(remaining_images)}")
                        for i, img in enumerate(remaining_images[:5], 1):  # Show first 5 of remaining
                            st.write(f"  - **Image {i}:** {img.get('url', 'No URL')}")
                            if img.get('alt'):
                                st.write(f"    Alt: {img.get('alt')}")
                        if len(remaining_images) > 5:
                            st.write(f"    ... and {len(remaining_images) - 5} more")
                else:
                    st.write("No images found on the page.")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with tab5:
                st.markdown("""
                <div class="tab-content">
                """, unsafe_allow_html=True)
                
                keyword_analysis = results.get('keyword_analysis', '')
                if keyword_analysis and keyword_analysis.strip():
                    st.subheader("🔑 Keyword Analysis")
                    st.markdown(keyword_analysis)
                else:
                    st.info("No keyword analysis available")
                    st.write("The keyword analysis data is not available in the current results.")
                    # Show basic keyword analysis based on scraped data
                    scraped_data = results.get('scraped_data', {})
                    if scraped_data:
                        st.subheader("🔑 Basic Keyword Analysis")
                        # Extract potential keywords from title and headings
                        title = scraped_data.get('title', '')
                        headings = scraped_data.get('headings', {})
                        all_text = title + ' ' + ' '.join([h for h_list in headings.values() for h in h_list if h])
                        
                        # Simple keyword extraction (words that appear multiple times)
                        import re
                        words = re.findall(r'\b\w+\b', all_text.lower())
                        word_count = {}
                        for word in words:
                            if len(word) > 3:  # Only words longer than 3 characters
                                word_count[word] = word_count.get(word, 0) + 1
                        
                        # Show top keywords
                        top_keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
                        if top_keywords:
                            st.write("**Potential Keywords (based on frequency):**")
                            for word, count in top_keywords:
                                st.write(f"  - {word}: {count} times")
                        else:
                            st.write("No significant keywords found.")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with tab6:
                st.markdown("""
                <div class="tab-content">
                """, unsafe_allow_html=True)
                
                backlink_analysis = results.get('backlink_analysis', '')
                if backlink_analysis and backlink_analysis.strip():
                    st.subheader("🔗 Backlink Analysis")
                    st.markdown(backlink_analysis)
                else:
                    st.info("No backlink analysis available")
                    st.write("The backlink analysis data is not available in the current results.")
                    # Show basic backlink analysis
                    st.subheader("🔗 Basic Backlink Analysis")
                    st.write("**Note:** Backlink analysis requires external data sources.")
                    st.write("**Recommendations:**")
                    st.write("  - Use tools like Ahrefs, Moz, or SEMrush for comprehensive backlink analysis")
                    st.write("  - Focus on building high-quality, relevant backlinks")
                    st.write("  - Monitor your backlink profile regularly")
                    st.write("  - Disavow toxic backlinks if necessary")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with tab7:
                st.markdown("""
                <div class="tab-content">
                """, unsafe_allow_html=True)
                
                url_analysis = results.get('url_analysis', '')
                if url_analysis and url_analysis.strip():
                    st.subheader("🔗 URL Analysis")
                    st.markdown(url_analysis)
                else:
                    st.info("No URL analysis available")
                    st.write("The URL analysis data is not available in the current results.")
                    # Show basic URL analysis
                    st.subheader("🔗 Basic URL Analysis")
                    current_url = results.get('url', '')
                    if current_url:
                        st.write(f"**Current URL:** {current_url}")
                        st.write(f"**URL Length:** {len(current_url)} characters")
                        st.write(f"**Contains Keywords:** {'Yes' if any(word in current_url.lower() for word in ['about', 'contact', 'blog', 'product']) else 'No'}")
                        st.write(f"**Uses HTTPS:** {'Yes' if current_url.startswith('https://') else 'No'}")
                        st.write(f"**Has Query Parameters:** {'Yes' if '?' in current_url else 'No'}")
                        st.write(f"**Has Fragments:** {'Yes' if '#' in current_url else 'No'}")
                        
                        st.write("**URL Optimization Tips:**")
                        st.write("  - Keep URLs short and descriptive")
                        st.write("  - Include relevant keywords")
                        st.write("  - Use hyphens instead of underscores")
                        st.write("  - Avoid unnecessary parameters")
                        st.write("  - Use lowercase letters")
                
                st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
