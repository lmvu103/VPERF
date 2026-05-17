import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def exponential_decline(t, qi, d):
    """Mô hình suy giảm hàm mũ: q = qi * exp(-d*t)"""
    return qi * np.exp(-d * t)

def hyperbolic_decline(t, qi, di, b):
    """Mô hình suy giảm Hyperbol: q = qi / (1 + b*di*t)**(1/b)"""
    # Tránh lỗi chia cho 0 hoặc số mũ âm không hợp lệ
    return qi / np.maximum((1 + b * di * t), 1e-6)**(1/b)

def fit_decline_curve(t, q, model_type='hyperbolic'):
    """
    Khớp dữ liệu lịch sử khai thác để tìm thông số suy giảm.
    t: thời gian (tháng hoặc ngày từ điểm bắt đầu)
    q: lưu lượng
    """
    if len(t) < 3:
        return None, None
        
    try:
        if model_type == 'exponential':
            # q = qi * exp(-d*t)
            popt, _ = curve_fit(exponential_decline, t, q, p0=[q[0], 0.01], bounds=(0, [np.inf, 1]))
            return popt, exponential_decline
        else:
            # Hyperbolic: p0=[qi, di, b]
            popt, _ = curve_fit(hyperbolic_decline, t, q, p0=[q[0], 0.01, 0.5], bounds=(0, [np.inf, 1, 1]))
            return popt, hyperbolic_decline
    except Exception as e:
        print(f"Error fitting decline curve: {e}")
        return None, None

def full_well_allocation(well_history_df, plt_df, all_perf_intervals):
    """
    Phân bổ lưu lượng tổng cho TẤT CẢ các khoảng bắn xuyên suốt lịch sử.
    well_history_df: [Date, Oil_Rate]
    plt_df: [Well_Name, Date, Top, Base, Contribution_Pct]
    all_perf_intervals: [Top, Base, Permeability, Thickness] (tất cả các khoảng đã bắn)
    """
    well_history_df['Date'] = pd.to_datetime(well_history_df['Date'])
    if not plt_df.empty:
        plt_df['Date'] = pd.to_datetime(plt_df['Date'])
    
    # Tính KH (Permeability * Thickness) cho từng tầng để phân bổ khi không có PLT
    for interval in all_perf_intervals:
        interval['KH'] = interval.get('Permeability', 1.0) * interval.get('Thickness', 0.1)
    
    total_kh = sum(inter['KH'] for inter in all_perf_intervals)
    
    allocation_results = []
    
    for _, prod_row in well_history_df.iterrows():
        prod_date = prod_row['Date']
        total_rate = prod_row['Oil_Rate']
        
        # Kiểm tra xem ngày này có đo PLT không (hoặc gần ngày đo PLT trong vòng 30 ngày)
        current_plt = pd.DataFrame()
        if not plt_df.empty:
            time_diff = (plt_df['Date'] - prod_date).abs().dt.days
            current_plt = plt_df[time_diff <= 30] # Ngưỡng 1 tháng
        
        if not current_plt.empty:
            # --- TRƯỜNG HỢP CÓ PLT: Sử dụng tỷ lệ từ PLT ---
            # Lưu ý: PLT có thể không bao phủ hết tất cả các tầng. 
            # Chúng ta sẽ ưu tiên PLT, phần còn lại phân bổ theo KH cho các tầng thiếu.
            plt_sum_pct = current_plt['Contribution_Pct'].sum()
            
            for interval in all_perf_intervals:
                layer_id = f"{interval['Top']}-{interval['Base']}"
                # Tìm xem tầng này có trong PLT không
                plt_match = current_plt[
                    (current_plt['Top'] >= interval['Top'] - 0.5) & 
                    (current_plt['Base'] <= interval['Base'] + 0.5)
                ]
                
                if not plt_match.empty:
                    pct = plt_match['Contribution_Pct'].values[0]
                else:
                    # Nếu không có trong PLT, phân bổ phần còn lại của 100% dựa trên tỷ lệ KH của các tầng thiếu
                    remaining_pct = max(0, 100 - plt_sum_pct)
                    other_intervals_kh = sum(inter['KH'] for inter in all_perf_intervals if inter not in current_plt.values) # Logic đơn giản hóa
                    # Để đơn giản: Nếu không có trong PLT thì coi như đóng góp cực thấp hoặc theo KH của phần còn lại
                    pct = (interval['KH'] / total_kh) * remaining_pct if total_kh > 0 else 0
                
                allocation_results.append({
                    'Date': prod_date,
                    'Top': interval['Top'],
                    'Base': interval['Base'],
                    'Total_Rate': total_rate,
                    'Allocated_Rate': total_rate * (pct / 100),
                    'Contribution_Pct': pct,
                    'Source': 'PLT'
                })
        else:
            # --- TRƯỜNG HỢP KHÔNG CÓ PLT: Phân bổ theo KH ---
            for interval in all_perf_intervals:
                pct = (interval['KH'] / total_kh) * 100 if total_kh > 0 else 0
                allocation_results.append({
                    'Date': prod_date,
                    'Top': interval['Top'],
                    'Base': interval['Base'],
                    'Total_Rate': total_rate,
                    'Allocated_Rate': total_rate * (pct / 100),
                    'Contribution_Pct': pct,
                    'Source': 'KH_Logic'
                })
                
    return pd.DataFrame(allocation_results)

def calculate_layer_decline(allocated_df):
    """
    Tính toán hệ số suy giảm riêng cho từng tầng dựa trên chuỗi số liệu PLT.
    allocated_df: Kết quả từ match_with_plt, group theo khoảng (Top-Base)
    """
    layer_stats = []
    # Nhóm theo khoảng độ sâu
    allocated_df['Layer_ID'] = allocated_df['Top'].astype(str) + "-" + allocated_df['Base'].astype(str)
    
    for layer in allocated_df['Layer_ID'].unique():
        layer_df = allocated_df[allocated_df['Layer_ID'] == layer].sort_values('Date')
        if len(layer_df) >= 2:
            # Tính suy giảm đơn giản (exponential) giữa điểm đầu và cuối
            t_diff = (layer_df['Date'].iloc[-1] - layer_df['Date'].iloc[0]).days / 365.25 # năm
            if t_diff > 0:
                q_start = layer_df['Allocated_Rate'].iloc[0]
                q_end = layer_df['Allocated_Rate'].iloc[-1]
                # q_end = q_start * exp(-d*t) => d = -ln(q_end/q_start)/t
                if q_start > 0 and q_end > 0:
                    d = -np.log(q_end / q_start) / t_diff
                    layer_stats.append({
                        'Layer_ID': layer,
                        'Top': layer_df['Top'].iloc[0],
                        'Base': layer_df['Base'].iloc[0],
                        'Decline_Rate_Annual': d,
                        'Current_Rate': q_end,
                        'Last_Measured_Date': layer_df['Date'].iloc[-1]
                    })
                    
    return pd.DataFrame(layer_stats)
