import streamlit as st

def apply_finviz_style():
    """
    Applies the custom CSS for the Finviz-style dashboard.
    """
    st.markdown("""
    <style>
        /* Global Styles */
        .main {
            background-color: #0E1117;
        }
        
        /* Finviz Style Row */
        .finviz-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
            padding: 4px 0;
            font-size: 0.8rem;
        }
        .finviz-label {
            color: #aaa;
            font-weight: 500;
            text-align: left;
        }
        .finviz-value {
            font-weight: 700;
            text-align: right;
            color: #eee;
        }
        .fv-green { color: #00AA00 !important; }
        .fv-red { color: #AA0000 !important; }
        
        /* Card Style for Overview */
        .metric-card {
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            margin: 5px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            text-align: center;
        }
        .metric-card-label {
            font-size: 0.9rem;
            color: #aaa;
            margin-bottom: 5px;
        }
        .metric-card-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: baseline;
            gap: 8px;
        }
        .metric-delta {
            font-size: 0.8rem;
        }
        .delta-up { color: #4CAF50; }
        .delta-down { color: #FF5252; }
        
    </style>
    """, unsafe_allow_html=True)

def create_metric_card(label, value, delta=None, delta_pct=None, prefix="", suffix=""):
    """
    Generates HTML for a card-style metric.
    """
    delta_html = ""
    if delta is not None:
        try:
            delta_val = float(delta)
            pct_str = ""
            if delta_pct is not None:
                pct_str = f" ({delta_pct:+.2f}%)"
                
            if delta_val > 0:
                delta_html = f'<div class="metric-delta delta-up">▲ {delta_val:.2f}{pct_str}</div>'
            elif delta_val < 0:
                delta_html = f'<div class="metric-delta delta-down">▼ {abs(delta_val):.2f}{pct_str}</div>'
            elif delta_val == 0:
                 delta_html = '<div class="metric-delta" style="color: gray;">- 0.00 (0.00%)</div>'
        except:
             delta_html = "" 
            
    html_content = f"""
    <div class="metric-card">
        <div class="metric-card-label">{label}</div>
        <div class="metric-card-value">{prefix}{value}{suffix}{delta_html}</div>
    </div>
    """
    return html_content

def create_finviz_row(label, value, is_good=False, is_bad=False, suffix="", prefix=""):
    """
    Generates HTML for a single row in the metrics dashboard.
    """
    color_class = ""
    if is_good:
        color_class = "fv-green"
    elif is_bad:
        color_class = "fv-red"
    
    display_value = f"{prefix}{value}{suffix}" if value is not None and value != "N/A" else "-"
    
    html_content = f"""
    <div class="finviz-row">
        <div class="finviz-label">{label}</div>
        <div class="finviz-value {color_class}">{display_value}</div>
    </div>
    """
    return html_content
