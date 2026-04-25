import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def build_overlay_chart(df_merged: pd.DataFrame, selected_pair: str, selected_cot_name: str, date_density: str = "Auto") -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    colors = ["#16a34a" if val > 0 else "#dc2626" for val in df_merged["Net_Pct_of_OI"]]

    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["close"],
            mode="lines",
            name="MT5 Price",
            line=dict(color="gold", width=2.5),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>MT5 Price=%{y:.5f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI"],
            name=f"{selected_cot_name} Net OI %",
            marker_color=colors,
            opacity=0.4,
            hovertemplate="Date=%{x|%Y-%m-%d}<br>Pair Net OI=%{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI_dxy"],
            mode="lines+markers",
            name="USD Index Net OI %",
            line=dict(color="dodgerblue", width=2),
            marker=dict(size=4),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>USD Index Net OI=%{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.add_hline(y=0, line_dash="dot", line_color="gray", secondary_y=True)
    fig.update_layout(
        title=f"<b>{selected_pair} Price vs Net OI% (Overlay)</b>",
        xaxis_title="Date",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=760,
    )

    x_axis_kwargs = {
        "type": "date",
        "hoverformat": "%Y-%m-%d",
        "showgrid": True,
        "gridcolor": "rgba(148,163,184,0.15)",
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "rangeslider": dict(visible=False)
    }

    if date_density == "1 Year":
        x_axis_kwargs.update({"dtick": "M12", "tickformat": "%Y", "tickmode": "linear"})
    elif date_density == "2 Years":
        x_axis_kwargs.update({"dtick": "M24", "tickformat": "%Y", "tickmode": "linear"})
    elif date_density == "Quarterly":
        x_axis_kwargs.update({"dtick": "M3", "tickformat": "Q%q %Y", "tickmode": "linear"})
    elif date_density == "Monthly":
        x_axis_kwargs.update({"dtick": "M1", "tickformat": "%b %Y", "tickmode": "linear"})
    else:
        x_axis_kwargs.update({"nticks": 20, "tickmode": "auto"})

    fig.update_xaxes(**x_axis_kwargs)

    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.update_yaxes(title_text="Net Open Interest (%)", secondary_y=True)


    return fig


def build_stacked_chart(df_merged: pd.DataFrame, selected_pair: str, selected_cot_name: str, date_density: str = "Auto") -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            f"{selected_pair} MT5 Price",
            f"{selected_cot_name} Net OI %",
            "USD INDEX Net OI %",
        ),
    )

    colors = ["#16a34a" if val > 0 else "#dc2626" for val in df_merged["Net_Pct_of_OI"]]

    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["close"],
            mode="lines",
            name="MT5 Price",
            line=dict(color="gold", width=2.5),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>MT5 Price=%{y:.5f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI"],
            name=f"{selected_cot_name} Net OI %",
            marker_color=colors,
            opacity=0.5,
            hovertemplate="Date=%{x|%Y-%m-%d}<br>Pair Net OI=%{y:.2f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI_dxy"],
            mode="lines+markers",
            name="USD Index Net OI %",
            line=dict(color="dodgerblue", width=2),
            marker=dict(size=4),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>USD Index Net OI=%{y:.2f}%<extra></extra>",
        ),
        row=3,
        col=1,
    )

    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=3, col=1)
    fig.update_layout(
        title=f"<b>{selected_pair} Price and OI% (Stacked)</b>",
        hovermode="x unified",
        height=980,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    x_axis_kwargs = {
        "type": "date",
        "hoverformat": "%Y-%m-%d",
        "showgrid": True,
        "gridcolor": "rgba(148,163,184,0.15)",
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor"
    }

    if date_density == "1 Year":
        x_axis_kwargs.update({"dtick": "M12", "tickformat": "%Y", "tickmode": "linear"})
    elif date_density == "2 Years":
        x_axis_kwargs.update({"dtick": "M24", "tickformat": "%Y", "tickmode": "linear"})
    elif date_density == "Quarterly":
        x_axis_kwargs.update({"dtick": "M3", "tickformat": "Q%q %Y", "tickmode": "linear"})
    elif date_density == "Monthly":
        x_axis_kwargs.update({"dtick": "M1", "tickformat": "%b %Y", "tickmode": "linear"})
    else:
        x_axis_kwargs.update({"nticks": 20, "tickmode": "auto"})

    fig.update_xaxes(**x_axis_kwargs)

    fig.update_xaxes(
        title_text="Date",
        row=3,
        col=1,
        rangeslider=dict(visible=False),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Pair Net OI %", row=2, col=1)
    fig.update_yaxes(title_text="USD Index Net OI %", row=3, col=1)


    return fig


def build_heatmap_chart(df_merged: pd.DataFrame, selected_pair: str, selected_cot_name: str) -> go.Figure:
    df = df_merged.copy()
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month_name().str[:3]

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            f"{selected_pair} Pearson Correlation Matrix",
            f"{selected_cot_name} Net OI % Seasonality (Average by Month & Year)",
            f"{selected_pair} MT5 Price Seasonality (Average by Month & Year)"
        ),
        vertical_spacing=0.1
    )

    # 1. Pearson Correlation Matrix
    corr_df = df[['close', 'Net_Pct_of_OI', 'Net_Pct_of_OI_dxy']].corr()
    labels = ['MT5 Price', f'{selected_cot_name} Net OI %', 'USD Index Net OI %']

    text_corr = np.where(pd.notna(corr_df.values), np.round(corr_df.values, 2).astype(str), "")

    fig.add_trace(
        go.Heatmap(
            z=corr_df.values,
            x=labels,
            y=labels,
            colorscale='RdBu',
            zmin=-1, zmax=1,
            text=text_corr,
            texttemplate="%{text}",
            hovertemplate="X: %{x}<br>Y: %{y}<br>Corr: %{z:.2f}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Pearson<br>Correlation", x=1.02, len=0.28, y=0.86)
        ),
        row=1, col=1
    )

    # 2. Seasonality Calendar Matrix
    pivot = df.pivot_table(values='Net_Pct_of_OI', index='Year', columns='Month', aggfunc='mean')
    months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    pivot = pivot.reindex(columns=[m for m in months_order if m in pivot.columns])

    text_season = np.where(pd.notna(pivot.values), np.round(pivot.values, 1).astype(str), "")

    fig.add_trace(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,
            text=text_season,
            texttemplate="%{text}",
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Avg Net OI: %{z:.1f}%<extra></extra>",
            showscale=True,
            colorbar=dict(title="Net OI %", x=1.02, len=0.28, y=0.5)
        ),
        row=2, col=1
    )

    # 3. Seasonality Calendar Matrix Build for MT5 Price
    pivot_price = df.pivot_table(values='close', index='Year', columns='Month', aggfunc='mean')
    pivot_price = pivot_price.reindex(columns=[m for m in months_order if m in pivot_price.columns])

    text_price = np.where(pd.notna(pivot_price.values), np.round(pivot_price.values, 5).astype(str), "")

    fig.add_trace(
        go.Heatmap(
            z=pivot_price.values,
            x=pivot_price.columns,
            y=pivot_price.index,
            colorscale='Cividis',
            text=text_price,
            texttemplate="%{text}",
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Avg Price: %{z:.5f}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Price", x=1.02, len=0.28, y=0.14)
        ),
        row=3, col=1
    )

    fig.update_layout(
        title=f"<b>{selected_pair} Heatmap Analysis</b>",
        height=1300,
        hovermode="closest",
    )

    fig.update_yaxes(autorange="reversed", row=1, col=1) # Matrix top-down view
    fig.update_yaxes(autorange="reversed", type='category', dtick=1, row=2, col=1) # Ensure years don't skip
    fig.update_yaxes(autorange="reversed", type='category', dtick=1, row=3, col=1) # Ensure years don't skip

    return fig

