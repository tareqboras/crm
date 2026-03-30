import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import get_customers, get_quotes, get_users
from utils.ui_helpers import STAGE_COLORS, apply_global_style, section_header
import datetime, io

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

def show(user):
    apply_global_style()
    section_header("Rapporter", "Analys och statistik")

    customers = get_customers(user["id"], user["role"])
    quotes = get_quotes(user_id=user["id"], role=user["role"])
    users = get_users()
    sellers = {u["id"]: u["name"] for u in users}

    # ── FILTERS ───────────────────────────────────────────────────────────────
    now = datetime.date.today()
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        period = st.selectbox("Period", ["Denna månad", "Senaste 3 månader", "Detta år", "Totalt"])
    with fc2:
        if user["role"] == "admin":
            seller_filter = st.selectbox("Säljare", ["Alla"] + [u["name"] for u in users])
        else:
            seller_filter = user["name"]
    with fc3:
        pass

    # Filter customers by period
    def in_period(date_str):
        if not date_str:
            return False
        try:
            d = datetime.date.fromisoformat(date_str[:10])
        except:
            return False
        if period == "Denna månad":
            return d.year == now.year and d.month == now.month
        elif period == "Senaste 3 månader":
            return d >= now - datetime.timedelta(days=90)
        elif period == "Detta år":
            return d.year == now.year
        return True

    filtered_custs = [c for c in customers if in_period(c.get("updated_at",""))]
    if seller_filter != "Alla" and user["role"] == "admin":
        seller_id = next((u["id"] for u in users if u["name"] == seller_filter), None)
        filtered_custs = [c for c in filtered_custs if c.get("assigned_to") == seller_id]

    won = [c for c in filtered_custs if c["status"] == "Vunnen"]
    lost = [c for c in filtered_custs if c["status"] == "Förlorad"]
    active = [c for c in filtered_custs if c["status"] not in ["Vunnen","Förlorad"]]

    filtered_quotes = [q for q in quotes if in_period(q.get("created_at",""))]

    # ── KPI ROW ───────────────────────────────────────────────────────────────
    kc = st.columns(5)
    kpi_data = [
        ("Kunder i period", len(filtered_custs), "#3b82f6"),
        ("Vunna", len(won), "#10b981"),
        ("Förlorade", len(lost), "#ef4444"),
        ("Win rate", f"{round(len(won)/max(len(won)+len(lost),1)*100)}%", "#f59e0b"),
        ("Offerter skapade", len(filtered_quotes), "#8b5cf6"),
    ]
    for i, (label, val, color) in enumerate(kpi_data):
        with kc[i]:
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:14px;border:1px solid #e2e8f0;text-align:center;">
                <div style="font-size:10px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
                <div style="font-size:26px;font-weight:800;color:{color};margin-top:4px;">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CHARTS ────────────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Pipeline-fördelning**")
        stage_counts = {}
        for s, color in STAGE_COLORS.items():
            count = sum(1 for c in customers if c["status"] == s)
            if count > 0:
                stage_counts[s] = count

        if stage_counts and HAS_PLOTLY:
            fig = go.Figure(go.Bar(
                x=list(stage_counts.keys()),
                y=list(stage_counts.values()),
                marker_color=[STAGE_COLORS.get(s,"#64748b") for s in stage_counts],
                text=list(stage_counts.values()),
                textposition="outside",
            ))
            fig.update_layout(
                height=280, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Inter"),
                xaxis=dict(showgrid=False, tickfont=dict(size=11)),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            for s, count in stage_counts.items():
                color = STAGE_COLORS.get(s,"#64748b")
                bar_w = max(count / max(stage_counts.values(), default=1) * 100, 3)
                st.markdown(f"""
                <div style="margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
                        <span style="color:#1e293b;font-weight:600;">{s}</span>
                        <span style="color:{color};font-weight:700;">{count}</span>
                    </div>
                    <div style="background:#f1f5f9;border-radius:4px;height:8px;">
                        <div style="background:{color};width:{bar_w}%;height:8px;border-radius:4px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

    with chart_col2:
        st.markdown("**Lead-källfördelning**")
        lead_counts = {}
        for c in customers:
            ls = c.get("lead_source") or "Okänd"
            lead_counts[ls] = lead_counts.get(ls, 0) + 1

        if lead_counts and HAS_PLOTLY:
            fig2 = go.Figure(go.Pie(
                labels=list(lead_counts.keys()),
                values=list(lead_counts.values()),
                hole=0.5,
                marker_colors=["#3b82f6","#10b981","#f59e0b","#8b5cf6","#06b6d4","#ef4444","#64748b"],
            ))
            fig2.update_layout(
                height=280, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="white", font=dict(family="Inter"),
                showlegend=True, legend=dict(font=dict(size=10)),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            for ls, count in sorted(lead_counts.items(), key=lambda x: -x[1]):
                pct = round(count / len(customers) * 100)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:13px;">
                    <span style="color:#1e293b;">{ls}</span>
                    <span style="color:#64748b;font-weight:600;">{count} ({pct}%)</span>
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SELLER TABLE ──────────────────────────────────────────────────────────
    if user["role"] == "admin":
        st.markdown("**Säljartabell**")
        seller_stats = []
        for u in users:
            uid = u["id"]
            u_custs = [c for c in customers if c.get("assigned_to") == uid]
            u_won = sum(1 for c in u_custs if c["status"] == "Vunnen")
            u_lost = sum(1 for c in u_custs if c["status"] == "Förlorad")
            u_active = sum(1 for c in u_custs if c["status"] not in ["Vunnen","Förlorad"])
            u_quotes = [q for q in quotes if q.get("created_by") == uid or
                        any(c.get("id") == q.get("customer_id") and c.get("assigned_to") == uid for c in customers)]
            u_saving = sum(q.get("monthly_saving",0) or 0 for q in u_quotes) * 12
            wr = round(u_won / max(u_won+u_lost, 1) * 100)
            seller_stats.append({
                "Säljare": u["name"],
                "Kunder": len(u_custs),
                "Aktiva": u_active,
                "Vunna": u_won,
                "Förlorade": u_lost,
                "Win rate": f"{wr}%",
                "Pipeline-värde/år": f"{u_saving:,.0f} kr",
            })

        for row in seller_stats:
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:14px 18px;margin-bottom:6px;border:1px solid #e2e8f0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:800;font-size:14px;color:#1e293b;">👤 {row['Säljare']}</div>
                    <div style="display:flex;gap:20px;font-size:13px;">
                        <span><b>{row['Kunder']}</b> <span style="color:#64748b;">kunder</span></span>
                        <span><b style="color:#10b981;">{row['Vunna']}</b> <span style="color:#64748b;">vunna</span></span>
                        <span><b style="color:#ef4444;">{row['Förlorade']}</b> <span style="color:#64748b;">förlorade</span></span>
                        <span><b style="color:#f59e0b;">{row['Win rate']}</b> <span style="color:#64748b;">win rate</span></span>
                        <span><b style="color:#8b5cf6;">{row['Pipeline-värde/år']}</b> <span style="color:#64748b;">pipeline/år</span></span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # ── EXPORT ────────────────────────────────────────────────────────────────
    st.markdown("**Exportera data**")
    ec1, ec2 = st.columns(2)
    with ec1:
        if HAS_PANDAS:
            if st.button("⬇️ Exportera kunder (Excel)", use_container_width=True):
                df = pd.DataFrame(customers)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Kunder")
                st.download_button("📥 Ladda ned", data=buf.getvalue(),
                                    file_name="kunder_export.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Installera pandas för Excel-export: pip install pandas openpyxl")
    with ec2:
        if HAS_PANDAS:
            if st.button("⬇️ Exportera offerter (Excel)", use_container_width=True):
                df_q = pd.DataFrame(quotes)
                buf2 = io.BytesIO()
                with pd.ExcelWriter(buf2, engine="openpyxl") as writer:
                    df_q.to_excel(writer, index=False, sheet_name="Offerter")
                st.download_button("📥 Ladda ned", data=buf2.getvalue(),
                                    file_name="offerter_export.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
