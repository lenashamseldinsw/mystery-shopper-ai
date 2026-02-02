import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import google.generativeai as genai
from dotenv import load_dotenv
import io
import base64
import os
from datetime import datetime
import re
import sys

# Try to import toml for direct secrets file reading
try:
    import toml
except ImportError:
    toml = None

# Add current directory to path for local imports
sys.path.append(os.path.dirname(__file__))

# Load environment variables
load_dotenv()

# Set page config for RTL support
st.set_page_config(
    page_title="تحليل مراكز الخدمة - جمارك أبوظبي",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for RTL support and styling
st.markdown("""
<style>
    /* Global RTL support */
    .main .block-container {
        direction: rtl;
        text-align: right;
    }
    
    /* Move sidebar to right - simpler approach */
    .stApp {
        flex-direction: row-reverse;
    }
    
    /* RTL for main content */
    .stApp > div:first-child {
        direction: rtl;
    }
    
    /* Sidebar RTL alignment */
    section[data-testid="stSidebar"] > div {
        direction: rtl;
        text-align: right;
    }
    
    /* Tab content RTL */
    .stTabs [data-baseweb="tab-panel"] {
        direction: rtl;
        text-align: right;
    }
    
    .rtl {
        direction: rtl;
        text-align: right;
        font-family: 'Arial', sans-serif;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }
    .summary-text {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 10px;
        border-right: 4px solid #1f77b4;
        margin: 20px 0;
        direction: rtl;
        text-align: right;
        font-size: 16px;
        line-height: 1.8;
    }
    .pillar-analysis {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 10px;
        border-right: 4px solid #28a745;
        margin: 20px 0;
        direction: rtl;
        text-align: right;
        font-size: 16px;
        line-height: 1.8;
    }
    .header-arabic {
        color: #2c3e50;
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
        direction: rtl;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
    }
    .main-title {
        color: #2c3e50;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin: 10px 0 30px 0;
        direction: rtl;
    }
    .tab-title {
        color: #2c3e50;
        font-size: 18px;
        font-weight: bold;
        text-align: right;
        margin: 10px 0 20px 0;
        direction: rtl;
    }
    .pillar-score {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .insight-section {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        border-left: 4px solid #28a745;
        direction: rtl;
        text-align: right;
    }
    .recommendation-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-right: 4px solid #17a2b8;
        direction: rtl;
        text-align: right;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-excellent {
        background-color: #d4edda;
        color: #155724;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-needs-improvement {
        background-color: #fff3cd;
        color: #856404;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-critical {
        background-color: #f8d7da;
        color: #721c24;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .loading-text {
        text-align: center;
        color: #666;
        font-style: italic;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    
    
    
    /* RTL for Arabic text elements */
    .rtl, .rtl h1, .rtl h2, .rtl h3, .rtl h4, .rtl h5, .rtl h6, .rtl p {
        direction: rtl;
        text-align: right;
    }
    
    /* Plotly charts RTL */
    .js-plotly-plot {
        direction: ltr; /* Keep charts LTR for proper rendering */
    }
</style>
""", unsafe_allow_html=True)

def load_api_key_from_secrets_file():
    """Fallback method to read secrets file directly"""
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path) and toml:
        try:
            with open(secrets_path, 'r') as f:
                secrets = toml.load(f)
                # Try direct key first
                if 'GEMINI_API_KEY' in secrets:
                    return secrets['GEMINI_API_KEY']
                # Fallback to section-based key
                elif 'gemini' in secrets and 'api_key' in secrets['gemini']:
                    return secrets['gemini']['api_key']
                return None
        except Exception:
            return None
    return None

def setup_gemini_api():
    """Setup Gemini API with key from Streamlit secrets, environment, or user input"""
    api_key = None
    
    # Method 1: Try Streamlit secrets (works in Streamlit Cloud)
    try:
        # Check if secrets exist at all
        if hasattr(st, 'secrets'):
            # Try direct key first (preferred method)
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            
            # Fallback: Check [gemini] section for backward compatibility
            elif "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
                api_key = st.secrets["gemini"]["api_key"]
            
            # Validate the API key if found
            if api_key:
                # Convert to string and validate
                api_key = str(api_key).strip() if api_key else None
                
                if not (api_key and api_key not in ["your_gemini_api_key_here", "your_actual_api_key_here"] and len(api_key) > 10):
                    api_key = None
    except Exception as e:
        api_key = None
    
    # Method 2: Try direct file reading if st.secrets failed (local development)
    if not api_key:
        api_key = load_api_key_from_secrets_file()
        if not (api_key and api_key not in ["your_gemini_api_key_here", "your_actual_api_key_here"] and len(api_key) > 10):
            api_key = None
    
    # Method 3: Try environment variable (fallback)
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
        if not (api_key and len(api_key) > 10):
            api_key = None
    
    
    if not api_key:
        # Show error message for deployment configuration
        # Show main error message
        st.error("🚨 **Streamlit Cloud Secrets Configuration Required**")
        st.error("**تكوين المفاتيح السرية في Streamlit Cloud مطلوب**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 English Instructions")
            st.write("**Your app needs API key configuration in Streamlit Cloud:**")
            st.write("1. Go to your Streamlit Cloud app dashboard")
            st.write("2. Click **'Settings'** → **'Secrets'**")
            st.write("3. Add this exact content:")
            st.code("""GEMINI_API_KEY = "your_actual_api_key_here" """)
            st.write("4. Click **'Save'** and wait for app restart")
            st.info("💡 Replace `your_actual_api_key_here` with your real Gemini API key")
            st.info("🔗 Get your API key from: https://aistudio.google.com/app/apikey")
        
        with col2:
            st.subheader("🔧 التعليمات العربية")
            st.write("**يحتاج التطبيق إلى تكوين مفتاح API في Streamlit Cloud:**")
            st.write("1. اذهب إلى لوحة تحكم Streamlit Cloud")
            st.write("2. اضغط على **'Settings'** ثم **'Secrets'**")
            st.write("3. أضف النص التالي بالضبط:")
            st.code("""GEMINI_API_KEY = "your_actual_api_key_here" """)
            st.write("4. اضغط **'Save'** وانتظر إعادة تشغيل التطبيق")
            st.info("💡 استبدل `your_actual_api_key_here` بمفتاح Gemini API الحقيقي")
            st.info("🔗 احصل على مفتاح API من: https://aistudio.google.com/app/apikey")
        
        st.markdown("---")
        st.subheader("🐛 Debug Information")
        st.write("Use this information to troubleshoot the configuration:")
        
        # Show debug info in main area too
        for info in debug_info:
            if "✅" in info:
                st.success(info)
            elif "❌" in info:
                st.error(info)
            elif "⚠️" in info:
                st.warning(info)
            else:
                st.info(info)
        
        st.markdown("---")
        st.info("🔄 **After configuring secrets, refresh this page to continue.**")
        st.stop()  # Stop execution instead of asking for manual input
    
    try:
        genai.configure(api_key=api_key)
        
        # Try different model names in order of preference
        model_names = [
            'gemini-2.5-flash',
            'models/gemini-2.5-flash',
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-pro',
            'gemini-1.0-pro'
        ]
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                return model
            except Exception as model_error:
                continue
        
        # If all models fail, list available models
        try:
            available_models = genai.list_models()
            model_list = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            st.sidebar.error(f"النماذج المتاحة: {model_list}")
        except:
            pass
            
        st.error("فشل في تحميل أي نموذج من نماذج Gemini")
        return None
        
    except Exception as e:
        st.error(f"خطأ في إعداد Gemini API: {str(e)}")
        return None

def clean_and_format_text(text):
    """Clean asterisk formatting and convert to proper HTML bold"""
    if not text:
        return text
    
    # Replace **text** with <b>text</b>
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Replace *text* with <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    return text

def load_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {str(e)}")
        return None

def calculate_overall_score(data):
    """Calculate overall score based on pillar scores and weights"""
    total_score = 0
    total_weight = 0
    
    for pillar in data:
        pillar_score = pillar.get('pillar_score', 0)
        # Calculate pillar weight based on number of attributes
        pillar_weight = 0
        for sub_pillar in pillar.get('sub_pillars', []):
            for attribute in sub_pillar.get('attributes', []):
                if attribute.get('score') != '-':  # Exclude N/A items
                    pillar_weight += attribute.get('weight', 1)
        
        total_score += pillar_score * pillar_weight
        total_weight += pillar_weight
    
    return (total_score / total_weight * 100) if total_weight > 0 else 0

