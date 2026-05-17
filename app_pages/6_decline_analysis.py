import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.production_analysis import fit_decline_curve, full_well_allocation, calculate_layer_decline

st.title("📉 Decline & PLT Matching Analysis")

# Dịch thuật
texts = {
    "English": {
        "upload_history": "Upload Production History (CSV)",
        "upload_plt": "Upload PLT Data (CSV)",
        "no_data": "Please upload production history and PLT data to begin analysis.",
        "analysis_header": "Well Performance Analysis",
        "dca_header": "Decline Curve Fitting (Total Well)",
        "plt_header": "Full Layer Allocation (PLT + KH Matching)",
        "layer_decline_header": "Individual Layer Decline Rates",
        "integration_info": "💡 This information is integrated with ML Advisor's current potential predictions."
    },
    "Vietnamese": {
        "upload_history": "Tải lên Lịch sử Khai thác (CSV)",
        "upload_plt": "Tải lên Dữ liệu PLT (CSV)",
        "no_data": "Vui lòng tải lên lịch sử khai thác và dữ liệu PLT để bắt đầu phân tích.",
        "analysis_header": "Phân tích Hiệu năng Giếng",
        "dca_header": "Khớp đường cong suy giảm (Toàn giếng)",
        "plt_header": "Phân bổ lưu lượng toàn giếng (PLT + KH Matching)",
        "layer_decline_header": "Hệ số suy giảm riêng từng tầng",
        "integration_info": "💡 Thông tin này đã được tích hợp để hiệu chỉnh dự báo lưu lượng hiện tại của ML Advisor."
    }
}
t = texts[st.session_state.lang]

# Helper: Lấy danh sách tất cả các khoảng đã bắn từ dữ liệu Log
def get_all_perf_intervals(df):
    if df is None: return []
    actual_perfs = df[df['Is_Perforated'] == True].copy()
    if actual_perfs.empty: return []
    
    # Nhóm các điểm bắn liên tiếp thành khoảng
    actual_perfs['group'] = (
        (actual_perfs['Well_Name'] != actual_perfs['Well_Name'].shift()) |
        (actual_perfs['Depth'].diff() > 1.2)
    ).cumsum()
    
    intervals = []
    for g_id in actual_perfs['group'].unique():
        g_df = actual_perfs[actual_perfs['group'] == g_id]
        intervals.append({
            'Top': g_df['Depth'].min(),
            'Base': g_df['Depth'].max(),
            'Permeability': g_df['Permeability'].mean() if 'Permeability' in g_df.columns else 1.0,
            'Thickness': g_df['Depth'].max() - g_df['Depth'].min() if len(g_df) > 1 else 0.1
        })
    return intervals

col1, col2 = st.columns(2)
with col1:
    history_file = st.file_uploader(t["upload_history"], type="csv")
with col2:
    plt_file = st.file_uploader(t["upload_plt"], type="csv")

# Helper: Tạo dữ liệu mẫu
def create_sample_data():
    dates = pd.date_range(start='2020-01-01', periods=48, freq='ME')
    history = pd.DataFrame({
        'Date': dates,
        'Oil_Rate': 500 * np.exp(-0.02 * np.arange(48)) + np.random.normal(0, 10, 48)
    })
    
    # Lấy các khoảng bắn thực tế từ raw_df
    raw_df = st.session_state.get('raw_df')
    actual_intervals = []
    well_name = 'Well-A'
    if raw_df is not None and not raw_df.empty:
        well_name = raw_df['Well_Name'].iloc[0] if 'Well_Name' in raw_df.columns else 'Well-A'
        well_raw_df = raw_df[raw_df['Well_Name'] == well_name]
        actual_intervals = get_all_perf_intervals(well_raw_df)
        
    if actual_intervals:
        num_layers = len(actual_intervals)
        
        # Phân bổ tỷ lệ đóng góp lúc đầu (2021-06-01) và lúc sau (2023-06-01)
        if num_layers == 1:
            pct_start = [100.0]
            pct_end = [100.0]
        else:
            base_pcts = np.linspace(60, 40, num_layers)
            sum_base = sum(base_pcts)
            pct_start = [(p / sum_base) * 100.0 for p in base_pcts]
            
            end_pcts = np.linspace(30, 70, num_layers)
            sum_end = sum(end_pcts)
            pct_end = [(p / sum_end) * 100.0 for p in end_pcts]
            
        plt_rows = []
        # Thời điểm 1: 2021-06-01
        for i, interval in enumerate(actual_intervals):
            plt_rows.append({
                'Well_Name': well_name,
                'Date': '2021-06-01',
                'Top': interval['Top'],
                'Base': interval['Base'],
                'Contribution_Pct': round(pct_start[i], 1)
            })
        # Thời điểm 2: 2023-06-01
        for i, interval in enumerate(actual_intervals):
            plt_rows.append({
                'Well_Name': well_name,
                'Date': '2023-06-01',
                'Top': interval['Top'],
                'Base': interval['Base'],
                'Contribution_Pct': round(pct_end[i], 1)
            })
            
        plt = pd.DataFrame(plt_rows)
    else:
        # PLT đo tại 2 thời điểm cho 2 tầng mặc định
        plt = pd.DataFrame({
            'Well_Name': ['Well-A'] * 4,
            'Date': ['2021-06-01', '2021-06-01', '2023-06-01', '2023-06-01'],
            'Top': [3150.0, 3170.0, 3150.0, 3170.0],
            'Base': [3160.0, 3180.0, 3160.0, 3180.0],
            'Contribution_Pct': [60, 40, 30, 70]
        })
        
    return history, plt

