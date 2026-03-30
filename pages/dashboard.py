import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import get_stats, get_customers, get_quotes, get_activities, log_activity
from utils.ui_helpers import STAGE_COLORS, STAGE_ICONS, badge, apply_global_style, section_header
import datetime

def show(user):
    apply_global_style()
    stats = get_stats(user["id"], user["role"])

    section_header("Dashboard", f"Välkommen tillbaka, {user['name'].split()[0]}! 👋")

    # ── KPI CARDS ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:18px 20px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;">Kunder totalt</div>
            <div style="font-size:30px;font-weight:800;color:#1e293b;margin-top:4px;">{stats['total_customers']}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:18px 20px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;">Offerter ute</div>
            <div style="font-size:30px;font-weight:800;color:#3b82f6;margin-top:4px;">{stats['quotes_out']}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:18px 20px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;">Vunna denna månad</div>
            <div style="font-size:30px;font-weight:800;color:#10b981;margin-top:4px;">{stats['won_month']}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        val = f"{stats['pipeline_value']:,.0f} kr"
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:12px;padding:18px 20px;">
            <div style="font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;">Pipeline-värde / år</div>
            <div style="font-size:24px;font-weight:800;color:#f59e0b;margin-top:4px;">{val}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        color = "#ef4444" if stats["due_reminders"] > 0 else "#10b981"
        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:18px 20px;border:1px solid {'#fecaca' if stats['due_reminders']>0 else '#e2e8f0'};">
            <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;">Påminnelser</div>
            <div style="font-size:30px;font-weight:800;color:{color};margin-top:4px;">{stats['due_reminders']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PIPELINE OVERVIEW ─────────────────────────────────────────────────────
    customers = get_customers(user["id"], user["role"])
    stage_counts = {}
    for s in STAGE_COLORS:
        stage_counts[s] = sum(1 for c in customers if c["status"] == s)

    st.markdown("#### Pipeline-översikt")
    cols = st.columns(len(STAGE_COLORS))
    for i, (stage, color) in enumerate(STAGE_COLORS.items()):
        with cols[i]:
            count = stage_counts.get(stage, 0)
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:14px;text-align:center;
                        border-top:3px solid {color};border:1px solid #e2e8f0;border-top:3px solid {color};">
                <div style="font-size:10px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.06em;">{STAGE_ICONS.get(stage,'')} {stage}</div>
                <div style="font-size:26px;font-weight:800;color:#1e293b;margin-top:4px;">{count}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── LATEST ACTIVITY + RECENT CUSTOMERS ───────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Senaste kunder")
        recent = customers[:8]
        if recent:
            for c in recent:
                color = STAGE_COLORS.get(c["status"], "#64748b")
                icon = STAGE_ICONS.get(c["status"], "•")
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:12px 16px;margin-bottom:6px;
                            border:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-weight:700;font-size:14px;color:#1e293b;">{c['company_name']}</div>
                        <div style="font-size:12px;color:#64748b;">{c.get('contact_person','') or ''} · {c.get('assigned_name','') or ''}</div>
                    </div>
                    <span style="background:{color}20;color:{color};padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;">{icon} {c['status']}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Inga kunder ännu. Lägg till din första kund!")

    with col_right:
        st.markdown("#### Snabbåtgärder")
        if st.button("➕  Ny kund", use_container_width=True, type="primary"):
            st.session_state.page = "customers"
            st.session_state.action = "new"
            st.rerun()
        st.markdown("<div style='height:6px'/>", unsafe_allow_html=True)
        if st.button("📄  Skapa offert", use_container_width=True):
            st.session_state.page = "quotes"
            st.rerun()
        st.markdown("<div style='height:6px'/>", unsafe_allow_html=True)
        if st.button("📊  Visa pipeline", use_container_width=True):
            st.session_state.page = "pipeline"
            st.rerun()
        st.markdown("<div style='height:6px'/>", unsafe_allow_html=True)
        if st.button("📈  Rapporter", use_container_width=True):
            st.session_state.page = "reports"
            st.rerun()

        # Due reminders
        if stats["due_reminders"] > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:14px;">
                <div style="font-weight:700;color:#dc2626;font-size:13px;">⏰ {stats['due_reminders']} påminnelser förfallna</div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">Kunder väntar på uppföljning.</div>
            </div>""", unsafe_allow_html=True)
