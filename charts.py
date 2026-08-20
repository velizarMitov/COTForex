"""Plotly chart builders for the COT vs Price dashboard.

Design goals
------------
* Panels that are meant to be compared share one symmetric scale and one
  visual language (filled area, green above zero / red below).
* Raw Net OI% is kept as the primary metric, with historical extreme zones
  (P90 / P10) shaded so "crowded" is visible without reading numbers.
* One dark theme, one x-axis config, applied everywhere.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------
# Theme
# --------------------------------------------------------------------------
BG = "#0E1117"          # matches Streamlit dark background
GRID = "rgba(148,163,184,0.13)"
FG = "#E6EDF3"
MUTED = "rgba(230,237,243,0.55)"

POS = "#22C55E"
NEG = "#EF4444"
GOLD = "#F5C518"
BLUE = "#3B82F6"
VIOLET = "#A78BFA"

# Pass this to st.plotly_chart(fig, config=PLOTLY_CONFIG)
PLOTLY_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "doubleClick": "reset",
    "modeBarButtonsToAdd": [
        "drawline",
        "drawopenpath",
        "drawrect",
        "eraseshape",
    ],
}


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _theme(fig: go.Figure, height: int, title: str, unified: bool = True) -> go.Figure:
    """Single place where global look & feel is defined."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=FG, size=12),
        title=dict(
            text=f"<b>{title}</b>",
            x=0.005,
            xanchor="left",
            y=0.985,
            yanchor="top",
            font=dict(size=18, color=FG),
        ),
        height=height,
        margin=dict(l=64, r=28, t=104, b=48),
        hovermode="x unified" if unified else "closest",
        hoverdistance=100,
        spikedistance=-1,
        showlegend=False,
        bargap=0.02,
        hoverlabel=dict(bgcolor="rgba(17,24,39,0.92)", bordercolor=MUTED, font_size=12),
        dragmode="pan",
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor="rgba(148,163,184,0.25)",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor="rgba(148,163,184,0.25)",
        title_font=dict(size=11, color=MUTED),
        tickfont=dict(size=11),
    )

    # Subplot titles: left aligned, smaller, muted.
    for ann in fig.layout.annotations:
        if ann.text and ann.yref == "paper":
            ann.font.size = 12.5
            ann.font.color = FG
            ann.xanchor = "left"
            ann.x = 0.004
    return fig


def _x_axis_kwargs(date_density: str = "Auto", spikes: bool = True) -> dict:
    kwargs = {
        "type": "date",
        "hoverformat": "%Y-%m-%d",
        "showgrid": True,
        "gridcolor": GRID,
    }
    if spikes:
        kwargs.update(
            {
                "showspikes": True,
                "spikemode": "across",
                "spikesnap": "cursor",
                "spikecolor": "rgba(230,237,243,0.5)",
                "spikethickness": 1,
                "spikedash": "dot",
            }
        )

    if date_density == "1 Year":
        kwargs.update({"dtick": "M12", "tickformat": "%Y", "tickmode": "linear"})
    elif date_density == "2 Years":
        kwargs.update({"dtick": "M24", "tickformat": "%Y", "tickmode": "linear"})
    elif date_density == "Quarterly":
        kwargs.update({"dtick": "M3", "tickformat": "Q%q %Y", "tickmode": "linear"})
    elif date_density == "Monthly":
        kwargs.update({"dtick": "M1", "tickformat": "%b %Y", "tickmode": "linear"})
    else:
        kwargs.update({"nticks": 20, "tickmode": "auto"})

    return kwargs


def _range_selector() -> dict:
    """Quick zoom presets - 20 years in one frame is unreadable otherwise."""
    return dict(
        buttons=[
            dict(count=1, label="1Y", step="year", stepmode="backward"),
            dict(count=3, label="3Y", step="year", stepmode="backward"),
            dict(count=5, label="5Y", step="year", stepmode="backward"),
            dict(count=10, label="10Y", step="year", stepmode="backward"),
            dict(step="all", label="All"),
        ],
        bgcolor="rgba(30,41,59,0.92)",
        activecolor="rgba(59,130,246,0.9)",
        bordercolor="rgba(148,163,184,0.3)",
        borderwidth=1,
        font=dict(color=FG, size=11),
        # Right aligned: subplot titles are left aligned, so this avoids the
        # buttons landing on top of the row-1 title.
        x=1,
        xanchor="right",
        y=1.02,
        yanchor="bottom",
    )


