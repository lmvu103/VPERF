import streamlit as st
import pandas as pd
import numpy as np
from utils.ml import train_advanced_model, EXTENDED_FEATURES

def analyze_historical_intervals(df, available_features):
    """Phân tích các khoảng bắn lịch sử để tìm đặc trưng và chiều dày"""
    actual_perfs = df[df['Is_Perforated'] == True].copy()
    if actual_perfs.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    actual_perfs = actual_perfs.sort_values(['Well_Name', 'Depth'])
    # Tạo ID nhóm cho các điểm bắn liên tiếp có cùng Production_Class
    actual_perfs['group'] = (
        (actual_perfs['Production_Class'] != actual_perfs['Production_Class'].shift()) | 
        (actual_perfs['Well_Name'] != actual_perfs['Well_Name'].shift()) |
        (actual_perfs['Depth'].diff() > 1.2) # Dùng threshold tương tự plot log
    ).cumsum()
    
    hist_results = []
    for g_id in actual_perfs['group'].unique():
        g_df = actual_perfs[actual_perfs['group'] == g_id]
        if g_df.empty: continue
        
        top = g_df['Depth'].min()
        base = g_df['Depth'].max()
        thick = base - top if base > top else 0.1
        
        # Lấy lưu lượng (giả sử lưu lượng được gán cho toàn bộ khoảng hoặc điểm đầu)
        rate = g_df['Initial_Rate'].iloc[0] if 'Initial_Rate' in g_df.columns else np.nan
        
        res = {
            'Production_Class': g_df['Production_Class'].iloc[0],
            'Thickness': thick,
            'Initial_Rate': rate
        }
        # Thêm trung bình các features
        for feat in available_features:
            if feat in g_df.columns:
                res[feat] = g_df[feat].mean()
        
        hist_results.append(res)
    
    hist_df = pd.DataFrame(hist_results)
    
    # Bảng đặc trưng theo phân loại
    char_df = hist_df.groupby('Production_Class').mean().drop(columns=['Thickness', 'Initial_Rate'], errors='ignore')
    
    return hist_df, char_df

