import streamlit as st
import pandas as pd
import numpy as np
import os
import lasio
import tempfile
from utils.ml import train_and_predict

# Dịch thuật
texts = {
    "English": {
        "desc": "Upload reservoir data (CSV or LAS well log format) to start analysis.",
        "sample": "Download sample data file (sample_data.csv)",
        "uploader": "Upload reservoir data (.csv, .las)",
        "spinner": "Processing and analyzing data...",
        "success": "Data uploaded successfully! Please switch to other pages to see results.",
        "info": "Data is already loaded. You can continue viewing or upload a new file.",
        "clear": "Clear current data",
        "las_success": "LAS file parsed successfully! Well Name: '{well}', Curves mapped: {mapped}."
    },
    "Vietnamese": {
        "desc": "Tải lên dữ liệu mỏ (định dạng CSV hoặc tệp well log LAS) để bắt đầu phân tích.",
        "sample": "Tải file dữ liệu mẫu (sample_data.csv)",
        "uploader": "Upload dữ liệu mỏ (.csv, .las)",
        "spinner": "Đang xử lý và phân tích dữ liệu...",
        "success": "Tải dữ liệu thành công! Hãy chuyển sang các trang khác để xem kết quả.",
        "info": "Dữ liệu đã được tải. Bạn có thể tiếp tục xem hoặc tải file mới lên.",
        "clear": "Xóa dữ liệu hiện tại",
        "las_success": "Đọc tệp LAS thành công! Tên giếng: '{well}', Các đường log ánh xạ: {mapped}."
    }
}

t = texts[st.session_state.lang]

st.markdown(t["desc"])