def analyze_performance_by_status(data):
    """Analyze performance by status (E, R, N)"""
    status_counts = {'E': 0, 'R': 0, 'N': 0, 'NA': 0}
    status_scores = {'E': [], 'R': [], 'N': [], 'NA': []}
    
    for pillar in data:
        for sub_pillar in pillar.get('sub_pillars', []):
            for attribute in sub_pillar.get('attributes', []):
                status = attribute.get('status', 'N')
                score = attribute.get('score', 0)
                
                if score == '-':
                    status_counts['NA'] += 1
                else:
                    status_counts[status] += 1
                    status_scores[status].append(float(score))
    
    return status_counts, status_scores

def analyze_pillar_performance(data, pillar_name_en):
    """Analyze performance for a specific pillar"""
    pillar_data = None
    for pillar in data:
        if pillar.get('pillar_en') == pillar_name_en:
            pillar_data = pillar
            break
    
    if not pillar_data:
        return None
    
    status_counts = {'E': 0, 'R': 0, 'N': 0, 'NA': 0}
    sub_pillar_analysis = []
    
    for sub_pillar in pillar_data.get('sub_pillars', []):
        sub_status_counts = {'E': 0, 'R': 0, 'N': 0, 'NA': 0}
        attributes_detail = []
        
        for attribute in sub_pillar.get('attributes', []):
            status = attribute.get('status', 'N')
            score = attribute.get('score', 0)
            
            if score == '-':
                status_counts['NA'] += 1
                sub_status_counts['NA'] += 1
            else:
                status_counts[status] += 1
                sub_status_counts[status] += 1
            
            attributes_detail.append({
                'description': attribute.get('attribute_en', ''),
                'status': status,
                'score': score,
                'notes_ar': attribute.get('notes_ar', ''),
                'weight': attribute.get('weight', 1)
            })
        
        sub_pillar_analysis.append({
            'name_ar': sub_pillar.get('sub_pillar_ar', ''),
            'name_en': sub_pillar.get('sub_pillar_en', ''),
            'status_counts': sub_status_counts,
            'attributes': attributes_detail
        })
    
    return {
        'pillar_name_ar': pillar_data.get('pillar_ar', ''),
        'pillar_score': pillar_data.get('pillar_score', 0),
        'status_counts': status_counts,
        'sub_pillars': sub_pillar_analysis
    }

def prepare_data_for_gemini(data, overall_score, status_counts):
    """Prepare structured data summary for Gemini analysis"""
    
    # Extract key information
    pillars_summary = []
    detailed_findings = []
    
    for pillar in data:
        pillar_name_ar = pillar.get('pillar_ar', pillar.get('pillar_en', ''))
        pillar_name_en = pillar.get('pillar_en', '')
        pillar_score = pillar.get('pillar_score', 0)
        
        pillar_info = {
            'name_ar': pillar_name_ar,
            'name_en': pillar_name_en,
            'score': pillar_score,
            'sub_pillars': []
        }
        
        for sub_pillar in pillar.get('sub_pillars', []):
            sub_pillar_name_ar = sub_pillar.get('sub_pillar_ar', sub_pillar.get('sub_pillar_en', ''))
            sub_pillar_name_en = sub_pillar.get('sub_pillar_en', '')
            
            attributes_summary = []
            for attribute in sub_pillar.get('attributes', []):
                attr_summary = {
                    'description': attribute.get('attribute_en', ''),
                    'status': attribute.get('status', 'N'),
                    'score': attribute.get('score', 0),
                    'weight': attribute.get('weight', 1),
                    'notes_ar': attribute.get('notes_ar', ''),
                    'report_notes_ar': attribute.get('report_notes_ar', '')
                }
                attributes_summary.append(attr_summary)
                
                # Add to detailed findings for context
                if attribute.get('notes_ar'):
                    detailed_findings.append({
                        'pillar': pillar_name_ar,
                        'sub_pillar': sub_pillar_name_ar,
                        'status': attribute.get('status', 'N'),
                        'notes': attribute.get('notes_ar', '')
                    })
            
            pillar_info['sub_pillars'].append({
                'name_ar': sub_pillar_name_ar,
                'name_en': sub_pillar_name_en,
                'attributes': attributes_summary
            })
        
        pillars_summary.append(pillar_info)
    
    return {
        'overall_score': overall_score,
        'status_counts': status_counts,
        'pillars': pillars_summary,
        'detailed_findings': detailed_findings
    }

def generate_executive_summary(model, data_summary):
    """Generate executive summary using Gemini"""
    
    prompt = f"""
أنت محلل خبير في تقييم مراكز الخدمة الحكومية. بناءً على البيانات التالية من تقييم مركز خدمة جمارك أبوظبي، اكتب ملخصاً تنفيذياً شاملاً باللغة العربية.

البيانات:
- المعدل الكلي للأداء: {data_summary['overall_score']:.1f}%
- العناصر المتميزة (E): {data_summary['status_counts']['E']} عنصر
- العناصر التي تحتاج تحسين (R): {data_summary['status_counts']['R']} عنصر  
- العناصر الحرجة (N): {data_summary['status_counts']['N']} عنصر

المحاور الرئيسية:
{json.dumps(data_summary['pillars'], ensure_ascii=False, indent=2)}

المطلوب:
1. اكتب ملخصاً تنفيذياً مهنياً باللغة العربية (3-4 فقرات)
2. ركز على النقاط الإيجابية والتحديات الرئيسية
3. قدم توصيات عملية للتحسين
4. استخدم أسلوباً مهنياً يناسب التقارير الحكومية
5. اذكر الأرقام والنسب المئوية بشكل طبيعي في النص

تعليمات مهمة:
- لا تبدأ بعبارات مثل "يسرنا تقديم" أو "نتشرف بتقديم" أو أي عبارات ترحيبية
- ابدأ مباشرة بالتحليل والنتائج
- استخدم أسلوباً تقريرياً مهنياً ومباشراً
- لا تستخدم عناوين أو نقاط، فقط نص متدفق ومترابط
- اجعل التحليل موضوعياً وقائماً على البيانات
- لا تستخدم تنسيق markdown مثل **نص** أو *نص*
"""

    try:
        response = model.generate_content(prompt)
        if response and hasattr(response, 'text') and response.text:
            return response.text
        else:
            st.error("لم يتم إنتاج أي محتوى من النموذج")
            return None
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            st.error("النموذج المطلوب غير متاح. يرجى المحاولة مرة أخرى.")
        elif "quota" in error_msg.lower():
            st.error("تم تجاوز حد الاستخدام المسموح. يرجى المحاولة لاحقاً.")
        elif "api_key" in error_msg.lower():
            st.error("مشكلة في مفتاح API. يرجى التحقق من صحة المفتاح.")
        else:
            st.error(f"خطأ في توليد التحليل: {error_msg}")
        return None

def generate_pillar_analysis(model, pillar_data, pillar_name):
    """Generate detailed analysis for a specific pillar"""
    
    prompt = f"""
أنت محلل خبير في تقييم مراكز الخدمة. اكتب تحليلاً تفصيلياً لمحور "{pillar_name}" بناءً على البيانات التالية:

بيانات المحور:
- اسم المحور: {pillar_data['pillar_name_ar']}
- نتيجة المحور: {pillar_data['pillar_score']}
- العناصر المتميزة: {pillar_data['status_counts']['E']}
- العناصر التي تحتاج تحسين: {pillar_data['status_counts']['R']}
- العناصر الحرجة: {pillar_data['status_counts']['N']}

المحاور الفرعية والتفاصيل:
{json.dumps(pillar_data['sub_pillars'], ensure_ascii=False, indent=2)}

المطلوب:
1. ابدأ بجملة تلخص الأداء العام للمحور مع ذكر النسبة المئوية
2. اكتب فقرة تحليلية تفصيلية (150-200 كلمة) تشمل:
   - النقاط الإيجابية المحققة
   - التحديات والفجوات المحددة
   - تأثير هذه النتائج على تجربة المتعاملين
3. اختتم بجملة تلخص النتيجة العامة للمحور (مرتفع/منخفض/متوسط)

استخدم أسلوباً مهنياً ومترابطاً، ولا تستخدم نقاط أو عناوين فرعية.

تعليمات التنسيق:
- لا تستخدم تنسيق markdown مثل **نص** أو *نص*
- اكتب النص بشكل عادي بدون رموز تنسيق
"""

    try:
        response = model.generate_content(prompt)
        if response and hasattr(response, 'text') and response.text:
            return response.text
        else:
            return None
    except Exception as e:
        st.error(f"خطأ في توليد تحليل المحور: {str(e)}")
        return None

