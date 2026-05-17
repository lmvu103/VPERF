import streamlit as st

# CSS tùy chỉnh để làm giao diện hướng dẫn sử dụng và thẻ tác giả trông cực kỳ sang trọng (Premium Glassmorphism)
st.markdown("""
    <style>
        .workflow-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
            margin-bottom: 20px;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .workflow-card:hover {
            transform: translateY(-5px);
            border-color: rgba(26, 127, 55, 0.4);
            box-shadow: 0 12px 40px 0 rgba(26, 127, 55, 0.15);
        }
        .step-badge {
            background: linear-gradient(135deg, #2ea44f 0%, #1a7f37 100%);
            color: white;
            font-weight: 700;
            font-size: 0.9rem;
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(26, 127, 55, 0.3);
        }
        .step-title {
            font-size: 1.35rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #ffffff;
        }
        .step-desc {
            font-size: 1.05rem;
            color: #d0d0d0;
            line-height: 1.6;
        }
        .author-card {
            background: linear-gradient(135deg, rgba(20, 20, 20, 0.65) 0%, rgba(30, 30, 30, 0.75) 100%);
            backdrop-filter: blur(15px);
            border-radius: 16px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.3);
            text-align: center;
            max-width: 500px;
            margin: 40px auto 20px auto;
            transition: all 0.4s ease;
        }
        .author-card:hover {
            border-color: rgba(26, 127, 55, 0.6);
            box-shadow: 0 15px 50px 0 rgba(26, 127, 55, 0.25);
        }
        .author-avatar {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2ea44f 0%, #1a7f37 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.2rem;
            font-weight: bold;
            color: white;
            margin: 0 auto 15px auto;
            box-shadow: 0 6px 20px rgba(26, 127, 55, 0.4);
        }
        .author-name {
            font-size: 1.6rem;
            font-weight: 700;
            color: white;
            margin-bottom: 5px;
            letter-spacing: 0.5px;
        }
        .author-title {
            font-size: 1.05rem;
            color: #a0a0a0;
            font-weight: 500;
            margin-bottom: 20px;
        }
        .author-contact {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 10px 15px;
            font-size: 1.05rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: inline-flex;
            align-items: center;
            gap: 10px;
            color: #e0e0e0;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        .author-contact:hover {
            background: rgba(26, 127, 55, 0.15);
            border-color: rgba(26, 127, 55, 0.3);
            color: #2ea44f;
        }
    </style>
""", unsafe_allow_html=True)

