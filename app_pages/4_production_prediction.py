import streamlit as st
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt
import plotly.express as px
from utils.ml import train_production_model, PRODUCTION_FEATURES

if st.session_state.raw_df is None:
    # Dịch thông báo lỗi nếu chưa upload dữ liệu
    warn_msg = "Please upload data at the Data Upload page first." if st.session_state.lang == "English" else "Vui lòng tải dữ liệu ở trang Upload Dữ Liệu trước."
    st.warning(warn_msg, icon=":material/warning:")
    st.stop()

df = st.session_state.raw_df

# Dịch thuật
texts = {
    "English": {
        "subheader": "Initial Oil Rate Prediction",
        "train_btn": "Train Production Model",
        "training_spinner": "Training production prediction model...",
        "error_data": "Need more historical production data (Initial_Rate) from old wells to train (at least 10 samples).",
        "success_train": "Training successful!",
        "perf_header": "📊 Actual vs. Predicted (Model Performance)",
        "actual_label": "Actual (BOPD)",
        "pred_label": "Predicted (BOPD)",
        "chart_title": "Comparison of Actual and Predicted Flow Rates",
        "mae_info": "Mean Absolute Error of the model: **",
        "proposals_header": "🎯 Production forecast for potential layers (filtered by Net Pay)",
        "showing_proposals_prefix": "Displaying forecast for **",
        "showing_proposals_suffix": "** potential layers meeting Net Pay standards.",
        "shap_header": "SHAP Explanation for Potential Layer",
        "select_layer": "Select layer for analysis (Well @ Top):",
        "shap_info": "The SHAP analysis above explains the forecast value at the reservoir top (",
        "warn_ml_advisor": "Please perform analysis and set Net Pay threshold at the **'ML Advisor'** page first."
    },
    "Vietnamese": {
        "subheader": "Dự Báo Lưu Lượng Dầu Ban Đầu (Initial Rate Prediction)",
        "train_btn": "Huấn luyện Mô Hình Lưu Lượng",
        "training_spinner": "Đang huấn luyện mô hình dự báo lưu lượng...",
        "error_data": "Cần thêm dữ liệu lưu lượng thực tế (Initial_Rate) từ các giếng cũ để huấn luyện (ít nhất 10 mẫu).",
        "success_train": "Huấn luyện thành công!",
        "perf_header": "📊 Đối chiếu Thực tế vs Dự báo (Model Performance)",
        "actual_label": "Thực tế (BOPD)",
        "pred_label": "Dự báo (BOPD)",
        "chart_title": "So sánh Lưu lượng Thực tế và Dự báo",
        "mae_info": "Sai số trung bình của mô hình: **",
        "proposals_header": "🎯 Dự báo lưu lượng cho các tầng tiềm năng (đã lọc Net Pay)",
        "showing_proposals_prefix": "Đang hiển thị dự báo cho **",
        "showing_proposals_suffix": "** tầng tiềm năng đạt tiêu chuẩn Net Pay.",
        "shap_header": "Giải thích SHAP cho tầng tiềm năng",
        "select_layer": "Chọn tầng để phân tích (Well @ Top):",
        "shap_info": "Phân tích SHAP phía trên giải thích cho giá trị dự báo tại đỉnh vỉa (",
        "warn_ml_advisor": "Vui lòng thực hiện phân tích và thiết lập ngưỡng Net Pay tại trang **'ML Advisor'** trước."
    }
}
t = texts[st.session_state.lang]

st.subheader(t["subheader"], divider=False)

if st.button(t["train_btn"], type="primary"):
    with st.spinner(t["training_spinner"]):
        model, features_used = train_production_model(df)
        if model is None:
            st.error(t["error_data"], icon=":material/error:")
        else:
            st.session_state.production_model = model
            st.session_state.production_features = features_used
            st.success(t["success_train"], icon=":material/check_circle:")

model = st.session_state.production_model
features = st.session_state.production_features

if model:
    # 1. ĐỐI CHIẾU THỰC TẾ VS DỰ BÁO TRÊN DỮ LIỆU CŨ
    st.markdown(f"### {t['perf_header']}")
    train_df = df[df['Is_Perforated'] == True].dropna(subset=['Initial_Rate'])
    if not train_df.empty:
        train_df['Predicted_Qo'] = model.predict(train_df[features])
        
        fig = px.scatter(train_df, x='Initial_Rate', y='Predicted_Qo', 
                         hover_data=['Well_Name', 'Depth'],
                         labels={'Initial_Rate': t['actual_label'], 'Predicted_Qo': t['pred_label']},
                         title=t['chart_title'])
        max_val = max(train_df['Initial_Rate'].max(), train_df['Predicted_Qo'].max())
        fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="Red", dash="dash"))
        st.plotly_chart(fig, use_container_width=True)
        
        mae = np.mean(np.abs(train_df['Initial_Rate'] - train_df['Predicted_Qo']))
        st.info(f"{t['mae_info']}{mae:.2f} BOPD**.", icon=":material/analytics:")

    # 2. DỰ BÁO CHO CÁC KHOẢNG ĐÃ QUA BỘ LỌC NET PAY (ML ADVISOR)
    st.markdown(f"### {t['proposals_header']}")
    
    ml_proposals = st.session_state.get('ml_proposals')
    
    if ml_proposals is not None and not ml_proposals.empty:
        st.write(f"{t['showing_proposals_prefix']}{len(ml_proposals)}{t['showing_proposals_suffix']}")
        
        display_df = ml_proposals.copy()
        if 'Predicted_Qo' in display_df.columns:
            qo_label = 'Dự báo Qo (BOPD)' if st.session_state.lang == "Vietnamese" else 'Predicted Qo (BOPD)'
            display_df.rename(columns={'Predicted_Qo': qo_label}, inplace=True)
            
        st.dataframe(display_df.sort_values('Net_Pay', ascending=False), use_container_width=True)
        
        # Giải thích SHAP cho tầng được chọn
        st.markdown(f"### {t['shap_header']}")
        selected_idx = st.selectbox(t["select_layer"], 
                                    ml_proposals.index, 
                                    format_func=lambda x: f"{ml_proposals.loc[x, 'Well_Name']} @ {ml_proposals.loc[x, 'Top']}m")
        
        target_well = ml_proposals.loc[selected_idx, 'Well_Name']
        target_top = ml_proposals.loc[selected_idx, 'Top']
        
        # Lấy dữ liệu chi tiết của tầng này từ raw_df để SHAP
        instance_df = df[(df['Well_Name'] == target_well) & (df['Depth'] == target_top)].head(1)
        
        if not instance_df.empty:
            instance = instance_df[features]
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(instance)
            
            plt.clf()
            shap.force_plot(explainer.expected_value, shap_values[0, :], instance.iloc[0, :], matplotlib=True, show=False)
            st.pyplot(plt.gcf(), bbox_inches='tight')
            
            st.info(f"{t['shap_info']}{target_top}m).", icon=":material/info:")
    else:
        st.info(t["warn_ml_advisor"], icon=":material/info:")
