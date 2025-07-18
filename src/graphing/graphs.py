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
        template="plotly_white",
        height=500,
        width=900
    )

    if save_path:
        fig.write_image(save_path)
        print(f"Plot saved to {save_path}")
    else:
        fig.show()

def plot_sector_relative_strength(tickers: Optional[List[str]] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days: Optional[int] = 30, normalize: bool = True, timeframe: str = 'daily'):
    
    if timeframe not in ['daily','weekly', 'monthly']:
        raise ValueError("freq must be 'daily', 'weekly', or 'monthly'")
    
    all_rs = {}

    for ticker in tickers:
        if ticker == benchmark:
            update_data(ticker)
            continue
        rs = get_relative_strength(ticker, benchmark, lookback_days, normalize, timeframe=timeframe)
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

    chartinterval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]

    fig.update_layout(
        title=f"Relative Strength vs {benchmark} (Last {lookback_days} {chartinterval})",
        xaxis_title="Date",
        yaxis_title="Relative Strength" + (" (Normalized)" if normalize else ""),
        hovermode="x unified",
        legend_title="Sector ETF",
        template="plotly_white",
        width=1000,
        height=600,
    )

    fig.show()

def plot_relative_strength_momentum(target: str, benchmark: str = config['benchmark'], lookback_days: int = 30, momentum_window: int = 5, normalize: bool = True, save_path: Optional[str] = None, timeframe: str = 'daily') -> None:
    
    if timeframe not in ['daily','weekly', 'monthly']:
        raise ValueError("freq must be 'daily', 'weekly', or 'monthly'")
    
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
        template="plotly_white",
        width=900,
        height=500
    )

    if save_path:
        fig.write_image(save_path)
        print(f"Plot saved to {save_path}")
    else:
        fig.show()

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
        x=df['Momentum'],
        y=df.index,
        orientation='h',
        marker=dict(color='steelblue'),
    ))

    chartinterval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]

    fig.update_layout(
        title=f"Relative Strength Momentum (vs {benchmark}) (Timeframe: {lookback_days} {chartinterval}, Window: {momentum_window}, Normalized: {normalize})",
        xaxis_title="Momentum Score",
        yaxis_title="Sector ETF",
        template="plotly_white",
        height=500,
        width=800
    )

    fig.show()