# Dịch thuật ngôn ngữ
texts = {
    "English": {
        "subheader": "Reservoir Perforation Optimization Workflow",
        "intro": "Welcome to **VPERF** dashboard! Below is the step-by-step workflow designed to guide you from raw logging data up to comprehensive reservoir economics.",
        "step1_badge": "STEP 01",
        "step1_title": "📂 Well Logging Data Upload",
        "step1_desc": "Upload geophysical well log files in `.csv` format. The system automatically performs validation, parsing, and quality control. This data forms the base foundation for all subsequent evaluations.",
        
        "step2_badge": "STEP 02",
        "step2_title": "📊 Geophysical Log Visualizer",
        "step2_desc": "Explore 4 vital tracks simultaneously: **Porosity, Sw, Vshale, and Netpay**. Use Plotly interactive zoom and pan to pinpoint high-potential layers highlighted with custom semi-transparent green shading.",
        
        "step3_badge": "STEP 03",
        "step3_title": "🧠 AI-Driven Perforation Selection (ML Advisor)",
        "step3_desc": "Train Machine Learning classifiers to predict reservoir quality classes (BEST, GOOD, MEDIUM). Propose optimal new perforation intervals clean of **Shale (Vshale < 0.4)** and **Water (Sw <= 0.6)**, merged safely up to 2.0m using priority propagation.",
        
        "step4_badge": "STEP 04",
        "step4_title": "💧 Production Rate Forecasting",
        "step4_desc": "Predict the initial oil flow rate ($Q_o$ - BOPD) of new zones. Using regression algorithms, the flow rate is evaluated against average geophysical reservoir indicators inside the proposed open boundaries.",
        
        "step5_badge": "STEP 05",
        "step5_title": "📉 Decline Curves & Production Allocation (PLT)",
        "step5_desc": "Upload well history & PLT data, or click 'Generate Sample' to automatically extract your well's historical intervals and synthesize PLT timelines. Match production decline curves (Arps) and allocate rates to calculate per-layer decline coefficients.",
        
        "step6_badge": "STEP 06",
        "step6_title": "💰 Financial & Economic Assessment",
        "step6_desc": "Compute 3-Year NPV and investment Payback Period. Using custom financial parameters, all new proposals are ranked by investment priority so you target only the economically viable best reservoir bands.",
        
        "author_title": "Lead Software & Reservoir Engineer",
        "author_contact": "📧 Get in Touch:"
    },
    "Vietnamese": {
        "subheader": "Quy trình tối ưu hóa thiết kế khoảng bắn mở vỉa",
        "intro": "Chào mừng bạn đến với **VPERF**! Dưới đây là quy trình làm việc từng bước được thiết kế bài bản để dẫn dắt kỹ sư từ tập số liệu địa vật lý thô ban đầu đến đánh giá chi tiết hiệu quả kinh tế mỏ.",
        "step1_badge": "BƯỚC 01",
        "step1_title": "📂 Tải lên dữ liệu địa vật lý giếng (Data Upload)",
        "step1_desc": "Tải lên tệp log địa vật lý giếng dạng `.csv`. Hệ thống sẽ tự động xác minh cấu trúc, kiểm tra chất lượng dữ liệu và làm sạch các khoảng khuyết thiếu. Đây là nền tảng số liệu đầu vào cho toàn bộ chuỗi tính toán phía sau.",
        
        "step2_badge": "BƯỚC 02",
        "step2_title": "📊 Trực quan hóa log địa vật lý (Log Visualizer)",
        "step2_desc": "Trực quan hóa tương tác 4 track log cốt lõi gồm: **Porosity, Sw, Vshale** và **Netpay**. Track Netpay được tô phủ màu xanh lá mờ đặc trưng giúp kỹ sư định vị nhanh các vỉa chứa dầu tiềm năng cao.",
        
        "step3_badge": "BƯỚC 03",
        "step3_title": "🧠 Đề xuất khoảng bắn bằng trí tuệ nhân tạo (ML Advisor)",
        "step3_desc": "Huấn luyện mô hình học máy phân loại chất lượng tầng chứa (`BEST`, `GOOD`, `MEDIUM`). Thuật toán gộp thông minh tự động loại bỏ sét (`Vshale >= 0.4`) và nước (`Sw > 0.6`), gộp khoảng cách `<= 2.0m` không chứa sét/nước và kế thừa nhãn tối ưu.",
        
        "step4_badge": "BƯỚC 04",
        "step4_title": "💧 Dự báo lưu lượng khai thác dầu ban đầu",
        "step4_desc": "Dự báo lưu lượng khai thác dầu khí ban đầu ($Q_o$ - BOPD) của các khoảng đề xuất mới. Sử dụng mô hình hồi quy nâng cao phân tích trên các thuộc tính trung bình địa vật lý trong phạm vi tầng chứa.",
        
        "step5_badge": "BƯỚC 05",
        "step5_title": "📉 Phân tích suy giảm sản lượng & Khớp dữ liệu PLT",
        "step5_desc": "Nạp lịch sử khai thác và dữ liệu PLT (hoặc tự động sinh PLT đồng bộ tuyệt đối theo các khoảng bắn cũ của giếng hiện tại). Khớp đường cong suy giảm sản lượng Arps toàn giếng và phân bổ lưu lượng chi tiết để tìm hệ số suy giảm riêng từng tầng.",
        
        "step6_badge": "BƯỚC 06",
        "step6_title": "💰 Đánh giá hiệu quả kinh tế đầu tư",
        "step6_desc": "Tính toán chỉ số NPV 3 năm và Thời gian hoàn vốn đầu tư (Payback Period). Dựa trên giá dầu dự báo và các tham số chi phí, hệ thống sẽ xếp hạng ưu tiên đầu tư để hỗ trợ ra quyết định bắn mở vỉa hiệu quả.",
        
        "author_title": "Kỹ sư Công nghệ & Phầm mềm Dầu khí",
        "author_contact": "📧 Liên hệ tác giả:"
    }
}

t = texts[st.session_state.lang]

st.subheader(t["subheader"], divider=False)
st.write(t["intro"])
st.write("")

# Hiển thị Workflow theo dạng thẻ Glassmorphism cao cấp
steps = [
    ("step1_badge", "step1_title", "step1_desc"),
    ("step2_badge", "step2_title", "step2_desc"),
    ("step3_badge", "step3_title", "step3_desc"),
    ("step4_badge", "step4_title", "step4_desc"),
    ("step5_badge", "step5_title", "step5_desc"),
    ("step6_badge", "step6_title", "step6_desc"),
]

for badge_k, title_k, desc_k in steps:
    st.markdown(f"""
        <div class="workflow-card">
            <div class="step-badge">{t[badge_k]}</div>
            <div class="step-title">{t[title_k]}</div>
            <div class="step-desc">{t[desc_k]}</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")
st.divider()

# Thẻ tác giả Glassmorphism cực kỳ chuyên nghiệp ở phần cuối cùng
st.markdown(f"""
    <div class="author-card">
        <div class="author-avatar">LMV</div>
        <div class="author-name">Le Minh Vu</div>
        <div class="author-title">{t["author_title"]}</div>
        <a class="author-contact" href="mailto:lmvu103@gmail.com">
            {t["author_contact"]} <b>lmvu103@gmail.com</b>
        </a>
    </div>
""", unsafe_allow_html=True)
