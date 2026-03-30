import streamlit as st

STAGE_COLORS = {
    "Ny": "#6366f1",
    "Kontaktad": "#f59e0b",
    "Offert skickad": "#3b82f6",
    "Förhandling": "#8b5cf6",
    "Bokad": "#06b6d4",
    "Vunnen": "#10b981",
    "Förlorad": "#ef4444",
}

STAGE_ICONS = {
    "Ny": "🔵",
    "Kontaktad": "📞",
    "Offert skickad": "📄",
    "Förhandling": "🤝",
    "Bokad": "📅",
    "Vunnen": "✅",
    "Förlorad": "❌",
}

ACTIVITY_ICONS = {
    "Samtal": "📞",
    "E-post": "📧",
    "Möte": "🤝",
    "Offert": "📄",
    "Statusändring": "🔄",
    "Anteckning": "📝",
    "Påminnelse": "⏰",
}

SERVICE_TYPES = [
    "Mobiltelefoni", "Fast telefoni", "Bredband fiber",
    "Bredband 4G/5G", "Växel / PBX", "El", "Gas",
    "IT-support", "Molntjänst", "Försäkring", "Övrigt"
]

LEAD_SOURCES = [
    "Kallringning", "LinkedIn", "Hemsida", "Rekommendation",
    "Mässa / Event", "E-postkampanj", "Partner", "Övrigt"
]

STAGES = list(STAGE_COLORS.keys())

def badge(text, color=None):
    c = color or STAGE_COLORS.get(text, "#64748b")
    return f'<span style="background:{c}20;color:{c};padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;">{text}</span>'

def activity_badge(text):
    icon = ACTIVITY_ICONS.get(text, "•")
    return f"{icon} {text}"

def metric_card(label, value, delta=None, color="#3b82f6"):
    delta_html = ""
    if delta:
        dc = "#10b981" if "+" in str(delta) else "#ef4444"
        delta_html = f'<div style="font-size:12px;color:{dc};margin-top:2px;">{delta}</div>'
    st.markdown(f"""
    <div style="background:white;border-radius:12px;padding:20px 24px;
                border:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;
                    letter-spacing:0.05em;margin-bottom:6px;">{label}</div>
        <div style="font-size:28px;font-weight:800;color:{color};">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def section_header(title, subtitle=None):
    st.markdown(f"""
    <div style="margin-bottom:20px;">
        <h2 style="font-size:22px;font-weight:800;color:#1e293b;margin:0;">{title}</h2>
        {"<p style='color:#64748b;font-size:14px;margin:4px 0 0;'>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)

def info_row(label, value, icon=""):
    if value:
        st.markdown(f"""
        <div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid #f1f5f9;">
            <span style="color:#94a3b8;font-size:13px;min-width:140px;">{icon} {label}</span>
            <span style="color:#1e293b;font-size:13px;font-weight:500;">{value}</span>
        </div>
        """, unsafe_allow_html=True)

def apply_global_style():
    st.markdown("""
    <style>
    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    /* Hide streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    /* Cards */
    .stMetric { background: white; border-radius: 12px; padding: 16px; border: 1px solid #e2e8f0; }
    /* Buttons */
    .stButton > button {
        border-radius: 8px; font-weight: 600; transition: all 0.15s;
        border: none;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: #f8fafc; padding: 4px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; font-weight: 600; }
    /* Inputs */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 8px; border: 1.5px solid #e2e8f0; font-size: 14px;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #1e293b;
    }
    [data-testid="stSidebar"] * { color: #cbd5e1 !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent; color: #cbd5e1 !important;
        text-align: left; width: 100%; border-radius: 8px;
        padding: 10px 14px; font-size: 14px; font-weight: 500;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.1) !important; transform: none;
        box-shadow: none;
    }
    /* Dataframe */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    /* Success / error */
    .stAlert { border-radius: 10px; }
    /* Divider */
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 16px 0; }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)
