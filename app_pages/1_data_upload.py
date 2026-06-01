import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
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



# --- Sample file downloads ---
sample_files = {
    "sample_data.csv": {
        "en": "Download sample well log data (sample_data.csv)",
        "vi": "Tải file dữ liệu log giếng mẫu (sample_data.csv)",
    },
    "sample_production_history.csv": {
        "en": "Download sample production history (for DCA & PLT page)",
        "vi": "Tải file lịch sử khai thác mẫu (cho trang DCA & PLT)",
    },
    "sample_PLT.csv": {
        "en": "Download sample PLT data (for DCA & PLT page)",
        "vi": "Tải file dữ liệu PLT mẫu (cho trang DCA & PLT)",
    },
}

cols = st.columns(len(sample_files))
for col, (fname, labels) in zip(cols, sample_files.items()):
    fpath = fname
    label = labels["en"] if st.session_state.lang == "English" else labels["vi"]
    if os.path.exists(fpath):
        with open(fpath, "rb") as file:
            col.download_button(
                label=label,
                data=file,
                file_name=fname,
                mime="text/csv",
                icon=":material/download:",
                use_container_width=True,
            )

uploaded_file = st.file_uploader(t["uploader"], type=["csv"])

if uploaded_file:
    with st.spinner(t["spinner"]):
        raw_df = pd.read_csv(uploaded_file)
            
        st.session_state.raw_df = raw_df
        
        # Tự động huấn luyện & dự báo ML ở chế độ nền
        processed_df = train_and_predict(raw_df)
        st.session_state.processed_df = processed_df
        
    st.success(t["success"], icon=":material/check_circle:")

elif st.session_state.raw_df is not None:
    st.info(t["info"], icon=":material/info:")
    if st.button(t["clear"]):
        st.session_state.raw_df = None
        st.session_state.processed_df = None
        st.rerun()
