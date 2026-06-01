import streamlit as st
import pandas as pd
import shap
import matplotlib.pyplot as plt
from utils.plots import plot_well_logs
from utils.ml import PRODUCTION_FEATURES

@st.cache_data(show_spinner=False)
def cached_plot_well_logs(df_json, wells, depth_range, selected_logs, log_scales_json, show_proposal=False):
    """Cache wrapper to avoid re-rendering chart when inputs are unchanged."""
    import json
    from io import StringIO
    df = pd.read_json(StringIO(df_json), orient='split')
    log_scales = json.loads(log_scales_json) if log_scales_json else {}
    # Convert list tuples back
    log_scales = {w: {lg: tuple(v) for lg, v in logs.items()} for w, logs in log_scales.items()}
    return plot_well_logs(df, list(wells), depth_range, list(selected_logs), log_scales, show_proposal)

if st.session_state.processed_df is None:
    # Dịch thông báo lỗi nếu chưa upload dữ liệu
    warn_msg = "Please upload and analyze data at the Data Upload page first." if st.session_state.lang == "English" else "Vui lòng tải dữ liệu và phân tích ở trang Upload Dữ Liệu trước."
    st.warning(warn_msg, icon=":material/warning:")
    st.stop()

processed_df = st.session_state.processed_df

# Dịch thuật
texts = {
    "English": {
        "header": "Well Log and Prediction Comparison",
        "select_wells": "Select wells to view:",
        "no_well_name": "Data missing 'Well_Name' column.",
        "select_logs": "Select log tracks to display:",
        "scale_expander": "Customize Scale",
        "scale_mode": "Scale adjustment mode:",
        "scale_global": "Common to all wells",
        "scale_individual": "Individual per well",
        "well_label": "Well:",
        "depth_range_label": "Depth range (m)",
        "info_select_well": "Please select at least one well.",
        "info_select_log": "Please select at least one log track.",
        "zoom_tip": "Tip: You can zoom each well independently. Double-click to reset.",
        "shap_header": "SHAP Explanation for Selected Perforation",
        "shap_info": "Please train the model on the 'Production Prediction' page first to see SHAP explanation.",
        "shap_select_well": "Select well for analysis:",
        "shap_no_perf": "This well has no perforated interval data.",
        "shap_select_depth": "Select perforation depth:",
        "shap_spinner": "Calculating SHAP...",
        "shap_result_prefix": "Production at depth",
        "shap_result_suffix": "BOPD. The chart above explains factors affecting this value."
    },
    "Vietnamese": {
        "header": "So sánh Log và Dự báo giữa các giếng",
        "select_wells": "Chọn các giếng để xem:",
        "no_well_name": "Dữ liệu không có cột 'Well_Name'.",
        "select_logs": "Chọn các đường Log hiển thị:",
        "scale_expander": "Tùy chỉnh thang đo (Scale)",
        "scale_mode": "Chế độ chỉnh scale:",
        "scale_global": "Chung tất cả các giếng",
        "scale_individual": "Từng giếng riêng biệt",
        "well_label": "Giếng:",
        "depth_range_label": "Khoảng độ sâu (m)",
        "info_select_well": "Vui lòng chọn ít nhất một giếng.",
        "info_select_log": "Vui lòng chọn ít nhất một đường Log.",
        "zoom_tip": "Mẹo: Bạn có thể Zoom độc lập từng giếng. Để đồng bộ lại, hãy Double-click vào biểu đồ.",
        "shap_header": "Giải thích SHAP cho khoảng bắn đã chọn",
        "shap_info": "Vui lòng huấn luyện mô hình ở trang 'Dự Báo Lưu Lượng' trước để xem giải thích SHAP.",
        "shap_select_well": "Chọn giếng để phân tích:",
        "shap_no_perf": "Giếng này không có dữ liệu khoảng đã bắn.",
        "shap_select_depth": "Chọn độ sâu khoảng bắn:",
        "shap_spinner": "Đang tính toán SHAP...",
        "shap_result_prefix": "Lưu lượng tại độ sâu",
        "shap_result_suffix": "BOPD. Biểu đồ trên giải thích các yếu tố ảnh hưởng đến con số này."
    }
}
t = texts[st.session_state.lang]

st.subheader(t["header"], divider=False)

col1, col2 = st.columns([1, 2])

