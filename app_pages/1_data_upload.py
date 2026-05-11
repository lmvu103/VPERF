import streamlit as st
import pandas as pd
import os
from utils.ml import train_and_predict

# Dịch thuật
texts = {
    "English": {
        "desc": "Upload reservoir data (CSV format) to start analysis.",
        "sample": "Download sample data file (sample_data.csv)",
        "uploader": "Upload reservoir data (.csv)",
        "spinner": "Processing and analyzing data...",
        "success": "Data uploaded successfully! Please switch to other pages to see results.",
        "info": "Data is already loaded. You can continue viewing or upload a new file.",
        "clear": "Clear current data"
    },
    "Vietnamese": {
        "desc": "Tải lên dữ liệu mỏ (định dạng CSV) để bắt đầu phân tích.",
        "sample": "Tải file dữ liệu mẫu (sample_data.csv)",
        "uploader": "Upload dữ liệu mỏ (.csv)",
        "spinner": "Đang xử lý và phân tích dữ liệu...",
        "success": "Tải dữ liệu thành công! Hãy chuyển sang các trang khác để xem kết quả.",
        "info": "Dữ liệu đã được tải. Bạn có thể tiếp tục xem hoặc tải file mới lên.",
        "clear": "Xóa dữ liệu hiện tại"
    }
}

t = texts[st.session_state.lang]

st.markdown(t["desc"])

# Tải file mẫu
sample_file_path = "sample_data.csv"
if os.path.exists(sample_file_path):
    with open(sample_file_path, "rb") as file:
        st.download_button(
            label=t["sample"],
            data=file,
            file_name="sample_data.csv",
            mime="text/csv",
            icon=":material/download:"
        )

uploaded_file = st.file_uploader(t["uploader"], type=["csv"])

if uploaded_file:
    # Đọc dữ liệu
    raw_df = pd.read_csv(uploaded_file)
    st.session_state.raw_df = raw_df
    
    # Tự động xử lý ML cơ bản ở chế độ nền
    with st.spinner(t["spinner"]):
        processed_df = train_and_predict(raw_df)
        st.session_state.processed_df = processed_df
        
    st.success(t["success"], icon=":material/check_circle:")

elif st.session_state.raw_df is not None:
    st.info(t["info"], icon=":material/info:")
    if st.button(t["clear"]):
        st.session_state.raw_df = None
        st.session_state.processed_df = None
        st.rerun()
