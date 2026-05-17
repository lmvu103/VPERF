# VPERF 📉 - Advanced ML Perforation & Reservoir Economics Dashboard

**VPERF** là một ứng dụng web tiên tiến được xây dựng trên nền tảng **Streamlit**, kết hợp sức mạnh của **Machine Learning (Học máy)** và **Reservoir Engineering (Kỹ thuật vỉa)** để tối ưu hóa việc đề xuất khoảng bắn mở vỉa, khớp đường cong suy giảm sản lượng (DCA), phân bổ lưu lượng dòng sản phẩm bằng dữ liệu PLT và phân tích hiệu quả kinh tế đầu tư cho các giếng khai thác dầu khí.

---

## 🚀 Tính năng nổi bật & Các phân hệ cốt lõi

Ứng dụng được thiết kế theo quy trình làm việc khép kín, chuẩn hóa từ Phân tích kỹ thuật (Technical) đến Đánh giá kinh tế (Economics):

### 1. 📁 Upload Dữ Liệu (Data Upload)
- Hỗ trợ tải lên dữ liệu giếng khoan (định dạng `.csv`) chứa các thông số địa vật lý giếng khoan (Log) như: Độ sâu (Depth), Độ rỗng (Porosity), Độ bão hòa nước (Sw), Thể tích sét (Vshale), Trạng thái bắn cũ (Is_Perforated)...
- Tự động kiểm tra chất lượng dữ liệu (Data Validation), chuẩn hóa cấu trúc và xử lý dữ liệu khuyết thiếu.

### 2. 📊 Log Visualizer (Trực quan hóa Log giếng)
- Trực quan hóa các đường log địa vật lý tương tác đa chiều bằng thư viện **Plotly**.
- Hiển thị song song 4 track log quan trọng: **Porosity**, **Sw**, **Vshale** và **Netpay**.
- Track **Netpay** được tô màu xanh lá mờ nổi bật (`rgba(26, 127, 55, 0.2)`) giúp kỹ sư dễ dàng định vị các vỉa chứa dầu tiềm năng cao nhất.

### 3. 🧠 ML Advisor (Đề xuất khoảng bắn thông minh)
- Tích hợp mô hình học máy (XGBoost, Random Forest) để nhận diện và phân loại tiềm năng các tầng chứa (Phân loại: `BEST`, `GOOD`, `MEDIUM`, `POOR`).
- **Thuật toán lọc và gộp khoảng thông minh**:
  - **Lọc sét nghiêm ngặt**: Loại bỏ hoàn toàn các điểm có thể tích sét cao (`Vshale >= 0.4`).
  - **Lọc nước triệt để**: Loại bỏ toàn bộ các khoảng có độ bão hòa nước cao (`Sw > 0.6`) để tránh bắn nhầm vào tầng ngập nước.
  - **Chặn gộp qua ranh giới sét/nước**: Chỉ gộp các điểm tiềm năng cách nhau `<= 2.0m` thành một khoảng bắn gộp lớn nếu ở giữa không bị ngăn cách bởi bất kỳ điểm sét hoặc điểm ngập nước nào.
  - **Lan truyền nhãn tối ưu**: Khoảng bắn gộp tự động kế thừa nhãn chất lượng cao nhất (`BEST` > `GOOD` > `MEDIUM`) xuất hiện trong nhóm.

### 4. 💧 Dự Báo Lưu Lượng (Production Prediction)
- Huấn luyện mô hình hồi quy nâng cao dự báo lưu lượng khai thác dầu ban đầu ($Q_o$ - BOPD) cho các khoảng bắn mở vỉa đề xuất mới dựa trên các thuộc tính địa vật lý trung bình của khoảng đó.

### 5. 📉 Suy Giảm & PLT Matching (DCA & Khớp PLT)
- **Khớp đường cong suy giảm (DCA)**: Sử dụng mô hình suy giảm sản lượng Arps (Hyperbolic/Exponential) để khớp dữ liệu lịch sử khai thác toàn giếng.
- **Phân bổ lưu lượng tầng vỉa**: Phân bổ lưu lượng tổng của giếng xuống từng khoảng bắn lịch sử dựa trên dữ liệu đo PLT thực tế hoặc phân bổ theo tích số độ thấm - độ dày (thuyết $KH$).
- **Đồng bộ hóa dữ liệu mẫu**: Chức năng *"Generate Sample Data"* thông minh tự động quét độ sâu Top-Base của các khoảng bắn cũ trong tệp tin log của giếng hiện tại để tạo dữ liệu PLT mẫu đồng bộ tuyệt đối.
- **Tính toán hệ số suy giảm riêng**: Xác định tốc độ suy giảm sản lượng năm ($D_{annual}$) riêng biệt cho từng tầng vỉa để tích hợp ngược lại hiệu chỉnh dự báo dài hạn.

### 6. 💰 Phân Tích Kinh Tế (Economic Analysis)
- Đánh giá hiệu quả tài chính cho các khoảng mở vỉa đề xuất dựa trên các thông số kinh tế linh hoạt: Giá dầu dự báo ($/bbl), Tỷ lệ chiết khấu (%), CAPEX cố định mỗi lần bắn, CAPEX biến đổi theo chiều dài súng bắn.
- Tính toán và xếp hạng ưu tiên đầu tư dựa trên chỉ số **NPV 3 năm** và **Thời gian hoàn vốn (Payback Period)** của các khoảng bắn tiềm năng tốt nhất (`BEST`).

---

## 🛠️ Stack công nghệ sử dụng

- **Môi trường**: Python 3.10+
- **Giao diện**: Streamlit
- **Xử lý dữ liệu**: Pandas, NumPy
- **Machine Learning & Tính toán**: Scikit-Learn, SciPy (curve_fit)
- **Trực quan hóa**: Plotly Express & Plotly Graph Objects

---

## 💻 Hướng dẫn cài đặt và vận hành

### 1. Sao chép Repository
```bash
git clone https://github.com/lmvu103/VPERF.git
cd VPERF
```

### 2. Thiết lập môi trường ảo
**Trên Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Trên Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài đặt các thư viện phụ trợ
```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng Streamlit
```bash
streamlit run streamlit_app.py
```
Sau khi chạy lệnh, truy cập trình duyệt theo địa chỉ mặc định: [http://localhost:8501](http://localhost:8501)

---

## 📂 Cấu trúc dự án

```text
VPERF/
├── .streamlit/
│   └── config.toml           # Cấu hình giao diện Streamlit
├── app_pages/
│   ├── 1_data_upload.py       # Phân hệ tải lên dữ liệu
│   ├── 2_log_viewer.py        # Phân hệ xem Log tương tác
│   ├── 3_ml_advisor.py        # Phân hệ đề xuất ML Perforation
│   ├── 4_production_prediction.py # Phân hệ dự báo lưu lượng
│   ├── 5_economics.py         # Phân hệ phân tích kinh tế đầu tư
│   └── 6_decline_analysis.py  # Phân hệ DCA & PLT Matching
├── utils/
│   ├── economics.py           # Tính toán tài chính kinh tế
│   ├── plots.py               # Thư viện vẽ log & biểu đồ sản lượng
│   └── production_analysis.py # Thư viện DCA & Phân bổ lưu lượng
├── streamlit_app.py           # Tệp điều hướng chính của ứng dụng
├── requirements.txt           # Danh sách thư viện phụ thuộc
└── README.md                  # Hướng dẫn sử dụng dự án
```

---
*Phát triển bởi đội ngũ kỹ sư công nghệ dầu khí và học máy chuyên nghiệp.*