def apply_shared_crosshair(fig: go.Figure) -> go.Figure:
    """Adds a unified vertical crosshair that spans across all stacked subplots."""
    try:
        fig.update_layout(hoversubplots="axis")
    except Exception:
        pass
    return fig


# --------------------------------------------------------------------------
# Reusable trace / annotation helpers
# --------------------------------------------------------------------------
def _add_split_area(
    fig: go.Figure,
    x,
    y,
    row: int,
    name: str,
    hover_suffix: str = "%",
    pos_color: str = POS,
    neg_color: str = NEG,
    alpha: float = 0.55,
    outline: float = 1.1,
) -> None:
    """Green above zero, red below, as a filled area.

    At 1000+ weekly points bar traces collapse into 1px slivers; a filled
    area keeps the shape readable at every zoom level.
    """
    y = np.asarray(y, dtype=float)
    y_pos = np.where(np.isnan(y), np.nan, np.where(y > 0, y, 0.0))
    y_neg = np.where(np.isnan(y), np.nan, np.where(y < 0, y, 0.0))

    for series, color in ((y_pos, pos_color), (y_neg, neg_color)):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=series,
                mode="lines",
                line=dict(width=0),
                fill="tozeroy",
                fillcolor=_rgba(color, alpha),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=row,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name=name,
            line=dict(width=outline, color=MUTED),
            hovertemplate=f"{name}=%{{y:.2f}}{hover_suffix}<extra></extra>",
            showlegend=False,
        ),
        row=row,
        col=1,
    )

    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="rgba(148,163,184,0.55)",
        line_width=1,
        row=row,
        col=1,
    )


def _add_extreme_zones(
    fig: go.Figure,
    y,
    row: int,
    y_max: float,
    lo_pct: float = 10,
    hi_pct: float = 90,
) -> tuple:
    """Shade the historical top/bottom decile of the series.

    Upper decile = crowded long = reversal risk -> red tint.
    Lower decile = crowded short -> green tint.
    """
    y = np.asarray(y, dtype=float)
    finite = y[np.isfinite(y)]
    if finite.size < 20:
        return (np.nan, np.nan)

    hi = float(np.percentile(finite, hi_pct))
    lo = float(np.percentile(finite, lo_pct))

    fig.add_hrect(
        y0=hi, y1=y_max,
        fillcolor=_rgba(NEG, 0.09), line_width=0, layer="below",
        row=row, col=1,
    )
    fig.add_hrect(
        y0=-y_max, y1=lo,
        fillcolor=_rgba(POS, 0.09), line_width=0, layer="below",
        row=row, col=1,
    )
    for level, color in ((hi, NEG), (lo, POS)):
        fig.add_hline(
            y=level, line_dash="dash", line_width=1,
            line_color=_rgba(color, 0.5), row=row, col=1,
        )
    return (lo, hi)


def _extreme_blocks(
    dates: pd.Series, mask: np.ndarray, min_len: int = 2, max_blocks: int = 40
) -> list:
    """Collapse a boolean mask into contiguous (start, end) date blocks.

    Drawing one vrect per week would create hundreds of shapes; blocks keep
    the shading cheap and legible. Only the longest ``max_blocks`` survive so
    a pathological series cannot tank rendering performance.
    """
    raw = []  # (start_idx, end_idx, length)
    start = None
    count = 0
    for i, flag in enumerate(mask):
        if flag:
            if start is None:
                start = i
            count += 1
        else:
            if start is not None and count >= min_len:
                raw.append((start, i - 1, count))
            start, count = None, 0
    if start is not None and count >= min_len:
        raw.append((start, len(mask) - 1, count))

    if len(raw) > max_blocks:
        raw = sorted(raw, key=lambda b: b[2], reverse=True)[:max_blocks]

    return [(dates.iloc[s], dates.iloc[e]) for s, e, _ in sorted(raw)]


