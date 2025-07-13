import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
from scipy.stats import linregress
from typing import Optional, List

from src.process.relative_strength import get_relative_strength
from src.process.rs_momentum import get_relative_strength_momentum
from config.helper import get_sector_config
config = get_sector_config()



pio.renderers.default = "browser"

def plot_relative_strength(target: str, benchmark: str = config['benchmark'], lookback_days: Optional[int] = 30, normalize: bool = True, save_path: Optional[str] = None) -> None:    
    rs_series = get_relative_strength(target, benchmark, lookback_days=lookback_days, normalize=normalize)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rs_series.index,
        y=rs_series.values,
        mode='lines',
        name=rs_series.name,
        line=dict(width=2)
    ))

    if normalize:
        fig.add_hline(
            y=1.0,
            line=dict(color='black', width=2, dash='dash'),
            annotation_text='Baseline',
            annotation_position='top left'
        )

    fig.update_layout(
        title=f"Relative Strength: {target} vs {benchmark}" + (" (Normalized)" if normalize else ""),
        xaxis_title="Date",
        yaxis_title="Relative Strength",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        template="plotly_white",
        height=500,
        width=900
    )

    if save_path:
        fig.write_image(save_path)
        print(f"Plot saved to {save_path}")
    else:
        fig.show()

def plot_sector_relative_strength(tickers: Optional[List[str]] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days: Optional[int] = 30, normalize: bool = True):
    all_rs = {}

    for ticker in tickers:
        if ticker == benchmark:
            continue
        rs = get_relative_strength(ticker, benchmark, lookback_days, normalize)
        all_rs[ticker] = rs

    # Build figure
    fig = go.Figure()

    for ticker, series in all_rs.items():
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            mode='lines',
            name=ticker
        ))

    # Add 1.0 baseline line (normalized view only)
    if normalize:
        fig.add_shape(
            type='line',
            x0=min(series.index),
            x1=max(series.index),
            y0=1.0,
            y1=1.0,
            line=dict(color='black', width=2, dash='dash'),
        )

    fig.update_layout(
        title=f"Relative Strength vs {benchmark} (Last {lookback_days} Days)",
        xaxis_title="Date",
        yaxis_title="Relative Strength" + (" (Normalized)" if normalize else ""),
        hovermode="x unified",
        legend_title="Sector ETF",
        template="plotly_white",
        width=1000,
        height=600,
    )

    fig.show()

def plot_relative_strength_momentum(target: str, benchmark: str = config['benchmark'], lookback_days: int = 30, momentum_window: int = 5, normalize: bool = True, save_path: Optional[str] = None) -> None:
    rs_series = get_relative_strength(
        target, benchmark, lookback_days=lookback_days, normalize=normalize
    )

    # Trim to momentum window
    rs_series = rs_series.tail(momentum_window)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rs_series.index,
        y=rs_series.values,
        mode='lines+markers',
        name=f"{target} vs {benchmark}"
    ))

    fig.update_layout(
        title=f"RS Momentum: {target} vs {benchmark} (Timeframe: {lookback_days}days, Window: {momentum_window}, Normalized: {normalize})",
        xaxis_title="Date",
        yaxis_title="Relative Strength",
        template="plotly_white",
        width=900,
        height=500
    )

    if save_path:
        fig.write_image(save_path)
        print(f"Plot saved to {save_path}")
    else:
        fig.show()

def plot_sector_relative_strength_momentum(tickers: Optional[List[str]] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days: int = 30, momentum_window: int = 5, normalize: bool = True):
    momentum_scores = {}

    for ticker in tickers:
        if ticker == benchmark:
            continue
        try:
            score = get_relative_strength_momentum(
                target=ticker,
                benchmark=benchmark,
                lookback_days=lookback_days,
                momentum_window=momentum_window,
                normalize=normalize
            )
            momentum_scores[ticker] = score
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    df = pd.DataFrame.from_dict(momentum_scores, orient='index', columns=['Momentum'])
    df.sort_values(by='Momentum', ascending=True, inplace=True)  # Sort for bar order

    fig = go.Figure(go.Bar(
        x=df['Momentum'],
        y=df.index,
        orientation='h',
        marker=dict(color='steelblue'),
    ))

    fig.update_layout(
        title=f"Relative Strength Momentum (vs {benchmark}) (Timeframe: {lookback_days}days, Window: {momentum_window}, Normalized: {normalize})",
        xaxis_title="Momentum Score",
        yaxis_title="Sector ETF",
        template="plotly_white",
        height=500,
        width=800
    )

    fig.show()