with col1:
    if 'Well_Name' in processed_df.columns:
        all_wells = processed_df['Well_Name'].unique().tolist()
        default_wells = st.session_state.wells if st.session_state.wells else (all_wells[:1] if all_wells else [])
        wells = st.multiselect(t["select_wells"], all_wells, default=default_wells)
        st.session_state.wells = wells
    else:
        wells = []
        st.error(t["no_well_name"], icon=":material/error:")

    exclude_cols = ['Depth', 'Well_Name', 'Is_Perforated', 'Production_Class', 'Initial_Rate', 'Predicted_Class', 'Confidence', 'Predicted_Qo', 'Unnamed: 0', 'Zone']
    numeric_cols = processed_df.select_dtypes(include='number').columns.tolist()
    available_logs = [col for col in numeric_cols if col not in exclude_cols]
    
    default_logs = [log for log in ['Porosity', 'Sw', 'Vshale', 'GR'] if log in available_logs]
    if not default_logs and available_logs:
        default_logs = available_logs[:2]
        
    selected_logs = st.multiselect(t["select_logs"], available_logs, default=default_logs)

    log_scales = {}
    if wells and selected_logs:
        with st.expander(t["scale_expander"]):
            mode = st.radio(t["scale_mode"], [t["scale_global"], t["scale_individual"]])
            
            if mode == t["scale_global"]:
                for log in selected_logs:
                    c_min = float(processed_df[log].min())
                    c_max = float(processed_df[log].max())
                    s1, s2 = st.columns(2)
                    with s1: vmin = st.number_input(f"{log} Min", value=c_min, key=f"global_{log}_min")
                    with s2: vmax = st.number_input(f"{log} Max", value=c_max, key=f"global_{log}_max")
                    for w in wells:
                        if w not in log_scales: log_scales[w] = {}
                        log_scales[w][log] = (vmin, vmax)
            else:
                for w in wells:
                    st.markdown(f"**{t['well_label']} {w}**")
                    for log in selected_logs:
                        w_data = processed_df[processed_df['Well_Name'] == w]
                        c_min = float(w_data[log].min()) if not w_data.empty else 0.0
                        c_max = float(w_data[log].max()) if not w_data.empty else 1.0
                        s1, s2 = st.columns(2)
                        with s1: vmin = st.number_input(f"{w}-{log} Min", value=c_min, key=f"{w}_{log}_min")
                        with s2: vmax = st.number_input(f"{w}-{log} Max", value=c_max, key=f"{w}_{log}_max")
                        if w not in log_scales: log_scales[w] = {}
                        log_scales[w][log] = (vmin, vmax)

with col2:
    if 'Depth' in processed_df.columns:
        min_d = float(processed_df['Depth'].min())
        max_d = float(processed_df['Depth'].max())
        
        curr_min, curr_max = st.session_state.depth_range if isinstance(st.session_state.depth_range, tuple) else (min_d, min_d + 100.0)
        curr_min = max(min_d, min(curr_min, max_d))
        curr_max = max(min_d, min(curr_max, max_d))
        if curr_min >= curr_max:
            curr_max = min(curr_min + 100.0, max_d)
            
        depth_range = st.slider(t["depth_range_label"], min_d, max_d, (curr_min, curr_max))
        st.session_state.depth_range = depth_range
    else:
        depth_range = (0.0, 100.0)

if not wells:
    st.info(t["info_select_well"], icon=":material/info:")
elif not selected_logs:
    st.info(t["info_select_log"], icon=":material/info:")
else:
    import json
    with st.spinner("Đang vẽ biểu đồ..." if st.session_state.lang == "Vietnamese" else "Rendering chart..."):
        fig = cached_plot_well_logs(
            processed_df.to_json(orient='split'),
            tuple(wells),
            depth_range,
            tuple(selected_logs),
            json.dumps({w: {lg: list(v) for lg, v in logs.items()} for w, logs in log_scales.items()})
        )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(t["zoom_tip"])

    # Phần giải thích SHAP
    st.divider()
    st.subheader(t["shap_header"], divider=False)
    
    if st.session_state.production_model is None:
        st.info(t["shap_info"], icon=":material/info:")
    else:
        s_well = st.selectbox(t["shap_select_well"], wells, key="shap_well")
        w_perfs = processed_df[(processed_df['Well_Name'] == s_well) & (processed_df['Is_Perforated'] == True)]
        
        if w_perfs.empty:
            st.warning(t["shap_no_perf"])
        else:
            s_depth = st.selectbox(t["shap_select_depth"], sorted(w_perfs['Depth'].unique()), key="shap_depth")
            inst_df = w_perfs[w_perfs['Depth'] == s_depth].head(1)
            
            avail_feats = [f for f in PRODUCTION_FEATURES if f in inst_df.columns]
            instance = inst_df[avail_feats]
            
            with st.spinner(t["shap_spinner"]):
                explainer = shap.TreeExplainer(st.session_state.production_model)
                shap_values = explainer.shap_values(instance)
                
                plt.clf()
                shap.force_plot(explainer.expected_value, shap_values[0,:], instance.iloc[0,:], matplotlib=True, show=False)
                st.pyplot(plt.gcf(), bbox_inches='tight')
            
            rate = inst_df['Initial_Rate'].values[0] if 'Initial_Rate' in inst_df.columns else "N/A"
            st.write(f"{t['shap_result_prefix']} {s_depth}m: **{rate} BOPD**. {t['shap_result_suffix']}")