if not history_file or not plt_file:
    st.info(t["no_data"])
    if st.button("Generate Sample Data for Demo"):
        h_sample, p_sample = create_sample_data()
        st.session_state.history_df = h_sample
        st.session_state.plt_df = p_sample
        st.rerun()
else:
    st.session_state.history_df = pd.read_csv(history_file)
    st.session_state.plt_df = pd.read_csv(plt_file)

if "history_df" in st.session_state and "plt_df" in st.session_state:
    history_df = st.session_state.history_df
    plt_df = st.session_state.plt_df
    
    # Lấy danh sách khoảng bắn thực tế từ dữ liệu Log
    all_perf_intervals = get_all_perf_intervals(st.session_state.get('raw_df'))
    
    # Nếu không có dữ liệu log, tạo giả định từ PLT để demo
    if not all_perf_intervals and not plt_df.empty:
        unique_layers = plt_df.drop_duplicates(['Top', 'Base'])
        for _, row in unique_layers.iterrows():
            all_perf_intervals.append({
                'Top': row['Top'], 'Base': row['Base'], 'Permeability': 10.0, 'Thickness': row['Base'] - row['Top']
            })

    st.divider()
    st.subheader(t["analysis_header"])
    
    # 1. DCA Fitting
    history_df['Date'] = pd.to_datetime(history_df['Date'])
    history_df = history_df.sort_values('Date')
    days_since_start = (history_df['Date'] - history_df['Date'].iloc[0]).dt.days.values
    rates = history_df['Oil_Rate'].values
    
    popt, model_func = fit_decline_curve(days_since_start, rates)
    
    if popt is not None:
        st.markdown(f"#### {t['dca_header']}")
        fig_dca = go.Figure()
        fig_dca.add_trace(go.Scatter(x=history_df['Date'], y=rates, name="Actual", mode='markers'))
        fig_dca.add_trace(go.Scatter(x=history_df['Date'], y=model_func(days_since_start, *popt), 
                                     name="Matched (Arps)", line=dict(color='red', width=3)))
        st.plotly_chart(fig_dca, use_container_width=True)
        
        # 2. Full Well Allocation (Matching with PLT & KH)
        st.markdown(f"#### {t['plt_header']}")
        if all_perf_intervals:
            allocated_df = full_well_allocation(history_df, plt_df, all_perf_intervals)
            if not allocated_df.empty:
                allocated_df['Layer'] = allocated_df['Top'].astype(str) + " - " + allocated_df['Base'].astype(str)
                fig_plt = px.area(allocated_df, x='Date', y='Allocated_Rate', color='Layer',
                                 title="Total Production Allocated to All Layers (PLT + KH Matching)",
                                 hover_data=['Contribution_Pct', 'Source'])
                st.plotly_chart(fig_plt, use_container_width=True)
                
                # 3. Layer Decline
                st.markdown(f"#### {t['layer_decline_header']}")
                layer_decline = calculate_layer_decline(allocated_df)
                if not layer_decline.empty:
                    st.dataframe(layer_decline.style.format({'Decline_Rate_Annual': '{:.2%}', 'Current_Rate': '{:.1f}'}), use_container_width=True)
                    st.session_state.layer_decline = layer_decline
                    st.success(t["integration_info"])
                else:
                    st.warning("Not enough points to calculate per-layer decline.")
        else:
            st.warning("No perforation intervals found.")
    else:
        st.error("Could not fit decline curve. Check your data format.")
