import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import get_pipeline, update_customer_status, log_activity
from utils.ui_helpers import STAGE_COLORS, STAGE_ICONS, STAGES, apply_global_style, section_header

def show(user):
    apply_global_style()
    section_header("Pipeline", "Drag & drop — flytta kunder mellan steg")

    customers = get_pipeline(user["id"], user["role"])

    # Group by stage
    stages_data = {s: [] for s in STAGES}
    for c in customers:
        s = c.get("status", "Ny")
        if s in stages_data:
            stages_data[s].append(c)

    # Stats bar
    active = [c for c in customers if c["status"] not in ["Vunnen","Förlorad"]]
    won = [c for c in customers if c["status"] == "Vunnen"]
    lost = [c for c in customers if c["status"] == "Förlorad"]

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f"""<div style="background:white;border-radius:10px;padding:14px;border:1px solid #e2e8f0;text-align:center;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Aktiva leads</div>
            <div style="font-size:28px;font-weight:800;color:#1e293b;">{len(active)}</div></div>""",
                    unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div style="background:white;border-radius:10px;padding:14px;border:1px solid #e2e8f0;text-align:center;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Vunna</div>
            <div style="font-size:28px;font-weight:800;color:#10b981;">{len(won)}</div></div>""",
                    unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""<div style="background:white;border-radius:10px;padding:14px;border:1px solid #e2e8f0;text-align:center;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Förlorade</div>
            <div style="font-size:28px;font-weight:800;color:#ef4444;">{len(lost)}</div></div>""",
                    unsafe_allow_html=True)
    with sc4:
        win_rate = round(len(won) / max(len(won)+len(lost), 1) * 100)
        st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:11px;color:#94a3b8;font-weight:700;text-transform:uppercase;">Win rate</div>
            <div style="font-size:28px;font-weight:800;color:#f59e0b;">{win_rate}%</div></div>""",
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Kanban columns
    cols = st.columns(len(STAGES))
    for i, stage in enumerate(STAGES):
        color = STAGE_COLORS[stage]
        icon  = STAGE_ICONS[stage]
        cards = stages_data.get(stage, [])

        with cols[i]:
            st.markdown(f"""
            <div style="background:{color}15;border-radius:12px;border-top:3px solid {color};padding:12px 10px 4px;">
                <div style="font-size:11px;font-weight:800;color:{color};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">
                    {icon} {stage} <span style="background:{color}30;border-radius:10px;padding:1px 7px;">{len(cards)}</span>
                </div>
            """, unsafe_allow_html=True)

            if not cards:
                st.markdown(f"""<div style="text-align:center;padding:20px 0;color:{color}60;font-size:12px;">Tom</div>""",
                            unsafe_allow_html=True)

            for c in cards:
                last = (c.get("last_activity") or "")[:10]
                st.markdown(f"""
                <div style="background:white;border-radius:8px;padding:10px 12px;margin-bottom:6px;
                            border:1px solid {color}30;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <div style="font-weight:700;font-size:12px;color:#1e293b;">{c['company_name']}</div>
                    <div style="font-size:11px;color:#64748b;margin-top:2px;">{c.get('contact_person') or '—'}</div>
                    <div style="font-size:10px;color:#94a3b8;margin-top:4px;">👤 {c.get('assigned_name','—')}</div>
                    {"<div style='font-size:10px;color:#94a3b8;'>🕐 " + last + "</div>" if last else ""}
                    {"<div style='font-size:10px;color:#3b82f6;'>📄 " + str(c.get('quote_count',0)) + " offert(er)</div>" if c.get('quote_count') else ""}
                </div>""", unsafe_allow_html=True)

                # Move buttons
                move_col1, move_col2 = st.columns(2)
                with move_col1:
                    if st.button("👁", key=f"view_kb_{c['id']}", help="Visa kundkort",
                                  use_container_width=True):
                        st.session_state.page = "customers"
                        st.session_state.customer_view = "detail"
                        st.session_state.selected_customer = c["id"]
                        st.rerun()
                with move_col2:
                    # Quick move to next stage
                    curr_idx = STAGES.index(stage)
                    if curr_idx < len(STAGES) - 1:
                        next_stage = STAGES[curr_idx + 1]
                        if st.button("→", key=f"move_kb_{c['id']}",
                                      help=f"Flytta till {next_stage}",
                                      use_container_width=True):
                            update_customer_status(c["id"], next_stage)
                            log_activity(c["id"], user["id"], "Statusändring",
                                          f"Flyttad i pipeline: {stage} → {next_stage}")
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── MOVE FORM (alternative) ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Flytta kund manuellt**")
    all_company_names = {f"{c['company_name']} ({c['status']})": c["id"] for c in customers}
    if all_company_names:
        move_c1, move_c2, move_c3 = st.columns([3, 2, 1])
        with move_c1:
            selected_cust = st.selectbox("Välj kund", list(all_company_names.keys()),
                                          label_visibility="collapsed", key="pipeline_cust_sel")
        with move_c2:
            new_stage = st.selectbox("Ny status", STAGES, label_visibility="collapsed",
                                      key="pipeline_stage_sel")
        with move_c3:
            if st.button("Flytta", type="primary", use_container_width=True):
                cid = all_company_names[selected_cust]
                update_customer_status(cid, new_stage)
                log_activity(cid, user["id"], "Statusändring", f"Manuellt flyttad till: {new_stage}")
                st.rerun()
