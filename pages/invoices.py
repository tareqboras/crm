import streamlit as st
import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import (get_customers, get_customer, save_customer, get_invoices,
                              save_invoice, log_activity, get_api_key, init_invoice_tables)
from utils.ai_analyzer import analyze_invoice_with_ai, save_invoice_file
from utils.ui_helpers import LEAD_SOURCES, STAGES, apply_global_style

def show(user):
    apply_global_style()
    init_invoice_tables()

    st.markdown("""
    <style>
    html,body,[class*="css"],.stApp{background:#080C14!important;font-family:'Inter',sans-serif!important}
    .block-container{padding-top:0!important;max-width:100%!important}
    #MainMenu,footer,header{visibility:hidden}
    [data-testid="stSidebar"]{background:#0D1117!important;border-right:1px solid #161b22!important}
    [data-testid="stSidebar"] *{color:#8b949e!important}
    [data-testid="stSidebar"] .stButton>button{background:transparent!important;color:#8b949e!important;text-align:left!important;width:100%!important;border-radius:8px!important;border:none!important}
    [data-testid="stSidebar"] .stButton>button:hover{background:rgba(255,255,255,0.05)!important;color:white!important}
    .stButton>button{border-radius:8px!important;font-weight:600!important;border:1px solid #21262d!important;background:#161b22!important;color:#e6edf3!important}
    .stButton>button[kind="primary"]{background:#10b981!important;border-color:#10b981!important;color:white!important}
    .stTextInput input,.stTextArea textarea,.stNumberInput input{background:#161b22!important;border:1px solid #30363d!important;color:#e6edf3!important;border-radius:8px!important}
    .stSelectbox>div>div{background:#161b22!important;border:1px solid #30363d!important;color:#e6edf3!important;border-radius:8px!important}
    label,.stMarkdown p{color:#8b949e!important;font-size:13px!important}
    .stFileUploader{background:#161b22!important;border:1px solid #30363d!important;border-radius:8px!important}
    hr{border-color:#21262d!important}
    </style>
    """, unsafe_allow_html=True)

    if "invoice_view" not in st.session_state:
        st.session_state.invoice_view = "upload"

    # Header
    st.markdown("""
    <div style="background:linear-gradient(180deg,#0D1420,#080C14);border-bottom:1px solid #161b22;
                padding:24px 32px;margin:-1rem -1rem 0;">
        <div style="font-size:24px;font-weight:800;color:#e6edf3;">🤖 AI Fakturaanalys</div>
        <div style="font-size:13px;color:#8b949e;margin-top:4px;">Ladda upp en faktura — AI analyserar och beräknar besparingar automatiskt</div>
    </div>
    <div style="height:24px;"></div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📤 Ladda upp faktura", "📋 Analyserade fakturor"])

    # ── TAB 1: UPLOAD & ANALYZE ───────────────────────────────────────────────
    with tab1:
        customers = get_customers(user["id"], user["role"])
        if not customers:
            st.markdown("""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px;text-align:center;">
                <div style="font-size:32px;margin-bottom:12px;">👥</div>
                <div style="color:#e6edf3;font-weight:700;">Lägg till en kund först</div>
                <div style="color:#8b949e;font-size:13px;margin-top:8px;">Gå till Kunder och skapa ett kundkort innan du laddar upp en faktura</div>
            </div>""", unsafe_allow_html=True)
            if st.button("➕ Gå till kunder", type="primary"):
                st.session_state.page = "customers"
                st.rerun()
            return

        # Customer selector
        cust_opts = {f"{c['company_name']}": c["id"] for c in customers}
        pre_cid = st.session_state.get("invoice_customer")
        pre_name = next((k for k,v in cust_opts.items() if v == pre_cid), list(cust_opts.keys())[0])

        col1, col2 = st.columns([3,2])
        with col1:
            selected_cust = st.selectbox("Välj kund", list(cust_opts.keys()),
                                          index=list(cust_opts.keys()).index(pre_name))
            customer_id = cust_opts[selected_cust]

        with col2:
            api_key = get_api_key("anthropic")
            if not api_key:
                st.markdown("""
                <div style="background:#1a0f00;border:1px solid #4d3000;border-radius:8px;padding:12px;font-size:12px;color:#f59e0b;">
                ⚠️ Ingen API-nyckel → Demo-analys används. Lägg till nyckel i Inställningar.
                </div>""", unsafe_allow_html=True)

        # Upload area
        st.markdown("<div style='height:12px'/>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:11px;font-weight:700;color:#8b949e;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px;">LADDA UPP FAKTURA</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Dra och släpp faktura här (PDF eller bild)",
            type=["pdf","png","jpg","jpeg"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            file_bytes = uploaded_file.read()
            file_ext = uploaded_file.name.split(".")[-1].lower()

            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 16px;margin:12px 0;">
                <span style="font-size:13px;color:#e6edf3;">📎 {uploaded_file.name}</span>
                <span style="font-size:12px;color:#8b949e;margin-right:12px;"> · {len(file_bytes)/1024:.1f} KB</span>
            </div>""", unsafe_allow_html=True)

            if st.button("🤖 Analysera med AI", type="primary", use_container_width=True):
                with st.spinner("AI analyserar fakturan... detta tar 10–30 sekunder"):
                    result = analyze_invoice_with_ai(file_bytes, file_ext, api_key or None)

                if "error" in result:
                    st.error(f"Fel vid analys: {result['error']}")
                else:
                    # Save invoice
                    file_path = save_invoice_file(file_bytes, uploaded_file.name, customer_id)
                    save_invoice(
                        customer_id=customer_id,
                        filename=uploaded_file.name,
                        file_path=file_path,
                        user_id=user["id"],
                        ai_analysis=result,
                        total_monthly=result.get("total_monthly_excl_vat", 0),
                        supplier=result.get("supplier",""),
                        invoice_date=result.get("invoice_date","")
                    )
                    log_activity(customer_id, user["id"], "Offert",
                                  f"Faktura uppladdad och analyserad: {uploaded_file.name}")

                    st.session_state[f"analysis_result_{customer_id}"] = result
                    st.session_state.invoice_view = "result"
                    st.rerun()

        # Show analysis result
        if st.session_state.get("invoice_view") == "result":
            result = st.session_state.get(f"analysis_result_{customer_id}")
            if result:
                show_analysis_result(result, customer_id, user)

    # ── TAB 2: HISTORY ────────────────────────────────────────────────────────
    with tab2:
        all_customers = get_customers(user["id"], user["role"])
        for cust in all_customers:
            invoices = get_invoices(cust["id"])
            if not invoices:
                continue
            st.markdown(f"""
            <div style="font-size:13px;font-weight:700;color:#e6edf3;margin:16px 0 8px;
                        border-bottom:1px solid #161b22;padding-bottom:8px;">{cust['company_name']}</div>""",
                        unsafe_allow_html=True)
            for inv in invoices:
                analysis = inv.get("ai_analysis", {})
                savings = analysis.get("savings_analysis", {})
                monthly_saving = savings.get("estimated_saving_monthly_low", 0) or 0
                yearly_saving = monthly_saving * 12
                st.markdown(f"""
                <div style="background:#0d1117;border:1px solid #161b22;border-radius:10px;
                            padding:14px 16px;margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-weight:700;font-size:13px;color:#e6edf3;">📎 {inv['filename']}</div>
                            <div style="font-size:11px;color:#484f58;margin-top:3px;">
                                {inv.get('supplier','')} · {(inv.get('created_at') or '')[:10]}
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:13px;color:#f59e0b;font-weight:700;">{inv.get('total_monthly',0):,.0f} kr/mån</div>
                            <div style="font-size:11px;color:#10b981;">Besparing: ~{monthly_saving:,.0f} kr/mån</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

                if st.button(f"Visa analys", key=f"show_inv_{inv['id']}"):
                    st.session_state[f"show_full_inv_{inv['id']}"] = not st.session_state.get(f"show_full_inv_{inv['id']}", False)

                if st.session_state.get(f"show_full_inv_{inv['id']}"):
                    show_analysis_result(inv["ai_analysis"], cust["id"], user, compact=True)


def show_analysis_result(result: dict, customer_id: int, user, compact=False):
    savings = result.get("savings_analysis", {})
    services = result.get("services", [])
    total_monthly = result.get("total_monthly_excl_vat", 0) or 0
    saving_low = savings.get("estimated_saving_monthly_low", 0) or 0
    saving_high = savings.get("estimated_saving_monthly_high", 0) or 0
    saving_pct_low = savings.get("estimated_saving_pct_low", 35)
    saving_pct_high = savings.get("estimated_saving_pct_high", 45)

    # Hero savings banner
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#071a10,#0a2518);border:2px solid #10b981;
                border-radius:16px;padding:28px 32px;margin:16px 0;
                box-shadow:0 0 30px rgba(16,185,129,0.15);">
        <div style="font-size:11px;font-weight:700;color:#10b981;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:16px;">
            🤖 AI ANALYSRESULTAT — {result.get('company_name','') or result.get('supplier','')}
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:20px;">
            <div>
                <div style="font-size:11px;color:#484f58;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.1em;">NUVARANDE / MÅN</div>
                <div style="font-family:monospace;font-size:28px;font-weight:700;color:#e6edf3;">{total_monthly:,.0f} kr</div>
            </div>
            <div>
                <div style="font-size:11px;color:#484f58;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.1em;">MÖJLIG BESPARING / MÅN</div>
                <div style="font-family:monospace;font-size:28px;font-weight:700;color:#10b981;">{saving_low:,.0f}–{saving_high:,.0f} kr</div>
            </div>
            <div>
                <div style="font-size:11px;color:#484f58;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.1em;">BESPARING / ÅR</div>
                <div style="font-family:monospace;font-size:28px;font-weight:700;color:#f59e0b;">{saving_low*12:,.0f}–{saving_high*12:,.0f} kr</div>
            </div>
            <div>
                <div style="font-size:11px;color:#484f58;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.1em;">PROCENT</div>
                <div style="font-family:monospace;font-size:28px;font-weight:700;color:#a78bfa;">{saving_pct_low}–{saving_pct_high}%</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Services breakdown
    st.markdown('<div style="font-size:11px;font-weight:700;color:#8b949e;letter-spacing:0.15em;text-transform:uppercase;margin:20px 0 10px;">TJÄNSTER IDENTIFIERADE</div>', unsafe_allow_html=True)

    savings_per_svc = {s["service_type"]: s for s in savings.get("savings_per_service", [])}

    for svc in services:
        stype = svc.get("service_type","")
        sav = savings_per_svc.get(stype, {})
        sav_monthly = sav.get("saving_monthly", 0) or 0
        sav_pct = sav.get("saving_pct", 0) or 0
        hw_badge = '<span style="background:#3d1a7a20;color:#a78bfa;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;">HW</span>' if svc.get("is_hardware") else ""

        st.markdown(f"""
        <div style="background:#0d1117;border:1px solid #161b22;border-radius:10px;padding:14px 18px;margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="flex:1;">
                    <div style="font-weight:700;font-size:13px;color:#e6edf3;">
                        {stype} {hw_badge}
                        <span style="font-size:11px;color:#484f58;font-weight:400;margin-right:8px;"> · {svc.get('provider','')} · {svc.get('quantity',1)}x</span>
                    </div>
                    <div style="font-size:12px;color:#484f58;margin-top:3px;">{svc.get('description','')}</div>
                    {f'<div style="font-size:11px;color:#30363d;margin-top:2px;">Bindning: {svc.get("binding_months",0)} mån</div>' if svc.get('binding_months') else ''}
                </div>
                <div style="text-align:right;min-width:180px;">
                    <div style="font-family:monospace;font-size:15px;color:#e6edf3;font-weight:700;">{svc.get('monthly_price',0):,.0f} kr/mån</div>
                    {f'<div style="font-size:12px;color:#10b981;font-weight:600;">Spar ~{sav_monthly:,.0f} kr ({sav_pct}%)</div>' if sav_monthly > 0 else ''}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    # Analysis notes
    if savings.get("analysis_notes"):
        st.markdown(f"""
        <div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;padding:16px;margin:16px 0;">
            <div style="font-size:11px;font-weight:700;color:#3b82f6;letter-spacing:0.1em;margin-bottom:8px;">💡 AI:S ANALYS</div>
            <div style="font-size:13px;color:#8b949e;line-height:1.6;">{savings['analysis_notes']}</div>
        </div>""", unsafe_allow_html=True)

    # Action buttons
    if not compact:
        st.markdown("<div style='height:8px'/>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Skapa offert baserat på analysen", type="primary", use_container_width=True):
                st.session_state.page = "quotes"
                st.session_state.quote_customer = customer_id
                st.rerun()
        with c2:
            if st.button("👤 Gå till kundkort", use_container_width=True):
                st.session_state.page = "customers"
                st.session_state.customer_view = "detail"
                st.session_state.selected_customer = customer_id
                st.rerun()
