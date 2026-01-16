
import plotly.graph_objects as go

def create_target_price_chart(current_price, low, mean, high, currency="$"):
    """
    Creates a Horizontal Chart comparing Current Price vs Analyst Targets.
    """
    if not all([current_price, low, mean, high]):
        return None
        
    fig = go.Figure()
    
    # 1. Analyst Range (Low to High) - Background Bar
    fig.add_trace(go.Scatter(
        x=[low, high],
        y=["Target", "Target"],
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.2)', width=10),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # 2. Analyst Mean - Blue Dot
    fig.add_trace(go.Scatter(
        x=[mean],
        y=["Target"],
        mode='markers+text',
        marker=dict(size=16, color='#2962ff'),
        text=[f"Mean: {currency}{mean:,.2f}"],
        textposition="top center",
        name="Analyst Mean",
        hoverinfo='x+name'
    ))
    
    # 3. Low/High markers
    fig.add_trace(go.Scatter(
        x=[low, high],
        y=["Target", "Target"],
        mode='markers+text',
        marker=dict(size=10, color='white', symbol='line-ns-open'),
        text=[f"Low: {currency}{low:,.2f}", f"High: {currency}{high:,.2f}"],
        textposition="bottom center",
        name="Range",
        hoverinfo='x'
    ))

    # 4. Current Price - Red/Green Indicator
    # Determine color: Green if below mean (upside), Red if above mean (downside) logic?
    # Or just neutral Distinct color. Let's use a Vertical Line marker overlay.
    
    color_curr = "#ff0000" # Red for visibility
    
    fig.add_trace(go.Scatter(
        x=[current_price],
        y=["Target"],
        mode='markers+text',
        marker=dict(size=18, color=color_curr, symbol='line-ns', line=dict(width=3, color=color_curr)),
        text=[f"Current: {currency}{current_price:,.2f}"],
        textposition="middle right" if current_price < mean else "middle left",
        name="Current Price",
        hoverinfo='x+name'
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"},
        xaxis=dict(showgrid=False, zeroline=False, visible=True, title="Price"),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        margin=dict(l=20, r=20, t=30, b=30),
        height=150,
        showlegend=False
    )
    
    return fig
