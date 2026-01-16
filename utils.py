import pandas as pd
import plotly.graph_objects as go
from textblob import TextBlob
import numpy as np



def calculate_technical_indicators(df):
    """
    RSI(14)와 MACD(12, 26, 9)를 계산하여 데이터프레임에 추가합니다.
    """
    try:
        df = df.copy()
        
        # RSI Calculation
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD Calculation
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
        
        return df
    except Exception:
        return df

def format_currency(val):
    """
    Converts a number to a shortened currency string (e.g. 1.5B, 300M).
    Used in charts and DCF table.
    """
    if pd.isna(val):
        return ""
    val_abs = abs(val)
    if val_abs >= 1_000_000_000:
        return f'{val/1_000_000_000:.2f}B'
    elif val_abs >= 1_000_000:
        return f'{val/1_000_000:.2f}M'
    elif val_abs >= 1_000:
        return f'{val/1_000:.2f}K'
    else:
        return f'{val:.2f}'

# Metric helpers
def fmt(n, format_str="{:.2f}", suffix="", scale=1):
    if n is None: return "N/A"
    return f"{format_str.format(n*scale)}{suffix}"

def fmt_bn(n):
    if n is None: return "-"
    if n >= 1e12: return f"{n/1e12:.2f}T"
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.2f}M"
    return f"{n:.2f}"



def create_sparkline_chart(data, color):
    """
    Creates a minimalist Sparkline chart for the index cards.
    """
    fig = go.Figure()
    
    # Fill color (semi-transparent)
    fill_color = 'rgba(0, 255, 0, 0.1)' if color == '#00FF00' else 'rgba(255, 0, 0, 0.1)'
    if color == 'green': fill_color = 'rgba(46, 204, 113, 0.2)'
    if color == 'red': fill_color = 'rgba(231, 76, 60, 0.2)'
    
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['Close'], 
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=fill_color
    ))
    
    # Minimalist Layout
    fig.update_layout(
        showlegend=False,
        margin=dict(t=5, l=0, r=0, b=0),
        height=60, # Small height
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_fear_greed_gauge(score):
    """
    Creates a Horizontal Linear Gauge (Bullet Chart) for better readability.
    """
    if score is None:
        return None
        
    score = float(score)
    
    # Determine Label
    if score < 25: 
        label = "EXTREME FEAR"
        label_color = "#ef5350"
    elif score < 45: 
        label = "FEAR"
        label_color = "#ffa726"
    elif score <= 55: 
        label = "NEUTRAL"
        label_color = "#ffca28"
    elif score < 75: 
        label = "GREED"
        label_color = "#9ccc65"
    else: 
        label = "EXTREME GREED"
        label_color = "#66bb6a"
        



    fig = go.Figure(go.Indicator(
        mode = "gauge", 
        value = score,
        domain = {'x': [0.05, 0.95], 'y': [0.0, 0.3]}, 
        gauge = {
            'shape': "bullet",
            'axis': {
                'range': [0, 100], 
                'tickmode': 'array',
                'tickvals': [0, 25, 45, 55, 75, 100], # Exact boundaries
                'ticktext': ['0', '25', '45', '55', '75', '100'],
                'tickcolor': 'white',
                'tickfont': {'color': '#bbb', 'size': 14}, # Larger font
                'tickwidth': 1,
                'ticklen': 10
            },
            'bgcolor': "rgba(0,0,0,0)",
            'bar': {'color': "rgba(0,0,0,0)"}, 
            'steps': [
                {'range': [0, 25], 'color': '#b71c1c'},
                {'range': [25, 45], 'color': '#e64a19'},
                {'range': [45, 55], 'color': '#fbc02d'},
                {'range': [55, 75], 'color': '#7cb342'},
                {'range': [75, 100], 'color': '#2e7d32'}
            ],
            'threshold': {
                'line': {'color': "rgba(0,0,0,0)", 'width': 0}, 
                'thickness': 0,
                'value': score
            }
        }
    ))
    
    # Calculate Position for Arrow
    x_pos = 0.05 + (score / 100.0) * 0.90
    y_bar_top = 0.3 

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"},
        margin=dict(l=20, r=20, t=20, b=50), # Increased bottom margin for Tick Labels
        height=220, # Increased total height for spacing
        annotations=[
            # 1. Arrow Indicator
            dict(
                x=x_pos, y=y_bar_top,
                ax=0, ay=-30, 
                xref='paper', yref='paper', 
                axref='pixel', ayref='pixel',
                text='', 
                showarrow=True,
                arrowhead=2, arrowsize=1, arrowwidth=3, arrowcolor='white'
            ),
            # 2. Combined Score & Label
            dict(
                x=0.5, y=0.9,  # Moved UP to create gap
                text=f"<span style='font-size:52px; font-weight:bold; color:white'>{int(score)}</span>   <span style='font-size:40px; font-weight:700; letter-spacing: 1px; color:{label_color}'>{label}</span>",
                showarrow=False, 
                xref='paper', yref='paper'
            )
        ]
    )
    
    return fig