def generate_recommendations(model, data_summary):
    """Generate development recommendations using Gemini"""
    
    prompt = f"""
بناءً على تقييم مركز خدمة جمارك أبوظبي، قدم مقترحات تطويرية محددة وقابلة للتطبيق مقسمة حسب المجالات.

البيانات:
- المعدل الكلي: {data_summary['overall_score']:.1f}%
- المشاكل الحرجة: {data_summary['status_counts']['N']} عنصر
- العناصر التي تحتاج تحسين: {data_summary['status_counts']['R']} عنصر

التحديات الرئيسية:
{json.dumps([f for f in data_summary['detailed_findings'] if f['status'] in ['N', 'R']][:10], ensure_ascii=False, indent=2)}

المطلوب تقسيم المقترحات إلى 5 مجالات رئيسية:

### البيئة العامة
● مقترح محدد وعملي للبيئة العامة
● مقترح آخر للبيئة العامة

### مواقف السيارات  
● مقترح محدد وعملي لمواقف السيارات
● مقترح آخر لمواقف السيارات

### المبنى
● مقترح محدد وعملي للمبنى
● مقترح آخر للمبنى

### القدرة الاستيعابية والانتظار
● مقترح محدد وعملي للقدرة الاستيعابية
● مقترح آخر للقدرة الاستيعابية

### سهولة الوصول إلى الموقع
● مقترح محدد وعملي لسهولة الوصول
● مقترح آخر لسهولة الوصول

تعليمات مهمة للتنسيق:
- لا تستخدم قوائم مرقمة (1. 2. 3.)
- استخدم عناوين بـ ### لكل مجال
- استخدم رمز ● للنقاط (سيتم تحويله إلى شرطة عربية في التقرير)
- لا تستخدم تنسيق markdown مثل **نص** أو *نص*
- اكتب كل مقترح في جملة واضحة ومحددة
"""

    try:
        response = model.generate_content(prompt)
        if response and hasattr(response, 'text') and response.text:
            return response.text
        else:
            return None
    except Exception as e:
        st.error(f"خطأ في توليد التوصيات: {str(e)}")
        return None

def create_score_gauge(score):
    """Create a circular gauge chart for the overall score"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "المعدل الكلي", 'font': {'size': 24, 'family': 'Arial'}},
        delta = {'reference': 70},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#1f77b4"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ffcccc'},
                {'range': [50, 70], 'color': '#fff2cc'},
                {'range': [70, 100], 'color': '#d4edda'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor = "white",
        font = {'color': "darkblue", 'family': "Arial"},
        height = 400
    )
    
    return fig

def create_pillar_status_chart(pillar_data):
    """Create a status chart for pillar sub-elements"""
    sub_pillars = []
    statuses = []
    colors = []
    
    color_map = {'E': '#28a745', 'R': '#ffc107', 'N': '#dc3545', 'NA': '#6c757d'}
    status_map = {'E': 'مرتفع', 'R': 'متوسط', 'N': 'منخفض', 'NA': 'لا ينطبق'}
    
    for sub_pillar in pillar_data['sub_pillars']:
        # Determine dominant status for this sub-pillar
        status_counts = sub_pillar['status_counts']
        dominant_status = max(status_counts.items(), key=lambda x: x[1])[0]
        
        sub_pillars.append(sub_pillar['name_ar'])
        statuses.append(status_map[dominant_status])
        colors.append(color_map[dominant_status])
    
    fig = go.Figure(data=[
        go.Bar(
            y=sub_pillars,
            x=[1] * len(sub_pillars),
            orientation='h',
            marker_color=colors,
            text=statuses,
            textposition='inside',
            textfont=dict(color='white', size=14, family='Arial'),
            hovertemplate='<b>%{y}</b><br>المستوى: %{text}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=f"مستويات الأداء - {pillar_data['pillar_name_ar']}",
        title_font=dict(size=18, family='Arial'),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(autorange="reversed"),
        height=400,
        margin=dict(l=200, r=50, t=80, b=50),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    
    return fig

def create_recommendations_flowchart():
    """Create a visual flowchart for recommendations"""
    # This is a simplified representation using plotly
    categories = [
        "البيئة العامة",
        "مواقف السيارات", 
        "المبنى",
        "القدرة الاستيعابية والانتظار",
        "سهولة الوصول إلى الموقع"
    ]
    
    fig = go.Figure()
    
    # Add boxes for each category
    for i, category in enumerate(categories):
        fig.add_shape(
            type="rect",
            x0=0, y0=i*2, x1=4, y1=i*2+1,
            fillcolor="#f8f9fa",
            line=dict(color="#6c757d", width=2)
        )
        
        fig.add_annotation(
            x=2, y=i*2+0.5,
            text=category,
            showarrow=False,
            font=dict(size=14, family='Arial', color='#2c3e50'),
            bgcolor="white",
            bordercolor="#6c757d",
            borderwidth=1
        )
    
    fig.update_layout(
        title="مجالات التطوير المقترحة",
        title_font=dict(size=18, family='Arial'),
        showlegend=False,
        xaxis=dict(showticklabels=False, showgrid=False, range=[-0.5, 4.5]),
        yaxis=dict(showticklabels=False, showgrid=False, range=[-0.5, len(categories)*2]),
        height=400,
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    
    return fig

def generate_html_report(data, overall_score, status_counts, ai_summary, accessibility_analysis, appearance_analysis, recommendations):
    """Generate HTML report with proper Arabic support"""
    
    # Clean text function for HTML
    def clean_text_for_html(text):
        if not text:
            return ""
        # Keep HTML formatting but clean dangerous tags
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        return text
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>تقرير تحليل أداء مراكز الخدمة - جمارك أبوظبي</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
            
            body {{
                font-family: 'Noto Sans Arabic', Arial, sans-serif;
                direction: rtl;
                text-align: right;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
            }}
            
            .header h1 {{
                color: #2c3e50;
                font-size: 24px;
                margin: 0;
                font-weight: 700;
            }}
            
            .date {{
                color: #666;
                font-size: 14px;
                margin-top: 10px;
            }}
            
            .section {{
                margin: 30px 0;
                page-break-inside: avoid;
            }}
            
            .section-title {{
                color: #2c3e50;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 15px;
                border-right: 4px solid #3498db;
                padding-right: 15px;
            }}
            
            .metrics-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .metrics-table th {{
                background-color: #34495e;
                color: white;
                padding: 12px;
                text-align: right;
                font-weight: 700;
            }}
            
            .metrics-table td {{
                padding: 12px;
                border-bottom: 1px solid #ddd;
                text-align: right;
            }}
            
            .metrics-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            .content-box {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-right: 4px solid #3498db;
                margin: 15px 0;
                line-height: 1.8;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            @media print {{
                body {{
                    margin: 0;
                    padding: 15px;
                }}
                .page-break {{
                    page-break-before: always;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>تقرير تحليل أداء مراكز الخدمة</h1>
            <h2 style="color: #7f8c8d; font-size: 16px; margin: 5px 0;">جمارك أبوظبي</h2>
            <div class="date">تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}</div>
        </div>

        <div class="section">
            <h2 class="section-title">التحليل المدعوم بالذكاء الاصطناعي</h2>
            
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>المؤشر</th>
                        <th>القيمة</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>المعدل الكلي للأداء</td>
                        <td><strong>{overall_score:.1f}%</strong></td>
                    </tr>
                    <tr>
                        <td>العناصر المتميزة</td>
                        <td><strong>{status_counts["E"]} عنصر</strong></td>
                    </tr>
                    <tr>
                        <td>العناصر التي تحتاج تحسين</td>
                        <td><strong>{status_counts["R"]} عنصر</strong></td>
                    </tr>
                    <tr>
                        <td>العناصر الحرجة</td>
                        <td><strong>{status_counts["N"]} عنصر</strong></td>
                    </tr>
                </tbody>
            </table>
            
            {f'<div class="content-box">{clean_text_for_html(ai_summary)}</div>' if ai_summary else ''}
        </div>

        <div class="section page-break">
            <h2 class="section-title">نتائج التقييم - محور سهولة الوصول</h2>
            {f'<div class="content-box">{clean_text_for_html(accessibility_analysis)}</div>' if accessibility_analysis else '<p>لا توجد بيانات متاحة</p>'}
        </div>

        <div class="section page-break">
            <h2 class="section-title">نتائج التقييم - محور المظهر العام</h2>
            {f'<div class="content-box">{clean_text_for_html(appearance_analysis)}</div>' if appearance_analysis else '<p>لا توجد بيانات متاحة</p>'}
        </div>

        <div class="section page-break">
            <h2 class="section-title">المقترحات التطويرية بناءً على الفرص التحسينية</h2>
            {f'<div class="content-box">{clean_text_for_html(recommendations)}</div>' if recommendations else '<p>لا توجد مقترحات متاحة</p>'}
        </div>
    </body>
    </html>
    """
    
    return html_content

