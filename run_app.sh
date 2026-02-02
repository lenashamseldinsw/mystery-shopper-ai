#!/bin/bash
# Startup script for Abu Dhabi Customs Streamlit App

echo "🚀 Starting Abu Dhabi Customs Service Center Analysis App..."

# Check if .env file exists and load it
if [ -f .env ]; then
    echo "✅ Loading environment variables from .env file"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  .env file not found"
fi

# Check if API key is available
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY not found in environment"
    echo "Please check your .env file or .streamlit/secrets.toml"
else
    echo "✅ GEMINI_API_KEY is available"
fi

# Check if required files exist
echo "🔍 Checking required files..."
required_files=("streamlit_analysis.py" "service_center_api_schema_RTL_FIXED.json" "abuDhabiCustomsLogo.png")

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING"
        exit 1
    fi
done

echo "🎯 All checks passed! Starting Streamlit app..."
echo "📱 The app will open in your browser automatically"
echo "🔑 API key will be loaded automatically from your configuration"
echo ""

# Start the Streamlit app
streamlit run streamlit_analysis.py