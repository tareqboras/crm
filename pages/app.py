import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils.database import init_db, verify_user
from utils.ui_helpers import apply_global_style, STAGE_COLORS

# Init DB on startup
init_db()

st.set_page_config(
    page_title="CRM — Säljsystem",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── LOGIN ──────────────────────────────────────────────────────────────────────
def show_login():
    apply_global_style()
    st.markdown("""
    <style>
    .login-wrap { max-width: 420px; margin: 80px auto 0; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:48px;margin-bottom:8px;">💼</div>
            <h1 style="font-size:28px;font-weight:900;color:#1e293b;margin:0;">CRM Säljsystem</h1>
            <p style="color:#64748b;margin-top:6px;">Logga in för att fortsätta</p>
        </div>""", unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("📧 E-post", placeholder="admin@crm.se")
            password = st.text_input("🔒 Lösenord", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Logga in →", use_container_width=True, type="primary")

        if submitted:
            user = verify_user(email, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Fel e-post eller lösenord")

        st.markdown("""
        <div style="text-align:center;margin-top:20px;padding:14px;background:#f8fafc;border-radius:10px;">
            <div style="font-size:12px;color:#64748b;font-weight:600;">DEMOKONTON</div>
            <div style="font-size:12px;color:#64748b;margin-top:4px;">
                <b>Admin:</b> admin@crm.se / admin123<br>
                <b>Säljare:</b> sara@crm.se / seller123
            </div>
        </div>""", unsafe_allow_html=True)


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
def show_sidebar(user):
    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="padding:16px 4px 8px;margin-bottom:4px;">
            <div style="font-size:20px;font-weight:900;color:white;letter-spacing:0.02em;">💼 CRM</div>
            <div style="font-size:11px;color:#64748b;margin-top:2px;">Säljsystem</div>
        </div>""", unsafe_allow_html=True)

        # User badge
        role_color = "#3b82f6" if user["role"] == "admin" else "#10b981"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.07);border-radius:10px;padding:10px 12px;margin-bottom:16px;">
            <div style="font-size:13px;font-weight:700;color:white;">{user['name']}</div>
            <div style="font-size:11px;padding:1px 6px;background:{role_color}30;color:{role_color};
                        border-radius:6px;display:inline-block;margin-top:3px;">{user['role'].upper()}</div>
        </div>""", unsafe_allow_html=True)

        current = st.session_state.get("page", "dashboard")

        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("customers", "👥  Kunder"),
            ("quotes", "📄  Offerter"),
            ("pipeline", "🔄  Pipeline"),
            ("leaderboard", "⚡  Säljtavla"),
            ("reports", "📈  Rapporter"),
        ]
        if user["role"] == "admin":
            nav_items.append(("settings", "⚙️  Inställningar"))

        for page_key, label in nav_items:
            is_active = current == page_key
            btn_style = "primary" if is_active else "secondary"

            # Active indicator
            if is_active:
                st.markdown(f"""
                <div style="background:rgba(59,130,246,0.15);border-radius:8px;padding:8px 12px;
                            margin-bottom:2px;border-left:3px solid #3b82f6;">
                    <span style="color:white;font-size:14px;font-weight:600;">{label}</span>
                </div>""", unsafe_allow_html=True)
            else:
                if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.page = page_key
                    # Reset sub-states
                    st.session_state.customer_view = "list"
                    st.session_state.quote_view = "list"
                    st.session_state.selected_customer = None
                    st.rerun()

        st.markdown("<div style='flex:1'/>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:16px 0;'>", unsafe_allow_html=True)

        if st.button("🚪  Logga ut", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ── MAIN ROUTER ────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    show_login()
else:
    user = st.session_state.user

    # Init navigation state
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "customer_view" not in st.session_state:
        st.session_state.customer_view = "list"
    if "quote_view" not in st.session_state:
        st.session_state.quote_view = "list"

    show_sidebar(user)

    page = st.session_state.get("page", "dashboard")

    if page == "dashboard":
        from pages.dashboard import show
        show(user)
    elif page == "customers":
        from pages.customers import show
        show(user)
    elif page == "quotes":
        from pages.quotes import show
        show(user)
    elif page == "pipeline":
        from pages.pipeline import show
        show(user)
    elif page == "reports":
        from pages.reports import show
        show(user)
    elif page == "settings":
        from pages.settings import show
        show(user)
