import streamlit as st
import pandas as pd
from utils.economics import calculate_economics

if st.session_state.raw_df is None:
    # Dịch thông báo lỗi nếu chưa upload dữ liệu
    warn_msg = "Please upload data at the Data Upload page first." if st.session_state.lang == "English" else "Vui lòng tải dữ liệu ở trang Upload Dữ Liệu trước."
    st.warning(warn_msg, icon=":material/warning:")
    st.stop()

# Lấy danh sách đề xuất từ ML Advisor & Dự báo lưu lượng
ml_proposals = st.session_state.get('ml_proposals')

# Dịch thuật
texts = {
    "English": {
        "warn_ml": "Please perform analysis and filter potential layers at the 'ML Advisor' & 'Production Prediction' pages first.",
        "warn_prod": "Please train the model and forecast production at the 'Production Prediction' page first.",
        "subheader": "Economic Efficiency Analysis for Potential Layers",
        "info_best": "💡 The system only evaluates the economics of BEST layers that passed the Net Pay filter.",
        "sidebar_header": "Economic Parameters",
        "oil_price_label": "Forecasted Oil Price ($/bbl)",
        "discount_rate_label": "Discount Rate (%)",
        "capex_base_label": "Fixed CAPEX per perforation ($)",
        "capex_var_label": "Variable CAPEX ($/gun meter)",
        "ranking_header": "### Investment Priority Ranking",
        "success_finish": "Economic evaluation completed for **",
        "no_data": "No suitable potential layer data for calculation.",
        "col_well": "Well",
        "col_top": "Top (m)",
        "col_base": "Base (m)",
        "col_netpay": "Net Pay (m)",
        "col_qo": "Predicted Qo (BOPD)",
        "col_npv": "NPV 3-Year ($)",
        "col_payback": "Payback (Months)"
    },
    "Vietnamese": {
        "warn_ml": "Vui lòng thực hiện phân tích và lọc tầng tiềm năng ở trang 'ML Advisor' & 'Dự Báo Lưu Lượng' trước.",
        "warn_prod": "Vui lòng huấn luyện mô hình và dự báo lưu lượng ở trang 'Dự Báo Lưu Lượng' trước.",
        "subheader": "Phân tích Hiệu quả Kinh tế cho các Tầng Tiềm năng",
        "info_best": "💡 Hệ thống chỉ đánh giá kinh tế cho các tầng BEST đã vượt qua bộ lọc Net Pay.",
        "sidebar_header": "Thông số Kinh tế",
        "oil_price_label": "Giá dầu dự báo ($/bbl)",
        "discount_rate_label": "Tỷ lệ chiết khấu (%)",
        "capex_base_label": "CAPEX cố định mỗi lần bắn ($)",
        "capex_var_label": "CAPEX biến đổi ($/mét súng)",
        "ranking_header": "### Bảng xếp hạng ưu tiên đầu tư",
        "success_finish": "Đã hoàn tất đánh giá kinh tế cho **",
        "no_data": "Không có dữ liệu tầng tiềm năng phù hợp để tính toán.",
        "col_well": "Giếng",
        "col_top": "Đỉnh (m)",
        "col_base": "Đáy (m)",
        "col_netpay": "Net Pay (m)",
        "col_qo": "Dự báo Qo (BOPD)",
        "col_npv": "NPV 3-Năm ($)",
        "col_payback": "Hoàn vốn (Tháng)"
    }
}
t = texts[st.session_state.lang]

if ml_proposals is None or ml_proposals.empty:
    st.warning(t["warn_ml"], icon=":material/warning:")
    st.stop()

# Kiểm tra xem đã có dự báo lưu lượng chưa
if 'Predicted_Qo' not in ml_proposals.columns or ml_proposals['Predicted_Qo'].isna().all():
    st.warning(t["warn_prod"], icon=":material/warning:")
    st.stop()

st.subheader(t["subheader"], divider=False)
st.info(t["info_best"], icon=":material/info:")

with st.sidebar:
    st.header(t["sidebar_header"])
    oil_price = st.number_input(t["oil_price_label"], value=75)
    discount_rate = st.slider(t["discount_rate_label"], 5, 20, 12) / 100
    perf_cost_base = st.number_input(t["capex_base_label"], value=50000)
    perf_cost_per_m = st.number_input(t["capex_var_label"], value=2000)

results = []
for idx, row in ml_proposals.iterrows():
    # Sử dụng Net_Pay làm độ dày khoảng bắn
    thickness = row['Net_Pay']
    
    # Tính toán kinh tế dựa trên Qo dự báo
    npv, pb = calculate_economics(
        q_start=row['Predicted_Qo'], 
        decline_rate=0.15, # Mặc định 15%
        thickness=thickness,
        oil_price=oil_price,
        discount_rate=discount_rate,
        perf_cost_base=perf_cost_base,
        perf_cost_per_m=perf_cost_per_m
    )
    
    results.append({
        t['col_well']: row['Well_Name'],
        t['col_top']: row['Top'],
        t['col_base']: row['Base'],
        t['col_netpay']: thickness,
        t['col_qo']: row['Predicted_Qo'],
        t['col_npv']: f"{npv:,.0f}",
        t['col_payback']: f"{pb:.1f}" if pb > 0 else "N/A"
    })

if results:
    econ_df = pd.DataFrame(results)
    st.markdown(t["ranking_header"])
    st.dataframe(
        econ_df.sort_values(t['col_npv'], ascending=False),
        use_container_width=True
    )
    
    st.success(f"{t['success_finish']}{len(results)}** tầng tiềm năng.", icon=":material/payments:")
else:
    st.info(t["no_data"], icon=":material/info:")
