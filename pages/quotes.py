import streamlit as st
import sys, os, tempfile
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import (get_customers, get_customer, get_services, save_quote,
                              get_quotes, get_quote, get_quote_items, update_quote_status,
                              get_users, log_activity)
from utils.pdf_generator import make_pdf
from utils.ui_helpers import SERVICE_TYPES, STAGES, apply_global_style, section_header

def show(user):
    apply_global_style()

    if "quote_view" not in st.session_state:
        st.session_state.quote_view = "list"

    # Pre-selected customer from customer card
    if st.session_state.get("quote_customer"):
        st.session_state.quote_view = "new"

    if st.session_state.quote_view == "list":
        show_list(user)
    elif st.session_state.quote_view == "new":
        show_builder(user)


def show_list(user):
    section_header("Offerter", "Alla offerter du skapat")

    col1, col2 = st.columns([5, 2])
    with col2:
        if st.button("➕  Ny offert", type="primary", use_container_width=True):
            st.session_state.quote_view = "new"
            st.rerun()

    quotes = get_quotes(user_id=user["id"], role=user["role"])
    if not quotes:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#64748b;">
            <div style="font-size:48px;">📄</div>
            <div style="font-size:18px;font-weight:600;margin-top:12px;">Inga offerter ännu</div>
        </div>""", unsafe_allow_html=True)
        return

    # Stats bar
    total_saving = sum(q.get("monthly_saving", 0) or 0 for q in quotes)
    sent = sum(1 for q in quotes if q.get("status") == "Skickad")
    won = sum(1 for q in quotes if q.get("status") == "Accepterad")

    mc1, mc2, mc3 = st.columns(3)
    for col, label, val, color in [
        (mc1, "Offerter totalt", len(quotes), "#3b82f6"),
        (mc2, "Skickade", sent, "#f59e0b"),
        (mc3, "Accepterade", won, "#10b981"),
    ]:
        with col:
            col.markdown(f"""
            <div style="background:white;border-radius:10px;padding:14px 18px;border:1px solid #e2e8f0;margin-bottom:16px;">
                <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">{label}</div>
                <div style="font-size:26px;font-weight:800;color:{color};">{val}</div>
            </div>""", unsafe_allow_html=True)

    for q in quotes:
        status_colors = {
            "Utkast": "#64748b", "Skickad": "#3b82f6",
            "Accepterad": "#10b981", "Avvisad": "#ef4444"
        }
        sc = status_colors.get(q.get("status","Utkast"), "#64748b")
        saving_m = q.get("monthly_saving", 0) or 0
        saving_y = q.get("yearly_saving", 0) or 0

        with st.container():
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:14px 18px;margin-bottom:6px;
                        border:1px solid #e2e8f0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:800;font-size:15px;color:#1e293b;">#{q['id']:04d} — {q['company_name']}</span>
                        <span style="background:{sc}20;color:{sc};padding:2px 8px;border-radius:8px;font-size:11px;font-weight:700;margin-right:8px;"> {q.get('status','Utkast')}</span>
                        <span style="font-size:12px;color:#64748b;">{(q.get('created_at') or '')[:10]} · {q.get('seller_name','')}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:14px;color:#10b981;font-weight:800;">+{saving_m:,.0f} kr/mån</span>
                        <span style="font-size:12px;color:#64748b;"> · +{saving_y:,.0f} kr/år</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            qc1, qc2, qc3, qc4 = st.columns([1,1,1,5])
            with qc1:
                if st.button("📥 PDF", key=f"pdf_{q['id']}"):
                    generate_and_download(q["id"], user)
            with qc2:
                new_s = st.selectbox("", ["Utkast","Skickad","Accepterad","Avvisad"],
                                      index=["Utkast","Skickad","Accepterad","Avvisad"].index(q.get("status","Utkast")),
                                      key=f"qs_{q['id']}", label_visibility="collapsed")
                if new_s != q.get("status"):
                    update_quote_status(q["id"], new_s)
                    log_activity(q["customer_id"], user["id"], "Offert", f"Offertstatus: {new_s}")
                    st.rerun()


def show_builder(user):
    section_header("Skapa offert", "Välj kund och lägg till tjänster")

    if st.button("← Tillbaka till offerter"):
        st.session_state.quote_view = "list"
        st.session_state.quote_customer = None
        st.rerun()

    customers = get_customers(user["id"], user["role"])
    if not customers:
        st.warning("Lägg till en kund innan du skapar en offert.")
        return

    cust_opts = {f"{c['company_name']} — {c.get('contact_person','')}": c["id"] for c in customers}

    # Pre-select if coming from customer card
    pre_cid = st.session_state.get("quote_customer")
    pre_name = next((k for k, v in cust_opts.items() if v == pre_cid), list(cust_opts.keys())[0])

    selected_cust_name = st.selectbox("Välj kund", list(cust_opts.keys()),
                                       index=list(cust_opts.keys()).index(pre_name)
                                       if pre_name in cust_opts else 0)
    customer_id = cust_opts[selected_cust_name]
    customer = get_customer(customer_id)
    existing_services = get_services(customer_id)

    # Show existing services as starting point
    if existing_services:
        st.markdown(f"""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px 16px;margin-bottom:16px;">
            <div style="font-weight:700;color:#166534;font-size:13px;">✅ {len(existing_services)} befintliga tjänster hittades</div>
            <div style="font-size:12px;color:#166534;">Nuvarande total: {sum(s.get('current_price',0) or 0 for s in existing_services):,.0f} kr/mån</div>
        </div>""", unsafe_allow_html=True)

    # Build quote items
    st.markdown("**Offertrader**")
    st.markdown("Fyll i en rad per tjänst. Lägg till leverantör, nuv. pris och ert erbjudna pris.")
    st.markdown("<br>", unsafe_allow_html=True)

    if "quote_items" not in st.session_state:
        # Pre-populate from existing services
        if existing_services:
            st.session_state.quote_items = [
                {"service_type": s["service_type"], "provider_current": s.get("provider",""),
                 "price_current": s.get("current_price", 0) or 0,
                 "provider_offered": "", "price_offered": 0, "binding_months": 24, "notes": ""}
                for s in existing_services
            ]
        else:
            st.session_state.quote_items = [
                {"service_type": "Mobiltelefoni", "provider_current": "",
                 "price_current": 0, "provider_offered": "", "price_offered": 0,
                 "binding_months": 24, "notes": ""}
            ]

    items = st.session_state.quote_items
    updated_items = []

    for idx, item in enumerate(items):
        with st.container():
            st.markdown(f"""<div style="background:white;border-radius:10px;border:1px solid #e2e8f0;padding:16px;margin-bottom:8px;">
            <div style="font-weight:700;font-size:13px;color:#64748b;margin-bottom:10px;">RAD {idx+1}</div>""",
                        unsafe_allow_html=True)
            r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns([2, 2, 1.5, 2, 1.5, 1.5])
            with r1c1:
                svc = st.selectbox("Tjänst", SERVICE_TYPES,
                                    index=SERVICE_TYPES.index(item["service_type"])
                                    if item["service_type"] in SERVICE_TYPES else 0,
                                    key=f"svc_{idx}")
            with r1c2:
                prov_cur = st.text_input("Nuv. leverantör", value=item.get("provider_current",""),
                                          key=f"pcur_{idx}", placeholder="ex. Telia")
            with r1c3:
                price_cur = st.number_input("Nuv. pris/mån", value=float(item.get("price_current",0) or 0),
                                             min_value=0.0, step=50.0, key=f"pcurp_{idx}")
            with r1c4:
                prov_off = st.text_input("Vår leverantör", value=item.get("provider_offered",""),
                                          key=f"poff_{idx}", placeholder="ex. Telenor")
            with r1c5:
                price_off = st.number_input("Vårt pris/mån", value=float(item.get("price_offered",0) or 0),
                                             min_value=0.0, step=50.0, key=f"poffp_{idx}")
            with r1c6:
                binding = st.number_input("Bindning (mån)", value=int(item.get("binding_months",24) or 24),
                                           min_value=0, step=12, key=f"bind_{idx}")
            st.markdown("</div>", unsafe_allow_html=True)

            saving = price_cur - price_off
            if saving != 0:
                color = "#10b981" if saving > 0 else "#ef4444"
                st.markdown(f"""<div style="font-size:12px;color:{color};font-weight:700;margin:-4px 0 6px 4px;">
                    Besparing: {saving:+,.0f} kr/mån · {saving*12:+,.0f} kr/år</div>""",
                             unsafe_allow_html=True)

            updated_items.append({
                "service_type": svc, "provider_current": prov_cur, "price_current": price_cur,
                "provider_offered": prov_off, "price_offered": price_off,
                "binding_months": binding, "notes": ""
            })

    st.session_state.quote_items = updated_items

    col_add, col_rem, _, col_save = st.columns([1.5, 1.5, 3, 2])
    with col_add:
        if st.button("➕ Lägg till rad"):
            st.session_state.quote_items.append({
                "service_type": "Mobiltelefoni", "provider_current": "",
                "price_current": 0, "provider_offered": "", "price_offered": 0,
                "binding_months": 24, "notes": ""
            })
            st.rerun()
    with col_rem:
        if st.button("➖ Ta bort sista") and len(st.session_state.quote_items) > 1:
            st.session_state.quote_items.pop()
            st.rerun()

    # Summary
    total_cur = sum(i.get("price_current", 0) or 0 for i in updated_items)
    total_off = sum(i.get("price_offered", 0) or 0 for i in updated_items)
    saving_m = total_cur - total_off
    saving_y = saving_m * 12

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:#1e293b;border-radius:12px;padding:20px 24px;display:flex;gap:32px;align-items:center;">
        <div><span style="font-size:12px;color:#94a3b8;">Nuv. total</span><br>
             <span style="font-size:20px;font-weight:800;color:white;">{total_cur:,.0f} kr/mån</span></div>
        <div style="font-size:24px;color:#64748b;">→</div>
        <div><span style="font-size:12px;color:#94a3b8;">Vårt pris</span><br>
             <span style="font-size:20px;font-weight:800;color:#3b82f6;">{total_off:,.0f} kr/mån</span></div>
        <div style="font-size:24px;color:#64748b;">=</div>
        <div><span style="font-size:12px;color:#94a3b8;">Besparing/mån</span><br>
             <span style="font-size:20px;font-weight:800;color:#10b981;">{saving_m:+,.0f} kr</span></div>
        <div><span style="font-size:12px;color:#94a3b8;">Besparing/år</span><br>
             <span style="font-size:20px;font-weight:800;color:#f59e0b;">{saving_y:+,.0f} kr</span></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with col_save:
        if st.button("💾  Spara & generera PDF", type="primary", use_container_width=True):
            valid_items = [i for i in updated_items if i.get("service_type")]
            if not valid_items:
                st.error("Lägg till minst en rad")
            else:
                quote_id = save_quote(customer_id, user["id"], valid_items)
                log_activity(customer_id, user["id"], "Offert",
                              f"Offert #{quote_id:04d} skapad — besparing {saving_m:,.0f} kr/mån")
                st.session_state.quote_items = None
                st.session_state.quote_customer = None
                st.success(f"✅ Offert #{quote_id:04d} sparad!")
                generate_and_download(quote_id, user)
                st.session_state.quote_view = "list"
                st.rerun()


def generate_and_download(quote_id, user):
    from utils.database import get_quote, get_quote_items, get_customer
    q = get_quote(quote_id)
    if not q:
        st.error("Offert hittades inte")
        return
    customer = get_customer(q["customer_id"])
    items = get_quote_items(quote_id)
    sellers = {u["id"]: u["name"] for u in get_users()}
    seller_name = sellers.get(q.get("created_by"), "Säljare")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        pdf_path = f.name

    make_pdf(q, customer, items, seller_name, pdf_path)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    st.download_button(
        label=f"⬇️ Ladda ned offert #{quote_id:04d}.pdf",
        data=pdf_bytes,
        file_name=f"offert_{quote_id:04d}_{customer.get('company_name','').replace(' ','_')}.pdf",
        mime="application/pdf",
        key=f"dl_final_{quote_id}"
    )
