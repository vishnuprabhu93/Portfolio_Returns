# ── Color tokens (Terra palette) ─────────────────────────────────────────────
COLOR_POSITIVE = "#2ca02c"   # gains, unchanged, already intuitive
COLOR_NEGATIVE = "#d62728"   # losses, unchanged, already intuitive

COLOR_PRIMARY = "#B15E3B"                    # terracotta
COLOR_PRIMARY_FILL = "rgba(177,94,59,0.12)"
COLOR_PRIMARY_FILL_LIGHT = "rgba(177,94,59,0.08)"
COLOR_ACCENT = "#3E7C7B"                     # teal
COLOR_HIGHLIGHT = "#D2A24C"                  # amber, for callout markers/annotations
COLOR_NEUTRAL_FILL = "rgba(122,113,104,0.15)"
COLOR_GRAY = "#7A7168"                       # warm muted gray, for neutral reference lines

BG = "#FAF7F2"
SURFACE = "#FFFFFF"
TEXT = "#2E2A25"
TEXT_MUTED = "#7A7168"
BORDER = "#EAE0D4"
METRIC_BG = SURFACE

# Categorical sequence for pie/bar charts with multiple series
PIE_COLOR_SEQUENCE = ["#B15E3B", "#3E7C7B", "#D2A24C", "#7C93A8", "#8A9A6B", "#C9B8A3"]

# Diverging scale for the correlation heatmap: teal (negative) → paper (0) → terracotta (positive)
CORRELATION_COLOR_SCALE = [[0, "#3E7C7B"], [0.5, "#F3EEE6"], [1, "#B15E3B"]]

FONT_DISPLAY = "'Sora', sans-serif"
FONT_BODY = "'Karla', sans-serif"

# ── Shared CSS ───────────────────────────────────────────────────────────────
BASE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Karla:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: {FONT_BODY};
}}

h1, h2, h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
    font-family: {FONT_DISPLAY};
    font-weight: 700;
    color: {TEXT};
}}

.block-container {{ padding-top: 2rem; }}

div[data-testid="metric-container"] {{
    background: {METRIC_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 14px 16px;
}}
div[data-testid="stMetricValue"] {{
    font-variant-numeric: tabular-nums;
    color: {TEXT};
}}
div[data-testid="stMetricLabel"] {{
    color: {TEXT_MUTED};
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    font-size: 15px;
    font-weight: 600;
    color: {TEXT_MUTED};
}}
.stTabs [aria-selected="true"] {{ color: {COLOR_PRIMARY} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {COLOR_PRIMARY} !important; }}
</style>
"""


def color_val(v, fmt=".2f"):
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    color = COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE
    return f'<span style="color:{color};font-weight:600">{sign}{v:{fmt}}</span>'
