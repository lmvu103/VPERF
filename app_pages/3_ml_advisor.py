import streamlit as st
import pandas as pd
import numpy as np
from utils.ml import train_advanced_model, EXTENDED_FEATURES

def calculate_net_pay(df, class_col='Predicted_Class', target_class='BEST', prod_model=None, prod_features=None):
    """Tính toán Net Pay và Dự báo lưu lượng cho các khoảng liên tục"""
    df = df.sort_values(['Well_Name', 'Depth'])
    results = []
    
    for well in df['Well_Name'].unique():
        well_df = df[df['Well_Name'] == well].copy()
        well_df['is_target'] = (well_df[class_col] == target_class)
        
        # Tạo ID nhóm cho các điểm liên tục
        well_df['group'] = (well_df['is_target'] != well_df['is_target'].shift()).cumsum()
        
        target_groups = well_df[well_df['is_target'] == True]
        
        for g_id in target_groups['group'].unique():
            group_df = target_groups[target_groups['group'] == g_id]
            top = group_df['Depth'].min()
            base = group_df['Depth'].max()
            net_pay = base - top
            
            if net_pay == 0 and len(group_df) > 0:
                net_pay = 0.1 
            
            # Dự báo lưu lượng nếu có mô hình production
            pred_rate = None
            if prod_model and prod_features:
                # Kiểm tra đủ features
                if all(f in group_df.columns for f in prod_features):
                    # Dự báo cho tất cả các điểm trong tầng và lấy trung bình
                    rates = prod_model.predict(group_df[prod_features])
                    pred_rate = round(np.mean(rates), 1)
            
            results.append({
                'Well_Name': well,
                'Top': top,
                'Base': base,
                'Net_Pay': round(net_pay, 2),
                'Avg_Confidence': round(group_df['Confidence'].mean(), 2),
                'Predicted_Qo': pred_rate
            })
            
    return pd.DataFrame(results)

if st.session_state.raw_df is None:
    # Dịch thông báo lỗi nếu chưa upload dữ liệu
    warn_msg = "Please upload data at the Data Upload page first." if st.session_state.lang == "English" else "Vui lòng tải dữ liệu ở trang Upload Dữ Liệu trước."
    st.warning(warn_msg, icon=":material/warning:")
    st.stop()

df = st.session_state.raw_df

# Dịch thuật
texts = {
    "English": {
        "subheader": "Advanced Analysis using Gradient Boosting",
        "missing_cols": "Missing data columns:",
        "full_data": "Full extended data available for the model.",
        "train_btn": "Train Advanced Model",
        "training_spinner": "Training...",
        "error_data": "Not enough historical data to train (need at least 15 perforated intervals).",
        "success_train": "Training successful!",
        "feat_imp_header": "Analysis of Influencing Factors (Feature Importance)",
        "feat_imp_info_prefix": "Analysis shows that **",
        "feat_imp_info_suffix": "** is the most decisive factor for production in this area.",
        "best_zones_header": "🎯 Proposed New Perforation Intervals (BEST Zones)",
        "min_net_pay_label": "Minimum Net Pay threshold (m):",
        "prod_model_info": "💡 Note: To see production forecast (Qo), please train the model on the 'Production Prediction' page first.",
        "found_intervals_prefix": "Found **",
        "found_intervals_suffix": "** potential layers with Net Pay >= ",
        "no_best_zones": "No BEST layers reach the minimum thickness of ",
        "no_proposals": "No potential BEST intervals found.",
        "log_header": "📈 Log Visualizer: Comparison of Proposals vs. Actuals",
        "select_wells_log": "Select wells to display Log:",
        "depth_range_label": "Depth range (m)",
        "info_select_well": "Please select at least one well to view the Log chart."
    },
    "Vietnamese": {
        "subheader": "Phân tích nâng cao bằng Gradient Boosting",
        "missing_cols": "Thiếu các cột dữ liệu:",
        "full_data": "Đầy đủ dữ liệu mở rộng cho mô hình.",
        "train_btn": "Huấn luyện Mô Hình Nâng Cao",
        "training_spinner": "Đang huấn luyện...",
        "error_data": "Không đủ dữ liệu lịch sử để huấn luyện (cần ít nhất 15 khoảng đã bắn).",
        "success_train": "Huấn luyện thành công!",
        "feat_imp_header": "Phân tích các yếu tố ảnh hưởng (Feature Importance)",
        "feat_imp_info_prefix": "Phân tích cho thấy **",
        "feat_imp_info_suffix": "** là yếu tố quyết định nhất đến lưu lượng tại khu vực này.",
        "best_zones_header": "🎯 Đề xuất khoảng bắn mới (BEST Zones)",
        "min_net_pay_label": "Ngưỡng Net Pay tối thiểu (m):",
        "prod_model_info": "💡 Lưu ý: Để thấy dự báo lưu lượng (Qo), hãy huấn luyện mô hình ở trang 'Dự Báo Lưu Lượng' trước.",
        "found_intervals_prefix": "Tìm thấy **",
        "found_intervals_suffix": "** tầng tiềm năng có chiều dày Net Pay >= ",
        "no_best_zones": "Không có tầng BEST nào đạt chiều dày tối thiểu ",
        "no_proposals": "Không tìm thấy khoảng tiềm năng BEST nào.",
        "log_header": "📈 Log Visualizer: Đối chiếu Đề Xuất vs Thực Tế",
        "select_wells_log": "Chọn các giếng để hiển thị Log:",
        "depth_range_label": "Khoảng độ sâu (m)",
        "info_select_well": "Vui lòng chọn ít nhất một giếng để xem biểu đồ Log."
    }
}
t = texts[st.session_state.lang]

st.subheader(t["subheader"], divider=False)

