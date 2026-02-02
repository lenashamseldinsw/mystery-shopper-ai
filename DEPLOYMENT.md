# Streamlit App Deployment Guide
# دليل نشر تطبيق Streamlit

This guide will help you deploy your Abu Dhabi Customs Service Center Analysis Streamlit app securely.

## 🔐 Security Setup (إعداد الأمان)

### 1. Configure Secrets (إعداد المفاتيح السرية)

The app now uses Streamlit's secure secrets management instead of environment variables.

**For Local Development:**
1. Copy the template secrets file:
   ```bash
   cp .streamlit/secrets.toml .streamlit/secrets_local.toml
   ```

2. Edit `.streamlit/secrets.toml` and add your actual API key:
   ```toml
   [gemini]
   api_key = "your_actual_gemini_api_key_here"
   ```

3. Get your Gemini API key from: https://makersuite.google.com/app/apikey

### 2. Files Protected by .gitignore

The following sensitive files are now protected and won't be committed to your repository:

- `MS Use Case*.docx` - MS Use Case documents
- `MS Use Case*.xlsx` - MS Use Case spreadsheets  
- `MS Use Case*.pptx` - MS Use Case presentations
- `secrets.toml` - Streamlit secrets file
- `streamlit_data_export.txt` - Data export files
- Generated reports (*.docx, *.pdf)
- API keys and credentials

## 🚀 Deployment Options

### Option 1: Streamlit Community Cloud (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add secure secrets management and update gitignore"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io/
   - Connect your GitHub repository
   - Select your repository and main branch
   - Set the main file path: `streamlit_analysis.py`

3. **Add Secrets in Streamlit Cloud:**
   - In your app dashboard, go to "Settings" → "Secrets"
   - Add your secrets in TOML format:
     ```toml
     [gemini]
     api_key = "your_actual_gemini_api_key_here"
     ```

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

## 🔧 Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up your API key (choose one method):

**Method A: Using secrets.toml (Recommended)**
```bash
# Edit .streamlit/secrets.toml and add your API key
```

**Method B: Using environment variable**
```bash
export GEMINI_API_KEY="your_actual_api_key_here"
```

**Method C: Enter manually in the app**
- The app will prompt you to enter the API key in the sidebar

### 3. Run the App
```bash
streamlit run streamlit_analysis.py
```

## 📁 Project Structure

```
AbuDhabiCustoms/
├── streamlit_analysis.py          # Main Streamlit app
├── report_utils.py               # Report generation utilities
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── secrets.toml             # Streamlit secrets (DO NOT COMMIT)
├── .gitignore                   # Git ignore file (updated)
├── DEPLOYMENT.md               # This deployment guide
├── README.md                   # Project documentation
└── service_center_api_schema_RTL_FIXED.json  # Data file
```

## ⚠️ Security Best Practices

1. **Never commit secrets to version control**
2. **Use different API keys for development and production**
3. **Regularly rotate your API keys**
4. **Monitor API usage and set up billing alerts**
5. **Use environment-specific secrets files**

## 🐛 Troubleshooting

### Common Issues:

1. **"No API key found" error:**
   - Check that your secrets.toml file exists and has the correct format
   - Verify the API key is valid and active

2. **Import errors:**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+ recommended)

3. **File not found errors:**
   - Ensure the JSON data file exists in the correct location
   - Check file permissions

### Getting Help:

- Check Streamlit documentation: https://docs.streamlit.io/
- Gemini API documentation: https://ai.google.dev/docs
- For deployment issues, check the specific platform's documentation

## 📞 Support

For technical support or questions about this deployment:
- Check the logs in your deployment platform
- Verify all environment variables and secrets are set correctly
- Test locally first before deploying to production

---

**Last Updated:** $(date)
**Version:** 1.0.0