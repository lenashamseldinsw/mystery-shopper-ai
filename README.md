# Abu Dhabi Customs Service Center Analysis
## تحليل مراكز الخدمة - جمارك أبوظبي

A Streamlit application powered by AI for analyzing service center performance data and generating intelligent insights in Arabic using Gemini Flash.

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up your API key (choose one method):**

**Method 1: Streamlit Secrets (Recommended for deployment)**
```toml
# Edit .streamlit/secrets.toml and add your API key
[gemini]
api_key = "your_actual_api_key_here"
```

**Method 2: Environment Variable**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

**Method 3: Manual Input**
- The app will prompt you to enter the key in the sidebar

3. **Run the application:**
```bash
streamlit run streamlit_analysis.py
```

## ✨ Features

- **AI-Powered Analysis**: Uses Gemini Flash to generate deep analytical insights
- **Custom Executive Summary**: Analyzes actual data and generates tailored insights
- **Smart Recommendations**: Specific and actionable improvement suggestions
- JSON data loading and analysis
- Overall performance score calculation
- Circular gauge display for total score
- Performance breakdown by pillars and sub-elements
- RTL support for Arabic text
- **Secure Secret Management**: Uses Streamlit Secrets
- **Sensitive File Protection**: Hides MS Use Case files and sensitive data
- **Deployment Ready**: Supports Streamlit Cloud, Heroku, and Docker

## 📊 Data Structure

The application expects a JSON file containing:
- Main pillars (المحاور الرئيسية)
- Sub-pillars (المحاور الفرعية)
- Attributes with scores and notes (الخصائص مع النتائج والملاحظات)

## 📱 Usage

1. Open the application in your browser
2. Upload a JSON file or use the default file
3. View the executive summary and detailed analysis
4. Download Arabic reports in DOCX format

## 🚀 Deployment

### Option 1: Streamlit Community Cloud (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy Abu Dhabi Customs analysis app"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io/
   - Connect your GitHub repository
   - Select your repository and main branch
   - Set the main file path: `streamlit_analysis.py`

3. **🚨 CRITICAL: Add Secrets in Streamlit Cloud:**
   - In your app dashboard, go to "Settings" → "Secrets"
   - Add your secrets in EXACT TOML format:
     ```toml
     [gemini]
     api_key = "your_actual_gemini_api_key_here"
     ```
   - **IMPORTANT**: Use the exact format above, including the section header `[gemini]`
   - Click "Save" and wait for the app to restart

### 🚨 **Common Deployment Issue**

If you see "يرجى إدخال مفتاح Gemini API لتوليد التحليلات الذكية" on your deployed app:

**➡️ This means you need to configure secrets in Streamlit Cloud**

**Quick Fix (2 minutes):**
1. Go to your Streamlit Cloud app dashboard
2. Click "Settings" → "Secrets"
3. Add this exact text:
   ```toml
   [gemini]
   api_key = "your_actual_gemini_api_key_here"
   ```
4. Click "Save" and wait for restart
5. ✅ Done! You should see "✅ تم تحميل مفتاح API من الإعدادات الآمنة" in the sidebar

### Option 2: Heroku Deployment

1. **Create Procfile:**
   ```bash
   echo "web: streamlit run streamlit_analysis.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile
   ```

2. **Deploy to Heroku:**
   ```bash
   heroku create your-app-name
   heroku config:set GEMINI_API_KEY="your_actual_api_key_here"
   git push heroku main
   ```

### Option 3: Docker Deployment

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8501
   HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
   ENTRYPOINT ["streamlit", "run", "streamlit_analysis.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and run:**
   ```bash
   docker build -t abu-dhabi-customs-app .
   docker run -p 8501:8501 -e GEMINI_API_KEY="your_api_key" abu-dhabi-customs-app
   ```

## 🔐 Security Features

- **Secure Secret Management**: Uses Streamlit Secrets for API keys
- **Protected Sensitive Files**: MS Use Case files and credentials excluded from git
- **Environment Variable Fallbacks**: Multiple secure loading methods
- **No Hardcoded Secrets**: API keys never exposed in code

### Files Protected by .gitignore

- `MS Use Case*.docx/xlsx/pptx` - MS Use Case documents
- `secrets.toml` - Streamlit secrets file
- `streamlit_data_export.txt` - Data export files
- Generated reports and credentials

## 🐛 Troubleshooting

### Common Issues:

1. **"No API key found" error:**
   - Check that your secrets are configured in Streamlit Cloud
   - Verify the API key format is correct
   - Ensure the API key is valid and active

2. **Import errors:**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+ recommended)

3. **File not found errors:**
   - Ensure the JSON data file exists in the correct location
   - Check that required files are committed to your repository

### Getting Help:

- Check Streamlit documentation: https://docs.streamlit.io/
- Gemini API documentation: https://ai.google.dev/docs
- Check the logs in your deployment platform

## 📁 Project Structure

```
AbuDhabiCustoms/
├── streamlit_analysis.py          # Main Streamlit app
├── report_utils.py               # Report generation utilities
├── requirements.txt              # Python dependencies
├── service_center_api_schema_RTL_FIXED.json  # Data file (REQUIRED)
├── abuDhabiCustomsLogo.png       # Logo file (REQUIRED)
├── .streamlit/
│   └── secrets.toml             # Streamlit secrets (DO NOT COMMIT)
├── .gitignore                   # Git ignore file (updated)
├── README.md                   # This comprehensive guide
├── QUICK_FIX.md               # Quick deployment fix
├── STREAMLIT_CLOUD_SETUP.md   # Detailed deployment guide
├── run_app.sh                 # Local startup script
└── streamlit_data_export.txt    # Temp file (auto-generated)
```

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **AI/ML**: Google Gemini Flash API
- **Data Processing**: Pandas, Plotly
- **Document Generation**: python-docx
- **Language Support**: Arabic (RTL) with English interface

## ⚠️ Security Best Practices

1. **Never commit secrets to version control**
2. **Use different API keys for development and production**
3. **Regularly rotate your API keys**
4. **Monitor API usage and set up billing alerts**
5. **Test locally before deploying to production**

---

**Get your Gemini API key from:** https://makersuite.google.com/app/apikey  
**Last Updated:** February 2026  
**Version:** 1.0.0
