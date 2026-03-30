import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import get_stats, get_customers, get_quotes
from utils.ui_helpers import STAGE_COLORS, STAGE_ICONS
import datetime

def show(user):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="css"], .stApp { background: #080C14 !important; font-family: 'Inter', sans-serif !important; }
    .block-container { padding-top: 0 !important; max-width: 100% !important; }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid #161b22 !important; }
    [data-testid="stSidebar"] * { color: #8b949e !important; font-family: 'Inter', sans-serif !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important; color: #8b949e !important;
        text-align: left !important; width: 100% !important;
        border-radius: 8px !important; padding: 10px 14px !important;
        font-size: 13px !important; font-weight: 500 !important; border: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,0.05) !important; color: white !important; }
    .stButton > button { border-radius: 8px !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; border: 1px solid #21262d !important; background: #161b22 !important; color: #e6edf3 !important; transition: all 0.15s !important; }
    .stButton > button:hover { background: #21262d !important; border-color: #30363d !important; }
    .stButton > button[kind="primary"] { background: #10b981 !important; border-color: #10b981 !important; color: white !important; }
    .stTextInput input, .stSelectbox > div > div, .stTextArea textarea, .stNumberInput input { background: #161b22 !important; border: 1px solid #30363d !important; color: #e6edf3 !important; border-radius: 8px !important; }
    label { color: #8b949e !important; font-size: 13px !important; }
    .stTabs [data-baseweb="tab-list"] { background: #161b22 !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid #21262d !important; }
    .stTabs [data-baseweb="tab"] { color: #8b949e !important; border-radius: 8px !important; font-weight: 600 !important; }
    .stTabs [aria-selected="true"] { background: #21262d !important; color: #e6edf3 !important; }
    hr { border-color: #21262d !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #080C14; }
    ::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }
    @keyframes slideIn { from{transform:translateY(-16px);opacity:0} to{transform:translateY(0);opacity:1} }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
    @keyframes glow { 0%,100%{box-shadow:0 0 20px rgba(16,185,129,0.2)} 50%{box-shadow:0 0 40px rgba(16,185,129,0.4)} }
    </style>
    """, unsafe_allow_html=True)

    stats = get_stats(user["id"], user["role"])
    customers = get_customers(user["id"], user["role"])
    now = datetime.datetime.now()
    greeting = "God morgon" if now.hour < 12 else "God eftermiddag" if now.hour < 17 else "God kväll"
    first_name = user["name"].split()[0]

    st.markdown(f"""
    <div style="background:linear-gradient(180deg,#0D1420 0%,#080C14 100%);border-bottom:1px solid #161b22;
                padding:24px 32px;margin:-1rem -1rem 0;display:flex;justify-content:space-between;align-items:center;">
        <div>
            <div style="font-size:12px;font-weight:600;color:#8b949e;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:4px;">
                {greeting}, {first_name} 👋
            </div>
            <div style="font-size:24px;font-weight:800;color:#e6edf3;">Dashboard</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:8px;height:8px;border-radius:50%;background:#10b981;animation:pulse 2s infinite;box-shadow:0 0 6px #10b981;"></div>
            <span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#30363d;">{now.strftime('%H:%M · %d %b %Y')}</span>
        </div>
    </div>
    <div style="height:28px;"></div>
    """, unsafe_allow_html=True)

    pipeline_val = stats.get('pipeline_value', 0) or 0
    reminders = stats.get('due_reminders', 0) or 0

    kpis = [
        ("KUNDER", str(stats['total_customers']), "#3b82f6", "#0a1628", "#1e3a5f", "👥"),
        ("OFFERTER UTE", str(stats['quotes_out']), "#f59e0b", "#1a0f00", "#4d3000", "📄"),
        ("VUNNA / MÅN", str(stats['won_month']), "#10b981", "#071a10", "#134d2a", "🏆"),
        ("PIPELINE / ÅR", f"{pipeline_val:,.0f} kr", "#a78bfa", "#12071a", "#3d1a7a", "💰"),
        ("PÅMINNELSER", str(reminders), "#ef4444" if reminders > 0 else "#10b981", "#1a0707" if reminders > 0 else "#071a10", "#4d1515" if reminders > 0 else "#134d2a", "⏰"),
    ]

    cols = st.columns(5)
    for i, (label, value, color, bg, border_c, icon) in enumerate(kpis):
        with cols[i]:
            glow = "animation:glow 3s infinite;" if i == 2 else ""
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{bg},{bg}cc);border:1px solid {border_c};border-radius:14px;padding:22px 20px;{glow}animation:slideIn {0.2+i*0.08}s ease;">
                <div style="font-size:10px;font-weight:700;color:{color};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:10px;opacity:0.8;">{icon} {label}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;color:#e6edf3;line-height:1;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;font-weight:700;color:#8b949e;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:12px;">PIPELINE ÖVERSIKT</div>', unsafe_allow_html=True)

    stage_cols = st.columns(7)
    for i, stage in enumerate(["Ny","Kontaktad","Offert skickad","Förhandling","Bokad","Vunnen","Förlorad"]):
        color = STAGE_COLORS.get(stage, "#64748b")
        icon = STAGE_ICONS.get(stage, "•")
        count = sum(1 for c in customers if c.get("status") == stage)
        with stage_cols[i]:
            st.markdown(f"""
            <div style="background:#0d1117;border:1px solid #161b22;border-top:2px solid {color};border-radius:10px;padding:14px 10px;text-align:center;">
                <div style="font-size:16px;margin-bottom:4px;">{icon}</div>
                <div style="font-size:9px;color:#484f58;margin-bottom:4px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">{stage}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;color:#e6edf3;">{count}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#8b949e;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:12px;">SENASTE AKTIVITET</div>', unsafe_allow_html=True)
        for c in customers[:8]:
            color = STAGE_COLORS.get(c["status"], "#64748b")
            icon = STAGE_ICONS.get(c["status"], "•")
            updated = (c.get("updated_at") or "")[:10]
            st.markdown(f"""
            <div style="background:#0d1117;border:1px solid #161b22;border-radius:10px;padding:12px 16px;margin-bottom:6px;border-right:3px solid {color};">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-weight:700;font-size:13px;color:#e6edf3;">{c['company_name']}</div>
                        <div style="font-size:11px;color:#484f58;margin-top:2px;">{c.get('contact_person') or '—'} · {c.get('assigned_name') or '—'}</div>
                    </div>
                    <div style="text-align:right;">
                        <span style="background:{color}20;color:{color};padding:2px 8px;border-radius:8px;font-size:10px;font-weight:700;">{icon} {c['status']}</span>
                        <div style="font-size:10px;color:#30363d;margin-top:4px;">{updated}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#8b949e;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:12px;">SNABBÅTGÄRDER</div>', unsafe_allow_html=True)
        for label, page, kind in [
            ("➕  Ny kund", "customers", "primary"),
            ("📄  Ny offert", "quotes", "secondary"),
            ("⚡  Säljtavla", "leaderboard", "secondary"),
            ("🔄  Pipeline", "pipeline", "secondary"),
            ("📈  Rapporter", "reports", "secondary"),
        ]:
            if st.button(label, use_container_width=True, type="primary" if kind=="primary" else "secondary", key=f"db_{page}"):
                st.session_state.page = page
                st.rerun()
            st.markdown("<div style='height:4px'/>", unsafe_allow_html=True)

        if reminders > 0:
            st.markdown(f"""
            <div style="background:#1a0707;border:1px solid #4d1515;border-radius:10px;padding:14px;margin-top:8px;">
                <div style="font-weight:700;color:#ef4444;font-size:12px;">⏰ {reminders} påminnelser</div>
                <div style="font-size:11px;color:#484f58;margin-top:4px;">Kunder väntar på uppföljning</div>
            </div>
            """, unsafe_allow_html=True)
