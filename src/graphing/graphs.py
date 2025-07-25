import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
from typing import Optional, List

from src.process.relative_strength import get_relative_strength
from src.process.rs_momentum import get_relative_strength_momentum
from src.process.lead_lag import sector_lead_lag_matrix, granger_lead_lag_matrix
from src.process.volatility import get_volatility_data
from config.helper import get_sector_config, get_resource
from src.fetch.update_data import update_data
config = get_sector_config()



pio.renderers.default = "browser"

def plot_relative_strength(target: str, benchmark: str = config['benchmark'], lookback_days: Optional[int] = 30, normalize: bool = True, save_path: Optional[str] = None, timeframe: str = 'daily') -> None:    
    
    if timeframe not in ['daily','weekly', 'monthly']:
        raise ValueError("freq must be 'daily', 'weekly', or 'monthly'")
    
    rs_series = get_relative_strength(target, benchmark, lookback_days=lookback_days, normalize=normalize, timeframe=timeframe)

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

    chartinterval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]

    fig.update_layout(
        title=f"Relative Strength: {target} vs {benchmark}" + (f" over {lookback_days} {chartinterval}" if lookback_days else "") + (" (Normalized)" if normalize else ""),
        xaxis_title="Date",
        yaxis_title="Relative Strength",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        template="plotly_dark",
        plot_bgcolor="#26282C",
        paper_bgcolor="#26282C",
        font=dict(color="#EBEBEB"),
        autosize=True,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    if save_path:
        fig.write_image(save_path)
        print(f"Plot saved to {save_path}")
    else:
        return fig.to_html(include_plotlyjs='cdn')

def plot_sector_relative_strength(tickers: Optional[List[str]] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days: int = 30, normalize: bool = True, timeframe: str = 'daily'):
    
    colors = px.colors.qualitative.Dark24
    
    if timeframe not in ['daily', 'weekly', 'monthly']:
        raise ValueError("freq must be 'daily', 'weekly', or 'monthly'")
    
    all_rs = {}

    for ticker in tickers:
        if ticker == benchmark:
            update_data(ticker)
            continue
        try:
            rs = get_relative_strength(ticker, benchmark, lookback_days, normalize, timeframe=timeframe)
            all_rs[ticker] = rs
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

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
            line=dict(color='white', width=2, dash='dash'),
        )

    chartinterval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]

    fig.update_layout(
        title=f"Relative Strength vs {benchmark} (Last {lookback_days} {chartinterval})",
        xaxis_title="Date",
        yaxis_title="Relative Strength" + (" (Normalized)" if normalize else ""),
        hovermode="x unified",
        legend_title="Sector ETF",
        template="plotly_dark",
        plot_bgcolor="#26282C",
        paper_bgcolor="#26282C",
        font=dict(color="#EBEBEB"),
        autosize=True,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    return fig.to_html(include_plotlyjs='cdn')

def plot_relative_strength_momentum(target: str, benchmark: str = config['benchmark'], lookback_days: int = 30, momentum_window: int = 5, normalize: bool = True, save_path: Optional[str] = None, timeframe: str = 'daily') -> None:
    
    if timeframe not in ['daily','weekly', 'monthly']:
        raise ValueError("freq must be 'daily', 'weekly', or 'monthly'")
    
    colors = px.colors.qualitative.Dark24

    rs_series = get_relative_strength(target, benchmark, lookback_days=lookback_days, normalize=normalize, timeframe=timeframe)

    # Trim to momentum window
    rs_series = rs_series.tail(momentum_window)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rs_series.index,
        y=rs_series.values,
        mode='lines+markers',
        name=f"{target} vs {benchmark}"
    ))

    chartinterval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]

    fig.update_layout(
        title=f"RS Momentum: {target} vs {benchmark} (Timeframe: {lookback_days} {chartinterval}, Window: {momentum_window}, Normalized: {normalize})",
        xaxis_title="Date",
        yaxis_title="Relative Strength",
        template="plotly_dark",
        plot_bgcolor="#26282C",
        paper_bgcolor="#26282C",
        font=dict(color="#EBEBEB"),
        autosize=True,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    if save_path:
        fig.write_image(save_path)
        print(f"Plot saved to {save_path}")
    else:
        return fig.to_html(include_plotlyjs='cdn')

def plot_sector_relative_strength_momentum(tickers: Optional[List[str]] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days: int = 30, momentum_window: int = 5, normalize: bool = True, timeframe: str = 'daily'):
    
    if timeframe not in ['daily','weekly', 'monthly']:
        raise ValueError("freq must be 'daily', 'weekly', or 'monthly'")
    
    momentum_scores = {}

    for ticker in tickers:
        if ticker == benchmark:
            update_data(ticker)
            continue
        try:
            score = get_relative_strength_momentum(
                target=ticker,
                benchmark=benchmark,
                lookback_days=lookback_days,
                momentum_window=momentum_window,
                normalize=normalize,
                timeframe=timeframe
            )
            momentum_scores[ticker] = score
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    df = pd.DataFrame.from_dict(momentum_scores, orient='index', columns=['Momentum'])
    df.sort_values(by='Momentum', ascending=True, inplace=True)  # Sort for bar order

    fig = go.Figure(go.Bar(
        x=df.index,
        y=df['Momentum'],
        marker=dict(color='steelblue'),
    ))

    chartinterval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]

    fig.update_layout(
        title=f"Relative Strength Momentum (vs {benchmark}) ({lookback_days} {chartinterval} back, {momentum_window} {chartinterval} window)",
        xaxis_title="Momentum Score",
        yaxis_title="Sector ETF",
        template="plotly_dark",
        plot_bgcolor="#26282C",
        paper_bgcolor="#26282C",
        font=dict(color="#EBEBEB"),
        autosize=True,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    return fig.to_html(include_plotlyjs='cdn')

def plot_rrg(
    tickers: Optional[List[str]] = config['sector_etfs'],
    benchmark: str = config['benchmark'],
    lookback_days: int = 30,
    momentum_window: int = 5,
    normalize: bool = True,
    timeframe: str = 'daily'
):
    if timeframe not in ['daily', 'weekly', 'monthly']:
        raise ValueError("timeframe must be 'daily', 'weekly', or 'monthly'")

    # Update benchmark data once
    update_data(benchmark)

    colors = px.colors.qualitative.Light24
    traces = []
    all_x, all_y = [], []

    total_lookback = lookback_days + momentum_window

    for i, ticker in enumerate(tickers):
        if ticker == benchmark:
            continue

        try:
            # Fetch target data
            update_data(ticker)

            # 1) RS series
            rs = get_relative_strength(
                target=ticker,
                benchmark=benchmark,
                lookback_days=total_lookback,
                normalize=normalize,
                timeframe=timeframe
            )

            # 2) Raw momentum list
            raw_mom = get_relative_strength_momentum(
                target=ticker,
                benchmark=benchmark,
                lookback_days=total_lookback,
                momentum_window=momentum_window,
                normalize=normalize,
                method='slope',
                return_series=True,
                timeframe=timeframe
            )

            # 3) Align momentum as Series indexed to rs (momentum starts at index shift)
            # momentum length should be len(rs) - momentum_window + 1
            start_idx = momentum_window - 1
            mom = pd.Series(raw_mom, index=rs.index[start_idx:])

            # Ensure counts match
            if len(rs) < momentum_window + 1 or len(mom) != len(rs) - momentum_window + 1:
                continue

            # 4) Extract tails (last momentum_window points)
            tail_rs  = rs.iloc[-momentum_window:].to_numpy()
            tail_mom = mom.iloc[-momentum_window:].to_numpy()

            # Collect all for axis scaling
            all_x.extend(tail_rs)
            all_y.extend(tail_mom)
            color = colors[i % len(colors)]

            # 5a) Line+markers trace (no text)
            traces.append(go.Scatter(
                x=tail_rs,
                y=tail_mom,
                mode='lines+markers',
                line=dict(shape='spline', color=color, width=4),
                marker=dict(size=8, color='white', line=dict(color=color, width=2)),
                name=ticker,
                legendgroup=ticker,
                showlegend=False
            ))

            # 5b) Final point with label
            traces.append(go.Scatter(
                x=[tail_rs[-1]],
                y=[tail_mom[-1]],
                mode='markers+text',
                marker=dict(size=16, color=color, line=dict(width=1.5, color='black')),
                text=[ticker],
                textposition='top center',
                name=ticker,
                legendgroup=ticker,
                showlegend=True
            ))

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    if not all_x or not all_y:
        print("No data available for RRG plot.")
        return '<p>No data available for RRG plot. Please check data availability.</p>'

    # Axis padding
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    x_pad = (x_max - x_min) * 0.2
    y_pad = (y_max - y_min) * 0.2

    fig = go.Figure(traces)

    # Quadrants at RS=1.0, Momentum=0.0
    fig.add_shape(type='rect', x0=x_min - x_pad, x1=1.0, y0=y_min - y_pad, y1=0.0,
                  fillcolor='rgba(255,0,0,0.1)', layer='below', line_width=0)
    fig.add_shape(type='rect', x0=1.0, x1=x_max + x_pad, y0=y_min - y_pad, y1=0.0,
                  fillcolor='rgba(255,255,0,0.1)', layer='below', line_width=0)
    fig.add_shape(type='rect', x0=x_min - x_pad, x1=1.0, y0=0.0, y1=y_max + y_pad,
                  fillcolor='rgba(0,0,255,0.1)', layer='below', line_width=0)
    fig.add_shape(type='rect', x0=1.0, x1=x_max + x_pad, y0=0.0, y1=y_max + y_pad,
                  fillcolor='rgba(0,255,0,0.1)', layer='below', line_width=0)
    fig.add_shape(type='line', x0=x_min - x_pad, x1=x_max + x_pad, y0=0.0, y1=0.0,
                  line=dict(color='white', width=1.5, dash='dot'))
    fig.add_shape(type='line', x0=1.0, x1=1.0, y0=y_min - y_pad, y1=y_max + y_pad,
                  line=dict(color='white', width=1.5, dash='dot'))

    interval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]
    fig.update_layout(
        title=(f"Relative Rotation Graph (RRG) vs {benchmark}: "
               f"{lookback_days} {interval} lookback, {momentum_window} {interval} tail"),
        xaxis=dict(title='RS Ratio', range=[x_min - x_pad, x_max + x_pad]),
        yaxis=dict(title='RS Momentum', range=[y_min - y_pad, y_max + y_pad]),
        template='plotly_dark',
        plot_bgcolor='#26282C', paper_bgcolor='#26282C',
        font=dict(color='#EBEBEB'),
        margin=dict(l=40, r=40, t=80, b=40)
    )

    return fig.to_html(include_plotlyjs='cdn')


