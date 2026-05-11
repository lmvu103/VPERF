import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def plot_well_logs(df, wells, depth_range, selected_logs=None, log_scales=None, show_proposal=False):
    """Vẽ biểu đồ Log với track độ sâu riêng biệt, hiển thị thực tế vs đề xuất ML kèm dự báo Qo"""
    if selected_logs is None:
        selected_logs = ['Porosity', 'Sw']
    if log_scales is None:
        log_scales = {}
        
    n_wells = len(wells)
    n_logs = len(selected_logs)
    
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
        'Reservoir_Pressure': '#e34c26'
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
                fig.add_trace(
                    go.Scatter(x=w_data[log], y=w_data['Depth'], name=log, 
                               legendgroup=log, showlegend=(i == 0),
                               line=dict(color=line_color),
                               hovertemplate=f"Depth: %{{y}}m<br>{log}: %{{x}}<extra></extra>"),
                    row=1, col=curr_col
                )
                well_s = log_scales.get(well, {})
                if log in well_s:
                    fig.update_xaxes(range=well_s[log], row=1, col=curr_col)
                
        # 3. Actual Perfs Track
        actual_perf_col = start_col + 1 + n_logs
        if 'Is_Perforated' in w_data.columns:
            perf_zones = w_data[(w_data['Is_Perforated'] == True) & 
                                (w_data['Production_Class'].isin(perf_colors.keys()))]
            if not perf_zones.empty:
                for p_class, color in perf_colors.items():
                    class_data = perf_zones[perf_zones['Production_Class'] == p_class]
                    if not class_data.empty:
                        rates = [f" {r:.0f}" if pd.notna(r) else "" for r in class_data['Initial_Rate']]
                        fig.add_trace(
                            go.Scatter(x=[1]*len(class_data), y=class_data['Depth'], 
                                       mode='markers+text', name=f"Actual: {p_class}",
                                       legendgroup=p_class, showlegend=(i==0),
                                       marker=dict(symbol='square', color=color, size=9),
                                       text=rates,
                                       textposition="middle right",
                                       textfont=dict(color=color, size=9, family="Inter, sans serif"),
                                       hovertemplate="<b>Actual " + p_class + "</b><br>Depth: %{y}m<extra></extra>"),
                            row=1, col=actual_perf_col
                        )
                fig.update_xaxes(range=[0, 3], showticklabels=False, row=1, col=actual_perf_col)

        # 4. Proposed Perfs Track (ML Advisor)
        if show_proposal:
            proposed_perf_col = actual_perf_col + 1
            if 'Predicted_Class' in w_data.columns:
                prop_zones = w_data[w_data['Predicted_Class'] == 'BEST']
                if not prop_zones.empty:
                    # Hiển thị dự báo Qo cho các khoảng đề xuất nếu có
                    p_rates = [f" {r:.0f}" if (pd.notna(r) and r > 0) else "" for r in prop_zones.get('Predicted_Qo', [np.nan]*len(prop_zones))]
                    
                    fig.add_trace(
                        go.Scatter(x=[1]*len(prop_zones), y=prop_zones['Depth'], 
                                   mode='markers+text', name="Đề xuất BEST",
                                   legendgroup="Proposed", showlegend=(i==0),
                                   marker=dict(symbol='star', color='#1a7f37', size=11, line=dict(color='white', width=1)),
                                   text=p_rates,
                                   textposition="middle right",
                                   textfont=dict(color='#1a7f37', size=10, family="Inter, sans serif"),
                                   hovertemplate="<b>Đề xuất BEST</b><br>Depth: %{y}m<br>Dự báo Qo: %{text} BOPD<extra></extra>"),
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
