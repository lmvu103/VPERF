import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def group_intervals(df, class_col, rate_col, threshold=1.0):
    """Nhóm các điểm liên tiếp thành các khoảng (intervals)"""
    if df.empty:
        return []
    
    df = df.sort_values('Depth')
    intervals = []
    
    current_interval = {
        'top': df.iloc[0]['Depth'],
        'bottom': df.iloc[0]['Depth'],
        'class': df.iloc[0][class_col],
        'rates': [df.iloc[0][rate_col]] if rate_col in df.columns else []
    }
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        # Nếu cùng class và khoảng cách độ sâu nhỏ (liên tiếp)
        if row[class_col] == current_interval['class'] and (row['Depth'] - current_interval['bottom']) <= threshold:
            current_interval['bottom'] = row['Depth']
            if rate_col in df.columns and pd.notna(row[rate_col]):
                current_interval['rates'].append(row[rate_col])
        else:
            # Lưu khoảng cũ
            avg_rate = np.mean(current_interval['rates']) if current_interval['rates'] else np.nan
            intervals.append({
                'top': current_interval['top'],
                'bottom': current_interval['bottom'],
                'class': current_interval['class'],
                'rate': avg_rate
            })
            # Bắt đầu khoảng mới
            current_interval = {
                'top': row['Depth'],
                'bottom': row['Depth'],
                'class': row[class_col],
                'rates': [row[rate_col]] if rate_col in df.columns else []
            }
            
    # Thêm khoảng cuối cùng
    avg_rate = np.mean(current_interval['rates']) if current_interval['rates'] else np.nan
    intervals.append({
        'top': current_interval['top'],
        'bottom': current_interval['bottom'],
        'class': current_interval['class'],
        'rate': avg_rate
    })
    
    return intervals

