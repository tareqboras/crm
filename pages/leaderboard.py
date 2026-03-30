import streamlit as st
import sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import get_conn, get_users
from utils.ui_helpers import apply_global_style
import datetime

def get_leaderboard():
    conn = get_conn()
    rows = conn.execute("""
        SELECT u.name, u.id,
               COUNT(CASE WHEN c.status='Vunnen' THEN 1 END) as wins,
               COALESCE(SUM(CASE WHEN c.status='Vunnen' THEN q.yearly_saving ELSE 0 END), 0) as tb_year,
               COALESCE(SUM(CASE WHEN c.status='Vunnen'
                    AND strftime('%Y-%m', c.updated_at)=strftime('%Y-%m','now')
                    THEN q.yearly_saving ELSE 0 END), 0) as tb_month,
               COUNT(CASE WHEN c.status='Vunnen'
                    AND strftime('%Y-%m', c.updated_at)=strftime('%Y-%m','now')
                    THEN 1 END) as wins_month
        FROM users u
        LEFT JOIN customers c ON c.assigned_to = u.id
        LEFT JOIN quotes q ON q.customer_id = c.id AND q.status != 'Avvisad'
        WHERE u.role = 'seller'
        GROUP BY u.id
        ORDER BY tb_year DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_win():
    conn = get_conn()
    row = conn.execute("""
        SELECT c.company_name, c.updated_at, u.name as seller_name,
               COALESCE(q.yearly_saving, 0) as tb
        FROM customers c
        LEFT JOIN users u ON c.assigned_to = u.id
        LEFT JOIN quotes q ON q.customer_id = c.id
        WHERE c.status = 'Vunnen'
        ORDER BY c.updated_at DESC LIMIT 1
    """).fetchone()
    conn.close()
    return dict(row) if row else None

def get_total_tb():
    conn = get_conn()
    row = conn.execute("""
        SELECT COALESCE(SUM(q.yearly_saving), 0) as total
        FROM quotes q JOIN customers c ON q.customer_id = c.id
        WHERE c.status = 'Vunnen'
    """).fetchone()
    conn.close()
    return row[0] if row else 0

def show(user):
    apply_global_style()

    # Auto-refresh every 15 seconds
    st.markdown("""
    <script>
    setTimeout(function(){ window.location.reload(); }, 15000);
    </script>
    """, unsafe_allow_html=True)

    leaderboard = get_leaderboard()
    latest_win = get_latest_win()
    total_tb = get_total_tb()
    total_wins = sum(r["wins"] for r in leaderboard)

    # ── GLOBAL STYLES ────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] { background: #080C14 !important; }
    .block-container { padding-top: 0 !important; max-width: 100% !important; }
    #MainMenu, footer, header { visibility: hidden; }

    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
    @keyframes slideIn { from{transform:translateY(-20px);opacity:0} to{transform:translateY(0);opacity:1} }
    @keyframes countUp { from{transform:scale(0.8);opacity:0} to{transform:scale(1);opacity:1} }
    @keyframes glow { 0%,100%{box-shadow:0 0 20px rgba(16,185,129,0.3)} 50%{box-shadow:0 0 40px rgba(16,185,129,0.6)} }
    @keyframes shimmer {
        0%{background-position:-200% center}
        100%{background-position:200% center}
    }
    </style>
    """, unsafe_allow_html=True)

    # ── TOP HEADER ────────────────────────────────────────────────────────────
    now = datetime.datetime.now().strftime("%H:%M:%S")
    month = datetime.datetime.now().strftime("%B %Y").upper()

    st.markdown(f"""
    <div style="background:linear-gradient(180deg,#0D1420 0%,#080C14 100%);
                border-bottom:1px solid #1e3a5f;padding:20px 32px;
                display:flex;justify-content:space-between;align-items:center;
                margin:-1rem -1rem 0;">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="width:10px;height:10px;border-radius:50%;background:#10b981;
                        animation:pulse 2s infinite;box-shadow:0 0 8px #10b981;"></div>
            <span style="font-family:'Inter',sans-serif;font-size:13px;font-weight:600;
                         color:#64748b;letter-spacing:0.15em;text-transform:uppercase;">LIVE</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#334155;">{now}</span>
        </div>
        <div style="font-family:'Inter',sans-serif;font-size:22px;font-weight:900;
                    color:white;letter-spacing:0.05em;">⚡ SÄLJTAVLA</div>
        <div style="font-family:'Inter',sans-serif;font-size:12px;font-weight:600;
                    color:#334155;letter-spacing:0.1em;">{month}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'/>", unsafe_allow_html=True)

    # ── HERO STATS ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;padding:0 8px;margin-bottom:24px;">

        <div style="background:linear-gradient(135deg,#0a1628,#0f2040);
                    border:1px solid #1e3a5f;border-radius:16px;padding:28px 24px;
                    animation:slideIn 0.4s ease;">
            <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                        color:#3b82f6;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:10px;">
                Total TB · Alla säljare
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:42px;font-weight:700;
                        color:white;line-height:1;animation:countUp 0.6s ease;">
                {total_tb:,.0f} <span style="font-size:20px;color:#3b82f6;">kr</span>
            </div>
            <div style="font-size:12px;color:#334155;margin-top:8px;font-family:'Inter',sans-serif;">
                Ackumulerat · Alla perioder
            </div>
        </div>

        <div style="background:linear-gradient(135deg,#071a10,#0a2518);
                    border:1px solid #134d2a;border-radius:16px;padding:28px 24px;
                    animation:glow 3s infinite,slideIn 0.5s ease;">
            <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                        color:#10b981;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:10px;">
                Vunna affärer totalt
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:42px;font-weight:700;
                        color:#10b981;line-height:1;">
                {total_wins}
            </div>
            <div style="font-size:12px;color:#134d2a;margin-top:8px;font-family:'Inter',sans-serif;">
                Kunder markerade Vunnen
            </div>
        </div>

        <div style="background:linear-gradient(135deg,#1a0f00,#2a1800);
                    border:1px solid #4d3000;border-radius:16px;padding:28px 24px;
                    animation:slideIn 0.6s ease;">
            <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                        color:#f59e0b;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:10px;">
                Denna månad
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:42px;font-weight:700;
                        color:#f59e0b;line-height:1;">
                {sum(r['wins_month'] for r in leaderboard)}
            </div>
            <div style="font-size:12px;color:#4d3000;margin-top:8px;font-family:'Inter',sans-serif;">
                Sälj hittills denna månad
            </div>
        </div>

    </div>
    """, unsafe_allow_html=True)

    # ── LATEST WIN BANNER ─────────────────────────────────────────────────────
    if latest_win and latest_win.get("seller_name"):
        ts = (latest_win.get("updated_at") or "")[:16].replace("T", " ")
        tb = latest_win.get("tb", 0) or 0
        st.markdown(f"""
        <div style="background:linear-gradient(90deg,#071a10,#0a2518,#071a10);
                    border:1px solid #10b981;border-radius:12px;padding:16px 24px;
                    margin:0 8px 24px;display:flex;justify-content:space-between;align-items:center;
                    animation:glow 3s infinite;">
            <div style="display:flex;align-items:center;gap:16px;">
                <span style="font-size:24px;">🏆</span>
                <div>
                    <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                                color:#10b981;letter-spacing:0.12em;text-transform:uppercase;">
                        SENASTE SÄLJ
                    </div>
                    <div style="font-family:'Inter',sans-serif;font-size:16px;font-weight:700;color:white;margin-top:2px;">
                        {latest_win['seller_name']} vann <span style="color:#10b981;">{latest_win['company_name']}</span>
                    </div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:#10b981;">
                    +{tb:,.0f} kr/år
                </div>
                <div style="font-size:11px;color:#334155;margin-top:2px;">{ts}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── LEADERBOARD ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:0 8px;margin-bottom:12px;">
        <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                    color:#334155;letter-spacing:0.15em;text-transform:uppercase;">
            TOPPLISTA — TB PER SÄLJARE
        </div>
    </div>
    """, unsafe_allow_html=True)

    medals = ["🥇", "🥈", "🥉"]
    rank_colors = ["#f59e0b", "#94a3b8", "#cd7f32"]
    bar_colors = ["#f59e0b", "#3b82f6", "#8b5cf6", "#10b981", "#ef4444", "#06b6d4", "#ec4899"]

    max_tb = max((r["tb_year"] for r in leaderboard), default=1) or 1

    for i, seller in enumerate(leaderboard):
        bar_pct = max(seller["tb_year"] / max_tb * 100, 2)
        medal = medals[i] if i < 3 else f"#{i+1}"
        rank_color = rank_colors[i] if i < 3 else "#475569"
        bar_color = bar_colors[i % len(bar_colors)]
        tb_month = seller.get("tb_month", 0) or 0
        wins = seller.get("wins", 0)
        wins_month = seller.get("wins_month", 0)

        # Highlight current user
        is_me = seller["id"] == user["id"]
        bg = "background:linear-gradient(90deg,#0a1628,#0d1f38);" if is_me else "background:#0d1117;"
        border = "border:1px solid #1e3a5f;" if is_me else "border:1px solid #161b22;"

        st.markdown(f"""
        <div style="{bg}{border}border-radius:14px;padding:20px 24px;
                    margin:0 8px 10px;animation:slideIn {0.3 + i*0.1}s ease;
                    transition:all 0.2s;">
            <div style="display:flex;align-items:center;gap:20px;">

                <!-- Rank -->
                <div style="font-size:24px;min-width:40px;text-align:center;">{medal}</div>

                <!-- Name + bars -->
                <div style="flex:1;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                        <div>
                            <span style="font-family:'Inter',sans-serif;font-size:16px;font-weight:800;
                                         color:{'white' if is_me else '#e2e8f0'};">
                                {seller['name']} {'⭐' if is_me else ''}
                            </span>
                            <span style="font-size:11px;color:#334155;margin-right:12px;font-family:'Inter',sans-serif;">
                                &nbsp;{wins} sälj totalt · {wins_month} denna månad
                            </span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-family:'JetBrains Mono',monospace;font-size:22px;
                                        font-weight:700;color:{bar_color};">
                                {seller['tb_year']:,.0f} <span style="font-size:13px;color:#475569;">kr/år</span>
                            </div>
                            <div style="font-size:11px;color:#334155;font-family:'Inter',sans-serif;">
                                Denna månad: {tb_month:,.0f} kr
                            </div>
                        </div>
                    </div>

                    <!-- Progress bar -->
                    <div style="background:#161b22;border-radius:4px;height:6px;overflow:hidden;">
                        <div style="background:linear-gradient(90deg,{bar_color}80,{bar_color});
                                    width:{bar_pct}%;height:6px;border-radius:4px;
                                    transition:width 1s ease;"></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if not leaderboard:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#334155;">
            <div style="font-size:48px;margin-bottom:16px;">🎯</div>
            <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:600;color:#475569;">
                Inga sälj ännu — vem tar första platsen?
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:24px;margin-top:16px;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#1e293b;">
            AUTO-UPPDATERAS VAR 15:E SEKUND
        </div>
    </div>
    """, unsafe_allow_html=True)
