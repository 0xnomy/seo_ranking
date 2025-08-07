# Use an official Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for Playwright and general use
RUN apt-get update && \
    apt-get install -y wget curl git build-essential \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libxss1 libasound2 libxtst6 libxrandr2 libgtk-3-0 libgbm-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium)
RUN python -m playwright install --with-deps chromium

# Copy the rest of the code
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Set environment variable for Streamlit to run in headless mode
ENV STREAMLIT_SERVER_HEADLESS=true

# Default command: run the Streamlit app via the launcher script
CMD ["python", "run_streamlit.py"]