def _first_touch(mask: np.ndarray, min_run: int = 2, cooldown: int = 8) -> np.ndarray:
    """Keep only the week a series *enters* an extreme, not every week inside it.

    A rolling min-max percentile prints 100 on every new 52-week high, so a
    trending market marks dozens of consecutive weeks for what is really one
    event. This collapses each run to its first bar, ignores runs shorter than
    ``min_run`` weeks, and suppresses re-entries within ``cooldown`` weeks.
    """
    mask = np.asarray(mask, dtype=bool)
    out = np.zeros(mask.shape, dtype=bool)
    last = -(10**9)
    i, n = 0, len(mask)

    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < n and mask[j]:
            j += 1
        if (j - i) >= min_run and (i - last) >= cooldown:
            out[i] = True
            last = i
        i = j

    return out


def _symmetric_limit(*series, pad: float = 1.10) -> float:
    vals = []
    for s in series:
        arr = np.asarray(s, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size:
            vals.append(np.max(np.abs(arr)))
    return (max(vals) * pad) if vals else 1.0


# --------------------------------------------------------------------------
# Chart 1: Overlay
# --------------------------------------------------------------------------
def build_overlay_chart(
    df_merged: pd.DataFrame,
    selected_pair: str,
    selected_cot_name: str,
    date_density: str = "Auto",
) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["close"],
            mode="lines",
            name="MT5 Price",
            line=dict(color=GOLD, width=2.2),
            hovertemplate="MT5 Price=%{y:.5f}<extra></extra>",
        ),
        secondary_y=False,
    )

    colors = [_rgba(POS, 0.5) if v > 0 else _rgba(NEG, 0.5) for v in df_merged["Net_Pct_of_OI"]]
    fig.add_trace(
        go.Bar(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI"],
            name=f"{selected_cot_name} Net OI %",
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="Pair Net OI=%{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI_dxy"],
            mode="lines",
            name="USD Index Net OI %",
            line=dict(color=BLUE, width=1.8),
            hovertemplate="USD Index Net OI=%{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.add_hline(y=0, line_dash="dot", line_color="rgba(148,163,184,0.55)", secondary_y=True)

    _theme(fig, 760, f"{selected_pair} Price vs Net OI% (Overlay)")
    fig.update_layout(
        showlegend=True,
        # Left aligned: the range selector buttons occupy the top right.
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(size=11),
        ),
    )

    fig.update_xaxes(**_x_axis_kwargs(date_density), rangeslider=dict(visible=False))
    fig.update_xaxes(title_text="Date", rangeselector=_range_selector())

    limit = _symmetric_limit(df_merged["Net_Pct_of_OI"], df_merged["Net_Pct_of_OI_dxy"])
    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.update_yaxes(
        title_text="Net Open Interest (%)",
        secondary_y=True,
        range=[-limit, limit],
        showgrid=False,
    )
    return fig


