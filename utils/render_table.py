import pandas as pd
import plotly.graph_objects as go
from decimal import Decimal

def render_query_result_table(data: list, max_rows: int = 1000):
    """
    Render a Plotly table from query result data.

    Args:
        data (list): List of dictionaries (query result).
        max_rows (int): Max rows to display in the table.

    Returns:
        plotly.graph_objects.Figure: A plotly table figure.
    """
    if not data:
        raise ValueError("No data provided")

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Convert Decimal to float and handle None
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
            df[col] = df[col].fillna("—")  # Replace None/NaN with dash

    # Truncate if too many rows
    if len(df) > max_rows:
        df = df.head(max_rows)

    # Build table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{col}</b>" for col in df.columns],
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='lavender',
            align='left'
        )
    )])

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=40 * len(df) + 100,
        title_text="Query Result Table",
        title_x=0.5
    )

    return fig