def plot_rrg(tickers: Optional[List[str]] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days=30, momentum_window=5, normalize=True):
    colors = px.colors.qualitative.Plotly
    traces = []
    color_map = {}

    all_x, all_y = [], []

    for i, ticker in enumerate(tickers):
        if ticker == benchmark:
            continue

        try:
            rs_series = get_relative_strength(ticker, benchmark, lookback_days, normalize)
            color = colors[i % len(colors)]
            color_map[ticker] = color
            
            # Only use the last momentum_window + 1 points to construct tail
            tail_rs_series = rs_series.tail(momentum_window + 1)

            # Make sure we have enough data
            if len(tail_rs_series) < momentum_window + 1:
                continue

            # Initialize lists
            tail_x, tail_y = [], []

            # Loop to create each tail point (1 less than full tail window)
            # Use existing momentum function instead
            for t in range(momentum_window):
                sub_rs_series = tail_rs_series.iloc[t:t + momentum_window + 1]
                if len(sub_rs_series) < momentum_window + 1:
                    continue

                slope = get_relative_strength_momentum(
                    target=ticker,
                    benchmark=benchmark,
                    lookback_days=lookback_days - (momentum_window - t),  # adjust lookback
                    momentum_window=momentum_window,
                    normalize=normalize
                )

                rs_val = sub_rs_series.iloc[-1]
                tail_x.append(slope)
                tail_y.append(rs_val)


            # Store for axis limits
            all_x.extend(tail_x)
            all_y.extend(tail_y)

            # Tail points (lighter, smaller)
            traces.append(go.Scatter(
                x=tail_x[:-1],
                y=tail_y[:-1],
                mode='markers',
                marker=dict(size=6, color=color, opacity=0.5, line=dict(width=0)),
                name=f"{ticker} trail",
                showlegend=False,
                hoverinfo='skip'
            ))

            # Most recent (main) point
            traces.append(go.Scatter(
                x=[tail_x[-1]],
                y=[tail_y[-1]],
                mode='markers+text',
                marker=dict(size=14, color=color, line=dict(width=1, color='black')),
                text=[ticker],
                textposition="top center",
                name=ticker
            ))
            
            traces.append(go.Scatter(
                x=tail_x,
                y=tail_y,
                mode='lines',
                line=dict(color=color, width=2, dash='dot'),
                name=f"{ticker} path",
                showlegend=False,
                hoverinfo='skip'
            ))

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    x_min, x_max = min(all_x) - 0.01, max(all_x) + 0.01
    y_min, y_max = min(all_y) - 0.01, max(all_y) + 0.01

    fig = go.Figure(traces)

    # Add quadrant fills
    fig.add_shape(type="rect", x0=x_min, x1=0, y0=y_min, y1=1,
                  fillcolor="rgba(255, 0, 0, 0.1)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=x_max, y0=y_min, y1=1,
                  fillcolor="rgba(255, 255, 0, 0.1)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=x_min, x1=0, y0=1, y1=y_max,
                  fillcolor="rgba(0, 0, 255, 0.1)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=x_max, y0=1, y1=y_max,
                  fillcolor="rgba(0, 255, 0, 0.1)", layer="below", line_width=0)

    # Crosshairs at (0, 1)
    fig.add_shape(type="line", x0=x_min, x1=x_max, y0=1.0, y1=1.0,
                  line=dict(color="black", width=1.5, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=0, y0=y_min, y1=y_max,
                  line=dict(color="black", width=1.5, dash="dot"))

    fig.update_layout(
        title=f"Relative Rotation Graph (RRG) with Tails (vs {benchmark})",
        xaxis_title="RS Momentum",
        yaxis_title="Relative Strength",
        template="plotly_white",
        width=950,
        height=650,
        xaxis=dict(range=[x_min, x_max]),
        yaxis=dict(range=[y_min, y_max])
    )

    fig.show()