# --------------------------------------------------------------------------
# Chart 2: Stacked
# --------------------------------------------------------------------------
def build_stacked_chart(
    df_merged: pd.DataFrame,
    selected_pair: str,
    selected_cot_name: str,
    date_density: str = "Auto",
) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.42, 0.29, 0.29],
        subplot_titles=(
            f"{selected_pair} MT5 Price",
            f"{selected_cot_name} Net OI %",
            "USD INDEX Net OI %",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["close"],
            mode="lines",
            name="MT5 Price",
            line=dict(color=GOLD, width=2.0),
            hovertemplate="MT5 Price=%{y:.5f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    _add_split_area(fig, df_merged["Date"], df_merged["Net_Pct_of_OI"], 2,
                    f"{selected_cot_name} Net OI")
    _add_split_area(fig, df_merged["Date"], df_merged["Net_Pct_of_OI_dxy"], 3,
                    "USD Index Net OI")

    # One shared symmetric scale so the two panels are directly comparable.
    limit = _symmetric_limit(df_merged["Net_Pct_of_OI"], df_merged["Net_Pct_of_OI_dxy"])

    _theme(fig, 980, f"{selected_pair} Price and OI% (Stacked)")
    apply_shared_crosshair(fig)

    fig.update_xaxes(**_x_axis_kwargs(date_density))
    fig.update_xaxes(rangeselector=_range_selector(), row=1, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1, rangeslider=dict(visible=False))

    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Pair Net OI %", row=2, col=1, range=[-limit, limit])
    fig.update_yaxes(title_text="USD Index Net OI %", row=3, col=1, range=[-limit, limit])
    return fig