# Hàm phân tích và xử lý tệp well log LAS
def parse_las_file(uploaded_file):
    # Ghi tạm file LAS ra ổ đĩa
    with tempfile.NamedTemporaryFile(delete=False, suffix=".las") as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name
        
    try:
        # Đọc file LAS bằng thư viện lasio
        las = lasio.read(temp_file_path)
        df = las.df().reset_index()
        
        # 1. Tìm cột Depth (Độ sâu)
        depth_col = None
        for col in df.columns:
            if col.upper() in ['DEPT', 'DEPTH']:
                depth_col = col
                break
        if not depth_col:
            for col in df.columns:
                if 'depth' in col.lower() or 'dept' in col.lower():
                    depth_col = col
                    break
        if depth_col:
            df = df.rename(columns={depth_col: 'Depth'})
        else:
            df = df.rename(columns={df.columns[0]: 'Depth'})
            
        # 2. Lấy tên giếng từ header
        well_name = 'Well-A'
        if 'WELL' in las.well and las.well.WELL.value:
            well_name = las.well.WELL.value.strip()
        df['Well_Name'] = well_name
        
        # 3. Ánh xạ các đường log quan trọng (Porosity, Sw, Vshale, Permeability)
        mapped_cols = {}
        mapped_logs = []
        
        # Porosity
        for col in df.columns:
            if col.upper() in ['PHIE', 'PHIT', 'POR', 'POROSITY', 'PORS']:
                mapped_cols[col] = 'Porosity'
                mapped_logs.append(f"{col}->Porosity")
                break
        if 'Porosity' not in mapped_cols.values():
            for col in df.columns:
                if 'phi' in col.lower() or 'por' in col.lower():
                    mapped_cols[col] = 'Porosity'
                    mapped_logs.append(f"{col}->Porosity")
                    break
                    
        # Sw
        for col in df.columns:
            if col.upper() in ['SW', 'SWE', 'SWT', 'SATURATION', 'S_W']:
                mapped_cols[col] = 'Sw'
                mapped_logs.append(f"{col}->Sw")
                break
        if 'Sw' not in mapped_cols.values():
            for col in df.columns:
                if 'sw' in col.lower() or 'sat' in col.lower():
                    mapped_cols[col] = 'Sw'
                    mapped_logs.append(f"{col}->Sw")
                    break
                    
        # Vshale
        for col in df.columns:
            if col.upper() in ['VSH', 'VSHALE', 'VCL', 'CLAY', 'V_SHALE']:
                mapped_cols[col] = 'Vshale'
                mapped_logs.append(f"{col}->Vshale")
                break
        if 'Vshale' not in mapped_cols.values():
            for col in df.columns:
                if 'vsh' in col.lower() or 'clay' in col.lower():
                    mapped_cols[col] = 'Vshale'
                    mapped_logs.append(f"{col}->Vshale")
                    break
                    
        # Permeability
        for col in df.columns:
            if col.upper() in ['PERM', 'K', 'PERMEABILITY', 'PERMS']:
                mapped_cols[col] = 'Permeability'
                mapped_logs.append(f"{col}->Permeability")
                break
        if 'Permeability' not in mapped_cols.values():
            for col in df.columns:
                if 'perm' in col.lower() or col.lower() == 'k':
                    mapped_cols[col] = 'Permeability'
                    mapped_logs.append(f"{col}->Permeability")
                    break
                    
        df = df.rename(columns=mapped_cols)
        
        # 4. Giả lập dữ liệu thiếu nếu các log cốt lõi không có
        np.random.seed(42)
        n_rows = len(df)
        
        if 'Porosity' not in df.columns:
            df['Porosity'] = 0.15 + 0.05 * np.sin(df['Depth'] / 10.0) + np.random.normal(0, 0.01, n_rows)
            df['Porosity'] = df['Porosity'].clip(0.01, 0.4)
            mapped_logs.append("Synthetic->Porosity")
            
        if 'Sw' not in df.columns:
            df['Sw'] = 0.4 + 0.3 * np.cos(df['Depth'] / 15.0) + np.random.normal(0, 0.02, n_rows)
            df['Sw'] = df['Sw'].clip(0.05, 0.98)
            mapped_logs.append("Synthetic->Sw")
            
        if 'Vshale' not in df.columns:
            # Nếu có Gamma Ray (GR), tính Vshale giả lập từ GR
            gr_col = None
            for col in df.columns:
                if col.upper() in ['GR', 'GAMMARAY', 'GAMMA']:
                    gr_col = col
                    break
            if gr_col:
                gr = df[gr_col]
                gr_min, gr_max = gr.min(), gr.max()
                df['Vshale'] = (gr - gr_min) / (gr_max - gr_min + 1e-5)
                mapped_logs.append(f"{gr_col}->Vshale")
            else:
                df['Vshale'] = 0.2 + 0.15 * np.sin(df['Depth'] / 5.0) + np.random.normal(0, 0.02, n_rows)
                mapped_logs.append("Synthetic->Vshale")
            df['Vshale'] = df['Vshale'].clip(0.0, 1.0)
            
        if 'Permeability' not in df.columns:
            df['Permeability'] = 10 ** (3 * df['Porosity']) * (1 - df['Sw']) ** 2
            df['Permeability'] = df['Permeability'].clip(0.01, 5000.0)
            mapped_logs.append("Coates-Dumanoir->Permeability")
            
        # 5. Giả lập các cột trạng thái bắn mẫu để máy học hoạt động bình thường
        df['Is_Perforated'] = False
        df['Production_Class'] = None
        df['Initial_Rate'] = None
        
        # Bắn 2 khoảng tiềm năng tốt nhất để làm tập mẫu huấn luyện
        good_points = (df['Porosity'] > 0.16) & (df['Sw'] < 0.45) & (df['Vshale'] < 0.25)
        
        if good_points.sum() > 10:
            df['is_good'] = good_points
            df['group'] = (df['is_good'] != df['is_good'].shift()).cumsum()
            
            groups = df[df['is_good'] == True].groupby('group')
            perf_count = 0
            for name, group in groups:
                if len(group) >= 5 and perf_count < 2:
                    df.loc[group.index, 'Is_Perforated'] = True
                    prod_class = 'BEST' if group['Porosity'].mean() > 0.2 else 'GOOD'
                    df.loc[group.index, 'Production_Class'] = prod_class
                    
                    avg_por = group['Porosity'].mean()
                    rate = 300 + 800 * (avg_por - 0.15) / 0.1 + np.random.normal(0, 20)
                    df.loc[group.index, 'Initial_Rate'] = round(max(50.0, rate), 1)
                    perf_count += 1
            
            df = df.drop(columns=['is_good', 'group'])
            
        if df['Is_Perforated'].sum() == 0:
            # Fallback nếu không có khoảng nào thỏa mãn tiêu chuẩn
            mid_idx = n_rows // 2
            perf_range = range(max(0, mid_idx - 10), min(n_rows, mid_idx + 10))
            df.loc[perf_range, 'Is_Perforated'] = True
            df.loc[perf_range, 'Production_Class'] = 'GOOD'
            df.loc[perf_range, 'Initial_Rate'] = 450.0
            
        df['Predicted_Class'] = None
        df['Confidence'] = None
        df['Predicted_Qo'] = None
        
        # Chỉ giữ lại các cột thiết yếu cùng các đường log gốc để phân tích
        essential_cols = [
            'Depth', 'Well_Name', 'Porosity', 'Sw', 'Vshale', 'Permeability', 
            'Is_Perforated', 'Production_Class', 'Initial_Rate',
            'Predicted_Class', 'Confidence', 'Predicted_Qo'
        ]
        
        for col in df.columns:
            if col not in essential_cols and col not in ['Unnamed: 0']:
                essential_cols.append(col)
                
        df = df[essential_cols]
        
        # Hiển thị thông báo ánh xạ thành công
        st.info(t["las_success"].format(well=well_name, mapped=", ".join(mapped_logs)), icon=":material/info:")
        return df
        
    finally:
        os.unlink(temp_file_path)

# Tải file mẫu CSV
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

uploaded_file = st.file_uploader(t["uploader"], type=["csv", "las"])

if uploaded_file:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    with st.spinner(t["spinner"]):
        if file_ext == '.las':
            raw_df = parse_las_file(uploaded_file)
        else:
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