# PDF functionality removed - using DOCX only
# class ArabicPDF(FPDF):
    """Custom FPDF class with Arabic/RTL support"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        # Add Unicode font support for Arabic
        self.font_family = 'Arial'  # Default fallback
        
        # Try various Arabic-supporting fonts available on macOS
        font_paths = [
            ('/System/Library/Fonts/Arial Unicode MS.ttf', 'ArialUni'),
            ('/System/Library/Fonts/Helvetica.ttc', 'Helvetica'),
            ('/Library/Fonts/Arial Unicode MS.ttf', 'ArialUni2'),
            ('/System/Library/Fonts/Times.ttc', 'Times')
        ]
        
        for font_path, font_name in font_paths:
            try:
                if os.path.exists(font_path):
                    self.add_font(font_name, '', font_path, uni=True)
                    if os.path.exists(font_path.replace('.ttf', ' Bold.ttf').replace('.ttc', ' Bold.ttc')):
                        self.add_font(font_name, 'B', font_path.replace('.ttf', ' Bold.ttf').replace('.ttc', ' Bold.ttc'), uni=True)
                    else:
                        self.add_font(font_name, 'B', font_path, uni=True)  # Use same font for bold
                    self.font_family = font_name
                    break
            except:
                continue
        
    def format_arabic_text(self, text):
        """Format Arabic text for proper RTL display"""
        if not text:
            return ""
        
        # Clean HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        try:
            # Reshape Arabic text
            reshaped_text = arabic_reshaper.reshape(text)
            
            # Apply bidirectional algorithm
            bidi_text = get_display(reshaped_text)
            
            return bidi_text
        except:
            # If Arabic processing fails, return original text
            return text
    
    def add_arabic_text(self, text, font_size=12, style=''):
        """Add Arabic text with proper formatting"""
        self.set_font(self.font_family, style, font_size)
        formatted_text = self.format_arabic_text(text)
        
        # Split text into lines that fit the page width
        lines = []
        words = formatted_text.split(' ')
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.get_string_width(test_line) < (self.w - 40):  # 20mm margins on each side
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Add each line
        for line in lines:
            self.cell(0, 8, line, ln=True, align='R')
    
    def add_section_title(self, title):
        """Add a section title with formatting"""
        self.ln(10)
        self.set_font(self.font_family, 'B', 16)
        self.set_text_color(44, 62, 80)  # Dark blue
        formatted_title = self.format_arabic_text(title)
        self.cell(0, 12, formatted_title, ln=True, align='R')
        self.ln(5)
        self.set_text_color(0, 0, 0)  # Reset to black
    
    def add_metrics_table(self, overall_score, status_counts):
        """Add metrics table"""
        self.ln(5)
        
        # Table data
        table_data = [
            ('المؤشر', 'القيمة'),
            ('المعدل الكلي للأداء', f'{overall_score:.1f}%'),
            ('العناصر المتميزة', f'{status_counts["E"]} عنصر'),
            ('العناصر التي تحتاج تحسين', f'{status_counts["R"]} عنصر'),
            ('العناصر الحرجة', f'{status_counts["N"]} عنصر')
        ]
        
        # Table styling
        col_width = (self.w - 40) / 2  # Two columns
        row_height = 10
        
        for i, (col1, col2) in enumerate(table_data):
            if i == 0:  # Header row
                self.set_fill_color(52, 73, 94)  # Dark blue
                self.set_text_color(255, 255, 255)  # White text
                self.set_font(self.font_family, 'B', 12)
            else:
                self.set_fill_color(248, 249, 250)  # Light gray
                self.set_text_color(0, 0, 0)  # Black text
                self.set_font(self.font_family, '', 11)
            
            # Format Arabic text
            formatted_col1 = self.format_arabic_text(col1)
            formatted_col2 = self.format_arabic_text(col2)
            
            # Add cells (RTL order)
            self.cell(col_width, row_height, formatted_col2, border=1, align='C', fill=True)
            self.cell(col_width, row_height, formatted_col1, border=1, align='C', fill=True, ln=True)
        
        self.ln(10)
        self.set_text_color(0, 0, 0)  # Reset color

# PDF functionality removed - using DOCX only
# def generate_comprehensive_pdf_report(data, overall_score, status_counts, ai_summary, accessibility_analysis, appearance_analysis, recommendations):
    """Generate comprehensive PDF report with all tab data and beautiful formatting"""
    
    try:
        # pdf = FPDF()  # PDF functionality removed
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # Add first page
        pdf.add_page()
        
        # Add logo to header
        logo_path = "abuDhabiCustomsLogo.png"
        if os.path.exists(logo_path):
            try:
                # Center the logo
                pdf.image(logo_path, x=60, y=20, w=90)
                pdf.ln(40)
            except:
                # Fallback if logo fails to load
                pdf.set_font('Arial', 'B', 24)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 15, "ABU DHABI CUSTOMS", ln=True, align='C')
                pdf.ln(10)
        else:
            # Fallback header
            pdf.set_font('Arial', 'B', 24)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 15, "ABU DHABI CUSTOMS", ln=True, align='C')
            pdf.ln(10)
        
        # Report title
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 15, "Service Center Performance Analysis Report", ln=True, align='C')
        
        # Date and subtitle
        pdf.set_font('Arial', '', 14)
        pdf.set_text_color(102, 102, 102)
        pdf.cell(0, 10, f"Report Generated: {datetime.now().strftime('%B %d, %Y')}", ln=True, align='C')
        pdf.ln(20)
        
        # Add decorative line
        pdf.set_draw_color(44, 62, 80)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(15)
        
        # Reset text color
        pdf.set_text_color(0, 0, 0)
        
        # ===== SECTION 1: EXECUTIVE SUMMARY =====
        pdf.add_section_header("1. AI-Powered Executive Summary")
        
        # Performance overview box
        pdf.set_fill_color(240, 248, 255)
        pdf.rect(20, pdf.get_y(), 170, 25, 'F')
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, f"Overall Performance Score: {overall_score:.1f}%", ln=True, align='C')
        pdf.ln(2)
        
        # Metrics in a professional table
        pdf.create_metrics_table(overall_score, status_counts)
        
        # AI Summary content
        if ai_summary:
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "Key Insights:", ln=True)
            pdf.ln(2)
            
            # Extract key points from AI summary (simplified for English)
            summary_points = [
                "The service center demonstrates good accessibility with proper signage and location visibility on Google Maps.",
                "Parking facilities are adequate with designated spaces for people of determination.",
                "Appearance aspects show room for improvement, particularly in maintenance and seating capacity.",
                "Noise levels and temperature control require attention for enhanced customer comfort.",
                "Overall performance indicates a solid foundation with specific areas identified for enhancement."
            ]
            
            pdf.set_font('Arial', '', 11)
            for i, point in enumerate(summary_points, 1):
                pdf.cell(8, 6, f"{i}.", align='L')
                pdf.cell(0, 6, point, ln=True, align='L')
                pdf.ln(1)
        
        # ===== SECTION 2: ACCESSIBILITY ANALYSIS =====
        pdf.add_page()
        pdf.add_section_header("2. Accessibility Assessment")
        
        # Get accessibility data
        accessibility_data = analyze_pillar_performance(data, "Accessibility")
        if accessibility_data:
            pdf.create_pillar_analysis_section(accessibility_data, "Accessibility")
        
        # Add detailed findings
        if accessibility_analysis:
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "Detailed Analysis:", ln=True)
            pdf.ln(2)
            
            # Simplified accessibility summary
            access_summary = [
                "Navigation: Service center location is correctly displayed on Google Maps with clear directions.",
                "Parking: Adequate parking spaces available including designated areas for people of determination.",
                "Signage: Service center signs are visible and readable from appropriate distances.",
                "Physical Access: Pathways are clear of obstacles with proper accessibility features."
            ]
            
            pdf.set_font('Arial', '', 11)
            for i, point in enumerate(access_summary, 1):
                pdf.cell(8, 6, f"{i}.", align='L')
                pdf.cell(0, 6, point, ln=True, align='L')
                pdf.ln(1)
        
        # ===== SECTION 3: APPEARANCE ANALYSIS =====
        pdf.add_page()
        pdf.add_section_header("3. Appearance & Environment Assessment")
        
        # Get appearance data
        appearance_data = analyze_pillar_performance(data, "Appearance")
        if appearance_data:
            pdf.create_pillar_analysis_section(appearance_data, "Appearance")
        
        # Add detailed findings
        if appearance_analysis:
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, "Detailed Analysis:", ln=True)
            pdf.ln(2)
            
            # Simplified appearance summary
            appear_summary = [
                "Ambience: Temperature and lighting are generally appropriate with some areas for improvement.",
                "Cleanliness: Both exterior and interior maintain acceptable cleanliness standards.",
                "Lighting: Adequate lighting throughout the facility supporting customer comfort.",
                "Seating: Limited seating capacity during peak hours requires attention for customer comfort."
            ]
            
            pdf.set_font('Arial', '', 11)
            for i, point in enumerate(appear_summary, 1):
                pdf.cell(8, 6, f"{i}.", align='L')
                pdf.cell(0, 6, point, ln=True, align='L')
                pdf.ln(1)
        
        # ===== SECTION 4: DEVELOPMENT RECOMMENDATIONS =====
        pdf.add_page()
        pdf.add_section_header("4. Strategic Development Recommendations")
        
        if recommendations:
            # Create recommendation categories
            rec_categories = [
                {
                    "title": "Environment & Ambience",
                    "items": [
                        "Implement noise reduction measures in waiting areas",
                        "Optimize temperature control systems for consistent comfort",
                        "Enhance lighting quality in service areas"
                    ]
                },
                {
                    "title": "Infrastructure & Facilities", 
                    "items": [
                        "Increase seating capacity for peak hour management",
                        "Upgrade signage visibility and clarity",
                        "Improve maintenance schedules for exterior areas"
                    ]
                },
                {
                    "title": "Accessibility & Navigation",
                    "items": [
                        "Enhance digital presence on mapping platforms",
                        "Improve directional signage within the facility",
                        "Optimize parking space allocation and marking"
                    ]
                }
            ]
            
            for category in rec_categories:
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 8, category["title"], ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(2)
                
                pdf.set_font('Arial', '', 11)
                for i, item in enumerate(category["items"], 1):
                    pdf.cell(10, 6, f"{i}.", align='L')
                    pdf.cell(0, 6, item, ln=True, align='L')
                    pdf.ln(1)
                pdf.ln(3)
        
        # ===== FOOTER SECTION =====
        pdf.ln(10)
        pdf.set_draw_color(44, 62, 80)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(102, 102, 102)
        pdf.cell(0, 6, "This report was generated using AI-powered analysis of service center evaluation data.", ln=True, align='C')
        pdf.cell(0, 6, f"Abu Dhabi Customs - Service Excellence Initiative - {datetime.now().year}", ln=True, align='C')
        
        # Generate PDF buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        return pdf_buffer
        
    except Exception as e:
        st.error(f"خطأ في إنتاج PDF: {str(e)}")
        return None

# Add helper methods to FPDF class
# PDF functionality removed - using DOCX only
# class FPDF(FPDF):
    def add_section_header(self, title):
        """Add a formatted section header"""
        self.ln(5)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(44, 62, 80)
        
        # Add background rectangle
        self.set_fill_color(240, 248, 255)
        self.rect(20, self.get_y(), 170, 12, 'F')
        
        self.cell(0, 12, title, ln=True, align='L')
        self.set_text_color(0, 0, 0)
        self.ln(5)
    
    def create_metrics_table(self, overall_score, status_counts):
        """Create a professional metrics table"""
        self.ln(10)
        
        # Table header
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(52, 73, 94)
        self.set_text_color(255, 255, 255)
        
        col_width = 85
        self.cell(col_width, 12, "Performance Metric", border=1, align='C', fill=True)
        self.cell(col_width, 12, "Value", border=1, align='C', fill=True, ln=True)
        
        # Table data
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        
        metrics = [
            ("Overall Performance Score", f"{overall_score:.1f}%"),
            ("Excellent Elements (E)", f"{status_counts['E']} items"),
            ("Needs Improvement (R)", f"{status_counts['R']} items"),
            ("Critical Elements (N)", f"{status_counts['N']} items"),
            ("Total Evaluated Items", f"{sum([status_counts[k] for k in ['E', 'R', 'N']])} items")
        ]
        
        for i, (metric, value) in enumerate(metrics):
            if i % 2 == 0:
                self.set_fill_color(248, 249, 250)
            else:
                self.set_fill_color(255, 255, 255)
                
            self.cell(col_width, 10, metric, border=1, align='L', fill=True)
            self.cell(col_width, 10, value, border=1, align='C', fill=True, ln=True)
    
    def create_pillar_analysis_section(self, pillar_data, pillar_name):
        """Create detailed pillar analysis section"""
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, f"Performance Overview - {pillar_name}", ln=True)
        self.ln(2)
        
        # Sub-pillar breakdown
        self.set_font('Arial', '', 11)
        for sub_pillar in pillar_data['sub_pillars']:
            sub_name = sub_pillar['name_en']
            status_counts = sub_pillar['status_counts']
            
            # Determine overall status for sub-pillar
            if status_counts['E'] > status_counts['R'] and status_counts['E'] > status_counts['N']:
                status_text = "Excellent"
                status_color = (40, 167, 69)
            elif status_counts['R'] > status_counts['N']:
                status_text = "Needs Improvement" 
                status_color = (255, 193, 7)
            else:
                status_text = "Critical"
                status_color = (220, 53, 69)
            
            self.set_text_color(*status_color)
            self.cell(8, 6, "-", align='L')
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, f"{sub_name}: {status_text}", ln=True, align='L')
            self.ln(1)

# Update the function alias
# generate_pdf_report = generate_comprehensive_pdf_report  # PDF functionality removed

def save_streamlit_data_to_txt(data, overall_score, status_counts, ai_summary, accessibility_analysis, appearance_analysis, recommendations):
    """Save all Streamlit data to a text file for PDF generation - PRESERVE ARABIC CONTENT"""
    
    # Keep original Arabic content from LLM
    ai_summary = ai_summary if ai_summary else 'لا يوجد ملخص متاح'
    accessibility_analysis = accessibility_analysis if accessibility_analysis else 'لا يوجد تحليل متاح'
    appearance_analysis = appearance_analysis if appearance_analysis else 'لا يوجد تحليل متاح'
    recommendations = recommendations if recommendations else 'لا توجد توصيات متاحة'
    
    content = f"""=== بيانات التصدير من التطبيق ===