# --------------------------------------------------------------------------
# Chart 3: Comparison (aligned) - the analytical view
# --------------------------------------------------------------------------
def build_comparison_chart(
    df_merged: pd.DataFrame,
    selected_pair: str,
    selected_cot_name: str,
    date_density: str = "Auto",
    invert_dxy: bool = True,
    show_extreme_zones: bool = True,
    show_extreme_markers: bool = True,
    show_extreme_shading: bool = False,
    corr_window: int = 26,
    ma_window: int = 26,
    extreme_threshold: float = 90.0,
    marker_mode: str = "First touch only",
    marker_min_run: int = 2,
    marker_cooldown: int = 8,
) -> go.Figure:
    """Five aligned panels built specifically for visual comparison.

    1. Price + moving average + positioning-extreme markers
    2. Pair Net OI %            -- shared symmetric scale
    3. USD Index Net OI %       -- shared symmetric scale, optionally inverted
    4. Spread (pair - USD index) = combined positioning score for the pair
    5. Rolling correlation between price and pair Net OI %
    """
    df = df_merged.copy().reset_index(drop=True)
    dates = df["Date"]

    pair_oi = df["Net_Pct_of_OI"].to_numpy(dtype=float)
    dxy_raw = df["Net_Pct_of_OI_dxy"].to_numpy(dtype=float)
    dxy_oi = -dxy_raw if invert_dxy else dxy_raw
    spread = pair_oi - dxy_raw  # long-pair-currency vs long-USD, always this way

    usd_is_base = selected_pair.upper().startswith("USD")
    spread_note = (
        " — higher = stronger "
        f"{selected_cot_name.title()} vs USD"
        + (f", i.e. {selected_pair} lower" if usd_is_base else f", i.e. {selected_pair} higher")
    )
    dxy_title = "USD INDEX Net OI %" + (" (inverted)" if invert_dxy else "")

    fig = make_subplots(
        rows=5,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.032,
        row_heights=[0.30, 0.175, 0.175, 0.185, 0.165],
        subplot_titles=(
            f"{selected_pair} MT5 Weekly Close",
            f"{selected_cot_name} Net OI %",
            dxy_title,
            f"Spread: {selected_cot_name} − USD Index{spread_note}",
            f"Rolling {corr_window}w Correlation — Price vs {selected_cot_name} Net OI %",
        ),
    )

    # ---- Row 1: price -----------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=df["close"],
            mode="lines",
            name="Price",
            line=dict(color=GOLD, width=2.0),
            hovertemplate="Price=%{y:.5f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    if ma_window and len(df) > ma_window:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df["close"].rolling(ma_window, min_periods=ma_window).mean(),
                mode="lines",
                name=f"MA{ma_window}",
                line=dict(color="rgba(230,237,243,0.45)", width=1.2, dash="dot"),
                hovertemplate=f"MA{ma_window}=%{{y:.5f}}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # ---- Rows 2 & 3: OI panels on one shared symmetric scale ---------------
    limit = _symmetric_limit(pair_oi, dxy_oi)

    _add_split_area(fig, dates, pair_oi, 2, f"{selected_cot_name} Net OI")
    _add_split_area(fig, dates, dxy_oi, 3, "USD Index Net OI")

    if show_extreme_zones:
        _add_extreme_zones(fig, pair_oi, 2, limit)
        _add_extreme_zones(fig, dxy_oi, 3, limit)

    # ---- Row 4: spread ----------------------------------------------------
    spread_limit = _symmetric_limit(spread)
    _add_split_area(fig, dates, spread, 4, "Spread", pos_color=VIOLET, neg_color="#F97316",
                    alpha=0.5)
    if show_extreme_zones:
        _add_extreme_zones(fig, spread, 4, spread_limit)

    # ---- Row 5: rolling correlation ---------------------------------------
    if len(df) > corr_window:
        corr = (
            df["close"]
            .rolling(corr_window, min_periods=corr_window)
            .corr(df["Net_Pct_of_OI"])
            .to_numpy(dtype=float)
        )
    else:
        corr = np.full(len(df), np.nan)

    _add_split_area(fig, dates, corr, 5, "Rolling corr", hover_suffix="",
                    pos_color=BLUE, neg_color="#F59E0B", alpha=0.45)
    for level in (0.5, -0.5):
        fig.add_hline(
            y=level, line_dash="dash", line_width=1,
            line_color="rgba(148,163,184,0.4)", row=5, col=1,
        )

    # ---- Extreme markers on price -----------------------------------------
    pct_col = "52-Week Percentile"
    if show_extreme_markers and pct_col in df.columns:
        pct = pd.to_numeric(df[pct_col], errors="coerce").to_numpy(dtype=float)
        price = df["close"].to_numpy(dtype=float)
        span = np.nanmax(price) - np.nanmin(price)
        offset = span * 0.035 if np.isfinite(span) and span > 0 else 0.0

        hi_thr = float(extreme_threshold)
        lo_thr = 100.0 - hi_thr

        bull_raw = pct >= hi_thr
        bear_raw = pct <= lo_thr

        # A rolling min-max percentile re-prints 100 on every new high, so
        # without this collapse a single trend produces dozens of markers.
        if marker_mode == "Every week":
            bull, bear = bull_raw, bear_raw
        else:
            bull = _first_touch(bull_raw, marker_min_run, marker_cooldown)
            bear = _first_touch(bear_raw, marker_min_run, marker_cooldown)

        marker_specs = (
            (bull, "triangle-down", NEG, +1, f"Crowded LONG (52w pct ≥ {hi_thr:.0f})"),
            (bear, "triangle-up", POS, -1, f"Crowded SHORT (52w pct ≤ {lo_thr:.0f})"),
        )
        for mask, symbol, color, direction, label in marker_specs:
            if not mask.any():
                continue
            fig.add_trace(
                go.Scatter(
                    x=dates[mask],
                    y=price[mask] + direction * offset,
                    mode="markers",
                    name=label,
                    marker=dict(
                        symbol=symbol,
                        size=10,
                        color=_rgba(color, 0.95),
                        line=dict(width=1, color=BG),
                    ),
                    hovertemplate=f"{label}<extra></extra>",
                ),
                row=1,
                col=1,
            )

        # Contiguous extreme periods shaded across every panel. Uses the raw
        # mask (the full duration of the event), not the de-duplicated one.
        if show_extreme_shading:
            for mask, color in ((bull_raw, NEG), (bear_raw, POS)):
                for x0, x1 in _extreme_blocks(dates, mask, min_len=6, max_blocks=12):
                    fig.add_vrect(
                        x0=x0, x1=x1,
                        fillcolor=_rgba(color, 0.055),
                        line_width=0, layer="below",
                        row="all", col=1,
                    )

    # ---- Layout -----------------------------------------------------------
    _theme(fig, 1240, f"{selected_pair} vs {selected_cot_name} & USD Index — Aligned Comparison")
    apply_shared_crosshair(fig)

    fig.update_xaxes(**_x_axis_kwargs(date_density))
    fig.update_xaxes(rangeselector=_range_selector(), row=1, col=1)
    fig.update_xaxes(title_text="Date", row=5, col=1, rangeslider=dict(visible=False))

    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Net OI %", row=2, col=1, range=[-limit, limit])
    fig.update_yaxes(title_text="Net OI %", row=3, col=1, range=[-limit, limit])
    fig.update_yaxes(title_text="Spread (pp)", row=4, col=1,
                     range=[-spread_limit, spread_limit])
    fig.update_yaxes(title_text="Corr", row=5, col=1, range=[-1.05, 1.05],
                     dtick=0.5)
    return fig