def plot_sector_lead_lag_matrix(
    sectors: Optional[List[str]] = None,
    timeframe: str = 'daily',
    max_lag: int = 10,
    show: bool = True,
    save_path: Optional[str] = None,
    color_scale: str = 'RdBu',
    zmin: Optional[int] = None,
    zmax: Optional[int] = None,
    **kwargs
):
    """
    Plot a heatmap of the cross-correlation lead-lag matrix for the given sectors.
    """
    if sectors is None:
        sectors = list(config['sector_etfs'])
    lag_matrix = sector_lead_lag_matrix(sectors=sectors, timeframe=timeframe, max_lag=max_lag, **kwargs)
    lag_matrix = lag_matrix.astype(float)
    if zmin is None:
        zmin = -max_lag
    if zmax is None:
        zmax = max_lag
    title = f"Sector Cross-Correlation Lead-Lag Matrix (Timeframe: {timeframe}, Max Lag: {max_lag})"
    fig = px.imshow(
        lag_matrix,
        x=lag_matrix.columns,
        y=lag_matrix.index,
        color_continuous_scale=color_scale,
        zmin=zmin,
        zmax=zmax,
        labels=dict(x="Laggard", y="Leader", color="Lag (periods)")
    )
    fig.update_layout(title=title, width=900, height=800)
    if save_path:
        fig.write_image(save_path)
    if show:
        fig.show()
    return fig.to_html(include_plotlyjs='cdn')