def plot_well_logs(df, wells, depth_range, selected_logs=None, log_scales=None, show_proposal=False):
    """Vẽ biểu đồ Log với track độ sâu riêng biệt, hiển thị thực tế vs đề xuất ML kèm dự báo Qo"""
    if selected_logs is None:
        selected_logs = ['Porosity', 'Sw']
    if log_scales is None:
        log_scales = {}
        
    n_wells = len(wells)
    n_logs = len(selected_logs)
    
    # Số lượng track: Depth + Logs + Actual (+ Proposed)
    n_tracks_per_well = 1 + n_logs + 1 
    if show_proposal:
        n_tracks_per_well += 1
        
    total_cols = n_wells * n_tracks_per_well
    
    column_titles = []
    for w in wells:
        column_titles.append("D")
        for log in selected_logs:
            column_titles.append(log[:4])
        column_titles.append("Actual")
        if show_proposal:
            column_titles.append("Proposed")

    fig = make_subplots(
        rows=1, cols=total_cols, 
        shared_yaxes=False, 
        column_titles=column_titles,
        horizontal_spacing=0.03
    )

    color_map = {
        'Porosity': '#0969da',
        'Sw': '#cf222e',
        'Permeability': '#8250df',
        'Vshale': '#bf8700',
        'Gamma_Ray': '#1a7f37',
        'GR': '#1a7f37',
        'Reservoir_Pressure': '#e34c26',
        'Netpay': '#1a7f37'
    }

    perf_colors = {
        'BEST': '#1a7f37',
        'GOOD': '#0969da',
        'MEDIUM': '#bf8700',
        'WORST': '#cf222e'
    }

    for i, well in enumerate(wells):
        w_data = df[(df['Well_Name'] == well) & 
                    (df['Depth'] >= depth_range[0]) & 
                    (df['Depth'] <= depth_range[1])]
        
        start_col = i * n_tracks_per_well + 1
        
        # 1. Depth Track
        depth_ticks = np.arange(np.floor(w_data['Depth'].min()/10)*10, 
                                np.ceil(w_data['Depth'].max()/10)*10 + 10, 10)
        fig.add_trace(
            go.Scatter(x=[0.5] * len(depth_ticks), y=depth_ticks, mode="text",
                       text=[str(int(d)) for d in depth_ticks],
                       textfont=dict(size=9, color="#57606a"), showlegend=False, hoverinfo="skip"),
            row=1, col=start_col
        )
        fig.update_xaxes(range=[0, 1], showticklabels=False, showgrid=False, row=1, col=start_col)

        # 2. Log Tracks
        for j, log in enumerate(selected_logs):
            curr_col = start_col + 1 + j
            if log in w_data.columns:
                line_color = color_map.get(log, '#57606a')
                fill_mode = 'tozerox' if log == 'Netpay' else None
                fill_color = 'rgba(26, 127, 55, 0.2)' if log == 'Netpay' else None
                
                fig.add_trace(
                    go.Scatter(x=w_data[log], y=w_data['Depth'], name=log, 
                               legendgroup=log, showlegend=(i == 0),
                               line=dict(color=line_color),
                               fill=fill_mode,
                               fillcolor=fill_color,
                               hovertemplate=f"Depth: %{{y}}m<br>{log}: %{{x}}<extra></extra>"),
                    row=1, col=curr_col
                )
                well_s = log_scales.get(well, {})
                if log in well_s:
                    fig.update_xaxes(range=well_s[log], row=1, col=curr_col)
                
        # 3. Actual Perfs Track (Đã được nhóm)
        actual_perf_col = start_col + 1 + n_logs
        if 'Is_Perforated' in w_data.columns:
            perf_df = w_data[w_data['Is_Perforated'] == True]
            intervals = group_intervals(perf_df, 'Production_Class', 'Initial_Rate', threshold=1.2)
            
            for interval in intervals:
                p_class = interval['class']
                color = perf_colors.get(p_class, '#57606a')
                mid_depth = (interval['top'] + interval['bottom']) / 2
                
                # Vẽ dải màu cho khoảng bắn
                fig.add_trace(
                    go.Scatter(
                        x=[1, 1], y=[interval['top'], interval['bottom']],
                        mode='lines',
                        line=dict(color=color, width=20), # Tăng độ rộng một chút để chứa chữ
                        name=f"Actual: {p_class}",
                        legendgroup=p_class,
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=1, col=actual_perf_col
                )
                
                # Hiển thị lưu lượng tại trung điểm - Nằm giữa dải màu
                rate_text = f"{interval['rate']:.0f}" if pd.notna(interval['rate']) else ""
                if rate_text:
                    fig.add_trace(
                        go.Scatter(
                            x=[1], y=[mid_depth],
                            mode='text',
                            text=[rate_text],
                            textposition="middle center",
                            textfont=dict(color='white', size=10, weight='bold'),
                            showlegend=False,
                            hovertemplate=f"<b>Actual {p_class}</b><br>Top: {interval['top']:.1f}m<br>Base: {interval['bottom']:.1f}m<br>Qo: {rate_text} BOPD<extra></extra>"
                        ),
                        row=1, col=actual_perf_col
                    )

            # Thêm legend giả
            if i == 0:
                for p_class, color in perf_colors.items():
                    fig.add_trace(
                        go.Scatter(x=[None], y=[None], mode='markers',
                                   marker=dict(symbol='square', color=color, size=10),
                                   name=f"Actual: {p_class}", legendgroup=p_class),
                        row=1, col=actual_perf_col
                    )

            fig.update_xaxes(range=[0, 2], showticklabels=False, row=1, col=actual_perf_col)

        # 4. Proposed Perfs Track (ML Advisor) - Đã được nhóm theo class
        if show_proposal:
            proposed_perf_col = actual_perf_col + 1
            if 'Predicted_Class' in w_data.columns:
                # Không lọc cứng 'BEST' nữa mà lấy tất cả các dòng có dự báo
                prop_df = w_data[w_data['Predicted_Class'].isin(perf_colors.keys())]
                prop_intervals = group_intervals(prop_df, 'Predicted_Class', 'Predicted_Qo', threshold=2.0)
                
                for interval in prop_intervals:
                    p_class = interval['class']
                    mid_depth = (interval['top'] + interval['bottom']) / 2
                    color = perf_colors.get(p_class, '#1a7f37') 
                    
                    # Vẽ dải màu cho khoảng đề xuất (nét đứt để phân biệt với Actual)
                    fig.add_trace(
                        go.Scatter(
                            x=[1, 1], y=[interval['top'], interval['bottom']],
                            mode='lines',
                            line=dict(color=color, width=20, dash='dot'),
                            name=f"Proposed: {p_class}",
                            legendgroup=f"Proposed_{p_class}",
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        row=1, col=proposed_perf_col
                    )
                    
                    rate_text = f"{interval['rate']:.0f}" if pd.notna(interval['rate']) else ""
                    if rate_text:
                        fig.add_trace(
                            go.Scatter(
                                x=[1], y=[mid_depth],
                                mode='text',
                                text=[rate_text],
                                textposition="middle center",
                                textfont=dict(color='white', size=10, weight='bold'),
                                showlegend=False,
                                hovertemplate=f"<b>Proposed {p_class}</b><br>Top: {interval['top']:.1f}m<br>Base: {interval['bottom']:.1f}m<br>Dự báo Qo: {rate_text} BOPD<extra></extra>"
                            ),
                            row=1, col=proposed_perf_col
                        )

                # Thêm legend cho Proposed (chỉ lần đầu)
                if i == 0:
                    for p_class, color in perf_colors.items():
                        fig.add_trace(
                            go.Scatter(x=[None], y=[None], mode='markers',
                                       marker=dict(symbol='square', color=color, size=10, line=dict(dash='dot', width=1)),
                                       name=f"Proposed: {p_class}", legendgroup=f"Proposed_{p_class}"),
                            row=1, col=proposed_perf_col
                        )
                fig.update_xaxes(range=[0, 4], showticklabels=False, row=1, col=proposed_perf_col)

        # Cấu hình trục Y
        well_y_id = f"y{start_col}" if start_col > 1 else "y"
        for track_offset in range(n_tracks_per_well):
            curr_col_idx = start_col + track_offset
            fig.update_yaxes(
                matches=well_y_id, 
                autorange="reversed", 
                showticklabels=(track_offset == 0), 
                title_text="Depth (m)" if (i==0 and track_offset==0) else "",
                row=1, col=curr_col_idx
            )

    # Well Name Annotations
    for i, well in enumerate(wells):
        x_pos = (i * n_tracks_per_well + n_tracks_per_well/2 - 0.5) / (total_cols - 1) if total_cols > 1 else 0.5
        fig.add_annotation(
            xref="paper", yref="paper", x=x_pos, y=1.08,
            text=f"<b>WELL: {well}</b>", showarrow=False,
            font=dict(size=13, color="#1f2328"), align="center"
        )

    fig.update_layout(
        height=800, 
        width=max(1000, n_wells * 350),
        template="plotly_white", 
        hovermode='y unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="center", x=0.5),
        margin=dict(t=150, l=50, r=50)
    )
    
    return fig
