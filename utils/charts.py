"""Shared Plotly chart builders for the Safety Stock Portal."""
import plotly.graph_objects as go
import plotly.express as px

# ── Shared layout base ───────────────────────────────────────────────────────
BASE_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(14,23,41,0.3)',
    font=dict(family='Inter', color='#798a9f', size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        bgcolor='rgba(14,23,41,0.8)',
        bordercolor='rgba(31,111,235,0.2)',
        borderwidth=1,
        font=dict(color='#c5d1e0')
    ),
)

AXIS_STYLE = dict(
    gridcolor='rgba(26,34,61,0.6)',
    tickcolor='#798a9f',
    linecolor='rgba(31,111,235,0.2)',
    tickfont=dict(color='#798a9f', size=11),
    title_font=dict(color='#798a9f'),
    showgrid=True,
    zeroline=False,
)

COLORS = {
    'primary':   '#1f6feb',
    'secondary': '#58a6ff',
    'cyan':      '#00d2ff',
    'success':   '#00c864',
    'warning':   '#ffb400',
    'danger':    '#ff3c50',
    'purple':    '#a371f7',
    'abc': {
        'A': '#1f6feb',
        'B': '#58a6ff',
        'C': '#00d2ff',
    },
    'xyz': {
        'X': '#00c864',
        'Y': '#ffb400',
        'Z': '#ff3c50',
    },
    'status': {
        'Sufficient': '#00c864',
        'Low': '#ffb400',
        'Critical': '#ff3c50',
    },
    'action': {
        'No Action Required': '#00c864',
        'Order Material': '#ff7800',
    }
}


def demand_chart(history: list, metrics: dict) -> go.Figure:
    """Line chart: historical demand + SES forecast point."""
    dates = [h['Date'] for h in history]
    demand = [h['Demand'] for h in history]

    fig = go.Figure()

    # Historical line
    fig.add_trace(go.Scatter(
        x=dates, y=demand,
        mode='lines+markers',
        name='Historical Demand',
        line=dict(color=COLORS['primary'], width=2.5),
        marker=dict(color=COLORS['primary'], size=5, line=dict(color='#0a0f1e', width=1.5)),
        fill='tozeroy',
        fillcolor='rgba(31,111,235,0.07)',
    ))

    # Forecast point — connect from last historical
    if dates and metrics.get('forecast_demand') is not None:
        last_date = dates[-1]
        last_demand = demand[-1]
        forecast_date = metrics.get('forecast_date', '')
        forecast_val = metrics['forecast_demand']

        fig.add_trace(go.Scatter(
            x=[last_date, forecast_date],
            y=[last_demand, forecast_val],
            mode='lines+markers',
            name='SES Forecast',
            line=dict(color=COLORS['cyan'], width=2.5, dash='dash'),
            marker=dict(
                color=COLORS['cyan'], size=10,
                symbol='diamond',
                line=dict(color='#f0f4f9', width=2)
            ),
        ))

    layout = BASE_LAYOUT.copy()
    layout.update(dict(
        title=dict(text='Historical Demand & SES Forecast', font=dict(color='#f0f4f9', size=15)),
        xaxis=dict(**AXIS_STYLE, title='Month'),
        yaxis=dict(**AXIS_STYLE, title='Demand Quantity'),
        hovermode='x unified',
    ))
    fig.update_layout(**layout)
    return fig


def pie_chart(labels: list, values: list, title: str, color_map: dict = None) -> go.Figure:
    """Generic pie / donut chart."""
    colors = [color_map.get(l, '#1f6feb') for l in labels] if color_map else None
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='#0a0f1e', width=2)),
        textfont=dict(color='#e6edf3', size=12),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>',
    ))
    layout = BASE_LAYOUT.copy()
    layout.update(dict(
        title=dict(text=title, font=dict(color='#f0f4f9', size=15)),
        legend=dict(**BASE_LAYOUT['legend'], orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
    ))
    fig.update_layout(**layout)
    return fig


def bar_chart(x: list, y: list, title: str, xaxis_title: str = '', yaxis_title: str = '',
              color: str = '#1f6feb', orientation: str = 'v') -> go.Figure:
    """Generic vertical or horizontal bar chart."""
    if orientation == 'h':
        fig = go.Figure(go.Bar(
            y=x, x=y, orientation='h',
            marker=dict(
                color=y,
                colorscale=[[0, '#0a3d80'], [0.5, '#1f6feb'], [1, '#00d2ff']],
                line=dict(color='rgba(0,0,0,0)', width=0)
            ),
            text=[f'${v:,.0f}' if yaxis_title == '$' else f'{v:,.0f}' for v in y],
            textposition='outside',
            textfont=dict(color='#c5d1e0', size=11),
            hovertemplate='<b>%{y}</b><br>Value: %{x:,.0f}<extra></extra>',
        ))
        layout = BASE_LAYOUT.copy()
        layout.update(dict(
            title=dict(text=title, font=dict(color='#f0f4f9', size=15)),
            xaxis=dict(**AXIS_STYLE, title=xaxis_title),
            yaxis=dict(**AXIS_STYLE, title=yaxis_title, automargin=True),
        ))
    else:
        fig = go.Figure(go.Bar(
            x=x, y=y,
            marker=dict(
                color=y if not color else color,
                line=dict(color='rgba(0,0,0,0)', width=0)
            ),
            text=[f'{v:,.0f}' for v in y],
            textposition='outside',
            textfont=dict(color='#c5d1e0', size=11),
            hovertemplate='<b>%{x}</b><br>%{y:,.0f}<extra></extra>',
        ))
        layout = BASE_LAYOUT.copy()
        layout.update(dict(
            title=dict(text=title, font=dict(color='#f0f4f9', size=15)),
            xaxis=dict(**AXIS_STYLE, title=xaxis_title),
            yaxis=dict(**AXIS_STYLE, title=yaxis_title),
        ))
    fig.update_layout(**layout)
    return fig


def grouped_bar(categories, series_dict, title) -> go.Figure:
    """Grouped bar chart for stacked breakdowns like ABC health."""
    color_list = [COLORS['success'], COLORS['warning'], COLORS['danger'], COLORS['primary']]
    fig = go.Figure()
    for i, (name, vals) in enumerate(series_dict.items()):
        fig.add_trace(go.Bar(
            name=name, x=categories, y=vals,
            marker_color=color_list[i % len(color_list)],
            text=[f'{v}' for v in vals],
            textposition='inside',
            insidetextfont=dict(color='white', size=11),
        ))
    layout = BASE_LAYOUT.copy()
    layout.update(dict(
        title=dict(text=title, font=dict(color='#f0f4f9', size=15)),
        barmode='stack',
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, title='Number of Materials'),
    ))
    fig.update_layout(**layout)
    return fig