def plot_granger_lead_lag_matrix(
    sectors: Optional[List[str]] = None,
    timeframe: str = 'daily',
    max_lag: int = 10,
    test: str = 'ssr_chi2test',
    plot: str = 'pvalue',  # 'pvalue' or 'lag'
    alpha: float = 0.05,
    mask_nonsignificant: bool = False,
    title: Optional[str] = None,
    show: bool = True,
    save_path: Optional[str] = None,
    color_scale: str = 'Viridis',
    zmin: Optional[float] = None,
    zmax: Optional[float] = None,
    **kwargs
):
    """
    Plot a heatmap of the Granger causality lead-lag matrix for the given sectors.
    """
    if sectors is None:
        sectors = list(config['sector_etfs'])
    granger_matrix = granger_lead_lag_matrix(sectors=sectors, timeframe=timeframe, max_lag=max_lag, test=test, **kwargs)
    if plot == 'pvalue':
        data = granger_matrix.map(lambda x: x[0] if isinstance(x, tuple) else np.nan).astype(float)
        if mask_nonsignificant:
            data = data.where(data <= alpha)
        if zmin is None:
            zmin = 0
        if zmax is None:
            zmax = 1
        colorbar_label = f"Min p-value ({test})"
        if not title:
            title = f"Granger Causality Min p-value Matrix (Timeframe: {timeframe}, Max Lag: {max_lag})"
    elif plot == 'lag':
        data = granger_matrix.applymap(lambda x: x[1] if isinstance(x, tuple) else np.nan).astype(float)
        if mask_nonsignificant:
            pvals = granger_matrix.applymap(lambda x: x[0] if isinstance(x, tuple) else np.nan).astype(float)
            data = data.where(pvals <= alpha)
        if zmin is None:
            zmin = 1
        if zmax is None:
            zmax = max_lag
        colorbar_label = f"Best Lag (periods)"
        if not title:
            title = f"Granger Causality Best Lag Matrix (Timeframe: {timeframe}, Max Lag: {max_lag})"
    else:
        raise ValueError("plot must be 'pvalue' or 'lag'")
    fig = px.imshow(
        data,
        x=data.columns,
        y=data.index,
        color_continuous_scale=color_scale,
        zmin=zmin,
        zmax=zmax,
        labels=dict(x="Laggard", y="Leader", color=colorbar_label)
    )
    fig.update_layout(title=title, width=900, height=800)
    if save_path:
        fig.write_image(save_path)
    if show:
        fig.show()
    return fig.to_html(include_plotlyjs='cdn')