def plot_rrg(tickers: Optional[List[str]] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days=30, momentum_window=5, normalize=True, timeframe: str = 'daily'):
    if timeframe not in ['daily','weekly', 'monthly']:
        raise ValueError("freq must be 'daily', 'weekly', or 'monthly'")
    
    colors = px.colors.qualitative.Dark24
    traces = []
    all_x, all_y = [], []

    for i, ticker in enumerate(tickers):
        if ticker == benchmark:
            update_data(ticker)
            continue

        try:
            rs_series = get_relative_strength(ticker, benchmark, lookback_days, normalize)
            if len(rs_series) < momentum_window + 1:
                continue

            color = colors[i % len(colors)]

            # Get RS momentum and relative strength values
            tail_x = get_relative_strength_momentum(
                target=ticker,
                benchmark=benchmark,
                lookback_days=lookback_days,
                momentum_window=momentum_window,
                normalize=normalize,
                return_series=True,
                timeframe=timeframe
            )
            tail_y = rs_series.tail(len(tail_x)).tolist()
            
            tail_x = tail_x[-momentum_window:]
            tail_y = tail_y[-momentum_window:]

            if len(tail_x) != len(tail_y):
                print(f"Skipping {ticker} due to length mismatch.")
                continue

            all_x.extend(tail_x)
            all_y.extend(tail_y)

            traces.append(go.Scatter(
                x=tail_x,
                y=tail_y,
                mode='lines+markers',
                line=dict(shape='spline', color=color, width=4),
                marker=dict(size=6, color='white', opacity=1, line=dict(color=color, width=2)),
                name=ticker,
                legendgroup=ticker,
                showlegend=False
            ))
            
            # Trail points
            traces.append(go.Scatter(
                x=tail_x[:-1],
                y=tail_y[:-1],
                mode='markers',
                marker=dict(size=8, color='white', opacity=1, line=dict(color=color, width=5)),
                name=ticker,  # Use same name
                legendgroup=ticker,  # Group them
                showlegend=False
            ))

            # --- Latest head point on top of everything ---
            traces.append(go.Scatter(
                x=[tail_x[-1]],
                y=[tail_y[-1]],
                mode='markers+text',
                marker=dict(size=16, color=color, line=dict(width=1.5, color='black')),
                text=[ticker],
                textposition="top center",
                name=ticker,
                legendgroup=ticker,
            ))
                                    
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    # Calculate padding
    x_range = max(all_x) - min(all_x)
    y_range = max(all_y) - min(all_y)

    x_pad = x_range * 0.2
    y_pad = y_range * 0.2

    x_min, x_max = min(all_x) - x_pad, max(all_x) + x_pad
    y_min, y_max = min(all_y) - y_pad, max(all_y) + y_pad
    
    fig = go.Figure(traces)

    # Quadrants
    fig.add_shape(type="rect", x0=x_min, x1=0, y0=y_min, y1=1, fillcolor="rgba(255, 0, 0, 0.1)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=x_max, y0=y_min, y1=1, fillcolor="rgba(255, 255, 0, 0.1)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=x_min, x1=0, y0=1, y1=y_max, fillcolor="rgba(0, 0, 255, 0.1)", layer="below", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=x_max, y0=1, y1=y_max, fillcolor="rgba(0, 255, 0, 0.1)", layer="below", line_width=0)

    # Crosshairs
    fig.add_shape(type="line", x0=x_min, x1=x_max, y0=1.0, y1=1.0, line=dict(color="black", width=1.5, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=0, y0=y_min, y1=y_max, line=dict(color="black", width=1.5, dash="dot"))

    chartinterval = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months'}[timeframe]
    
    # Layout
    fig.update_layout(
        title=f"Relative Rotation Graph (RRG) with Tails (vs {benchmark} \n ({lookback_days} {chartinterval} back with {momentum_window} {chartinterval} window))",
        xaxis_title="RS Momentum",
        yaxis_title="Relative Strength",
        template="plotly_white",
        width=1425,
        height=975,
        xaxis=dict(range=[x_min, x_max]),
        yaxis=dict(range=[y_min, y_max])
    )

    fig.show()

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
    return fig

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
    return fig


def plot_volatility_heatmap(
    tickers: Optional[List[str]] = None,
    window: int = 20,
    show: bool = True,
    save_path: Optional[str] = None,
    color_scale: str = 'RdBu',
    zmin: Optional[float] = None,
    zmax: Optional[float] = None,
    raw_volatility: bool = False,
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
    vol_df = get_volatility_data(tickers=tickers, window=window, raw_volatility=raw_volatility, **kwargs)
    
    # Choose which columns to plot based on raw_volatility parameter
    if raw_volatility:
        timeframes = ['DailyVol', 'WeeklyVol', 'MonthlyVol']
        timeframe_names = ['Daily Volatility', 'Weekly Volatility', 'Monthly Volatility']
        value_type = "Annualized Volatility"
    else:
        timeframes = ['DailyZVol', 'WeeklyZVol', 'MonthlyZVol']
        timeframe_names = ['Daily Z-Score', 'Weekly Z-Score', 'Monthly Z-Score']
        value_type = "Z-Score"
    
    figs = []
    
    for tf, tf_name in zip(timeframes, timeframe_names):
        if tf not in vol_df.columns:
            continue
            
        # Prepare data for heatmap
        tf_data = vol_df[tf].dropna()
        
        # Create heatmap data - reshape for single column heatmap
        heatmap_data = tf_data.to_numpy().reshape(-1, 1)
        ticker_labels = tf_data.index.tolist()
        
        # Create heatmap
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
            title=f"{tf_name} (Window: {window})",
            width=400,
            height=600,
            template="plotly_white"
        )
        
        # Update colorbar
        fig.update_coloraxes(
            colorbar=dict(
                title=value_type,
            )
        )
        
        if save_path:
            # Create filename with timeframe
            base_path = save_path.replace('.png', '').replace('.jpg', '').replace('.html', '')
            tf_save_path = f"{base_path}_{tf_name.lower().replace(' ', '_')}.png"
            fig.write_image(tf_save_path)
            print(f"Volatility heatmap saved to {tf_save_path}")
        
        if show:
            fig.show()
        
        figs.append(fig)
    
    return figs