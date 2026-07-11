# ── Color tokens ─────────────────────────────────────────────────────────────
COLOR_POSITIVE = "#2ca02c"
COLOR_NEGATIVE = "#d62728"
COLOR_PRIMARY = "#1f77b4"
COLOR_PRIMARY_FILL = "rgba(31,119,180,0.1)"
COLOR_PRIMARY_FILL_LIGHT = "rgba(31,119,180,0.08)"
COLOR_NEUTRAL_FILL = "rgba(150,150,150,0.15)"
COLOR_GRAY = "gray"
COLOR_ORANGE = "orange"
METRIC_BG = "#f7f9fc"

PIE_COLOR_SEQUENCE = "Set2"          # px.colors.qualitative.Set2
CORRELATION_COLOR_SCALE = "RdYlGn"

# ── Shared CSS ───────────────────────────────────────────────────────────────
BASE_CSS = """
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="metric-container"] { background: #f7f9fc; border-radius: 8px; padding: 12px; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; }
</style>
"""


def color_val(v, fmt=".2f"):
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    color = COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE
    return f'<span style="color:{color};font-weight:600">{sign}{v:{fmt}}</span>'