def plot_volatility_heatmap(
    tickers: Optional[List[str]] = None,
    timeframe: str = 'daily',
    lookback_days: int = 20,
    show: bool = False,
    save_path: Optional[str] = None,
    color_scale: str = 'RdBu',
    zmin: Optional[float] = None,
    zmax: Optional[float] = None,
    normalize: bool = False,
    **kwargs
):
    """
    Plot heatmaps of volatility across daily, weekly, and monthly timeframes.
    
    Args:
        tickers: List of ticker symbols
        window: Rolling window for volatility calculation
        show: Whether to display the plots
        save_path: Path to save the plots
        color_scale: Color scale for the heatmap
        zmin, zmax: Min/max values for color scale
        raw_volatility: If True, plot raw annualized volatility; if False, plot z-scores (default: False)
        **kwargs: Additional arguments passed to get_volatility_data
    """
    if tickers is None:
        tickers = list(config['sector_etfs'])
    vol_df = get_volatility_data(tickers=tickers, timeframe=timeframe, window=lookback_days, raw_volatility=normalize, **kwargs)
    
    col_name = f"{timeframe.capitalize()}Vol" if normalize else f"{timeframe.capitalize()}ZVol"
    value_type = "Annualized Volatility" if normalize else "Z-Score"
    title = f"{timeframe} {'Volatility' if normalize else 'Z-Score'} (lookback: {lookback_days})"

    tf_data = vol_df[col_name].dropna()

    if tf_data.empty:
        print(f"No data available for timeframe: {timeframe}")
        return None
    
    tf_data = vol_df[col_name].dropna().sort_values(ascending=False)

    # Create heatmap
    heatmap_data = tf_data.to_numpy().reshape(-1, 1)
    ticker_labels = tf_data.index.tolist()

    import plotly.express as px
    fig = px.imshow(
        heatmap_data,
        x=[value_type],
        y=ticker_labels,
        color_continuous_scale=color_scale,
        zmin=zmin,
        zmax=zmax,
        labels=dict(x="", y="Ticker", color=value_type),
        aspect="auto"
    )

    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="#26282C",
        paper_bgcolor="#26282C",
        font=dict(color="#EBEBEB"),
        autosize=True,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    if save_path:
        base_path = save_path.replace('.png', '').replace('.jpg', '').replace('.html', '')
        tf_save_path = f"{base_path}_{timeframe}_{'vol' if normalize else 'zvol'}.png"
        fig.write_image(tf_save_path)
        print(f"Volatility heatmap saved to {tf_save_path}")

    if show:
        fig.show()

    return fig.to_html(include_plotlyjs='cdn')