#!/usr/bin/env python3
"""
Streamlit App Launcher for SEO Analysis Tool
"""

import os
import sys
import subprocess
from pathlib import Path
import dotenv 

dotenv.load_dotenv()

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'plotly', 
        'pandas',
        'crewai',
        'playwright'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Check if environment is properly configured"""
    if not os.getenv('GROQ_API_KEY'):
        print("❌ GROQ_API_KEY not found in environment variables")
        print("Please set your GROQ_API_KEY in a .env file or environment variables")
        return False
    
    return True

def install_playwright_browser():
    """Install Playwright browser if not already installed"""
    try:
        import playwright
        # Check if browser is installed
        result = subprocess.run(['playwright', 'install', 'chromium'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Playwright browser already installed")
        else:
            print("📦 Installing Playwright browser...")
            subprocess.run(['playwright', 'install', 'chromium'], check=True)
            print("✅ Playwright browser installed successfully")
    except Exception as e:
        print(f"⚠️ Could not verify Playwright browser: {e}")

def main():
    print("🚀 SEO Analysis Tool - Streamlit Launcher")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Install Playwright browser
    install_playwright_browser()
    
    print("\n✅ All checks passed!")
    print("🌐 Starting Streamlit app...")
    print("📱 The app will open in your browser at: http://localhost:8501")
    print("⏹️ Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Run Streamlit app
    try:
        subprocess.run(['streamlit', 'run', 'streamlit_app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped")
    except Exception as e:
        print(f"❌ Error running Streamlit app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
