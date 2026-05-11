import numpy as np

def calculate_economics(q_start, decline_rate, thickness, oil_price=75, discount_rate=0.12, perf_cost_base=50000, perf_cost_per_m=2000):
    """Tính toán NPV và Payback (thời gian hoàn vốn)."""
    # Ước tính CAPEX
    capex = perf_cost_base + (perf_cost_per_m * thickness)
    
    # Giả định dòng tiền trong 3 năm (36 tháng)
    months = np.arange(1, 37)
    q_monthly = q_start * np.exp(-decline_rate * months / 12)
    revenue = q_monthly * 30.5 * oil_price * 0.7  # 0.7 là trừ thuế và opex
    
    # Tính NPV
    pv = revenue / (1 + discount_rate/12)**months
    npv = np.sum(pv) - capex
    
    # Tính Payback
    cum_pv = np.cumsum(pv)
    payback_months = np.searchsorted(cum_pv, capex) + 1
    
    # Nếu không hoàn vốn được trong 36 tháng
    if payback_months > 36:
        payback_months = float('inf')
        
    return round(npv, 2), round(payback_months, 1)