def create_target_price_chart(current_price, low, mean, high, currency="$"):
    """
    Creates a Horizontal Chart comparing Current Price vs Analyst Targets using Annotations for layout control.
    """
    if not all([current_price, low, mean, high]):
        return None
        
    fig = go.Figure()
    
    # Fixed Y-axis value
    y_val = 1
    

    # 1. Analyst Range (Low to High) - Background Bar
    fig.add_trace(go.Scatter(
        x=[low, high],
        y=[y_val, y_val],
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.2)', width=30), # Thicker Bar
        hoverinfo='skip',
        showlegend=False
    ))
    
    # 2. Analyst Mean - Blue Dot
    fig.add_trace(go.Scatter(
        x=[mean],
        y=[y_val],
        mode='markers',
        marker=dict(size=24, color='#2962ff'), # Larger Dot
        hoverinfo='x',
        name="Analyst Mean"
    ))
    
    # 3. Low/High markers
    fig.add_trace(go.Scatter(
        x=[low, high],
        y=[y_val, y_val],
        mode='markers',
        marker=dict(size=12, color='white', symbol='line-ns-open'),
        hoverinfo='x',
        name="Range"
    ))

    # 4. Current Price - Red Marker
    color_curr = "#ff0000" 
    
    fig.add_trace(go.Scatter(
        x=[current_price],
        y=[y_val],
        mode='markers',
        marker=dict(size=26, color=color_curr, symbol='line-ns', line=dict(width=4, color=color_curr)),
        hoverinfo='x',
        name="Current Price"
    ))
    
    # Annotations to create spacing (Margin)
    annotations = [
        # Current Price (Above)
        dict(
            x=current_price, y=y_val,
            text=f"Current:<br>{currency}{current_price:,.2f}",
            showarrow=False,
            yshift=35, # Margin Up
            font=dict(color=color_curr, size=13)
        ),
        # Mean (Below)
        dict(
            x=mean, y=y_val,
            text=f"Mean:<br>{currency}{mean:,.2f}",
            showarrow=False,
            yshift=-35, # Margin Down
            font=dict(color='#2962ff', size=13)
        ),
        # Low (Below)
        dict(
            x=low, y=y_val,
            text=f"Low:<br>{currency}{low:,.2f}",
            showarrow=False,
            yshift=-35,
            font=dict(color='white', size=11)
        ),
        # High (Below)
        dict(
            x=high, y=y_val,
            text=f"High:<br>{currency}{high:,.2f}",
            showarrow=False,
            yshift=-35,
            font=dict(color='white', size=11)
        )
    ]
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"},
        xaxis=dict(showgrid=False, zeroline=False, visible=False, title=""), # Hidden Axis
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[0, 2]),
        margin=dict(l=20, r=20, t=50, b=50),
        height=180,
        showlegend=False,
        annotations=annotations
    )
    
    return fig
    return fig

def analyze_sentiment_from_news(news_list):
    """
    뉴스 헤드라인을 분석하여 평균 감성 점수(-1.0 ~ 1.0)를 반환합니다.
    TextBlob의 Polarity를 사용합니다.
    """
    if not news_list:
        return 0, 0, "Neutral"
        
    total_polarity = 0
    valid_count = 0
    
    for item in news_list:
        title = item.get('title', '')
        if title:
            # TextBlob sentiment: polarity (-1 to 1)
            analysis = TextBlob(title)
            total_polarity += analysis.sentiment.polarity
            valid_count += 1
            
    if valid_count == 0:
        return 0, 0, "Neutral"
        
    avg_polarity = total_polarity / valid_count
    
    # Scale to 0-100 for gauge
    # -1 => 0, 0 => 50, 1 => 100
    score = (avg_polarity + 1) * 50
    
    if score >= 60: rating = "Positive"
    elif score <= 40: rating = "Negative"
    else: rating = "Neutral"
    
    return avg_polarity, score, rating

def detect_candlestick_patterns(df):
    """
    DataFrame에 캔들스틱 패턴(Doji, Hammer, Engulfing 등)을 감지하여 
    'Pattern' 컬럼에 패턴 이름을 기록합니다.
    """
    df = df.copy()
    df['Pattern'] = None
    df['Pattern_Marker'] = None # 차트 표시용 값 (High or Low)
    
    # Vectorized check could be faster but iterating is simpler to read for patterns
    # Using iteration for clarity on logic (performance is okay for 1-5y daily data)
    
    for i in range(1, len(df)):
        open_p = df['Open'].iloc[i]
        close_p = df['Close'].iloc[i]
        high_p = df['High'].iloc[i]
        low_p = df['Low'].iloc[i]
        
        prev_open = df['Open'].iloc[i-1]
        prev_close = df['Close'].iloc[i-1]
        
        body = abs(close_p - open_p)
        total_range = high_p - low_p
        
        
        # 1. Doji (Removed)
        # if total_range > 0 and body <= (total_range * 0.1):
        #    df.at[df.index[i], 'Pattern'] = 'Doji'
        #    df.at[df.index[i], 'Pattern_Marker'] = high_p
        #    continue
            
        # 2. Hammer (하락세에서 아래 꼬리가 길고 몸통이 작음) - 여기서는 단순 형태만 체크
        lower_shadow = min(open_p, close_p) - low_p
        upper_shadow = high_p - max(open_p, close_p)
        
        if body > 0 and lower_shadow >= (2 * body) and upper_shadow <= (body * 0.5):
            df.at[df.index[i], 'Pattern'] = 'Hammer'
            df.at[df.index[i], 'Pattern_Marker'] = low_p
            continue
            
        # 3. Engulfing (장악형)
        # Bullish Engulfing: 음봉 뒤에 몸통이 더 큰 양봉
        if (prev_close < prev_open) and (close_p > open_p):
            if open_p < prev_close and close_p > prev_open:
                df.at[df.index[i], 'Pattern'] = 'Bullish Engulfing'
                df.at[df.index[i], 'Pattern_Marker'] = low_p
                continue

        # Bearish Engulfing: 양봉 뒤에 몸통이 더 큰 음봉
        if (prev_close > prev_open) and (close_p < open_p):
            if open_p > prev_close and close_p < prev_open:
                df.at[df.index[i], 'Pattern'] = 'Bearish Engulfing'
                df.at[df.index[i], 'Pattern_Marker'] = high_p
                continue
                
    return df
