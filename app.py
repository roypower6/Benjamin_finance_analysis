import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

import base64

# Custom Modules
from styles import apply_finviz_style, create_finviz_row, create_metric_card
from data import load_sp500_tickers, load_dow_tickers, load_nasdaq_tickers, load_stock_data, load_market_data, load_indices_data, fetch_fear_and_greed_index, get_all_tickers_dict, load_insider_trading, load_market_ticker_data, load_ownership_data
from utils import calculate_technical_indicators, format_currency, fmt, fmt_bn, create_sparkline_chart, create_fear_greed_gauge, create_target_price_chart, detect_candlestick_patterns


# 페이지 설정
st.set_page_config(
    page_title="주식 분석 대시보드",
    page_icon="📈",
    layout="wide"
)

# CSS 스타일 적용
apply_finviz_style()

# [CSS] Hide Streamlit Footer & Header & Remove Padding & Borders
st.markdown("""
<style>
    /* Hide Streamlit Footer ("Built with Streamlit") */
    footer {visibility: hidden;}
    
    /* Hide Top Decoration Bar - Commented out to show Redeploy button */
    /* header {visibility: hidden;} */ 
    
    /* Adjust padding for better readability - DEFAULT (Desktop) */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 5rem !important; /* Reduced from 7rem for better average fit */
        padding-right: 5rem !important;
        max-width: 95% !important;
        margin: 0 auto !important;
    }
    
    /* Mobile Optimization */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.2rem !important;
            padding-right: 0.2rem !important;
            padding-top: 0.2rem !important;
            max-width: 100% !important;
        }
        
        /* Adjust global font sizes if needed for mobile */
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.3rem !important; }
        
        /* Reduce gap between columns in mobile stack */
        div[data-testid="column"] {
            margin-bottom: 1rem !important;
        }
        
        /* Hide spacers on mobile */
        .desktop-spacer {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
    }
    
    /* Remove any white borders around the app */
    .stApp {
        border: none !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 0. Session State 초기화 (가장 먼저 실행)
# -------------------------------------------------------------
if 'ticker_symbol' not in st.session_state:
    st.session_state.ticker_symbol = ""

# -------------------------------------------------------------
# 1. 상단: 로고 (Home Link) & S&P 500 데이터 로드
# -------------------------------------------------------------
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

    

# -------------------------------------------------------------
# 1. 헤더 레이아웃: 로고 (Left) & 검색창 (Middle) & 여백 (Right)
# -------------------------------------------------------------
# [Logo 2.0] [Search 3.5] [Empty 4.5] -> Search takes ~35% width
col_header_logo, col_header_search, col_header_empty = st.columns([0.2, 0.35, 0.45])

with col_header_logo:
    try:
        logo_b64 = get_base64_of_bin_file("assets/logo.png")
        # Clickable Logo -> Refreshes Page (Home)
        st.markdown(
            f"""
            <style>
                .logo-img-hover {{
                    width: 90%;
                    max-width: 220px;
                    border-radius: 15px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
                    opacity: 0.95;
                }}
                .logo-img-hover:hover {{
                    transform: scale(1.05) translateY(-2px);
                    filter: drop-shadow(0 10px 20px rgba(41, 98, 255, 0.5)) brightness(1.1);
                    opacity: 1;
                    cursor: pointer;
                }}
            </style>
            <a href="." target="_self" style="text-decoration: none;">
                <img src="data:image/png;base64,{logo_b64}" 
                     class="logo-img-hover"
                     alt="Benjamin Financial Analysis">
            </a>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        # Fallback Text Title (Clickable)
        st.markdown('<a href="." target="_self" style="text-decoration: none; color: white;"><h2>📈 Benjamin</h2></a>', unsafe_allow_html=True)

with col_header_search:
    st.markdown('<div style="margin-top: 0px;"></div>', unsafe_allow_html=True)
    
    # 1. 맵 데이터 로드
    ticker_map = get_all_tickers_dict()
    
    # helper: Query Resolution
    def resolve_ticker(query):
        if not query: return None
        q = query.strip()
        
        # A. 티커 직접 매칭 (대문자로 변환하여 확인)
        q_upper = q.upper()
        if q_upper in ticker_map.values():
            return q_upper
            
        # B. 기업명 검색 (부분 일치 Case-insensitive)
        # 키 형식: "Apple Inc. (AAPL)" 등
        q_lower = q.lower()
        for label, ticker in ticker_map.items():
            if q_lower in label.lower():
                return ticker
        
        # C. 매칭 실패 시 입력값 그대로 티커로 사용 (직접 입력 모드)
        return q_upper

    # 2. Unified Search Input
    # 현재 세션의 티커를 기본값으로 표시
    current_val = st.session_state.ticker_symbol
    
    search_query = st.text_input(
        label="주식 검색 (티커를 입력)",
        value=current_val,
        placeholder="티커(AAPL, GOOGL, MSFT) 입력...",
        label_visibility="visible"
        # key를 지정하지 않음으로써 value 변경 시 UI 업데이트가 자연스럽게 되도록 유도
    )
    
    # 3. 변경 감지 및 처리
    if search_query != st.session_state.ticker_symbol:
        new_ticker = resolve_ticker(search_query)
        if new_ticker:
            # 입력값과 다른 티커가 리졸브 되었다면 (예: Apple -> AAPL)
            # 혹은 그냥 직접 입력 티커라면
            if new_ticker != st.session_state.ticker_symbol:
                st.session_state.ticker_symbol = new_ticker
                st.rerun()

# 편의를 위해 변수에 할당 (st.session_state.ticker_symbol과 동일)
ticker_symbol = st.session_state.ticker_symbol.upper() if st.session_state.ticker_symbol else ""

# -------------------------------------------------------------
# 2. 메인 앱 로직
# -------------------------------------------------------------

# Add Vertical Spacing between Header and Main Content
st.markdown('<div style="margin-bottom: 40px;"></div>', unsafe_allow_html=True)

if not ticker_symbol:
    # ---------------------------------------------------------
    # 초기 화면: S&P 500 스크리너 & 맵
    # ---------------------------------------------------------

    # -------------------------------------------------------------
    # 0. Market Ticker Marquee (Top)
    # -------------------------------------------------------------
    ticker_data = load_market_ticker_data()
    
    if ticker_data:
        ticker_items = []
        for item in ticker_data:
            color = "#00C853" if item['change'] >= 0 else "#FF3D00"
            icon = "▲" if item['change'] >= 0 else "▼"
            
            # Format display
            # item has 'prefix' ($ or empty) and 'suffix' (% or empty for yield, but we might want just unit)
            # Actually for Yield let's say: "US 10Y Yield: 4.25% (▲ 1.2%)"
            
            price_str = f"{item['prefix']}{item['price']:,.2f}{item['suffix']}"
            
            # Change display
            # If yield, change is also roughly in basis points terms from Yahoo, but change_pct is mostly what people look at for momentum or the absolute basis point move.
            # Let's stick to Pct Change for consistency, or absolute change for Yield?
            # User said: "Show as Yield"
            # Usually for Yields, we show "4.25% (+0.05)" meaning +5 bps.
            # But let's keep consistency with % change for now unless absolute is weird.
            # Users often prefer simple % change of the value.
            
            # Conditionally show change
            change_html = f"<span style='color: {color}; margin-left: 5px;'>{icon} {item['change_pct']:.2f}%</span>"
            
            # User request: "Crypto change remove"
            if item.get('type') == 'crypto':
                change_html = ""
            
            ticker_items.append(
                f"<span style='margin-left: 20px; font-weight: bold; color: #ddd;'>{item['name']}</span> "
                f"<span style='color: white;'>{price_str}</span> "
                f"{change_html}"
            )
        
        # 4x Duplication for smooth seamless loop on wide screens
        # Animation: Move -25% (one full length of original content)
        ticker_html_content = "".join(ticker_items) * 4  
        
        st.markdown(
            f"""
            <style>
            @keyframes marquee {{
                0%   {{ transform: translateX(0); }}
                100% {{ transform: translateX(-25%); }}
            }}
            .marquee-container {{
                width: 100%;
                overflow: hidden;
                white-space: nowrap;
                box-sizing: border-box;
                background-color: #0e1117;
                border-bottom: 1px solid #333;
                padding: 10px 0;
                margin-bottom: 20px;
            }}
            .marquee-content {{
                display: inline-block;
                /* Remove padding-left to avoid jumpiness */
                /* padding-left: 100%; */ 
                animation: marquee 20s linear infinite;
            }}
            /* Faster animation for better feel */
            .marquee-content:hover {{
                animation-play-state: paused;
            }}
            </style>
            <div class="marquee-container">
                <div class="marquee-content">
                    {ticker_html_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Market Index Screener (Indices)
    indices_data = load_indices_data()
    
    if indices_data:
        st.markdown("##### 🌏 주요 시장 지수 (Daily)")
        idx_cols = st.columns(4)
        idx_names = ["DOW", "NASDAQ", "S&P 500", "RUSSELL 2000"]
        
        for i, name in enumerate(idx_names):
            if name in indices_data:
                data = indices_data[name]
                with idx_cols[i]:
                    # Custom HTML Card (No st.container to avoid top padding)
                    change_color = "#39e75f" if data['change'] >= 0 else "#ff4b4b"
                    sign = "+" if data['change'] >= 0 else ""
                    change_text = f"{sign}{data['change']:,.2f} ({sign}{data['pct_change']:.2f}%)"
                    
                    st.markdown(f"""
                    <div style="
                        border: 1px solid rgba(49, 51, 63, 0.2);
                        border-radius: 0.25rem;
                        padding: 10px;
                        background-color: #1a1c24; 
                        margin-bottom: 0px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-weight: bold; font-size: 1.0rem; color: #ddd;">{name}</div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.1rem; font-weight: bold; color:white;">{data['price']:,.2f}</div>
                                <div style="font-size: 0.8rem; color: {change_color};">{change_text}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Fear & Greed Index Section
    fg_data = fetch_fear_and_greed_index()
    if fg_data and fg_data.get('score') is not None:
        st.markdown("---")
        st.subheader("CNN Fear & Greed Index")
        
        # 3-Column Layout: [Gauge] | [Historical Values] | [Indicators] | [ Spacer ]
        col_gauge, col_history, col_indicators, col_dummy = st.columns([0.4, 0.2, 0.35, 0.05])
        
        # 1. Gauge Chart (Left)
        with col_gauge:
            fig_fg = create_fear_greed_gauge(fg_data['score'])
            if fig_fg:
                # Increase height slightly for vertical feel if needed, or keep responsive
                fig_fg.update_layout(height=400)
                st.plotly_chart(fig_fg, use_container_width=True, key="fg_gauge")
                ts = fg_data.get('timestamp')
                if ts:
                    st.caption(f"Last Updated: {ts}")
        
        # 2. Historical Values (Middle, Vertical)
        with col_history:
            st.markdown("##### Historical Values")
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            def get_label(score):
                try:
                    s = float(score)
                    if s < 25: return "Extreme Fear"
                    elif s < 45: return "Fear"
                    elif s <= 55: return "Neutral"
                    elif s < 75: return "Greed"
                    else: return "Extreme Greed"
                except: return ""

            def get_color(label):
                l = label.lower()
                if 'extreme greed' in l: return "#66bb6a"
                elif 'greed' in l: return "#9ccc65"
                elif 'neutral' in l: return "#ffca28"
                elif 'extreme fear' in l: return "#ef5350"
                elif 'fear' in l: return "#ffa726"
                return "#eeeeee"

            def render_history_row(title, val):
                try: 
                    score = float(val)
                    label = get_label(score)
                    color = get_color(label)
                    value_str = f"{score:.0f}"
                except: 
                    value_str = "-"
                    label = ""
                    color = "#ccc"
                
                st.markdown(
                    f"""
                    <div style="margin-bottom: 20px;">
                        <div style="font-size: 1.2rem; color: #aaa; margin-bottom: 5px;">{title}</div>
                        <div style="font-size: 2.4rem; font-weight: bold; color: white;">
                            {value_str} <span style="font-size: 1.4rem; color: {color}; font-weight: 600; margin-left: 8px;">{label}</span>
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            # Render rows
            render_history_row("Prev Close", fg_data.get('previous_close'))
            render_history_row("1 Week Ago", fg_data.get('previous_1_week'))
            render_history_row("1 Month Ago", fg_data.get('previous_1_month'))
            render_history_row("1 Year Ago", fg_data.get('previous_1_year'))

        # 3. Sub-indicators (Right, Vertical)
        with col_indicators:
            st.markdown("##### Market Sentiment Indicators")
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            indicators_list = [
                ('market_momentum', 'Market Momentum'),
                ('stock_price_strength', 'Stock Price Strength'),
                ('stock_price_breadth', 'Stock Price Breadth'),
                ('put_call_options', 'Put and Call Options'),
                ('market_volatility', 'Market Volatility'),
                ('safe_haven_demand', 'Safe Haven Demand'),
                ('junk_bond_demand', 'Junk Bond Demand')
            ]
            
            for key, title in indicators_list:
                data = fg_data.get(key, {})
                rating = data.get('rating', 'N/A')
                if isinstance(rating, str):
                    rating = rating.title()
                
                # Color Mapping
                r_lower = rating.lower()
                if 'extreme greed' in r_lower: rating_color = "#66bb6a"
                elif 'greed' in r_lower: rating_color = "#9ccc65"
                elif 'neutral' in r_lower: rating_color = "#ffca28"
                elif 'extreme fear' in r_lower: rating_color = "#ef5350"
                elif 'fear' in r_lower: rating_color = "#ffa726"
                else: rating_color = "#eeeeee"

                score = data.get('score')
                
                # Format Score
                score_str = f"{float(score):.2f}" if score else '-'
                
                # Compact Card
                st.markdown(
                    f"""
                    <div style="
                        background-color: #262730; 
                        padding: 10px 15px; 
                        border-radius: 6px; 
                        border: 1px solid #444; 
                        margin-bottom: 10px;
                        display: flex; justify-content: space-between; align-items: center;
                    ">
                        <div style="font-size: 1.0rem; font-weight: 500; color: #eee;">{title}</div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.25rem; font-weight: 800; color: {rating_color}; letter-spacing: 0.5px;">{rating}</div>
                            <div style="font-size: 0.8rem; color: #999;">{score_str}</div>
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

    st.markdown("---")
    
    st.header("🏢 주요 지수 주간 퍼포먼스 맵")

    # 주식 맵 렌더링 함수
    def render_map_tab(index_name, load_tickers_func):
        tickers_df, err = load_tickers_func()
        if tickers_df is not None:
             # Auto load without button
             with st.spinner(f"{index_name} 데이터를 불러오는 중..."):
                tickers = tickers_df['Symbol'].tolist()
                tickers = [str(t).replace('.', '-') for t in tickers]
                market_df = load_market_data(tickers)
                
                if market_df is not None and not market_df.empty:
                    tickers_df['Symbol_YF'] = tickers_df['Symbol'].astype(str).str.replace('.', '-')
                    
                    # 컬럼 이름 표준화 (Sector, Name)
                    if 'GICS Sector' in tickers_df.columns:
                        tickers_df['Sector'] = tickers_df['GICS Sector']
                    elif 'Sector' in tickers_df.columns: 
                        tickers_df['Sector'] = tickers_df['Sector']
                    elif 'Industry' in tickers_df.columns:
                        tickers_df['Sector'] = tickers_df['Industry']
                    else:
                        tickers_df['Sector'] = 'Other'
                        
                    if 'Security' in tickers_df.columns:
                        tickers_df['Name'] = tickers_df['Security']
                    elif 'Company' in tickers_df.columns:
                        tickers_df['Name'] = tickers_df['Company']
                    else:
                        tickers_df['Name'] = tickers_df['Symbol']

                    merged_df = pd.merge(market_df, tickers_df[['Symbol_YF', 'Sector', 'Name']], 
                                         left_on='Symbol', right_on='Symbol_YF')
                    
                    # Finviz Style Color Scale
                    fig_tree = px.treemap(merged_df, 
                                          path=[px.Constant(index_name), 'Sector', 'Symbol'], 
                                          values='TradedValue',
                                          color='PctChange',
                                          color_continuous_scale=[(0, "#f63538"), (0.5, "#414554"), (1, "#30cc5a")],
                                          range_color=[-3, 3],
                                          custom_data=['Name', 'Price', 'PctChange', 'Symbol'])
                    
                    fig_tree.update_traces(
                        texttemplate="%{label}<br>%{customdata[2]:.2f}%",
                        hovertemplate='<b>%{customdata[0]}</b><br>Ticker: %{customdata[3]}<br>Price: $%{customdata[1]:.2f}<br>Change: %{customdata[2]:.2f}%<extra></extra>',
                        textposition="middle center",
                        textfont=dict(color='white', size=14, family="Arial")
                    )
                    
                    fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=600, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    
                    event = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun", selection_mode="points", key=f"map_{index_name}")
                    
                    if event and "selection" in event and "points" in event["selection"]:
                         points = event["selection"]["points"]
                         if points:
                             first_point = points[0]
                             if 'customdata' in first_point:
                                 clicked_ticker = first_point['customdata'][3]
                                 st.session_state.ticker_symbol = clicked_ticker
                                 st.rerun()
                else:
                    st.error(f"{index_name} 데이터 로드 실패. 시장이 열려있는지 확인하세요.")
        else:
            st.error(f"티커 리스트 로드 실패: {err}")

    # 탭 구성
    tab_sp500, tab_dow, tab_nasdaq = st.tabs(["S&P 500", "DOW", "NASDAQ 100"])
    
    with tab_sp500:
        render_map_tab("S&P 500", load_sp500_tickers)
    with tab_dow:
        render_map_tab("DOW", load_dow_tickers)
    with tab_nasdaq:
        render_map_tab("NASDAQ 100", load_nasdaq_tickers)

else:
    # ---------------------------------------------------------
    # 분석 화면: 기존 대시보드 로직
    # ---------------------------------------------------------
    
    # UI 레이아웃 준비
    overview_container = st.container()
    chart_container = st.container()
    controls_container = st.container()
    metrics_container = st.container() # Key Metrics Dashboard
    financials_container = st.container()

    # 컨트롤 영역: Daily, Weekly, Monthly 버튼
    with controls_container:
        # 3개의 버튼으로 구성 (Daily, Weekly, Monthly)
        # [Fix] 티커 변경 시 라디오 버튼 상태도 초기화되도록 key에 ticker_symbol을 포함
        timeframe = st.radio("데이터 간격 (Interval)", ["Daily", "Weekly", "Monthly"], horizontal=True, key=f"interval_{ticker_symbol}")
        
        # 선택에 따라 Period와 Interval 매핑
        if timeframe == "Daily":
            interval = "1d"
            period = "1y" # 드래그를 위해 넉넉한 기간
        elif timeframe == "Weekly":
            interval = "1wk"
            period = "3y"
        else: # Monthly
            interval = "1mo"
            period = "5y"

    # 데이터 로딩
    with st.spinner(f'{ticker_symbol} 데이터 불러오는 중...'):
        history, info, financials, quarterly_financials, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow, splits = load_stock_data(ticker_symbol, period, interval)

    if history is None or history.empty:
        overview_container.error(f"'{ticker_symbol}' 데이터를 찾을 수 없습니다.")
    else:
        # -----------------------------------------------------
        # 섹션 1: 회사 개요 (Custom Card Design)
        # -----------------------------------------------------
        with overview_container:
            info_col1, info_col2, info_col3 = st.columns(3)
            current_price = history['Close'].iloc[-1]
            previous_price = history['Close'].iloc[-2] if len(history) > 1 else current_price
            delta = current_price - previous_price
            delta_pct = (delta / previous_price) * 100 if previous_price != 0 else 0
            
            company_name = info.get('longName', ticker_symbol)
            sector = info.get('sector', 'N/A')
            
            with info_col1:
                st.markdown(create_metric_card("Company Name", company_name), unsafe_allow_html=True)
            with info_col2:
                st.markdown(create_metric_card("Sector / Industry", sector), unsafe_allow_html=True)
            with info_col3:
                # Price with Delta & Percentage
                st.markdown(create_metric_card("Current Price", f"{current_price:.2f}", delta=delta, delta_pct=delta_pct, prefix="$"), unsafe_allow_html=True)
            
            st.markdown("---")

        # -----------------------------------------------------
        # 섹션 2: 차트 (Chart Container)
        # -----------------------------------------------------
        with chart_container:
            # [NEW] Tabs for Charts
            tab_tech, tab_per = st.tabs(["기술적 분석 (Technical)", "PER 밴드 (PER Bands)"])
            
            # --- Tab 1: Technical Analysis (Existing Code) ---
            with tab_tech:
                # 기술적 지표 계산
                history = calculate_technical_indicators(history)
                history = detect_candlestick_patterns(history)
                
                # Subplots 생성 (Price, RSI, MACD)
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.1, 
                                    row_heights=[0.5, 0.25, 0.25],
                                    subplot_titles=(f'{ticker_symbol} Price', 'RSI', 'MACD'))
                
                # 1. Price Chart (Candlestick)
                fig.add_trace(go.Candlestick(x=history.index,
                                open=history['Open'],
                                high=history['High'],
                                low=history['Low'],
                                close=history['Close'], showlegend=False), row=1, col=1)
                
                # 2. RSI Chart
                fig.add_trace(go.Scatter(x=history.index, y=history['RSI'], name='RSI', line=dict(color='purple', width=1.5)), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="Overbought (70)")
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="Oversold (30)")
                
                # 3. MACD Chart
                # Histogram Colors
                colors = ['green' if val >= 0 else 'red' for val in history['MACD_Hist']]
                
                fig.add_trace(go.Bar(x=history.index, y=history['MACD_Hist'], name='MACD Hist', marker_color=colors), row=3, col=1)

                # [NEW] Chart Patterns Overlay
                # 1. Bullish Patterns
                bullish_pat = history[history['Pattern'].isin(['Hammer', 'Bullish Engulfing'])]
                if not bullish_pat.empty:
                    fig.add_trace(go.Scatter(
                        x=bullish_pat.index, y=bullish_pat['Pattern_Marker'],
                        mode='markers', marker=dict(symbol='triangle-up', size=12, color='#00ff00'),
                        text=bullish_pat['Pattern'], name='Bullish Pattern'
                    ), row=1, col=1)
                
                # 2. Bearish Patterns
                bearish_pat = history[history['Pattern'].isin(['Bearish Engulfing'])]
                if not bearish_pat.empty:
                    fig.add_trace(go.Scatter(
                        x=bearish_pat.index, y=bearish_pat['Pattern_Marker'],
                        mode='markers', marker=dict(symbol='triangle-down', size=12, color='#ff0000'),
                        text=bearish_pat['Pattern'], name='Bearish Pattern'
                    ), row=1, col=1)

                fig.add_trace(go.Scatter(x=history.index, y=history['MACD'], name='MACD', line=dict(color='blue', width=1.5)), row=3, col=1)
                fig.add_trace(go.Scatter(x=history.index, y=history['Signal_Line'], name='Signal', line=dict(color='orange', width=1.5)), row=3, col=1)
                
                title_text = f'{ticker_symbol} Technical Analysis ({timeframe})'
                
                fig.update_layout(
                    title=title_text,
                    yaxis_title='Price',
                    xaxis_rangeslider_visible=False,
                    height=800,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)' # 투명 배경
                )
                
                # Axis Styling for Boundaries (Subplots 구분선 명확화)
                axis_style = dict(showline=True, linewidth=1, linecolor='white', mirror=True)
                
                # Update all axes
                fig.update_xaxes(**axis_style)
                fig.update_yaxes(**axis_style)
                
                # Fix Title Overlap: Shift subplot titles up
                fig.update_annotations(yshift=20)

                # Specific constraints
                fig.update_yaxes(fixedrange=True, row=1, col=1)
                fig.update_yaxes(fixedrange=True, row=2, col=1, range=[0, 100])
                fig.update_yaxes(fixedrange=True, row=3, col=1)
                fig.update_xaxes(fixedrange=False, row=3, col=1)
                
                # [NEW] Layout Split: Chart vs Status Panel
                col_chart_main, col_chart_info = st.columns([0.85, 0.15])
                
                with col_chart_main:
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col_chart_info:
                    # 1. Spacer for Price Chart (Upper 50% of 800px = 400px)
                    # Adjusting for titles and margins
                    st.markdown("<div class='desktop-spacer' style='height: 380px;'></div>", unsafe_allow_html=True)
                    
                    # 2. RSI Status
                    last_rsi = history['RSI'].iloc[-1]
                    rsi_color = "#999"
                    rsi_msg = "Neutral"
                    
                    if last_rsi >= 70:
                        rsi_color = "#ff4b4b" # Red
                        rsi_msg = "Overbought (과매수)"
                    elif last_rsi <= 30:
                        rsi_color = "#00c853" # Green
                        rsi_msg = "Oversold (과매도)"
                        
                    st.markdown(f"""
                    <div style="
                        border-left: 3px solid {rsi_color}; 
                        padding-left: 10px; 
                        margin-bottom: 0px;
                    ">
                        <div style="font-size: 0.8rem; color: #aaa;">RSI (14)</div>
                        <div style="font-size: 1.4rem; font-weight: bold;">{last_rsi:.1f}</div>
                        <div style="font-size: 0.9rem; color: {rsi_color};">{rsi_msg}</div>
                        <div style="font-size: 0.7rem; color: #666; margin-top: 5px; line-height: 1.2;">
                            RSI가 70이상이면 과매수, 30이하이면 과매도 상태를 의미합니다.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 3. Spacer for RSI section (25% of 800px = ~200px)
                    st.markdown("<div class='desktop-spacer' style='height: 100px;'></div>", unsafe_allow_html=True)
                    
                    # 4. MACD Status
                    last_macd = history['MACD'].iloc[-1]
                    last_signal = history['Signal_Line'].iloc[-1]
                    
                    macd_bullish = last_macd > last_signal
                    macd_color = "#00c853" if macd_bullish else "#ff4b4b"
                    macd_msg = "Bullish (매수세)" if macd_bullish else "Bearish (매도세)"
                    
                    st.markdown(f"""
                    <div style="
                        border-left: 3px solid {macd_color}; 
                        padding-left: 10px;
                    ">
                        <div style="font-size: 0.8rem; color: #aaa;">MACD</div>
                        <div style="font-size: 1.4rem; font-weight: bold;">{last_macd:.2f}</div>
                        <div style="font-size: 0.9rem; color: #ccc;">Sig: {last_signal:.2f}</div>
                        <div style="font-size: 0.9rem; color: {macd_color}; margin-top: 2px;">{macd_msg}</div>
                        <div style="font-size: 0.7rem; color: #666; margin-top: 5px; line-height: 1.2;">
                            MACD가 시그널 선보다 높으면 상승 추세, 낮으면 하락 추세를 의미합니다.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.info("💡 가이드\n\nRSI가 무조건 과매수라고 해서 팔아서는 안됩니다! 대부분의 주식들은 상승세일 때 과매수와 그 아래를 조금씩 유지하며 상승세를 이어갑니다. 과매수 상태에서도 상승세가 더 유지될 수 있고, 과매도 상태에서도 하락세가 더 유지될 수 있습니다. 이 지표들은 단순히 보조 지표로 활용해야 하며, 기업의 펀더멘탈, 밸류에이션을 함께 판단하여 투자 결정을 내려야 합니다. \n\nMACD 지표는 단순히 매수세일때 사고 매도세에 매도하는 지표가 아닙니다. 매도세에서 매수세로 전환되는 지점이나, 매도세가 꺾이고 줄어드는 지점을 찾는 안목도 매우 중요합니다. 주의할 점은 매도세와 매수세가 단순히 반복되지는 않는다는 점입니다. 매도세가 끝나려는 흐름에서 더 이어가버릴 수도 있고, 그 반대의 경우도 충분히 발생할 수 있습니다. 이러한 이유들로 이 지표들을 단순히 매수매도 결정의 기준으로 사용하는 것은 위험한 판단이 될 수 있습니다.")

            # --- Tab 2: PER Bands ---
            with tab_per:
                 st.subheader(f"{ticker_symbol} PER Price Band")
                 
                 # 1. EPS Data Extraction (TTM Preferred)
                 # Use Quarterly Financials for TTM Calculation
                 q_eps = None
                 eps_source = "TTM (Quarterly)"
                 
                 if quarterly_financials is not None and 'Diluted EPS' in quarterly_financials.index:
                     q_eps = quarterly_financials.loc['Diluted EPS'].sort_index()
                 elif quarterly_financials is not None and 'Basic EPS' in quarterly_financials.index:
                     q_eps = quarterly_financials.loc['Basic EPS'].sort_index()
                 
                 final_eps_df = None
                 
                 # 2. Calculate TTM EPS
                 if q_eps is not None and len(q_eps) >= 1:
                     # Rolling Sum of last 4 quarters
                     # If data is sparse, simple rolling might be risky but usually fine for yfinance data
                     ttm_eps = q_eps.rolling(window=4).sum()
                     
                     # Fill NaN at the beginning with annualized single quarter or simple forward fill if acceptable?
                     # Better: just dropna for accurate TTM. 
                     # Or: If we want to show longer history even before 4 quarters, we can use Annual as fallback.
                     # For simplicity, let's use what we have.
                     ttm_eps = ttm_eps.dropna()
                     
                     # If TTM is empty (less than 4 quarters), fallback to Annual
                     if ttm_eps.empty and financials is not None:
                         # Fallback to Annual
                         eps_source = "Annual"
                         if 'Diluted EPS' in financials.index:
                             final_eps_df = financials.loc['Diluted EPS'].sort_index()
                         elif 'Basic EPS' in financials.index:
                             final_eps_df = financials.loc['Basic EPS'].sort_index()
                     else:
                         final_eps_df = ttm_eps
                 else:
                     # Fallback to Annual
                     eps_source = "Annual"
                     if financials is not None:
                         if 'Diluted EPS' in financials.index:
                             final_eps_df = financials.loc['Diluted EPS'].sort_index()
                         elif 'Basic EPS' in financials.index:
                             final_eps_df = financials.loc['Basic EPS'].sort_index()
                 
                 if final_eps_df is not None and not final_eps_df.empty:
                      # 3. Split Adjustment
                      # yfinance EPS is "As Reported" (usually). Splits happened in history.
                      # Price history is "Adjusted". 
                      # So we must adjust EPS for splits to match Price.
                      # Logic: If 4:1 split happened at date D, then EPS before D should be divided by 4.
                      
                      # splits is a Series: Date -> Split Ratio (e.g. 4.0)
                      # Sort splits just in case
                      if splits is not None and not splits.empty:
                          splits_sorted = splits.sort_index()
                          
                          # [Fix] Timezone Mismatch in Comparison
                          # splits index from yfinance is often tz-aware (America/New_York)
                          # financials dates are usually naive regular timestamps
                          if splits_sorted.index.tz is not None:
                              splits_sorted.index = splits_sorted.index.tz_localize(None)
                          
                          adj_eps_values = []
                          for date, val in final_eps_df.items():
                              # Find all splits that happened AFTER this EPS date
                              relevant_splits = splits_sorted[splits_sorted.index > date]
                              
                              # Cumulative split factor
                              # If splits were 4.0 and 2.0 after the date, factor is 8.0
                              split_factor = relevant_splits.prod() if not relevant_splits.empty else 1.0
                              
                              adj_val = val / split_factor
                              adj_eps_values.append(adj_val)
                              
                          final_eps_df = pd.Series(adj_eps_values, index=final_eps_df.index)
                      
                      # 4. Merge with Daily History
                      eps_df = pd.DataFrame({'EPS': final_eps_df})
                      eps_df.index = pd.to_datetime(eps_df.index)
                      eps_df = eps_df.sort_index()
                      
                      hist_sorted = history.sort_index()
                      
                      # [Fix] Timezone Mismatch Error
                      if hist_sorted.index.tz is not None:
                          hist_sorted.index = hist_sorted.index.tz_localize(None)
                      
                      if eps_df.index.tz is not None:
                           eps_df.index = eps_df.index.tz_localize(None)

                      # merge_asof
                      combined = pd.merge_asof(hist_sorted, eps_df, left_index=True, right_index=True, direction='backward')
                      combined = combined.dropna(subset=['EPS'])
                      
                      # Filter negative EPS for PER bands? usually PER bands only for +EPS
                      # But let's plot anyway, maybe user wants to see
                      
                      if not combined.empty:
                            # 5. Calculate Bands
                            combined['PER_10'] = combined['EPS'] * 10
                            combined['PER_15'] = combined['EPS'] * 15
                            combined['PER_20'] = combined['EPS'] * 20
                            combined['PER_25'] = combined['EPS'] * 25
                            combined['PER_30'] = combined['EPS'] * 30
                            
                            # 6. Plot
                            fig_per = go.Figure()
                            
                            # Price
                            fig_per.add_trace(go.Scatter(
                                x=combined.index, y=combined['Close'], 
                                name='Price', 
                                line=dict(color='white', width=2)
                            ))
                            
                            # Bands
                            bands = [
                                (10, '#ef5350'),  # Red
                                (15, '#ffa726'),  # Orange
                                (20, '#66bb6a'),  # Green
                                (25, '#42a5f5'),  # Blue
                                (30, '#ab47bc')   # Purple
                            ]
                            
                            for mult, col in bands:
                                # Show band only if EPS > 0
                                mask = combined['EPS'] > 0
                                if mask.any():
                                    fig_per.add_trace(go.Scatter(
                                        x=combined[mask].index, 
                                        y=combined.loc[mask, f'PER_{mult}'], 
                                        name=f'PER {mult}x', 
                                        line=dict(color=col, width=1, dash='dot'),
                                        hoverinfo='name+y'
                                    ))
                                
                            fig_per.update_layout(
                                title=f'{ticker_symbol} Price vs PER Bands ({eps_source})',
                                yaxis_title='Price',
                                height=600,
                                plot_bgcolor='rgba(0,0,0,0)',
                                xaxis_rangeslider_visible=False,
                                hovermode="x unified",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            
                            axis_style = dict(showline=True, linewidth=1, linecolor='white', mirror=True)
                            fig_per.update_xaxes(**axis_style)
                            fig_per.update_yaxes(**axis_style)

                            st.plotly_chart(fig_per, use_container_width=True)
                            
                            st.info(f"💡 **가이드**: 이 차트는 **{eps_source} EPS**와 **주식 분할(Split) 조정**이 반영된 데이터를 사용합니다. 주가가 수익성 대비 역사적으로 어느 구간(PER 10배~30배)에 있는지 확인하세요.")
                            
                      else:
                          st.warning("EPS 데이터를 매칭할 수 없어 밴드 차트를 그릴 수 없습니다.")
                 else:
                     st.warning("재무 데이터에서 EPS 정보를 찾을 수 없어 밴드 차트를 그릴 수 없습니다.")

        # -----------------------------------------------------
        # 섹션 2.5: 핵심 지표 대시보드 (Key Metrics)
        # -----------------------------------------------------
        with metrics_container:
            if info:
                # -------------------------
                # Data Extraction
                # -------------------------
                # Col 1
                index_name = "S&P 500" # Placeholder
                mkt_cap = info.get('marketCap')
                income = info.get('netIncomeToCommon')
                sales = info.get('totalRevenue')
                book_sh = info.get('bookValue')
                shares = info.get('sharesOutstanding')
                cash_sh = (info.get('totalCash') / shares) if (info.get('totalCash') and shares) else None
                div_yield = info.get('dividendYield')
                
                # Col 2
                employees = info.get('fullTimeEmployees')
                recom = info.get('recommendationMean')
                pe_ratio = info.get('trailingPE')
                fwd_pe = info.get('forwardPE')
                
                # Col 3
                peg_ratio = info.get('pegRatio')
                if peg_ratio is None: peg_ratio = info.get('trailingPegRatio')
                
                ps_ratio = info.get('priceToSalesTrailing12Months')
                pb_ratio = info.get('priceToBook')
                
                # P/C, P/FCF Helper
                total_cash = info.get('totalCash')
                fcf = info.get('freeCashflow')
                pc_ratio = (mkt_cap / total_cash) if (mkt_cap and total_cash) else None
                pfcf_ratio = (mkt_cap / fcf) if (mkt_cap and fcf) else None
                
                quick_ratio = info.get('quickRatio')
                current_ratio = info.get('currentRatio')
                
                # Col 4
                debt_eq = info.get('debtToEquity') # Usually returned as a number like 0.5 or 50? YF returns percentage usually, e.g. 150.
                lt_debt_eq = None # Not directly avail
                
                roa = info.get('returnOnAssets')
                roe = info.get('returnOnEquity')
                gross_margin = info.get('grossMargins')
                
                # ROIC (Custom)
                roic = None
                try:
                    if financials is not None and balance_sheet is not None:
                        op_inc = financials.loc['Operating Income'].iloc[0] if 'Operating Income' in financials.index else None
                        tax_prov = financials.loc['Tax Provision'].iloc[0] if 'Tax Provision' in financials.index else 0
                        pretax = financials.loc['Pretax Income'].iloc[0] if 'Pretax Income' in financials.index else None
                        equity = balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else None
                        debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
                        
                        if op_inc and equity:
                            tax_rate = (tax_prov / pretax) if (pretax and pretax != 0) else 0.21
                            nopat = op_inc * (1 - tax_rate)
                            inv_cap = equity + debt
                            if inv_cap > 0: roic = nopat / inv_cap
                except: pass

                # Col 5
                op_margin = info.get('operatingMargins')
                profit_margin = info.get('profitMargins')
                payout = info.get('payoutRatio')
                insider_own = info.get('heldPercentInsiders')
                inst_own = info.get('heldPercentInstitutions')
                
                # Col 6 (Performance)
                beta = info.get('beta')
                prev_close = info.get('previousClose')
                curr_price = history['Close'].iloc[-1] if not history.empty else 0
                change = curr_price - prev_close if prev_close else 0
                change_pct = (change / prev_close * 100) if prev_close else 0
                
                # Perf Calcs
                perf_week, perf_month, perf_year, volatility = None, None, None, None
                
                # Length Safety Checks
                hist_len = len(history)
                if hist_len >= 5:
                    perf_week = (curr_price / history['Close'].iloc[-5] - 1) * 100
                if hist_len >= 21:
                    perf_month = (curr_price / history['Close'].iloc[-21] - 1) * 100
                if hist_len >= 252:
                    perf_year = (curr_price / history['Close'].iloc[-252] - 1) * 100
                    
                if hist_len > 20:
                    # Volatility (Annualized std dev of daily returns)
                    daily_ret = history['Close'].pct_change()
                    volatility = daily_ret.std() * (252 ** 0.5) * 100

                # -------------------------
                # Rendering 6 Columns
                # -------------------------
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                
                with c1:
                    st.markdown(create_finviz_row("Index", "S&P 500"), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Market Cap", fmt_bn(mkt_cap)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Income", fmt_bn(income)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Sales", fmt_bn(sales)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Book/sh", fmt(book_sh)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Cash/sh", fmt(cash_sh)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Dividend", fmt(div_yield, scale=100, suffix="%")), unsafe_allow_html=True)

                with c2:
                    st.markdown(create_finviz_row("Employees", fmt(employees, "{:,.0f}")), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Optionable", "Yes"), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Shortable", "Yes"), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Recom", fmt(recom), is_good=(recom and recom<2), is_bad=(recom and recom>3)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("P/E", fmt(pe_ratio), is_good=(pe_ratio and pe_ratio<15), is_bad=(pe_ratio and pe_ratio>50)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Forward P/E", fmt(fwd_pe), is_good=(fwd_pe and fwd_pe<15)), unsafe_allow_html=True)

                with c3:
                    # PEG
                    peg_good = (peg_ratio and peg_ratio < 1)
                    peg_bad = (peg_ratio and peg_ratio > 2)
                    st.markdown(create_finviz_row("PEG", fmt(peg_ratio), is_good=peg_good, is_bad=peg_bad), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("P/S", fmt(ps_ratio), is_bad=(ps_ratio and ps_ratio>10)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("P/B", fmt(pb_ratio)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("P/C", fmt(pc_ratio)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("P/FCF", fmt(pfcf_ratio)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Quick Ratio", fmt(quick_ratio), is_good=(quick_ratio and quick_ratio>1), is_bad=(quick_ratio and quick_ratio<0.5)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Current Ratio", fmt(current_ratio), is_good=(current_ratio and current_ratio>1.5)), unsafe_allow_html=True)

                with c4:
                    st.markdown(create_finviz_row("Debt/Eq", fmt(debt_eq), is_bad=(debt_eq and debt_eq>200)), unsafe_allow_html=True) # Assuming %
                    st.markdown(create_finviz_row("LT Debt/Eq", "-"), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("ROA", fmt(roa, scale=100, suffix="%"), is_good=(roa and roa>0.15), is_bad=(roa and roa<0)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("ROE", fmt(roe, scale=100, suffix="%"), is_good=(roe and roe>0.20), is_bad=(roe and roe<0)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("ROIC", fmt(roic, scale=100, suffix="%"), is_good=(roic and roic>0.15)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Gross Margin", fmt(gross_margin, scale=100, suffix="%"), is_good=(gross_margin and gross_margin>0.4)), unsafe_allow_html=True)

                with c5:
                    st.markdown(create_finviz_row("Oper. Margin", fmt(op_margin, scale=100, suffix="%"), is_good=(op_margin and op_margin>0.2)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Profit Margin", fmt(profit_margin, scale=100, suffix="%"), is_good=(profit_margin and profit_margin>0.2)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Payout", fmt(payout, scale=100, suffix="%")), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Insider Own", fmt(insider_own, scale=100, suffix="%")), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Inst Own", fmt(inst_own, scale=100, suffix="%")), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("SMA20", "-"), unsafe_allow_html=True) # Todo
                    st.markdown(create_finviz_row("SMA50", "-"), unsafe_allow_html=True)
                    
                with c6:
                    st.markdown(create_finviz_row("Perf Week", fmt(perf_week, suffix="%"), is_good=(perf_week and perf_week>0), is_bad=(perf_week and perf_week<0)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Perf Month", fmt(perf_month, suffix="%"), is_good=(perf_month and perf_month>0), is_bad=(perf_month and perf_month<0)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Perf Year", fmt(perf_year, suffix="%"), is_good=(perf_year and perf_year>0), is_bad=(perf_year and perf_year<0)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Volatility", fmt(volatility, suffix="%")), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Beta", fmt(beta)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Prev Close", fmt(prev_close)), unsafe_allow_html=True)
                    st.markdown(create_finviz_row("Price", fmt(curr_price)), unsafe_allow_html=True)
                
                pass
            else:
                 st.info("지표 정보를 불러올 수 없습니다.")
            st.markdown("---")



        # -----------------------------------------------------
        # 섹션 4: 재무 데이터 시각화 (Financials Container)
        # -----------------------------------------------------
        with financials_container:
            # Layout: Header/Options (Left) | Horizontal Ad (Right)
            st.header("📊 재무 데이터 시각화")
            # 연간/분기 선택 라디오 버튼
            freq_option = st.radio("보고서 기준", ["연간 (Annual)", "분기별 (Quarterly)"], horizontal=True, key=f"freq_{ticker_symbol}")

            if freq_option == "연간 (Annual)":
                bs_data = balance_sheet
                fin_data = financials
                cf_data = cashflow
            else:
                bs_data = quarterly_balance_sheet
                fin_data = quarterly_financials
                cf_data = quarterly_cashflow
            
            # Tabs (Full Width)
            tab_viz, tab_data = st.tabs(["차트 보기", "데이터 보기"])
            
            # 재무제표가 있는 경우에만 처리
            if fin_data is not None and not fin_data.empty:
                # Transpose for easy plotting: Columns become dates, rows become metrics
                fin_T = fin_data.T
                # 인덱스(날짜)를 Datetime으로 변환하고 오름차순 정렬 (시계열 일치)
                fin_T.index = pd.to_datetime(fin_T.index)
                fin_T = fin_T.sort_index()
                
                # 그래프 표시를 위해 날짜 포맷 변경 (예: Mar 2023)
                fin_T_plot = fin_T.copy()
                fin_T_plot['Date_Str'] = fin_T_plot.index.strftime('%b %Y')

                with tab_viz:
                    viz_col1, viz_col2, viz_col3 = st.columns(3)
                    
                    # 공통 차트 설정 함수
                    # 공통 차트 설정 함수 (Bar + Line for Growth)
                    def create_bar_chart(df, y_col, title, color_seq=None):
                        # Side-effect 방지를 위한 복사
                        plot_df = df.copy()
                        
                        # 날짜순 정렬 보장
                        plot_df = plot_df.sort_index()
                        
                        # [Growth Calculation]
                        # pct_change() computes percentage change from immediately previous row
                        # 첫 번째 값은 NaN이 됨
                        plot_df['Pct_Change'] = plot_df[y_col].pct_change() * 100
                        
                        col_nametext = f'{y_col}_Text'
                        plot_df[col_nametext] = plot_df[y_col].apply(format_currency)
                        
                        # X축 레이블
                        plot_df['X_Label'] = plot_df['Date_Str'] + "<br>(" + plot_df[col_nametext] + ")"
                        
                        # Create Dual Axis Chart
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # 1. Bar Chart (Left Axis - Amount)
                        bar_color = color_seq[0] if color_seq else '#636efa' # Default Plotly Blue
                        fig.add_trace(
                            go.Bar(
                                x=plot_df['X_Label'], 
                                y=plot_df[y_col], 
                                name="Amount",
                                marker_color=bar_color,
                                hovertemplate='%{x}<br>Amount: %{text}',
                                text=plot_df[col_nametext] # For hover info mapping
                            ),
                            secondary_y=False
                        )
                        
                        # 2. Line Chart (Right Axis - Growth %)
                        fig.add_trace(
                            go.Scatter(
                                x=plot_df['X_Label'], 
                                y=plot_df['Pct_Change'], 
                                name="Growth %",
                                mode='lines+markers+text',
                                line=dict(color='#ff3d00', width=2), # Red/Orange for visibility
                                marker=dict(size=6, color='#ff3d00'),
                                text=plot_df['Pct_Change'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else ""),
                                textposition="top center",
                                textfont=dict(color='white', size=10, weight='bold'),
                                hovertemplate='%{x}<br>Growth: %{y:+.2f}%'
                            ),
                            secondary_y=True
                        )
                        
                        # Layout Updates
                        fig.update_layout(
                            title=dict(text=title, x=0, xanchor='left'),
                            showlegend=True,
                            height=400,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            hovermode="x unified" # Unified hover is nice for comparison
                        )
                        
                        # Axes
                        fig.update_yaxes(title_text="", showgrid=True, gridcolor='rgba(128,128,128,0.2)', secondary_y=False)
                        fig.update_yaxes(title_text="", showgrid=False, zeroline=False, secondary_y=True) # Hide grid for right axis
                        fig.update_xaxes(title_text='', type='category')
                        
                        # 막대 텍스트 제거 (X축으로 옮겼으므로)
                        return fig

                    # 1. 매출액 (Total Revenue)
                    with viz_col1:
                        if 'Total Revenue' in fin_data.index:
                            fig_rev = create_bar_chart(fin_T_plot, 'Total Revenue', f'매출액 ({freq_option})')
                            st.plotly_chart(fig_rev, use_container_width=True)
                    
                    # 2. 순이익 (Net Income)
                    with viz_col2:
                        if 'Net Income' in fin_data.index:
                            fig_net = create_bar_chart(fin_T_plot, 'Net Income', f'순이익 ({freq_option})', ['#2ca02c'])
                            st.plotly_chart(fig_net, use_container_width=True)

                    # 3. 영업이익 (Operating Income)
                    with viz_col3:
                        if 'Operating Income' in fin_data.index:
                            # 영업이익도 막대그래프로 변경
                            fig_op = create_bar_chart(fin_T_plot, 'Operating Income', f'영업이익 ({freq_option})', ['#ff7f0e'])
                            st.plotly_chart(fig_op, use_container_width=True)
                
                    # [NEW] 현금흐름표 차트 추가
                    if cf_data is not None and not cf_data.empty:
                        # 현금흐름 데이터 전처리
                        cf_T = cf_data.T
                        cf_T.index = pd.to_datetime(cf_T.index)
                        cf_T = cf_T.sort_index()
                        
                        cf_T_plot = cf_T.copy()
                        cf_T_plot['Date_Str'] = cf_T_plot.index.strftime('%b %Y')
                        
                        with st.container():
                            cf_col1, cf_col2, cf_col3 = st.columns(3)
                            
                            # 4. 영업활동 현금흐름
                            with cf_col1:
                                if 'Operating Cash Flow' in cf_data.index:
                                    fig_ocf = create_bar_chart(cf_T_plot, 'Operating Cash Flow', f'영업활동 현금흐름 ({freq_option})', ['#17becf'])
                                    st.plotly_chart(fig_ocf, use_container_width=True)
                                    
                            # 5. 투자활동 현금흐름
                            with cf_col2:
                                if 'Investing Cash Flow' in cf_data.index:
                                    fig_icf = create_bar_chart(cf_T_plot, 'Investing Cash Flow', f'투자활동 현금흐름 ({freq_option})', ['#9467bd'])
                                    st.plotly_chart(fig_icf, use_container_width=True)
                                    
                            # 6. 재무활동 현금흐름
                            with cf_col3:
                                if 'Financing Cash Flow' in cf_data.index:
                                    fig_fcf = create_bar_chart(cf_T_plot, 'Financing Cash Flow', f'재무활동 현금흐름 ({freq_option})', ['#bcbd22'])
                                    st.plotly_chart(fig_fcf, use_container_width=True)

                st.info("💡 가이드\n\n 순이익과 영업이익만 보고 기업의 모든 것을 판단해서는 안됩니다. 순이익과 영업이익은 생각보다 오염되기 쉽습니다. 인수합병, 자산상각, 임직원의 스톡옵션 행사 등 수많은 요소들이 영향을 미칠 수 있고, 심한 경우 경영진들이 의도적으로 부풀리거나 축소할 수도 있습니다. 특히나 임직원들의 스톡옵션 행사 비율이 높은 초기 IT 기업의 경우 순이익과 영업이익이 마이너스로 표기되는 경우가 많습니다.\n\n 기업이 제대로 돈을 벌고 있는지 확인하고 싶다면, 영업활동 현금흐름을 확인하는 것도 좋은 방법이 될 수 있습니다. 우량한 기업들의 경우 영업활동 현금흐름이 +, 투자활동, 재무활동 현금흐름이 -로 표기되는 경우가 많습니다. (금융 기업들의 경우 영업활동 현금흐름이 -로 표기되고, 재무활동 현금흐름이 +로 표기되는 경우도 있으니 참고하시기 바랍니다.)")

                with tab_data:
                    
                    # -----------------------------------------------------------------
                    # [NEW] Enhanced Financial Data Table with Growth % and Coloring
                    # -----------------------------------------------------------------
                    
                    # 재무제표 항목 한글 번역 매핑
                    FINANCIAL_TERM_MAPPING = {
                        # 대차대조표 (Balance Sheet)
                        "Total Assets": "총자산",
                        "Total Liabilities Net Minority Interest": "총부채",
                        "Total Equity Gross Minority Interest": "총자본",
                        "Total Capitalization": "총자본화",
                        "Common Stock Equity": "보통주 자본",
                        "Net Tangible Assets": "순유형자산",
                        "Working Capital": "운전자본",
                        "Invested Capital": "투자자본",
                        "Tangible Book Value": "유형장부가치",
                        "Total Debt": "총부채",
                        "Net Debt": "순부채",
                        "Share Issued": "발행주식수",
                        "Ordinary Shares Number": "보통주 수",
                        "Treasury Shares Number": "자사주 수",
                        
                        # 자산 세부
                        "Cash And Cash Equivalents": "현금 및 현금성자산",
                        "Other Short Term Investments": "기타 단기투자자산",
                        "Inventory": "재고자산",
                        "Accounts Receivable": "매출채권",
                        "Current Assets": "유동자산",
                        "Net PPE": "유형자산(순액)",
                        "Goodwill": "영업권",
                        "Intangible Assets": "무형자산",
                        "Goodwill And Other Intangible Assets": "영업권 및 기타무형자산",
                        "Non Current Assets": "비유동자산",
                        "Prepaid Assets": "선급금",
                        
                        # 부채 세부
                        "Accounts Payable": "매입채무",
                        "Current Debt": "단기차입금",
                        "Current Liabilities": "유동부채",
                        "Long Term Debt": "장기차입금",
                        "Long Term Debt And Capital Lease Obligation": "장기차입금 및 리스부채",
                        "Non Current Liabilities": "비유동부채",
                        "Current Deferred Revenue": "유동 이연수익",
                        "Deferred Revenue": "이연수익",
                        
                        # 현금흐름표 (Cash Flow)
                        "Operating Cash Flow": "영업활동 현금흐름",
                        "Investing Cash Flow": "투자활동 현금흐름",
                        "Financing Cash Flow": "재무활동 현금흐름",
                        "End Cash Position": "기말 현금잔액",
                        "Income Tax Paid Supplemental Data": "납부 법인세",
                        "Interest Paid Supplemental Data": "지급 이자",
                        "Capital Expenditure": "자본적 지출(CAPEX)",
                        "Issuance Of Capital Stock": "주식 발행",
                        "Issuance Of Debt": "차입금 조달",
                        "Repayment Of Debt": "차입금 상환",
                        "Repurchase Of Capital Stock": "자사주 매입",
                        "Free Cash Flow": "잉여현금흐름(FCF)",
                        "Changes In Cash": "현금 변동액",
                        "Effect Of Exchange Rate Changes": "환율 변동 효과",
                        "Beginning Cash Position": "기초 현금잔액",
                        "Net Income From Continuing Operations": "계속영업 당기순이익",
                        "Depreciation And Amortization": "감가상각비",
                        "Change In Working Capital": "운전자본 변동",
                        "Stock Based Compensation": "주식보상비용",
                        
                        # 손익계산서 (Income Statement)
                        "Total Revenue": "매출액",
                        "Cost Of Revenue": "매출원가",
                        "Gross Profit": "매출총이익",
                        "Operating Expense": "영업비용",
                        "Operating Income": "영업이익",
                        "Net Income": "당기순이익",
                        "EBIT": "EBIT",
                        "EBITDA": "EBITDA",
                        "Interest Expense": "이자비용",
                        "Tax Provision": "법인세비용",
                        "Diluted EPS": "희석 EPS",
                        "Basic EPS": "기본 EPS",
                        "Research And Development": "연구개발비(R&D)",
                        "Selling General And Administration": "판관비(SG&A)",
                        
                        # 기타 자주 나오는 항목들
                        "Minority Interest": "소수지분",
                        "Other Non Current Assets": "기타 비유동자산",
                        "Other Current Assets": "기타 유동자산",
                        "Other Non Current Liabilities": "기타 비유동부채",
                        "Other Current Liabilities": "기타 유동부채",
                        "Ppe Net": "유형자산(순액)",
                        "Retained Earnings": "이익잉여금",
                        "Gains Losses Not Affecting Retained Earnings": "기타포괄손익누계액(OCI)",
                        "Total Debt": "총차입금"
                    }

                    def create_growth_dataframe(df):
                        if df is None or df.empty:
                            return df, []
                        
                        # 1. 날짜 기준 내림차순 정렬 (최신이 왼쪽)
                        temp_df = df.copy()
                        temp_df.columns = pd.to_datetime(temp_df.columns)
                        temp_df = temp_df.sort_index(axis=1, ascending=False)
                        
                        # 2. 증감률 컬럼 생성을 위한 리스트 준비
                        final_cols = [] 
                        cols = temp_df.columns
                        data_collector = {}
                        
                        # 3. 반복문을 통해 (현재 컬럼) -> (증감률) -> (다음 컬럼) 순서로 배치
                        for i in range(len(cols)):
                            curr_col = cols[i]
                            curr_col_str = curr_col.strftime('%Y-%m-%d')
                            
                            # 현재 값 저장
                            data_collector[curr_col_str] = temp_df[curr_col]
                            final_cols.append(curr_col_str)
                            
                            # 마지막 컬럼이 아니면 증감률 계산
                            if i < len(cols) - 1:
                                prev_col = cols[i+1]
                                
                                # 증감률 계산 (Vectorized)
                                diff = temp_df[curr_col] - temp_df[prev_col]
                                pct_change = diff / temp_df[prev_col].abs()
                                
                                growth_col_name = f"DoD % ({i})" # 내부용 이름
                                data_collector[growth_col_name] = pct_change
                                final_cols.append(growth_col_name)

                        # 4. DataFrame 생성
                        growth_df = pd.DataFrame(data_collector, index=temp_df.index)
                        
                        # 컬럼 순서 재정렬
                        growth_df = growth_df[final_cols]
                        
                        return growth_df, final_cols

                    def display_styled_financials(title, df_raw):
                        if df_raw is None or df_raw.empty:
                            return

                        # [NEW] Translate Index to Korean
                        df_translated = df_raw.copy()
                        # 인덱스 값을 문자열로 변환하여 매핑 시도 (인덱스 타입 안전성 확보)
                        new_index = [FINANCIAL_TERM_MAPPING.get(str(idx), idx) for idx in df_translated.index]
                        df_translated.index = new_index
                        
                        # [Fixed] Remove Duplicate Indices to prevent Styler Error
                        if df_translated.index.duplicated().any():
                            df_translated = df_translated.loc[~df_translated.index.duplicated(keep='first')]

                        st.subheader(title)
                        
                        # Growth DF 생성 (번역된 DF 사용)
                        g_df, ordered_cols = create_growth_dataframe(df_translated)
                        
                        # Styler 적용
                        styler = g_df.style
                        
                        # 컬럼 포맷 설정
                        format_dict = {}
                        
                        # 숨길 컬럼 및 이름 변경 매핑
                        rename_cols = {}
                        
                        for col in ordered_cols:
                            if "DoD %" in col:
                                format_dict[col] = "{:+.1%}" # +12.5%
                                rename_cols[col] = "YoY %" if freq_option == "연간 (Annual)" else "QoQ %"
                            else:
                                # Value Columns: Apply formatter
                                # Styler for values: custom styling is harder with simple strings, 
                                # so we keep them as numbers and format via styler
                                format_dict[col] = lambda x: format_currency(x) if pd.notnull(x) else "-"
                        
                        styler.format(format_dict)
                        
                        # 색상 적용 함수
                        def color_growth_and_values(val):
                            # This applies to individual cells, but we need to know column type
                            return '' 

                        # Applymap for specific columns is better
                        growth_cols = [c for c in g_df.columns if "DoD %" in c]
                        
                        def color_arrow(val):
                            if pd.isna(val) or val == np.inf or val == -np.inf: return 'color: #888'
                            color = '#39e75f' if val > 0 else '#ff4b4b' if val < 0 else '#888'
                            return f'color: {color}'
                        
                        import numpy as np
                        styler.applymap(color_arrow, subset=growth_cols)
                        
                        # 컬럼 이름 변경 (Display용)
                        # Styler.hide(axis="index") option available? Yes
                        # Rename columns using explicit HTML styled headers? 
                        # Or simple rename
                        
                        # Streamlit dataframe column config can also handle this but standard Styler is more flexible for colors
                        # Let's use `st.dataframe` with `column_config` is easier for labels, but `style` for colors.
                        # Actually sending styler to st.dataframe works well
                        
                        # Rename columns in the styler proper (Make labels pretty)
                        # The "DoD % (0)" needs to be distinct keys, but shown as just "MoM %"
                        # We can use `set_table_styles` or modifying the header is tricky in pure Streamlit.
                        # Workaround: Use meaningful unique names, clean them up visually?
                        # Or just "Chg %"
                        
                        clean_renames = {c: ("기존 대비 증감" if "DoD" in c else c) for c in g_df.columns}
                        # Actually let's just make them "YoY %" or "QoQ %" with hidden unique ID?
                        # Streamlit doesn't support duplicate column names even in display normally.
                        
                        # Just use a simple trick: Append zero-width spaces for uniqueness if needed, 
                        # but "Vs Last" is okay.
                        
                        # Let's stick to the internal names and use `.relabel_index` or similar if supported?
                        # No, simpler: format the index (rows) and leave columns as dates vs changes.
                        
                        # Let's try replacing the Column Names with a Label map
                        # Note: dataframe needs unique columns.
                        
                        st.dataframe(styler, use_container_width=True, height=400)

                    # 렌더링 실행
                    display_styled_financials("손익계산서", fin_data)
                    
                    if bs_data is not None:
                        st.markdown("---")
                        display_styled_financials("대차대조표", bs_data)
                    
                    if cf_data is not None:
                        st.markdown("---")
                        display_styled_financials("현금흐름표", cf_data)
                
                # -----------------------------------------------------
                # Analyst Target Price Section
                # -----------------------------------------------------
                target_mean = info.get('targetMeanPrice')
                if target_mean:
                    st.markdown("---")
                    st.markdown("### 🎯 애널리스트 목표 주가 (Analyst Targets)")
                    
                    an_col1, an_col2 = st.columns([0.65, 0.35])
                    
                    with an_col1:
                        target_low = info.get('targetLowPrice')
                        target_high = info.get('targetHighPrice')
                        current_p = info.get('currentPrice')
                        if not current_p: current_p = curr_price
                        
                        currency = info.get('currency', 'USD')
                        sym = '$' if currency == 'USD' else ''
                        
                        fig_target = create_target_price_chart(current_p, target_low, target_mean, target_high, currency=sym)
                        if fig_target:
                            st.plotly_chart(fig_target, use_container_width=True)
                            
                    with an_col2:
                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 
                        st.markdown("#### 투자의견 (Consensus)")
                        
                        rec_mean = info.get('recommendationMean')
                        rec_key = info.get('recommendationKey', 'N/A').upper().replace('_', ' ')
                        num_analysts = info.get('numberOfAnalystOpinions')
                        
                        # Custom Metric styled
                        st.metric("투자의견", rec_key)
                        
                        mc1, mc2, mc3 = st.columns(3)
                        with mc1:
                             if rec_mean:
                                st.metric("Mean Score", f"{rec_mean:.1f}", help="1=Strong Buy, 5=Sell")
                        with mc2:
                             if target_mean:
                                st.metric("평균 목표주가", f"{sym}{target_mean:,.2f}", help="Average Analyst Target")
                        with mc3:
                             if num_analysts:
                                st.metric("애널리스트 수", f"{num_analysts}")

                st.markdown("---")
                st.markdown("### 💎 적정 가치 산출 (DCF)")
                
                st.markdown("##### DCF 가치평가 (간이 모델 - Annual Data)")
                
                # DCF는 항상 연간 데이터 기준 (TTM or Last Year)
                dcf_cf_data = cashflow
                dcf_bs_data = balance_sheet
                
                if dcf_cf_data is not None and not dcf_cf_data.empty and dcf_bs_data is not None and not dcf_bs_data.empty:
                    # 날짜 정렬 (Index: Date)
                    cf_T = dcf_cf_data.T
                    cf_T.index = pd.to_datetime(cf_T.index)
                    cf_T = cf_T.sort_index(ascending=True) # 과거 -> 최신
                    
                    bs_T = dcf_bs_data.T
                    bs_T.index = pd.to_datetime(bs_T.index)
                    bs_T = bs_T.sort_index(ascending=True)

                    try:
                        # 1. Base FCF (Latest Annual)
                        # Free Cash Flow = Operating Cash Flow - CapEx
                        recent_ocf = cf_T['Operating Cash Flow'].iloc[-1]
                        
                        if 'Capital Expenditure' in cf_T.columns:
                            recent_capex = abs(cf_T['Capital Expenditure'].iloc[-1])
                        elif 'Purchase Of PPE' in cf_T.columns:
                            recent_capex = abs(cf_T['Purchase Of PPE'].iloc[-1])
                        else:
                            recent_capex = 0
                        
                        fcf_base = recent_ocf - recent_capex
                        
                        st.markdown(f"**Base FCF (Latest Annual)**: {format_currency(fcf_base)}")
                        
                        
                        # 2. Scenarios Definition
                        # (Very Bearish, Bearish, Base, Bullish, Very Bullish)
                        scenarios = {
                            "최악 (Very Bearish)": {"wacc": 0.12, "growth": 0.05, "terminal": 0.015, "color": "#b71c1c"}, # Dark Red
                            "약세 (Bearish)": {"wacc": 0.105, "growth": 0.10, "terminal": 0.02, "color": "#ff4b4b"}, # Red
                            "평범 (Base)": {"wacc": 0.09, "growth": 0.15, "terminal": 0.025, "color": "#f0f2f6"}, # Default
                            "강세 (Bullish)": {"wacc": 0.075, "growth": 0.20, "terminal": 0.03, "color": "#69f0ae"}, # Light Green
                            "최상 (Very Bullish)": {"wacc": 0.06, "growth": 0.25, "terminal": 0.035, "color": "#00c853"} # Green
                        }

                        st.markdown("#### 시나리오별 적정 주가 (Scenario Analysis)")
                        
                        # Prepare columns for scenarios
                        s_cols = st.columns(5)
                        
                        # Loop through scenarios
                        for idx, (name, params) in enumerate(scenarios.items()):
                            wacc = params['wacc']
                            growth = params['growth']
                            terminal_rate = params['terminal']
                            color = params['color']
                            
                            # Calculation Logic
                            # 1. Projected FCFs (Years 1 to 5)
                            fcfs = []
                            current_fcf_proj = fcf_base
                            for i in range(1, 6):
                                current_fcf_proj *= (1 + growth)
                                fcfs.append(current_fcf_proj)
                            
                            # 2. Present Value of Projected FCFs
                            pv_fcfs = [fcf / (1 + wacc)**(i+1) for i, fcf in enumerate(fcfs)]
                            total_pv_fcfs = sum(pv_fcfs)
                            
                            # 3. Terminal Value
                            fcf_year_6 = fcfs[-1] * (1 + terminal_rate)
                            terminal_value = fcf_year_6 / (wacc - terminal_rate)
                            pv_terminal_value = terminal_value / ((1 + wacc) ** 5)
                            
                            # 4. Total Value & Net Cash
                            total_debt = 0
                            cash_and_equiv = 0
                            
                            if 'Total Debt' in bs_T.columns:
                                total_debt = bs_T['Total Debt'].iloc[-1]
                            if 'Cash And Cash Equivalents' in bs_T.columns:
                                cash_and_equiv = bs_T['Cash And Cash Equivalents'].iloc[-1]
                            
                            net_cash = cash_and_equiv - total_debt
                            
                            enterprise_value = total_pv_fcfs + pv_terminal_value
                            equity_value = enterprise_value + net_cash
                            
                            # Shares Outstanding
                            shares_outstanding = info.get('sharesOutstanding', 1)
                            if shares_outstanding is None: shares_outstanding = 1
                            
                            intrinsic_value = equity_value / shares_outstanding
                            
                            # Upside/Downside
                            upside = (intrinsic_value - current_price) / current_price * 100
                            
                            # Display Card
                            with s_cols[idx]:
                                st.markdown(f"""
                                <div style="
                                    border: 1px solid rgba(255, 255, 255, 0.1);
                                    border-radius: 8px;
                                    padding: 15px;
                                    background-color: #262730;
                                    text-align: center;
                                ">
                                    <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 10px; color: {color};">
                                        {name}
                                    </div>
                                    <div style="font-size: 0.9em; color: #aaa; margin-bottom: 5px;">
                                        WACC: {wacc*100:.1f}% | Growth: {growth*100:.1f}%
                                    </div>
                                    <div style="font-size: 1.8em; font-weight: bold; color: white;">
                                        ${intrinsic_value:,.2f}
                                    </div>
                                    <div style="font-size: 1.0em; color: {'#39e75f' if upside >= 0 else '#ff4b4b'};">
                                        {upside:+.2f}%
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Additional Detail for Base Case (Mental Check)
                        # Optional: Could add a toggle or expander to see calculation detail for Base
                        
                        st.markdown("")
                        st.info("💡 **가정 설명 (Assumptions)**: 각 시나리오는 WACC(할인율), 향후 5년 성장률, 영구 성장률을 다르게 적용하여 산출되었습니다.")

                    except Exception as e:
                        st.error(f"DCF 계산 중 오류가 발생했습니다: {e}")
                else:
                    st.warning("DCF 계산을 위한 충분한 재무 데이터(현금흐름표/대차대조표)가 없습니다.")

        # -----------------------------------------------------
        # 섹션 6: 내부자 거래 (Insider Trading)
        # -----------------------------------------------------
        st.markdown("---")
        st.header("👔 내부자 거래 (Insider Trading)")
        
        insider_data = load_insider_trading(ticker_symbol)
        
        if insider_data is not None and not insider_data.empty:
             st.info("💡 **가이드**: 내부자(경영진/주요주주)의 매수(Buy)는 기업 미래에 대한 자신감을, 매도(Sell)는 차익 실현을 의미할 수 있습니다.\n\n 전설적인 투자자 피터 린치는 내부자 매도는 여러 가지 이유가 있을 수 있지만, 내부자 매수의 이유는 한 가지라고 했습니다. 기업의 경영진으로서, 지금보다 주가가 더 오를 것이라고 판단하기 때문입니다.")
             
             # Data cleaning for display
             disp_insider = insider_data.copy()
             
             # If 'Date' is index, make it column
             if isinstance(disp_insider.index, pd.DatetimeIndex):
                 disp_insider.reset_index(inplace=True)
                 
             # Sort by latest
             if 'Start Date' in disp_insider.columns:
                disp_insider.sort_values('Start Date', ascending=False, inplace=True)
             
             # --- [NEW] Ratio Analysis Logic ---
             try:
                 # Filter last 1 year
                 one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
                 
                 # Ensure Start Date is datetime
                 temp_df = disp_insider.copy()
                 if 'Start Date' in temp_df.columns:
                     temp_df['Start Date'] = pd.to_datetime(temp_df['Start Date'], errors='coerce')
                     recent_df = temp_df[temp_df['Start Date'] >= one_year_ago]
                 else:
                     recent_df = temp_df # Fallback
                     
                 # Count Buy/Sell
                 buy_count = 0
                 sell_count = 0
                 buy_val = 0.0
                 sell_val = 0.0
                 
                 for idx, row in recent_df.iterrows():
                     text_val = ""
                     if 'Text' in row: text_val += str(row['Text']).lower()
                     if 'Transaction' in row: text_val += str(row['Transaction']).lower()
                     
                     # Get Value (Amount)
                     val = 0.0
                     if 'Value' in row and pd.notnull(row['Value']):
                         try:
                             val = float(row['Value'])
                         except:
                             val = 0.0
                     
                     if 'purchase' in text_val or 'buy' in text_val:
                         buy_count += 1
                         buy_val += val
                     elif 'sale' in text_val or 'sell' in text_val:
                         sell_count += 1
                         sell_val += val
                 
                 total_count = buy_count + sell_count
                 total_val = buy_val + sell_val
                 
                 if total_count > 0:
                     buy_ratio = buy_count / total_count
                     sell_ratio = sell_count / total_count
                     
                     st.markdown(f"**최근 1년 매수/매도 비율 (Total: {total_count}건)**")
                     
                     # 1. Count Ratio Bar
                     st.markdown(f"""
                     <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <div style="width: 80px; font-size: 0.8rem; color: #ccc;">건수 (Count)</div>
                        <div style="flex-grow: 1; margin-right: 10px;">
                            <div style="display: flex; height: 18px; border-radius: 9px; overflow: hidden; background-color: #333;">
                                <div style="width: {buy_ratio*100}%; background-color: #00C853; display: flex; align-items: center; justify-content: center; color: black; font-size: 0.7rem; font-weight: bold;">
                                    {buy_count}
                                </div>
                                <div style="width: {sell_ratio*100}%; background-color: #FF3D00; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7rem; font-weight: bold;">
                                    {sell_count}
                                </div>
                            </div>
                        </div>
                        <div style="font-size: 0.8rem; color: #ddd; width: 120px; text-align: right;">
                            <span style="color: #00C853;">{buy_ratio*100:.0f}%</span> vs <span style="color: #FF3D00;">{sell_ratio*100:.0f}%</span>
                        </div>
                     </div>
                     """, unsafe_allow_html=True)
                     
                     # 2. Value Ratio Bar
                     if total_val > 0:
                         buy_val_ratio = buy_val / total_val
                         sell_val_ratio = sell_val / total_val
                         
                         # Format values nicely (e.g. 1.2M)
                         b_val_str = fmt_bn(buy_val)
                         s_val_str = fmt_bn(sell_val)
                         
                         st.markdown(f"""
                         <div style="display: flex; align-items: center; margin-bottom: 20px;">
                            <div style="width: 80px; font-size: 0.8rem; color: #ccc;">금액 (Value)</div>
                            <div style="flex-grow: 1; margin-right: 10px;">
                                <div style="display: flex; height: 18px; border-radius: 9px; overflow: hidden; background-color: #333;">
                                    <div style="width: {buy_val_ratio*100}%; background-color: #00C853; display: flex; align-items: center; justify-content: center; color: black; font-size: 0.7rem; font-weight: bold;">
                                        {b_val_str}
                                    </div>
                                    <div style="width: {sell_val_ratio*100}%; background-color: #FF3D00; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7rem; font-weight: bold;">
                                        {s_val_str}
                                    </div>
                                </div>
                            </div>
                            <div style="font-size: 0.8rem; color: #ddd; width: 120px; text-align: right;">
                                <span style="color: #00C853;">{buy_val_ratio*100:.0f}%</span> vs <span style="color: #FF3D00;">{sell_val_ratio*100:.0f}%</span>
                            </div>
                         </div>
                         """, unsafe_allow_html=True)
             except Exception as e:
                 # st.error(f"비율 계산 중 오류: {e}")
                 pass
             # ----------------------------------
             
             # 1. Map Ownership ('D' -> Direct, 'I' -> Indirect)
             for owner_col in ['Ownership', 'Ownership Type']:
                 if owner_col in disp_insider.columns:
                     disp_insider[owner_col] = disp_insider[owner_col].map({'D': 'Direct', 'I': 'Indirect'}).fillna(disp_insider[owner_col])
            
             # Create Price Column if not exists
             if 'Value' in disp_insider.columns and 'Shares' in disp_insider.columns:
                 # Ensure numeric
                 try:
                     # Calculate Price = Value / Shares
                     # See if rounding helps display
                     disp_insider['Price'] = disp_insider.apply(
                         lambda row: round(row['Value'] / row['Shares'], 2) if row['Shares'] and row['Shares'] != 0 else None, 
                         axis=1
                     )
                 except:
                     pass

             # 2. Define Styling Function
             def highlight_insider(row):
                 # Logic to determine color based on hidden columns (Transaction/Text)
                 text_val = ""
                 if 'Text' in row.index: text_val += str(row['Text']).lower()
                 if 'Transaction' in row.index: text_val += str(row['Transaction']).lower()
                 
                 style = ''
                 if 'purchase' in text_val or 'buy' in text_val:
                     style = 'background-color: rgba(0, 200, 83, 0.2)' # Green
                 elif 'sale' in text_val or 'sell' in text_val:
                     style = 'background-color: rgba(255, 75, 75, 0.2)' # Red
                 
                 return [style] * len(row)

             # 3. Format Numbers (K, M, B)
             # Apply formatting directly to DataFrame columns for robust display
             
             if 'Value' in disp_insider.columns:
                 # Use format_currency for K, M, B support
                 disp_insider['Value'] = disp_insider['Value'].apply(lambda x: format_currency(x) if pd.notnull(x) else x)
                 
             if 'Shares' in disp_insider.columns:
                 disp_insider['Shares'] = disp_insider['Shares'].apply(lambda x: format_currency(x) if pd.notnull(x) else x)
                 
             if 'Price' in disp_insider.columns:
                 # User requested no decimal representation for Price (Integer)
                 disp_insider['Price'] = disp_insider['Price'].apply(lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) else x)

             # [NEW] 컬럼명 한글 변환
             # 화면 표시용이므로 포맷팅 이후에 변경
             insider_col_map = {
                 "Start Date": "날짜",
                 "Insider": "내부자",
                 "Relation": "직위",
                 "Position": "직위", 
                 "Shares": "수량",
                 "Value": "금액",
                 "Price": "평단가",
                 "Ownership": "소유 형태",
                 "Ownership Type": "소유 형태"
             }
             disp_insider.rename(columns=insider_col_map, inplace=True)

             # Create Styler
             styler = disp_insider.style.apply(highlight_insider, axis=1)
             
             # Format Columns (Removed styler specific formats as we did it in DF)
             # if 'Value' in disp_insider.columns:
             #      styler.format({'Value': '${:,.0f}'}) 
             # ...
             
             # Hide Columns
             cols_to_hide = ['URL', 'Transaction', 'Text', 'SEC Form 4', 'Id']
             existing_cols_to_hide = [c for c in cols_to_hide if c in disp_insider.columns]
             styler.hide(axis="columns", subset=existing_cols_to_hide)
             
             # Configure Columns
             hide_config = {
                 "날짜": st.column_config.DateColumn("날짜", format="YYYY-MM-DD"),
             }
             for c in existing_cols_to_hide:
                 hide_config[c] = None # Ensure logic hides them in dataframe config too depending on streamlit version
             
             st.dataframe(
                  styler,
                  use_container_width=True,
                  hide_index=True,
                  column_config=hide_config
             )
        else:
            st.write("최근 내부자 거래 내역이 없습니다.")

        # -----------------------------------------------------
        # 섹션 7: 투자자 분석 (Investor Analysis)
        # -----------------------------------------------------
        st.markdown("---")
        st.header("👥 투자자 분석 (Ownership Analysis)")
        
        ownership = load_ownership_data(ticker_symbol)
        
        if ownership:
             # 1. Top Institutional Holders Only (User Requested Deletion of Shareholders Pie Chart)
             st.subheader("주요 보유 기관 (Top Institutions)")
             inst_holders = ownership.get('institutional')
             
             if inst_holders is not None and not inst_holders.empty:
                 disp_inst = inst_holders.copy()
                 
                 # Format Numbers (Quantity/Value) uses fmt_bn (Billions/Millions/etc)
                 if 'Value' in disp_inst.columns:
                     disp_inst['Value'] = disp_inst['Value'].apply(lambda x: fmt_bn(x) if pd.notnull(x) else x)
                 if 'Shares' in disp_inst.columns:
                     disp_inst['Shares'] = disp_inst['Shares'].apply(lambda x: fmt_bn(x) if pd.notnull(x) else x)
                 if 'Date Reported' in disp_inst.columns:
                      disp_inst['Date Reported'] = pd.to_datetime(disp_inst['Date Reported']).dt.strftime('%Y-%m-%d')
                 
                 # Format Percentage Columns (Multiply by 100 and add %)
                 # yfinance usually returns 0.05 for 5%. User wants "5.00%"
                 for pct_col in ['pctHeld', 'pctChange']:
                     if pct_col in disp_inst.columns:
                         disp_inst[pct_col] = disp_inst[pct_col].apply(lambda x: f"{x*100:,.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x)

                 # Translate Columns
                 inst_columns_map = {
                     "Holder": "기관명",
                     "Shares": "보유 주식수",
                     "Date Reported": "보고일",
                     "pctHeld": "지분율",
                     "pctChange": "지분율 변화",
                     "Value": "평가 가치"
                 }
                 disp_inst.rename(columns=inst_columns_map, inplace=True)
                 
                 st.dataframe(disp_inst, use_container_width=True, hide_index=True)
             else:
                 st.info("기관 보유 데이터 없음")
        else:
            st.info("주주 데이터를 불러올 수 없습니다.")

# -------------------------------------------------------------
# Legal Footer (Custom HTML)
# -------------------------------------------------------------
st.html("""
<style>
    .footer {
        width: 100%;
        font-size: 12px;
        color: #888;
        text-align: center;
        padding: 40px 0 20px 0;
        border-top: 1px solid #333;
        margin-top: 50px;
    }
    .footer a {
        color: #aaa;
        text-decoration: none;
        margin: 0 8px;
    }
    .footer a:hover {
        color: #fff;
        text-decoration: underline;
    }
    .disclaimer {
        font-size: 11px;
        color: #666;
        margin-top: 15px;
        line-height: 1.5;
    }
</style>

<div class="footer">
    <div>
        본 서비스에서 제공하는 모든 금융 데이터(주가, 재무제표 등)는 <strong>Yahoo Finance</strong>로부터 제공받으며, 실시간 값이 아닐 수 있습니다 (최소 15분 지연).
    </div>

    <div class="disclaimer">
        <strong>면책 조항 (Disclaimer)</strong>: 본 사이트는 투자를 위한 정보 제공을 목적으로 하며, 투자의 책임은 전적으로 투자자 본인에게 있습니다. 어떠한 경우에도 본 사이트의 정보가 법적 책임소재의 증빙자료로 사용될 수 없습니다.<br>
        <br>
        데이터 출처: Yahoo Finance <br>
        개발 및 운영: Benjamin Finance Analysis Dashboard Team <br>
        문의: roy040707@gmail.com <br>
        <br>
        Copyright © 2026 Benjamin Finance Analysis Dashboard. All Rights Reserved.
    </div>
</div>
""")
