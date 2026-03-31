import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.database import get_users, create_user, hash_password, get_conn
from utils.ui_helpers import apply_global_style, section_header

def show(user):
    apply_global_style()
    section_header("Inställningar", "Hantera användare och systeminställningar")

    tab1, tab2 = st.tabs(["👥 Användare", "⚙️ Konto"])

    with tab1:
        if user["role"] != "admin":
            st.warning("Endast administratörer kan hantera användare.")
            return

        st.markdown("**Lägg till användare**")
        with st.form("new_user_form"):
            uc1, uc2 = st.columns(2)
            with uc1:
                new_name = st.text_input("Namn")
                new_email = st.text_input("E-post")
            with uc2:
                new_password = st.text_input("Lösenord", type="password")
                new_role = st.selectbox("Roll", ["seller", "admin"])
            if st.form_submit_button("➕ Skapa användare", type="primary"):
                if new_name and new_email and new_password:
                    ok = create_user(new_name, new_email, new_password, new_role)
                    if ok:
                        st.success(f"✅ Användare {new_name} skapad!")
                        st.rerun()
                    else:
                        st.error("E-postadressen är redan registrerad")
                else:
                    st.error("Fyll i alla fält")

        st.markdown("---")
        st.markdown("**Befintliga användare**")
        users = get_users()

        st.markdown('---')
        st.markdown('**🤖 AI-integration (Anthropic API)**')
        from utils.database import get_api_key, save_api_key
        current_key = get_api_key('anthropic')
        with st.form('api_key_form'):
            new_key = st.text_input('Anthropic API-nyckel', value=current_key,
                                     type='password', placeholder='sk-ant-...')
            st.markdown('<div style="font-size:12px;color:#64748b;">Hämta nyckel på console.anthropic.com · Krävs för AI-fakturaanalys</div>', unsafe_allow_html=True)
            if st.form_submit_button('💾 Spara API-nyckel', type='primary'):
                save_api_key('anthropic', new_key)
                st.success('✅ API-nyckel sparad!')
        for u in users:
            role_color = "#3b82f6" if u["role"] == "admin" else "#10b981"
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:12px 16px;margin-bottom:6px;border:1px solid #e2e8f0;
                        display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-weight:700;font-size:14px;color:#1e293b;">{u['name']}</span>
                    <span style="font-size:13px;color:#64748b;margin-right:10px;"> · {u['email']}</span>
                    <span style="background:{role_color}20;color:{role_color};padding:2px 8px;border-radius:8px;font-size:11px;font-weight:700;">{u['role'].upper()}</span>
                </div>
                <span style="font-size:12px;color:#94a3b8;">{(u.get('created_at') or '')[:10]}</span>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("**Byt lösenord**")
        with st.form("change_pw_form"):
            old_pw = st.text_input("Nuvarande lösenord", type="password")
            new_pw = st.text_input("Nytt lösenord", type="password")
            new_pw2 = st.text_input("Bekräfta nytt lösenord", type="password")
            if st.form_submit_button("🔒 Byt lösenord", type="primary"):
                from utils.database import verify_user
                if verify_user(user["email"], old_pw):
                    if new_pw == new_pw2 and len(new_pw) >= 6:
                        conn = get_conn()
                        conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                                     (hash_password(new_pw), user["id"]))
                        conn.commit(); conn.close()
                        st.success("✅ Lösenord bytt!")
                    else:
                        st.error("Lösenorden matchar inte eller är för korta (min 6 tecken)")
                else:
                    st.error("Fel nuvarande lösenord")

        st.markdown("---")
        st.markdown(f"""
        <div style="background:#f8fafc;border-radius:10px;padding:16px;">
            <div style="font-weight:700;font-size:14px;color:#1e293b;">Inloggad som</div>
            <div style="font-size:13px;color:#64748b;margin-top:4px;">{user['name']} · {user['email']} · Roll: {user['role']}</div>
        </div>""", unsafe_allow_html=True)