missing_cols = [col for col in EXTENDED_FEATURES if col not in df.columns]
if missing_cols:
    st.warning(f"{t['missing_cols']} {', '.join(missing_cols)}", icon=":material/warning:")
else:
    st.success(t["full_data"], icon=":material/check_circle:")

if st.button(t["train_btn"], type="primary"):
    with st.spinner(t["training_spinner"]):
        model, used_features = train_advanced_model(df)
        if model is None:
            st.error(t["error_data"], icon=":material/error:")
        else:
            st.session_state.advanced_model = model
            st.session_state.advanced_features = used_features
            st.success(t["success_train"], icon=":material/check_circle:")

model = st.session_state.advanced_model
used_features = st.session_state.advanced_features

if model and used_features:
    # Feature Importance
    st.markdown(f"### {t['feat_imp_header']}")
    importance = pd.DataFrame({
        'Feature': used_features,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    st.bar_chart(importance.set_index('Feature'))
    
    top_feat = importance.iloc[0]['Feature']
    st.info(f"{t['feat_imp_info_prefix']}{top_feat}{t['feat_imp_info_suffix']}", icon=":material/lightbulb:")

    # Dự báo khoảng mới
    unperf_df = df[df['Is_Perforated'] == False].copy()
    if not unperf_df.empty:
        preds = model.predict(unperf_df[used_features])
        probs = model.predict_proba(unperf_df[used_features])
        
        unperf_df['Predicted_Class'] = preds
        unperf_df['Confidence'] = np.max(probs, axis=1)

        st.markdown(f"### {t['best_zones_header']}")
        
        # Gộp dữ liệu dự báo vào data gốc để vẽ đồ thị
        full_df = df.copy()
        full_df.loc[unperf_df.index, 'Predicted_Class'] = unperf_df['Predicted_Class']
        full_df.loc[unperf_df.index, 'Confidence'] = unperf_df['Confidence']
        
        # Dự báo Qo điểm cho các khoảng BEST nếu có mô hình production
        prod_model = st.session_state.get('production_model')
        prod_features = st.session_state.get('production_features')
        if prod_model and prod_features:
            best_mask = (full_df['Predicted_Class'] == 'BEST') & (full_df['Is_Perforated'] == False)
            if best_mask.any():
                full_df.loc[best_mask, 'Predicted_Qo'] = prod_model.predict(full_df.loc[best_mask, prod_features])
        
        # Lấy mô hình production từ session state nếu có
        prod_model = st.session_state.get('production_model')
        prod_features = st.session_state.get('production_features')
        
        # Tính toán Net Pay và Dự báo Qo
        net_pay_df = calculate_net_pay(full_df, prod_model=prod_model, prod_features=prod_features)
        
        if not net_pay_df.empty:
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                min_net_pay = st.slider(t["min_net_pay_label"], 0.0, 5.0, 0.1, 0.1)
            
            filtered_proposals = net_pay_df[net_pay_df['Net_Pay'] >= min_net_pay]
            st.session_state.ml_proposals = filtered_proposals
            
            # --- CẬP NHẬT: Chỉ hiển thị các khoảng đã lọc trên Log Visualizer ---
            full_df.loc[full_df['Is_Perforated'] == False, 'Predicted_Class'] = None
            for _, row in filtered_proposals.iterrows():
                mask = (full_df['Well_Name'] == row['Well_Name']) & \
                       (full_df['Depth'] >= row['Top']) & \
                       (full_df['Depth'] <= row['Base']) & \
                       (full_df['Is_Perforated'] == False)
                full_df.loc[mask, 'Predicted_Class'] = 'BEST'

            if prod_model is None:
                st.info(t["prod_model_info"], icon=":material/info:")
            
            st.write(f"{t['found_intervals_prefix']}{len(filtered_proposals)}{t['found_intervals_suffix']}{min_net_pay}m.")
            if not filtered_proposals.empty:
                display_df = filtered_proposals.copy()
                if 'Predicted_Qo' in display_df.columns:
                    qo_label = 'Dự báo Qo (BOPD)' if st.session_state.lang == "Vietnamese" else 'Predicted Qo (BOPD)'
                    display_df.rename(columns={'Predicted_Qo': qo_label}, inplace=True)
                
                st.dataframe(display_df.sort_values('Net_Pay', ascending=False), use_container_width=True)
            else:
                st.info(f"{t['no_best_zones']}{min_net_pay}m.")
        else:
            st.info(t["no_proposals"])
            
        st.divider()
        st.markdown(f"### {t['log_header']}")
        
        from utils.plots import plot_well_logs
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if 'Well_Name' in full_df.columns:
                all_wells = full_df['Well_Name'].unique().tolist()
                default_wells = st.session_state.wells if st.session_state.wells else (all_wells[:1] if all_wells else [])
                wells = st.multiselect(t["select_wells_log"], all_wells, default=default_wells, key="ml_wells")
                st.session_state.wells = wells
            else:
                wells = []

        with col2:
            if 'Depth' in full_df.columns:
                min_d = float(full_df['Depth'].min())
                max_d = float(full_df['Depth'].max())
                curr_min, curr_max = st.session_state.depth_range if isinstance(st.session_state.depth_range, tuple) else (min_d, min_d + 100.0)
                curr_min = max(min_d, min(curr_min, max_d))
                curr_max = max(min_d, min(curr_max, max_d))
                if curr_min >= curr_max:
                    curr_max = min(curr_min + 100.0, max_d)
                    
                depth_range = st.slider(t["depth_range_label"], min_d, max_d, (curr_min, curr_max), key="ml_depth")
                st.session_state.depth_range = depth_range
            else:
                depth_range = (0.0, 100.0)
                
        if wells:
            fig = plot_well_logs(full_df, wells, depth_range, show_proposal=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t["info_select_well"], icon=":material/info:")
