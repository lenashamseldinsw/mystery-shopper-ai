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
- API key protection via .gitignore
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

For a comprehensive deployment guide, see [DEPLOYMENT.md](DEPLOYMENT.md) which includes:

- Streamlit Community Cloud deployment
- Heroku deployment
- Docker deployment
- Security best practices
- Troubleshooting common issues

## 🔐 Security Features

- Secure secret management using `secrets.toml`
- Comprehensive protection for sensitive files in `.gitignore`
- MS Use Case files protected from public deployment
- Secure deployment configurations

## 📁 Project Structure

```
AbuDhabiCustoms/
├── streamlit_analysis.py          # Main Streamlit app
├── report_utils.py               # Report generation utilities
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── secrets.toml             # Streamlit secrets (DO NOT COMMIT)
├── .gitignore                   # Git ignore file (updated)
├── DEPLOYMENT.md               # Deployment guide
├── README.md                   # This file
└── service_center_api_schema_RTL_FIXED.json  # Data file
```

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **AI/ML**: Google Gemini Flash API
- **Data Processing**: Pandas, Plotly
- **Document Generation**: python-docx
- **Language Support**: Arabic (RTL) with English interface