تاريخ الإنتاج: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== الملخص التنفيذي ===
المعدل الكلي للأداء: {overall_score:.1f}%
العناصر المتميزة: {status_counts['E']} عنصر
العناصر التي تحتاج تحسين: {status_counts['R']} عنصر
العناصر الحرجة: {status_counts['N']} عنصر
إجمالي العناصر: {sum([status_counts[k] for k in ['E', 'R', 'N']])} عنصر

التحليل المدعوم بالذكاء الاصطناعي:
{ai_summary}

=== تحليل سهولة الوصول ===
{accessibility_analysis}

=== تحليل المظهر العام ===
{appearance_analysis}

=== التوصيات التطويرية ===
{recommendations}

=== تفاصيل البيانات المفصلة ===
"""
    
    # Add detailed pillar data in Arabic
    for pillar in data:
        pillar_name_ar = pillar.get('pillar_ar', pillar.get('pillar_en', 'محور غير معروف'))
        pillar_name_en = pillar.get('pillar_en', '')
        pillar_score = pillar.get('pillar_score', 0)
        
        content += f"\n--- {pillar_name_ar} ({pillar_name_en}) - النتيجة: {pillar_score} ---\n"
        
        for sub_pillar in pillar.get('sub_pillars', []):
            sub_name_ar = sub_pillar.get('sub_pillar_ar', sub_pillar.get('sub_pillar_en', 'محور فرعي غير معروف'))
            content += f"\n  {sub_name_ar}:\n"
            
            for attr in sub_pillar.get('attributes', []):
                attr_name_en = attr.get('attribute_en', 'خاصية غير معروفة')
                status = attr.get('status', 'N')
                score = attr.get('score', 0)
                status_text = {'E': 'ممتاز', 'R': 'يحتاج تحسين', 'N': 'حرج', 'NA': 'غير قابل للتطبيق'}.get(status, 'غير محدد')
                
                content += f"    - {attr_name_en}: {status_text} (النتيجة: {score})\n"
    
    # Save to file - use relative path for deployment compatibility
    txt_file_path = "streamlit_data_export.txt"
    try:
        with open(txt_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return txt_file_path
    except Exception as e:
        st.error(f"Error saving data to text file: {str(e)}")
        return None

def _clean_content(content, is_executive_summary=False):
    """Clean content by removing unwanted elements and fixing formatting"""
    if not content:
        return content
    
    lines = content.split('\n')
    cleaned_lines = []
    skip_metrics = False
    
    for line in lines:
        line = line.strip()
        
        # Remove random dashes (lines that contain multiple dashes)
        if re.match(r'^-{2,}.*-{2,}$', line):
            continue
        if re.match(r'^--- .* ---$', line):
            continue
        
        # Remove lines that are just dashes or separators
        if re.match(r'^[-=]{3,}$', line):
            continue
            
        # Remove lines that start with single dash and space (like "- Correct address...")
        if re.match(r'^-\s+', line):
            continue
            
        # Remove unwanted subheading
        if 'ملخص تنفيذي لتقييم مركز خدمة جمارك أبوظبي' in line:
            continue
        
        # For executive summary, skip the repeated metrics section
        if is_executive_summary:
            if 'المعدل الكلي للأداء:' in line:
                skip_metrics = True
                continue
            elif 'التحليل المدعوم بالذكاء الاصطناعي:' in line:
                skip_metrics = False
                continue
            elif skip_metrics:
                continue
        
        # Keep all other lines
        if line:
            cleaned_lines.append(line)
        else:
            cleaned_lines.append('')  # Preserve empty lines for formatting
    
    return '\n'.join(cleaned_lines)

def generate_arabic_docx_from_txt(txt_file_path):
    """Generate DOCX report using the content from streamlit_data_export.txt with utilities"""
    
    if not txt_file_path or not os.path.exists(txt_file_path):
        st.error("Text file not found for DOCX generation")
        return None
    
    try:
        # Import utilities with error handling
        try:
            from report_utils import DOCXBuilder, ContentProcessor
        except ImportError as e:
            st.error(f"Error importing report utilities: {str(e)}")
            return None
        
        # Read the raw content from streamlit_data_export.txt
        try:
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except Exception as e:
            st.error(f"Error reading text file: {str(e)}")
            return None
        
        if not raw_content.strip():
            st.error("Text file is empty")
            return None
        
        # Initialize DOCX builder
        try:
            docx_builder = DOCXBuilder()
            doc = docx_builder.create_document()
        except Exception as e:
            st.error(f"Error initializing DOCX builder: {str(e)}")
            return None
        
        # Add logo header
        logo_path = "abuDhabiCustomsLogo.png"
        docx_builder.add_logo_header(doc, logo_path)
        
        # Add title section - Arabic only
        arabic_title = "تقرير المتسوق السري لجمارك ابو ظبي"
        
        docx_builder.add_title_section(doc, arabic_title)
        
        # Parse sections from content
        try:
            sections = ContentProcessor.parse_sections_from_text(raw_content)
            if not sections:
                st.warning("No sections found in text file")
        except Exception as e:
            st.error(f"Error parsing sections: {str(e)}")
            sections = {}
        
        # Extract metrics for summary
        # try:
        #     metrics = ContentProcessor.extract_metrics_from_content(raw_content)
        # except Exception as e:
        #     st.warning(f"Error extracting metrics: {str(e)}")
        #     metrics = {}
        
        # Skip the overview section as requested by user
        
        # Add each section with proper Arabic formatting and correct titles
        section_titles = {
            'الملخص التنفيذي': 'الملخص التنفيذي',
            'تحليل سهولة الوصول': 'نتائج التقييم - محور سهولة الوصول', 
            'تحليل المظهر العام': 'نتائج التقييم - محور المظهر العام',
            'التوصيات التطويرية': 'التوصيات التطويرية'
            # Removed 'تفاصيل البيانات المفصلة' section as requested
        }
        
        for section_key, arabic_section_title in section_titles.items():
            if section_key in sections and sections[section_key].strip():
                # Add page break for each section (except the first one)
                if section_key != 'الملخص التنفيذي':
                    doc.add_page_break()
                
                # Add section header
                docx_builder.add_section_header(doc, arabic_section_title)
                
                # Clean the content from markdown and unwanted repeated text
                section_content = sections[section_key]
                
                # Clean content based on section type
                is_executive = (section_key == 'الملخص التنفيذي')
                section_content = _clean_content(section_content, is_executive_summary=is_executive)
                
                docx_builder.add_formatted_paragraph(doc, section_content)
        
        # Add footer in Arabic
        arabic_footer = "تم إنتاج هذا التقرير باستخدام التحليل المدعوم بالذكاء الاصطناعي"
        docx_builder.add_footer(doc, arabic_footer)
        
        # Save to buffer
        return docx_builder.save_to_buffer(doc)
        
    except Exception as e:
        st.error(f"خطأ في إنتاج DOCX العربي: {str(e)}")
        return None        # Initialize PDF with working approach - use standard fonts with proper Arabic handling
        # pdf = FPDF()  # PDF functionality removed
        pdf.set_auto_page_break(auto=True, margin=20)
        
        pdf.add_page()
        
        # Add logo to header
        logo_path = "abuDhabiCustomsLogo.png"
        if os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=55, y=15, w=100)
                pdf.ln(45)
            except:
                pdf.set_font('Arial', 'B', 24)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 15, "Abu Dhabi Customs", ln=True, align='C')
                pdf.ln(10)
        
        # Report title with English transliteration for now
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 15, "Taqrir Tahlil Ada' Marakiz al-Khidma", ln=True, align='C')
        pdf.set_font('Arial', '', 16)
        pdf.cell(0, 10, "Service Center Performance Analysis Report", ln=True, align='C')
        
        # Date
        pdf.set_font('Arial', '', 12)
        pdf.set_text_color(102, 102, 102)
        pdf.cell(0, 10, f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
        pdf.ln(20)
        
        # Decorative line
        pdf.set_draw_color(44, 62, 80)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(15)
        pdf.set_text_color(0, 0, 0)
        
        # Create a function to handle Arabic text properly
        def process_arabic_text(text):
            """Process Arabic text for PDF display with comprehensive translation"""
            if not text:
                return ""
            
            import re
            
            # Comprehensive Arabic to English translation dictionary
            arabic_translations = {
                # Section headers
                'الملخص التنفيذي': 'Executive Summary',
                'تحليل سهولة الوصول': 'Accessibility Analysis',
                'تحليل المظهر العام': 'General Appearance Analysis',
                'التوصيات التطويرية': 'Development Recommendations',
                'تفاصيل البيانات المفصلة': 'Detailed Data Breakdown',
                'بيانات التصدير من التطبيق': 'Application Data Export',
                
                # Performance metrics
                'المعدل الكلي للأداء': 'Overall Performance Score',
                'العناصر المتميزة': 'Excellent Elements',
                'العناصر التي تحتاج تحسين': 'Elements Needing Improvement', 
                'العناصر الحرجة': 'Critical Elements',
                'إجمالي العناصر': 'Total Elements',
                'التحليل المدعوم بالذكاء الاصطناعي': 'AI-Powered Analysis',
                'تاريخ الإنتاج': 'Generation Date',
                'النتيجة': 'Score',
                'عنصر': 'element',
                
                # Status indicators
                'ممتاز': 'Excellent',
                'يحتاج تحسين': 'Needs Improvement',
                'حرج': 'Critical',
                'غير قابل للتطبيق': 'Not Applicable',
                'غير محدد': 'Undefined',
                'مرتفع': 'High',
                'متوسط': 'Medium',
                'منخفض': 'Low',
                
                # Common Arabic words and phrases
                'مركز': 'center',
                'خدمة': 'service',
                'جمارك': 'customs',
                'أبوظبي': 'Abu Dhabi',
                'تقييم': 'evaluation',
                'أداء': 'performance',
                'تحليل': 'analysis',
                'تقرير': 'report',
                'نتائج': 'results',
                'مستوى': 'level',
                'جودة': 'quality',
                'تحسين': 'improvement',
                'تطوير': 'development',
                'خدمات': 'services',
                'متعاملين': 'customers',
                'مبنى': 'building',
                'موقع': 'location',
                'وصول': 'access',
                'مظهر': 'appearance',
                'بيئة': 'environment',
                'نظافة': 'cleanliness',
                'إضاءة': 'lighting',
                'حرارة': 'temperature',
                'ضوضاء': 'noise',
                'مقاعد': 'seating',
                'انتظار': 'waiting',
                'مواقف': 'parking',
                'سيارات': 'cars',
                'لافتات': 'signage',
                'إرشادية': 'directional',
                'صيانة': 'maintenance',
                'أثاث': 'furniture',
                'تشطيبات': 'finishes',
                'مطار': 'airport',
                'طابق': 'floor',
                'أرضي': 'ground',
                'مصاعد': 'elevators',
                'منحدرات': 'ramps',
                'عوائق': 'barriers',
                'مدخل': 'entrance',
                'مخرج': 'exit',
                'علامة': 'sign',
                'واضحة': 'clear',
                'مسافة': 'distance',
                'قراءة': 'reading',
                'مريحة': 'comfortable',
                'جاذبة': 'attractive',
                'ذروة': 'peak',
                'أوقات': 'times',
                'وقوف': 'standing',
                'برودة': 'cold',
                'زائدة': 'excessive',
                'دورية': 'periodic',
                'خارجية': 'external',
                'داخلية': 'internal',
                'قطع': 'pieces',
                'تقادم': 'aging',
                'آثار': 'signs',
                'تظهر': 'appear',
                'عليها': 'on them',
                'كون': 'being',
                'تشكل': 'constitute',
                'تحديًا': 'challenge',
                'فعليًا': 'actual',
                'تعزيز': 'enhance',
                'تجربة': 'experience',
                'رفع': 'raise',
                'كفاءة': 'efficiency',
                'يوصى': 'recommended',
                'بالتركيز': 'focusing on',
                'وضوح': 'clarity',
                'داخل': 'inside',
                'مراجعة': 'review',
                'شاملة': 'comprehensive',
                'خيارات': 'options',
                'جلوس': 'seating',
                'لضمان': 'to ensure',
                'توفير': 'providing',
                'عدد': 'number',
                'كافٍ': 'sufficient',
                'يلبي': 'meets',
                'احتياجات': 'needs',
                'جميع': 'all',
                'الأوقات': 'times',
                'يتطلب': 'requires',
                'الأمر': 'matter',
                'ضبطًا': 'adjustment',
                'دقيقًا': 'precise',
                'درجة': 'degree',
                'الحرارة': 'temperature',
                'الداخلية': 'internal',
                'وضع': 'placing',
                'خطة': 'plan',
                'مجدولة': 'scheduled',
                'لتحسين': 'to improve',
                'المظهر': 'appearance',
                'العام': 'general',
                'للمبنى': 'of the building',
                'من': 'from',
                'الخارج': 'outside',
                'وتحديث': 'and update',
                'الأثاث': 'furniture',
                'والتشطيبات': 'and finishes',
                'الداخلية': 'internal',
                'شأن': 'matter',
                'هذه': 'these',
                'التحسينات': 'improvements',
                'أن': 'that',
                'ترفع': 'raise',
                'مستوى': 'level',
                'رضا': 'satisfaction',
                'المتعاملين': 'customers',
                'وتُعزز': 'and enhance',
                'مكانة': 'position',
                'المركز': 'center',
                'كنموذج': 'as a model',
                'رائد': 'leading',
                'في': 'in',
                'تقديم': 'providing',
                'الخدمات': 'services',
                'الحكومية': 'government',
                'مستفيدًا': 'benefiting',
                'نقاط': 'points',
                'قوته': 'strength',
                'الحالية': 'current',
                'سهولة': 'ease',
                'الوصول': 'access',
                'والنظافة': 'and cleanliness'
            }
            
            # Apply comprehensive translations
            processed_text = text
            
            # Sort by length (longest first) to avoid partial replacements
            for arabic_term in sorted(arabic_translations.keys(), key=len, reverse=True):
                english_term = arabic_translations[arabic_term]
                processed_text = processed_text.replace(arabic_term, english_term)
            
            # Handle any remaining Arabic text with a more intelligent approach
            # Instead of replacing with [Arabic text], try to preserve structure
            arabic_pattern = r'[\u0600-\u06FF]+'
            remaining_arabic = re.findall(arabic_pattern, processed_text)
            
            if remaining_arabic:
                # For remaining Arabic, replace with transliterated placeholder
                processed_text = re.sub(arabic_pattern, '(Arabic content)', processed_text)
            
            # Clean up multiple spaces and formatting
            processed_text = re.sub(r'\s+', ' ', processed_text)
            processed_text = processed_text.strip()
            
            return processed_text
        
        # Add all sections from the text file
        section_titles = {
            'الملخص التنفيذي': '1. Executive Summary',
            'تحليل سهولة الوصول': '2. Accessibility Analysis',
            'تحليل المظهر العام': '3. General Appearance Analysis',
            'التوصيات التطويرية': '4. Development Recommendations',
            'تفاصيل البيانات المفصلة': '5. Detailed Data Breakdown'
        }
        
        for section_key, section_title in section_titles.items():
            if section_key in sections:
                # Add section header with modern styling
                pdf.ln(8)
                pdf.set_fill_color(44, 62, 80)
                pdf.rect(20, pdf.get_y(), 170, 15, 'F')
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(0, 15, section_title, ln=True, align='C')
                pdf.set_text_color(0, 0, 0)
                pdf.ln(8)
                
                # Add section content directly from text file - NO PROCESSING
                content = sections[section_key]
                if content:
                    # Use content directly from streamlit_data_export.txt
                    # Split content into manageable chunks
                    lines = content.split('\n')
                    
                    # Try to use a font that might support Arabic better
                    try:
                        pdf.set_font('Arial', '', 11)
                        
                        for line in lines:
                            if line.strip():
                                # Add line directly without any text processing
                                try:
                                    # Handle long lines by wrapping
                                    if len(line) > 60:  # Shorter for Arabic text
                                        words = line.split()
                                        current_line = ""
                                        for word in words:
                                            test_line = current_line + " " + word if current_line else word
                                            if len(test_line) <= 60:
                                                current_line = test_line
                                            else:
                                                if current_line:
                                                    pdf.cell(0, 8, current_line, ln=True, align='R')  # Right align for Arabic
                                                current_line = word
                                        if current_line:
                                            pdf.cell(0, 8, current_line, ln=True, align='R')
                                    else:
                                        pdf.cell(0, 8, line, ln=True, align='R')  # Right align for Arabic
                                except Exception as e:
                                    # If Arabic characters cause issues, add a note
                                    pdf.cell(0, 8, f"[Content contains Arabic text - see source file]", ln=True, align='L')
                            else:
                                pdf.ln(3)
                    except Exception as e:
                        # Fallback if font issues
                        pdf.set_font('Arial', '', 11)
                        pdf.cell(0, 8, f"Section content available in source text file", ln=True, align='L')
                
                # Add page break between major sections (except last)
                if section_key != 'DETAILED DATA BREAKDOWN':
                    pdf.add_page()
        
        # Footer
        pdf.ln(15)
        pdf.set_draw_color(44, 62, 80)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(102, 102, 102)
        pdf.cell(0, 6, "This report was generated using AI-powered analysis", ln=True, align='C')
        pdf.cell(0, 6, f"Abu Dhabi Customs - Service Excellence Initiative - {datetime.now().year}", ln=True, align='C')
        
        # Generate PDF buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        return pdf_buffer
        
    except Exception as e:
        st.error(f"خطأ في إنتاج PDF العربي: {str(e)}")
        return None
    
    def force_rtl_paragraph(para, align="right"):
        pPr = para._element.get_or_add_pPr()

        # RTL direction
        bidi = OxmlElement("w:bidi")
        bidi.set(qn("w:val"), "1")
        pPr.append(bidi)

        # Explicit justification (THIS is the key)
        jc = OxmlElement("w:jc")
        jc.set(qn("w:val"), align)
        pPr.append(jc)


# Set the main DOCX generation function
generate_arabic_docx = generate_arabic_docx_from_txt

def main():
    # Set page direction to RTL
    st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-title" dir="rtl">تحليل أداء مراكز الخدمة</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Setup Gemini API
    model = setup_gemini_api()
    
    # Sidebar with logo
    # Display logo in sidebar
    try:
        st.sidebar.image("abuDhabiCustomsLogo.png", 
                        width=250)
    except:
        # Fallback if logo not found
        st.sidebar.markdown('<div style="text-align: center; font-weight: bold;">جمارك أبوظبي</div>', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.title("إعدادات التحليل")
    
    
    # Default file path - use relative path for deployment compatibility
    default_file = "service_center_api_schema_RTL_FIXED.json"
    
    # File upload option
    uploaded_file = st.sidebar.file_uploader(
        "اختر ملف JSON للتحليل",
        type=['json'],
        help="اختر ملف البيانات بصيغة JSON"
    )
    
    # Load data
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {str(e)}")
            return
    else:
        # Use default file
        if os.path.exists(default_file):
            data = load_data(default_file)
            st.sidebar.success("تم تحميل الملف ")
        else:
            st.error("لم يتم العثور على ملف البيانات. يرجى رفع ملف JSON.")
            return
    
    if data is None:
        return
    
    # Calculate metrics
    overall_score = calculate_overall_score(data)
    status_counts, status_scores = analyze_performance_by_status(data)
    data_summary = prepare_data_for_gemini(data, overall_score, status_counts)
    
    # Generate all analyses for PDF
    ai_summary = None
    accessibility_analysis = None
    appearance_analysis = None
    recommendations = None
    
    if model:
        with st.spinner("جاري إعداد التقرير..."):
            ai_summary = generate_executive_summary(model, data_summary)
            
            accessibility_data = analyze_pillar_performance(data, "Accessibility")
            if accessibility_data:
                accessibility_analysis = generate_pillar_analysis(model, accessibility_data, "سهولة الوصول")
            
            appearance_data = analyze_pillar_performance(data, "Appearance")
            if appearance_data:
                appearance_analysis = generate_pillar_analysis(model, appearance_data, "المظهر العام")
            
            recommendations = generate_recommendations(model, data_summary)
    
    # Single Arabic DOCX Report Generation and Download
    if model and ai_summary:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### تحميل التقرير العربي")
        
        # Single button that generates and downloads in one click
        with st.spinner("جاري إنتاج التقرير العربي..."):
            try:
                # Step 1: Save all Streamlit data to text file
                txt_file_path = save_streamlit_data_to_txt(
                    data, overall_score, status_counts, 
                    ai_summary, accessibility_analysis, 
                    appearance_analysis, recommendations
                )
                
                if txt_file_path:
                    # Step 2: Generate DOCX from text file
                    arabic_docx_buffer = generate_arabic_docx_from_txt(txt_file_path)
                    
                    if arabic_docx_buffer:
                        # Step 3: Provide immediate download
                        st.sidebar.download_button(
                            label="تحميل التقرير العربي DOCX",
                            data=arabic_docx_buffer,
                            file_name=f"تقرير_عربي_مراكز_الخدمة_{datetime.now().strftime('%Y%m%d')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary",
                            use_container_width=True
                        )
                        st.sidebar.success("تم إنتاج التقرير بنجاح! اضغط الزر أعلاه للتحميل")
                    else:
                        st.sidebar.error("فشل في إنتاج ملف DOCX")
                else:
                    st.sidebar.error("فشل في حفظ البيانات")
                
            except Exception as e:
                st.sidebar.error(f"خطأ في إنتاج التقرير: {str(e)}")
        
    else:
        st.sidebar.markdown("---")
        st.sidebar.info("يتطلب تفعيل Gemini API لإنتاج التقرير")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "الملخص التنفيذي", 
        "نتائج التقييم - محور سهولة الوصول",
        "نتائج التقييم - محور المظهر العام", 
        "المقترحات التطويرية"
    ])
    
    # Tab 1: Executive Summary
    with tab1:
        st.markdown('<div class="tab-title" dir="rtl">التحليل المدعوم بالذكاء الاصطناعي</div>', unsafe_allow_html=True)
        
        # Display overall score with gauge
        col1, col2 = st.columns([1, 2])
        
        with col1:
            fig = create_score_gauge(overall_score)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if ai_summary:
                formatted_summary = clean_and_format_text(ai_summary)
                st.markdown(f'<div class="summary-text">{formatted_summary}</div>', unsafe_allow_html=True)
            elif model:
                st.info("جاري تحميل التحليل...")
            else:
                st.warning("يرجى إعداد مفتاح Gemini API لتوليد التحليل الذكي")
        
        # Additional metrics
        st.markdown("---")
        st.markdown('<div class="rtl" dir="rtl"><h3>تفاصيل الأداء</h3></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_items = sum([v for k,v in status_counts.items() if k != 'NA'])
        
        with col1:
            st.metric(
                label="العناصر المتميزة",
                value=status_counts['E'],
                delta=f"{(status_counts['E']/total_items*100):.1f}%" if total_items > 0 else "0%"
            )
        
        with col2:
            st.metric(
                label="يحتاج تحسين",
                value=status_counts['R'],
                delta=f"{(status_counts['R']/total_items*100):.1f}%" if total_items > 0 else "0%"
            )
        
        with col3:
            st.metric(
                label="العناصر الحرجة",
                value=status_counts['N'],
                delta=f"{(status_counts['N']/total_items*100):.1f}%" if total_items > 0 else "0%"
            )
        
        with col4:
            st.metric(
                label="غير قابل للتطبيق",
                value=status_counts['NA'],
                delta="عناصر"
            )
    
    # Tab 2: Accessibility Analysis
    with tab2:
        st.markdown('<div class="tab-title" dir="rtl">نتائج التقييم - محور سهولة الوصول</div>', unsafe_allow_html=True)
        
        accessibility_data = analyze_pillar_performance(data, "Accessibility")
        if accessibility_data and model:
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if accessibility_analysis:
                    formatted_analysis = clean_and_format_text(accessibility_analysis)
                    st.markdown(f'<div class="pillar-analysis">{formatted_analysis}</div>', unsafe_allow_html=True)
                elif model:
                    st.info("جاري تحميل التحليل...")
                else:
                    st.warning("يرجى إعداد مفتاح Gemini API")
            
            with col2:
                fig = create_pillar_status_chart(accessibility_data)
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed breakdown
            st.markdown("---")
            st.markdown('<div class="rtl" dir="rtl"><h3>التفصيل حسب المحاور الفرعية</h3></div>', unsafe_allow_html=True)
            
            for sub_pillar in accessibility_data['sub_pillars']:
                with st.expander(f"{sub_pillar['name_ar']}"):
                    for attr in sub_pillar['attributes']:
                        status_class = {
                            'E': 'status-excellent',
                            'R': 'status-needs-improvement', 
                            'N': 'status-critical'
                        }.get(attr['status'], '')
                        
                        status_text = {
                            'E': 'ممتاز',
                            'R': 'يحتاج تحسين',
                            'N': 'ضعيف'
                        }.get(attr['status'], 'غير محدد')
                        
                        st.markdown(f"""
                        <div style="margin: 10px 0; padding: 10px; border-right: 3px solid #ddd;">
                            <span class="{status_class}">{status_text}</span> - النتيجة: {attr['score']}
                            <br><small style="color: #666;">{attr['notes_ar'][:200]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Tab 3: Appearance Analysis  
    with tab3:
        st.markdown('<div class="tab-title" dir="rtl">نتائج التقييم - محور المظهر العام</div>', unsafe_allow_html=True)
        
        appearance_data = analyze_pillar_performance(data, "Appearance")
        if appearance_data and model:
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if appearance_analysis:
                    formatted_analysis = clean_and_format_text(appearance_analysis)
                    st.markdown(f'<div class="pillar-analysis">{formatted_analysis}</div>', unsafe_allow_html=True)
                elif model:
                    st.info("جاري تحميل التحليل...")
                else:
                    st.warning("يرجى إعداد مفتاح Gemini API")
            
            with col2:
                fig = create_pillar_status_chart(appearance_data)
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed breakdown
            st.markdown("---")
            st.markdown('<div class="rtl" dir="rtl"><h3>التفصيل حسب المحاور الفرعية</h3></div>', unsafe_allow_html=True)
            
            for sub_pillar in appearance_data['sub_pillars']:
                with st.expander(f"{sub_pillar['name_ar']}"):
                    for attr in sub_pillar['attributes']:
                        status_class = {
                            'E': 'status-excellent',
                            'R': 'status-needs-improvement', 
                            'N': 'status-critical'
                        }.get(attr['status'], '')
                        
                        status_text = {
                            'E': 'ممتاز',
                            'R': 'يحتاج تحسين',
                            'N': 'ضعيف'
                        }.get(attr['status'], 'غير محدد')
                        
                        st.markdown(f"""
                        <div style="margin: 10px 0; padding: 10px; border-right: 3px solid #ddd;">
                            <span class="{status_class}">{status_text}</span> - النتيجة: {attr['score']}
                            <br><small style="color: #666;">{attr['notes_ar'][:200]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Tab 4: Development Recommendations
    with tab4:
        st.markdown('<div class="tab-title" dir="rtl">المقترحات التطويرية بناءً على الفرص التحسينية</div>', unsafe_allow_html=True)
        
        if model:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if recommendations:
                    formatted_recommendations = clean_and_format_text(recommendations)
                    st.markdown(f'<div class="recommendation-card">{formatted_recommendations}</div>', unsafe_allow_html=True)
                elif model:
                    st.info("جاري تحميل المقترحات...")
                else:
                    st.warning("يرجى إعداد مفتاح Gemini API")
            
            with col2:
                fig = create_recommendations_flowchart()
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("يرجى إعداد مفتاح Gemini API لتوليد المقترحات")

if __name__ == "__main__":
    main()