def calculate_net_pay(df, class_col='Predicted_Class', target_classes=None, prod_model=None, prod_features=None):
    """Tính toán Net Pay và Dự báo lưu lượng cho các khoảng liên tục và gộp khoảng gần nhau"""
    if target_classes is None:
        target_classes = ['BEST', 'GOOD', 'MEDIUM']
        
    df = df.sort_values(['Well_Name', 'Depth'])
    results = []
    
    class_priority = {'BEST': 3, 'GOOD': 2, 'MEDIUM': 1}
    
    for well in df['Well_Name'].unique():
        well_df = df[df['Well_Name'] == well].copy()
        
        # Lọc các điểm chưa bắn và có phân loại mục tiêu
        is_target = (well_df[class_col].isin(target_classes)) & (well_df['Is_Perforated'] == False)
        # Không được vào khoảng shale
        if 'Vshale' in well_df.columns:
            is_target = is_target & (well_df['Vshale'] < 0.4)
        # Không phải netpay và không đề xuất bắn nếu Sw > 0.6
        if 'Sw' in well_df.columns:
            is_target = is_target & (well_df['Sw'] <= 0.6)
            
        well_df['is_target'] = is_target
        
        target_df = well_df[well_df['is_target'] == True].copy()
        if target_df.empty:
            continue
            
        # Gộp các khoảng nhỏ gần nhau thành khoảng lớn liên tục (khoảng cách <= 2.0m và không có shale ở giữa)
        groups = []
        current_group = [target_df.iloc[0]]
        
        for idx in range(1, len(target_df)):
            row = target_df.iloc[idx]
            prev_row = current_group[-1]
            
            depth_gap = row['Depth'] - prev_row['Depth']
            
            has_blocker_in_gap = False
            if depth_gap <= 2.0:
                gap_points = well_df[(well_df['Depth'] > prev_row['Depth']) & (well_df['Depth'] < row['Depth'])]
                if 'Vshale' in gap_points.columns:
                    if (gap_points['Vshale'] >= 0.4).any():
                        has_blocker_in_gap = True
                if 'Sw' in gap_points.columns:
                    if (gap_points['Sw'] > 0.6).any():
                        has_blocker_in_gap = True
                        
            if depth_gap <= 2.0 and not has_blocker_in_gap:
                current_group.append(row)
            else:
                groups.append(current_group)
                current_group = [row]
        groups.append(current_group)
        
        for group in groups:
            if not group:
                continue
            # Lấy top và base của cả khoảng gộp
            top = min(r['Depth'] for r in group)
            base = max(r['Depth'] for r in group)
            
            # Chiều dày khoảng bắn gộp
            net_pay = base - top
            if net_pay < 0.15:
                net_pay = 0.15 # Chiều dày tối thiểu của 1 lớp
                
            # Xác định Predicted_Class của khoảng gộp (lấy class có độ ưu tiên cao nhất)
            classes_present = [r[class_col] for r in group if r[class_col] in class_priority]
            if classes_present:
                pred_class = max(classes_present, key=lambda c: class_priority[c])
            else:
                pred_class = group[0][class_col]
                
            # Tính độ tin cậy trung bình
            avg_conf = np.mean([r['Confidence'] for r in group])
            
            # Dự báo lưu lượng Qo trung bình của cả khoảng gộp
            group_df = pd.DataFrame(group)
            pred_rate = None
            if prod_model and prod_features:
                if all(f in group_df.columns for f in prod_features):
                    rates = prod_model.predict(group_df[prod_features])
                    pred_rate = np.mean(rates)
                    
                    if "layer_decline" in st.session_state:
                        ld_df = st.session_state.layer_decline
                        avg_decline = ld_df['Decline_Rate_Annual'].mean()
                        years = 3.0 
                        pred_rate = pred_rate * np.exp(-avg_decline * years)
                    
                    pred_rate = round(pred_rate, 1)
                    
            results.append({
                'Well_Name': well,
                'Top': top,
                'Base': base,
                'Predicted_Class': pred_class,
                'Net_Pay': round(net_pay, 2),
                'Avg_Confidence': round(avg_conf, 2),
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
        "analysis_tab": "Characteristic Analysis",
        "proposal_tab": "New Proposals (>= 0.1m)",
        "char_header": "Mean Characteristics by Production Class",
        "thick_header": "Thickness vs. Initial Rate Analysis",
        "best_zones_header": "🎯 Proposed New Perforation Intervals (MEDIUM, GOOD, BEST)",
        "min_net_pay_label": "Minimum Net Pay threshold (m):",
        "prod_model_info": "💡 Note: To see production forecast (Qo), please train the model on the 'Production Prediction' page first.",
        "found_intervals_prefix": "Found **",
        "found_intervals_suffix": "** potential layers with Net Pay >= ",
        "no_best_zones": "No potential layers reach the minimum thickness of ",
        "no_proposals": "No potential intervals found.",
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
        "analysis_tab": "Phân tích Đặc trưng",
        "proposal_tab": "Đề xuất Mới (>= 0.1m)",
        "char_header": "Tính chất trung bình theo phân loại (Actual)",
        "thick_header": "Phân tích Chiều dày vs. Lưu lượng thực tế",
        "best_zones_header": "🎯 Đề xuất khoảng bắn mới (MEDIUM, GOOD, BEST)",
        "min_net_pay_label": "Ngưỡng Net Pay tối thiểu (m):",
        "prod_model_info": "💡 Lưu ý: Để thấy dự báo lưu lượng (Qo), hãy huấn luyện mô hình ở trang 'Dự Báo Lưu Lượng' trước.",
        "found_intervals_prefix": "Tìm thấy **",
        "found_intervals_suffix": "** tầng tiềm năng có chiều dày Net Pay >= ",
        "no_best_zones": "Không có tầng tiềm năng nào đạt chiều dày tối thiểu ",
        "no_proposals": "Không tìm thấy khoảng tiềm năng nào.",
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
        
        # Dự báo Qo điểm cho các khoảng tiềm năng nếu có mô hình production
        prod_model = st.session_state.get('production_model')
        prod_features = st.session_state.get('production_features')
        if prod_model and prod_features:
            target_classes = ['BEST', 'GOOD', 'MEDIUM']
            best_mask = (full_df['Predicted_Class'].isin(target_classes)) & (full_df['Is_Perforated'] == False)
            if best_mask.any():
                full_df.loc[best_mask, 'Predicted_Qo'] = prod_model.predict(full_df.loc[best_mask, prod_features])
        
        # Tính toán Net Pay và Dự báo Qo
        net_pay_df = calculate_net_pay(full_df, prod_model=prod_model, prod_features=prod_features)
        
        if not net_pay_df.empty:
            # Khôi phục slider cấu hình Net Pay tối thiểu theo yêu cầu "có netpay lớn (bỏ default >0.1)"
            min_net_pay = st.slider(t["min_net_pay_label"], 0.1, 10.0, 1.0, step=0.1)
            
            filtered_proposals = net_pay_df[net_pay_df['Net_Pay'] >= min_net_pay]
            st.session_state.ml_proposals = filtered_proposals
            
            # --- CẬP NHẬT: Chỉ hiển thị các khoảng đã lọc trên Log Visualizer ---
            full_df.loc[full_df['Is_Perforated'] == False, 'Predicted_Class'] = None
            for _, row in filtered_proposals.iterrows():
                mask = (full_df['Well_Name'] == row['Well_Name']) & \
                       (full_df['Depth'] >= row['Top']) & \
                       (full_df['Depth'] <= row['Base']) & \
                       (full_df['Is_Perforated'] == False)
                # Gán lại class chính xác cho từng khoảng
                full_df.loc[mask, 'Predicted_Class'] = row['Predicted_Class']

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
            # Thêm track vshale và netpay theo yêu cầu
            selected_logs = ['Porosity', 'Sw', 'Vshale', 'Netpay']
            
            # Đảm bảo full_df có cột Netpay để hiển thị
            full_df['Netpay'] = 0.0
            target_mask = (full_df['Predicted_Class'].isin(['BEST', 'GOOD', 'MEDIUM'])) & (full_df['Is_Perforated'] == False)
            if 'Vshale' in full_df.columns:
                target_mask = target_mask & (full_df['Vshale'] < 0.4)
            if 'Sw' in full_df.columns:
                target_mask = target_mask & (full_df['Sw'] <= 0.6)
            full_df.loc[target_mask, 'Netpay'] = 1.0
            
            fig = plot_well_logs(full_df, wells, depth_range, selected_logs=selected_logs, show_proposal=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t["info_select_well"], icon=":material/info:")
