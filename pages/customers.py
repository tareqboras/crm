import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import (get_customers, get_customer, save_customer, delete_customer,
                              get_services, save_service, delete_service,
                              get_activities, log_activity, get_quotes, get_users,
                              update_customer_status)
from utils.ui_helpers import (STAGE_COLORS, STAGE_ICONS, ACTIVITY_ICONS, SERVICE_TYPES,
                               LEAD_SOURCES, STAGES, badge, apply_global_style, section_header)
import datetime

def show(user):
    apply_global_style()

    # ── STATE ─────────────────────────────────────────────────────────────────
    if "customer_view" not in st.session_state:
        st.session_state.customer_view = "list"
    if "selected_customer" not in st.session_state:
        st.session_state.selected_customer = None
    if st.session_state.get("action") == "new":
        st.session_state.customer_view = "new"
        st.session_state.action = None

    if st.session_state.customer_view == "list":
        show_list(user)
    elif st.session_state.customer_view == "new":
        show_form(user, None)
    elif st.session_state.customer_view == "edit":
        show_form(user, st.session_state.selected_customer)
    elif st.session_state.customer_view == "detail":
        show_detail(user, st.session_state.selected_customer)


def show_list(user):
    section_header("Kunder", "Alla dina kunder och leads")

    # Search + filter bar
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        search = st.text_input("🔍  Sök kund, kontakt, telefon...", key="cust_search",
                                placeholder="Sök...")
    with c2:
        status_filter = st.selectbox("Status", ["Alla"] + STAGES, key="cust_status")
    with c3:
        st.markdown("<div style='height:28px'/>", unsafe_allow_html=True)
        if st.button("➕  Ny kund", type="primary", use_container_width=True):
            st.session_state.customer_view = "new"
            st.rerun()

    status_val = None if status_filter == "Alla" else status_filter
    customers = get_customers(user["id"], user["role"],
                               search=search if search else None,
                               status=status_val)

    st.markdown(f"<div style='color:#64748b;font-size:13px;margin-bottom:12px;'>{len(customers)} kunder hittades</div>",
                unsafe_allow_html=True)

    if not customers:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#64748b;">
            <div style="font-size:48px;margin-bottom:12px;">👥</div>
            <div style="font-size:18px;font-weight:600;">Inga kunder ännu</div>
            <div style="font-size:14px;">Klicka på "Ny kund" för att lägga till din första kund</div>
        </div>""", unsafe_allow_html=True)
        return

    # Customer cards
    for c in customers:
        color = STAGE_COLORS.get(c["status"], "#64748b")
        icon = STAGE_ICONS.get(c["status"], "•")
        with st.container():
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:0;margin-bottom:8px;
                        border:1px solid #e2e8f0;border-right:4px solid {color};
                        transition:all 0.15s;">
                <div style="padding:14px 18px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-weight:800;font-size:15px;color:#1e293b;">{c['company_name']}</div>
                            <div style="font-size:12px;color:#64748b;margin-top:2px;">
                                {c.get('contact_person') or '—'} &nbsp;·&nbsp;
                                {c.get('phone') or '—'} &nbsp;·&nbsp;
                                {c.get('email') or '—'} &nbsp;·&nbsp;
                                📍 {c.get('city') or '—'}
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <span style="background:{color}20;color:{color};padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;">{icon} {c['status']}</span>
                            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">👤 {c.get('assigned_name') or '—'}</div>
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 5])
            with btn_col1:
                if st.button("👁 Visa", key=f"view_{c['id']}", use_container_width=True):
                    st.session_state.selected_customer = c["id"]
                    st.session_state.customer_view = "detail"
                    st.rerun()
            with btn_col2:
                if st.button("✏️ Redigera", key=f"edit_{c['id']}", use_container_width=True):
                    st.session_state.selected_customer = c["id"]
                    st.session_state.customer_view = "edit"
                    st.rerun()
            with btn_col3:
                if st.button("🗑", key=f"del_{c['id']}", use_container_width=True):
                    st.session_state[f"confirm_del_{c['id']}"] = True
                    st.rerun()

            if st.session_state.get(f"confirm_del_{c['id']}"):
                st.warning(f"Är du säker på att du vill ta bort **{c['company_name']}**?")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("Ja, ta bort", key=f"yes_del_{c['id']}", type="primary"):
                        delete_customer(c["id"])
                        st.session_state.pop(f"confirm_del_{c['id']}", None)
                        st.success("Kund borttagen")
                        st.rerun()
                with cc2:
                    if st.button("Avbryt", key=f"no_del_{c['id']}"):
                        st.session_state.pop(f"confirm_del_{c['id']}", None)
                        st.rerun()


def show_form(user, customer_id):
    existing = get_customer(customer_id) if customer_id else {}
    title = "Redigera kund" if customer_id else "Ny kund"
    section_header(title)

    if st.button("← Tillbaka"):
        st.session_state.customer_view = "list"
        st.rerun()

    users = get_users()
    user_opts = {u["name"]: u["id"] for u in users}

    with st.form("customer_form"):
        st.markdown("**Företagsinformation**")
        c1, c2 = st.columns(2)
        with c1:
            company = st.text_input("Företagsnamn *", value=existing.get("company_name",""))
            org = st.text_input("Organisationsnummer", value=existing.get("org_number","") or "")
            address = st.text_input("Adress", value=existing.get("address","") or "")
        with c2:
            city = st.text_input("Stad", value=existing.get("city","") or "")
            postal = st.text_input("Postnummer", value=existing.get("postal_code","") or "")
            lead_source = st.selectbox("Lead-källa", LEAD_SOURCES,
                                        index=LEAD_SOURCES.index(existing.get("lead_source","Kallringning"))
                                        if existing.get("lead_source") in LEAD_SOURCES else 0)

        st.markdown("---")
        st.markdown("**Kontaktperson**")
        c3, c4 = st.columns(2)
        with c3:
            contact = st.text_input("Kontaktperson", value=existing.get("contact_person","") or "")
            phone = st.text_input("Telefon", value=existing.get("phone","") or "")
        with c4:
            email = st.text_input("E-post", value=existing.get("email","") or "")
            status = st.selectbox("Status", STAGES,
                                   index=STAGES.index(existing.get("status","Ny"))
                                   if existing.get("status") in STAGES else 0)

        st.markdown("---")
        c5, c6 = st.columns(2)
        with c5:
            assigned_name = st.selectbox("Ansvarig säljare",
                                          list(user_opts.keys()),
                                          index=list(user_opts.values()).index(existing.get("assigned_to", user["id"]))
                                          if existing.get("assigned_to") in user_opts.values() else 0)
        with c6:
            notes = st.text_area("Anteckningar", value=existing.get("notes","") or "", height=80)

        submitted = st.form_submit_button("💾  Spara kund", type="primary", use_container_width=True)

        if submitted:
            if not company:
                st.error("Företagsnamn är obligatoriskt")
            else:
                data = {
                    "company_name": company, "org_number": org, "contact_person": contact,
                    "phone": phone, "email": email, "address": address, "city": city,
                    "postal_code": postal, "lead_source": lead_source,
                    "assigned_to": user_opts[assigned_name], "status": status, "notes": notes
                }
                cid = save_customer(data, customer_id)
                action = "Kund uppdaterad" if customer_id else "Ny kund skapad"
                log_activity(cid, user["id"], "Anteckning",
                              f"{'Kund uppdaterad' if customer_id else 'Kund skapad'}")
                st.success(f"✅ {action}!")
                st.session_state.selected_customer = cid
                st.session_state.customer_view = "detail"
                st.rerun()


def show_detail(user, customer_id):
    c = get_customer(customer_id)
    if not c:
        st.error("Kund hittades inte")
        return

    color = STAGE_COLORS.get(c["status"], "#64748b")

    # Top bar
    col_back, col_title, col_actions = st.columns([1, 5, 3])
    with col_back:
        if st.button("← Kunder"):
            st.session_state.customer_view = "list"
            st.rerun()
    with col_title:
        st.markdown(f"""
        <div style="padding:6px 0;">
            <h2 style="margin:0;font-size:22px;font-weight:800;color:#1e293b;">{c['company_name']}</h2>
            <span style="background:{color}20;color:{color};padding:2px 10px;border-radius:12px;font-size:12px;font-weight:700;">{STAGE_ICONS.get(c['status'],'')} {c['status']}</span>
        </div>""", unsafe_allow_html=True)
    with col_actions:
        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("✏️ Redigera", use_container_width=True):
                st.session_state.customer_view = "edit"
                st.rerun()
        with ca2:
            if st.button("📄 Ny offert", use_container_width=True, type="primary"):
                st.session_state.page = "quotes"
                st.session_state.quote_customer = customer_id
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Status changer
    new_status = st.selectbox("🔄 Ändra status", STAGES,
                               index=STAGES.index(c["status"]) if c["status"] in STAGES else 0,
                               key="status_changer")
    if new_status != c["status"]:
        if st.button("Uppdatera status"):
            update_customer_status(customer_id, new_status)
            log_activity(customer_id, user["id"], "Statusändring",
                          f"Status ändrad: {c['status']} → {new_status}")
            st.success(f"Status ändrad till {new_status}")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Info", "💼 Tjänster", "📄 Offerter", "📅 Aktivitet"])

    # ── TAB 1: INFO ───────────────────────────────────────────────────────────
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Kontaktuppgifter**")
            for label, val, icon in [
                ("Kontaktperson", c.get("contact_person"), "👤"),
                ("Telefon", c.get("phone"), "📞"),
                ("E-post", c.get("email"), "📧"),
                ("Adress", c.get("address"), "📍"),
                ("Stad", c.get("city"), "🏙"),
                ("Postnummer", c.get("postal_code"), ""),
            ]:
                if val:
                    st.markdown(f"""
                    <div style="display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #f1f5f9;">
                        <span style="color:#94a3b8;font-size:13px;min-width:130px;">{icon} {label}</span>
                        <span style="color:#1e293b;font-size:13px;font-weight:500;">{val}</span>
                    </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("**Övrigt**")
            for label, val, icon in [
                ("Org.nummer", c.get("org_number"), "🏢"),
                ("Lead-källa", c.get("lead_source"), "🎯"),
                ("Ansvarig", c.get("assigned_name"), "👤"),
                ("Skapad", (c.get("created_at") or "")[:10], "📅"),
                ("Uppdaterad", (c.get("updated_at") or "")[:10], "🔄"),
            ]:
                if val:
                    st.markdown(f"""
                    <div style="display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #f1f5f9;">
                        <span style="color:#94a3b8;font-size:13px;min-width:130px;">{icon} {label}</span>
                        <span style="color:#1e293b;font-size:13px;font-weight:500;">{val}</span>
                    </div>""", unsafe_allow_html=True)

        if c.get("notes"):
            st.markdown("<br>**Anteckningar**", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#f8fafc;border-radius:8px;padding:14px;border-left:3px solid #3b82f6;font-size:14px;color:#1e293b;">
                {c['notes']}
            </div>""", unsafe_allow_html=True)

        # Quick log activity
        st.markdown("<br>**Logga aktivitet**", unsafe_allow_html=True)
        with st.form("log_activity_form"):
            act_col1, act_col2 = st.columns([1, 3])
            with act_col1:
                act_type = st.selectbox("Typ", list(ACTIVITY_ICONS.keys()))
            with act_col2:
                act_desc = st.text_input("Beskrivning", placeholder="Vad hände?")
            if st.form_submit_button("✅ Logga", type="primary"):
                if act_desc:
                    log_activity(customer_id, user["id"], act_type, act_desc)
                    st.success("Aktivitet loggad!")
                    st.rerun()

    # ── TAB 2: SERVICES ───────────────────────────────────────────────────────
    with tab2:
        services = get_services(customer_id)
        st.markdown(f"**{len(services)} befintliga tjänster**")

        if services:
            total_monthly = sum(s.get("current_price") or 0 for s in services)
            st.markdown(f"""
            <div style="background:#1e293b;color:white;border-radius:10px;padding:12px 16px;margin-bottom:16px;display:inline-block;">
                <span style="font-size:13px;color:#94a3b8;">Total månadskostnad: </span>
                <span style="font-size:18px;font-weight:800;color:#f59e0b;">{total_monthly:,.0f} kr/mån</span>
            </div>""", unsafe_allow_html=True)

            for s in services:
                with st.expander(f"📦 {s['service_type']} — {s.get('provider','—')} — {s.get('current_price',0):,.0f} kr/mån"):
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1:
                        st.write(f"**Leverantör:** {s.get('provider','—')}")
                        st.write(f"**Pris/mån:** {s.get('current_price',0):,.0f} kr")
                    with sc2:
                        st.write(f"**Bindningstid:** {s.get('binding_months','—')} mån")
                        st.write(f"**Avtal slutar:** {s.get('contract_end','—') or '—'}")
                    with sc3:
                        if s.get("notes"):
                            st.write(f"**Notering:** {s['notes']}")
                    if st.button("🗑 Ta bort", key=f"del_srv_{s['id']}"):
                        delete_service(s["id"])
                        st.rerun()

        st.markdown("---")
        st.markdown("**Lägg till tjänst**")
        with st.form("add_service_form"):
            sc1, sc2 = st.columns(2)
            with sc1:
                svc_type = st.selectbox("Tjänst", SERVICE_TYPES)
                svc_provider = st.text_input("Leverantör")
                svc_price = st.number_input("Pris/mån (kr)", min_value=0.0, step=50.0)
            with sc2:
                svc_binding = st.number_input("Bindningstid (månader)", min_value=0, step=1)
                svc_end = st.text_input("Avtal slutar (ÅÅÅÅ-MM-DD)", placeholder="2025-12-31")
                svc_notes = st.text_input("Notering")
            if st.form_submit_button("➕ Lägg till tjänst"):
                save_service(customer_id, {
                    "service_type": svc_type, "provider": svc_provider,
                    "current_price": svc_price, "binding_months": svc_binding,
                    "contract_end": svc_end, "notes": svc_notes
                })
                log_activity(customer_id, user["id"], "Anteckning",
                              f"Tjänst tillagd: {svc_type} ({svc_provider}, {svc_price} kr/mån)")
                st.success("Tjänst sparad!")
                st.rerun()

    # ── TAB 3: QUOTES ─────────────────────────────────────────────────────────
    with tab3:
        quotes = get_quotes(customer_id=customer_id)
        if quotes:
            for q in quotes:
                q_color = {"Utkast":"#64748b","Skickad":"#3b82f6","Accepterad":"#10b981","Avvisad":"#ef4444"}.get(q["status"],"#64748b")
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:14px 18px;margin-bottom:8px;
                            border:1px solid #e2e8f0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-weight:700;font-size:14px;">Offert #{q['id']:04d}</span>
                            <span style="font-size:12px;color:#64748b;margin-right:12px;"> · {(q.get('created_at') or '')[:10]}</span>
                            <span style="background:{q_color}20;color:{q_color};padding:2px 8px;border-radius:8px;font-size:11px;font-weight:700;">{q['status']}</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:13px;color:#10b981;font-weight:700;">+{q.get('monthly_saving',0):,.0f} kr/mån</span>
                            <span style="font-size:12px;color:#64748b;"> · +{q.get('yearly_saving',0):,.0f} kr/år</span>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

                oc1, oc2 = st.columns([1, 4])
                with oc1:
                    if st.button("📥 PDF", key=f"dl_q_{q['id']}"):
                        st.session_state.page = "quotes"
                        st.session_state.view_quote = q["id"]
                        st.rerun()
        else:
            st.info("Inga offerter ännu för denna kund.")
        if st.button("➕ Skapa ny offert", type="primary"):
            st.session_state.page = "quotes"
            st.session_state.quote_customer = customer_id
            st.rerun()

    # ── TAB 4: ACTIVITY ───────────────────────────────────────────────────────
    with tab4:
        activities = get_activities(customer_id)
        if activities:
            for act in activities:
                icon = ACTIVITY_ICONS.get(act["activity_type"], "•")
                ts = (act.get("created_at") or "")[:16].replace("T", " ")
                st.markdown(f"""
                <div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #f1f5f9;align-items:flex-start;">
                    <span style="font-size:18px;min-width:28px;">{icon}</span>
                    <div style="flex:1;">
                        <div style="font-weight:600;font-size:13px;color:#1e293b;">{act['activity_type']}</div>
                        <div style="font-size:13px;color:#475569;margin-top:2px;">{act.get('description','')}</div>
                    </div>
                    <div style="text-align:right;min-width:120px;">
                        <div style="font-size:11px;color:#94a3b8;">{ts}</div>
                        <div style="font-size:11px;color:#64748b;">{act.get('user_name','')}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Ingen aktivitet loggad ännu.")
