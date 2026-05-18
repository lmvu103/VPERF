import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor

# --- DANH SÁCH FEATURES MỞ RỘNG ---
EXTENDED_FEATURES = [
    'Porosity', 'Sw', 'Permeability', 'Vshale', 
    'Distance_to_OWC', 'Reservoir_Pressure', 'TVD_Depth'
]

# --- DANH SÁCH FEATURES CHO PRODUCTION ---
PRODUCTION_FEATURES = ['Porosity', 'Sw', 'Permeability', 'Vshale', 'Distance_to_OWC', 'Reservoir_Pressure']


def train_and_predict(df):
    """Mô hình dự đoán các khoảng bắn tiềm năng cơ bản."""
    features = ['Porosity', 'Sw', 'Permeability', 'Vshale']
    # Huấn luyện trên các khoảng đã bắn, đảm bảo không có NaN trong features và Production_Class
    train_df = df[df['Is_Perforated'] == True].dropna(subset=features + ['Production_Class'])
    
    if len(train_df) > 5:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(train_df[features], train_df['Production_Class'])
        
        # Dự báo cho toàn bộ các khoảng chưa bắn
        unperf_mask = (df['Is_Perforated'] == False)
        # Chỉ dự báo nếu có dữ liệu chưa bắn và không có NaN trong features
        predict_mask = unperf_mask & df[features].notna().all(axis=1)
        
        if predict_mask.any():
            df.loc[predict_mask, 'Predicted_Class'] = model.predict(df.loc[predict_mask, features])
            
            # Lấy xác suất
            probs = model.predict_proba(df.loc[predict_mask, features])
            df.loc[predict_mask, 'Confidence'] = np.max(probs, axis=1)
    return df


def train_advanced_model(df):
    """Huấn luyện mô hình với bộ tính năng mở rộng bằng Gradient Boosting."""
    # Tạo bản sao tránh side-effect
    df = df.copy()
    
    # Tự động tính toán Permeability từ Porosity và Sw nếu cột này bị Null hoàn toàn hoặc phần lớn
    if 'Permeability' in df.columns and (df['Permeability'].isna().all() or df['Permeability'].isna().sum() > len(df) * 0.9):
        df['Permeability'] = 10 ** (3 * df['Porosity']) * (1 - df['Sw']) ** 2
        df['Permeability'] = df['Permeability'].clip(0.01, 5000.0)

    # Tự động giả lập khoảng cách tới OWC nếu bị khuyết
    if 'Distance_to_OWC' in df.columns and df['Distance_to_OWC'].isna().all():
        df['Distance_to_OWC'] = np.abs(df['Depth'] - 3150.0)

    # Tự động giả lập áp suất vỉa theo gradient thủy tĩnh
    if 'Reservoir_Pressure' in df.columns and df['Reservoir_Pressure'].isna().all():
        df['Reservoir_Pressure'] = 0.1 * df['Depth']

    # TVD Depth mặc định bằng Depth nếu bị Null
    if 'TVD_Depth' in df.columns and df['TVD_Depth'].isna().all():
        df['TVD_Depth'] = df['Depth']

    # Lọc dữ liệu lịch sử (đã bắn và có nhãn kết quả), bỏ qua các feature bị Null hoàn toàn
    available_features = [f for f in EXTENDED_FEATURES if f in df.columns and not df[f].isna().all()]
    if not available_features:
        return None, None
        
    train_df = df[df['Is_Perforated'] == True].dropna(subset=available_features + ['Production_Class'])
    
    if len(train_df) < 15: # Tăng ngưỡng dữ liệu tối thiểu
        return None, None
        
    X = train_df[available_features]
    y = train_df['Production_Class']
    
    # Sử dụng Gradient Boosting để học các mối quan hệ phi tuyến phức tạp
    model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X, y)
    
    return model, available_features


def train_production_model(df):
    """Huấn luyện mô hình dự báo lưu lượng Q_o."""
    df = df.copy()
    
    # Tự động tính toán Permeability từ Porosity và Sw nếu cột này bị Null hoàn toàn hoặc phần lớn
    if 'Permeability' in df.columns and (df['Permeability'].isna().all() or df['Permeability'].isna().sum() > len(df) * 0.9):
        df['Permeability'] = 10 ** (3 * df['Porosity']) * (1 - df['Sw']) ** 2
        df['Permeability'] = df['Permeability'].clip(0.01, 5000.0)

    # Tự động giả lập khoảng cách tới OWC nếu bị khuyết
    if 'Distance_to_OWC' in df.columns and df['Distance_to_OWC'].isna().all():
        df['Distance_to_OWC'] = np.abs(df['Depth'] - 3150.0)

    # Tự động giả lập áp suất vỉa theo gradient thủy tĩnh
    if 'Reservoir_Pressure' in df.columns and df['Reservoir_Pressure'].isna().all():
        df['Reservoir_Pressure'] = 0.1 * df['Depth']

    # Kiểm tra các feature cần thiết có trong DataFrame không
    available_features = [f for f in PRODUCTION_FEATURES if f in df.columns and not df[f].isna().all()]
    if not available_features:
        return None, None

    # Lấy các khoảng đã bắn và CÓ dữ liệu lưu lượng thực tế (Initial_Rate)
    train_df = df[df['Is_Perforated'] == True].dropna(subset=available_features + ['Initial_Rate'])
    
    if len(train_df) < 10:
        return None, None
        
    X = train_df[available_features]
    y = train_df['Initial_Rate']
    
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)
    
    return model, available_features