# --------------------------------------------------------------------------
# Chart 4: Heatmaps
# --------------------------------------------------------------------------
def build_heatmap_chart(
    df_merged: pd.DataFrame, selected_pair: str, selected_cot_name: str
) -> go.Figure:
    df = df_merged.copy()
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month_name().str[:3]

    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=(
            f"{selected_pair} Pearson Correlation Matrix",
            f"{selected_cot_name} Net OI % Seasonality (Average by Month & Year)",
            f"{selected_pair} MT5 Price Seasonality (Average by Month & Year)",
        ),
        vertical_spacing=0.08,
    )

    # 1. Pearson correlation matrix
    corr_df = df[["close", "Net_Pct_of_OI", "Net_Pct_of_OI_dxy"]].corr()
    labels = ["MT5 Price", f"{selected_cot_name} Net OI %", "USD Index Net OI %"]
    text_corr = np.where(pd.notna(corr_df.values), np.round(corr_df.values, 2).astype(str), "")

    fig.add_trace(
        go.Heatmap(
            z=corr_df.values,
            x=labels,
            y=labels,
            colorscale="RdBu",
            zmin=-1,
            zmax=1,
            text=text_corr,
            texttemplate="%{text}",
            hovertemplate="X: %{x}<br>Y: %{y}<br>Corr: %{z:.2f}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Pearson<br>Corr", x=1.02, len=0.28, y=0.86,
                          thickness=12, tickfont=dict(size=10)),
        ),
        row=1,
        col=1,
    )

    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # 2. Net OI seasonality
    pivot = df.pivot_table(values="Net_Pct_of_OI", index="Year", columns="Month", aggfunc="mean")
    pivot = pivot.reindex(columns=[m for m in months_order if m in pivot.columns])
    text_season = np.where(pd.notna(pivot.values), np.round(pivot.values, 1).astype(str), "")

    fig.add_trace(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="RdYlGn",
            zmid=0,
            text=text_season,
            texttemplate="%{text}",
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Avg Net OI: %{z:.1f}%<extra></extra>",
            showscale=True,
            colorbar=dict(title="Net OI %", x=1.02, len=0.28, y=0.5,
                          thickness=12, tickfont=dict(size=10)),
        ),
        row=2,
        col=1,
    )

    # 3. Price seasonality
    pivot_price = df.pivot_table(values="close", index="Year", columns="Month", aggfunc="mean")
    pivot_price = pivot_price.reindex(columns=[m for m in months_order if m in pivot_price.columns])
    text_price = np.where(pd.notna(pivot_price.values), np.round(pivot_price.values, 4).astype(str), "")

    fig.add_trace(
        go.Heatmap(
            z=pivot_price.values,
            x=pivot_price.columns,
            y=pivot_price.index,
            colorscale="Cividis",
            text=text_price,
            texttemplate="%{text}",
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Avg Price: %{z:.5f}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Price", x=1.02, len=0.28, y=0.14,
                          thickness=12, tickfont=dict(size=10)),
        ),
        row=3,
        col=1,
    )

    _theme(fig, 1300, f"{selected_pair} Heatmap Analysis", unified=False)
    fig.update_layout(dragmode=False)

    fig.update_yaxes(autorange="reversed", row=1, col=1)
    fig.update_yaxes(autorange="reversed", type="category", dtick=1, row=2, col=1)
    fig.update_yaxes(autorange="reversed", type="category", dtick=1, row=3, col=1)
    return fig
