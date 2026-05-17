import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Advanced ML Perforation Dashboard",
    page_icon=":material/analytics:",
    layout="wide",
)

# Tăng kích thước font chữ cho Sidebar
st.markdown("""
    <style>
        /* Toàn bộ text trong sidebar */
        [data-testid="stSidebar"] {
            font-size: 1.1rem !important;
        }
        /* Menu điều hướng */
        [data-testid="stSidebarNav"] span {
            font-size: 1.15rem !important;
        }
        /* Các nhãn của widget (selectbox, multiselect, slider...) */
        [data-testid="stSidebar"] label p {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        /* Nội dung markdown */
        [data-testid="stSidebar"] .stMarkdown p {
            font-size: 1.1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo các state chung
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "wells" not in st.session_state:
    st.session_state.wells = []
if "depth_range" not in st.session_state:
    st.session_state.depth_range = (0.0, 100.0)
if "conf_filter" not in st.session_state:
    st.session_state.conf_filter = 0.6
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "advanced_model" not in st.session_state:
    st.session_state.advanced_model = None
if "advanced_features" not in st.session_state:
    st.session_state.advanced_features = None
if "production_model" not in st.session_state:
    st.session_state.production_model = None
if "lang" not in st.session_state:
    st.session_state.lang = "English"

# --- LỰA CHỌN NGÔN NGỮ TRÊN SIDEBAR ---
with st.sidebar:
    st.markdown("### 🌐 Language / Ngôn ngữ")
    lang = st.selectbox(
        "Select Language / Chọn ngôn ngữ", 
        ["English", "Vietnamese"], 
        index=0 if st.session_state.lang == "English" else 1,
        key="lang_selector",
        label_visibility="collapsed"
    )
    st.session_state.lang = lang
    st.divider()

# Dịch tiêu đề trang
titles = {
    "English": {
        "guide": "User Guide",
        "upload": "Data Upload",
        "log": "Log Visualizer",
        "ml": "ML Advisor",
        "prod": "Production Prediction",
        "dca": "DCA & PLT Matching",
        "econ": "Economic Analysis"
    },
    "Vietnamese": {
        "guide": "Hướng Dẫn Sử Dụng",
        "upload": "Upload Dữ Liệu",
        "log": "Log Visualizer",
        "ml": "ML Advisor",
        "prod": "Dự Báo Lưu Lượng",
        "dca": "DCA & PLT Matching",
        "econ": "Phân Tích Kinh Tế"
    }
}

t = titles[st.session_state.lang]

# Định nghĩa các trang với tiêu đề động
pages = [
    st.Page("app_pages/0_user_guide.py", title=t["guide"], icon=":material/menu_book:"),
    st.Page("app_pages/1_data_upload.py", title=t["upload"], icon=":material/upload_file:"),
    st.Page("app_pages/2_log_viewer.py", title=t["log"], icon=":material/stacked_line_chart:"),
    st.Page("app_pages/3_ml_advisor.py", title=t["ml"], icon=":material/psychology:"),
    st.Page("app_pages/4_production_prediction.py", title=t["prod"], icon=":material/water_drop:"),
    st.Page("app_pages/6_decline_analysis.py", title="DCA & PLT Matching", icon=":material/trending_down:"),
    st.Page("app_pages/5_economics.py", title=t["econ"], icon=":material/monetization_on:"),
]

page = st.navigation(pages, position="sidebar")

st.title(f"{page.icon} {page.title}")

page.run()
