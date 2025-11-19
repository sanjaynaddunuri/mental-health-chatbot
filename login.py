import streamlit as st
import subprocess
import sys
import os
import threading
import webbrowser
from db_users import UserDatabase  # Now this import will work!

def show_auth_page():
    st.set_page_config(page_title="Document Vault - Login", page_icon="🔐", layout="centered")
    
    if st.session_state.get('auth_status'):
        st.sidebar.success(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("🚪 Logout"):
            for key in ['auth_status', 'user_id', 'username']:
                st.session_state.pop(key, None)
            st.rerun()
        return True

    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("https://img.icons8.com/clouds/100/000000/lock.png", width=100)
        st.markdown("<h1 style='color: #1E3A8A; text-align: center;'>Document Vault</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                user = st.text_input("Username", placeholder="Enter username")
                pwd = st.text_input("Password", type="password", placeholder="Enter password")
                if st.form_submit_button("🔐 Login", use_container_width=True):
                    if user and pwd:
                        db = UserDatabase()
                        success, data = db.verify_user(user, pwd)
                        if success:
                            st.session_state.auth_status = True
                            st.session_state.user_id = str(data['_id'])
                            st.session_state.username = data['username']
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials!")
                    else:
                        st.error("⚠️ Fill all fields!")
        
        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("Username", placeholder="Min 3 characters")
                new_pwd = st.text_input("Password", type="password", placeholder="Min 6 characters")
                confirm_pwd = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("📝 Sign Up", use_container_width=True):
                    if new_user and new_pwd and confirm_pwd:
                        if len(new_user) < 3: st.error("⚠️ Username too short!")
                        elif len(new_pwd) < 6: st.error("⚠️ Password too short!")
                        elif new_pwd != confirm_pwd: st.error("❌ Passwords don't match!")
                        else:
                            db = UserDatabase()
                            success, msg = db.register_user(new_user, new_pwd)
                            if success: st.success(f"✅ {msg}")
                            else: st.error(f"❌ {msg}")
                    else:
                        st.error("⚠️ Fill all fields!")
    
    return False

def run_app():
    os.system("streamlit run app.py")

def redirect_to_app():
    """✅ Runs app.py in a new tab using os.system"""
    if st.session_state.get('auth_status') and not st.session_state.get('redirected'):
        st.session_state.redirected = True
        st.success("🎉 Login successful! Launching Document Vault...")

        with st.spinner("Loading..."):
            try:
                # Run app.py in a separate thread so Streamlit doesn't freeze
                threading.Thread(target=run_app, daemon=True).start()
                st.info("📂 App launched in a new tab. If not opened, check your browser.")
                st.stop()
            except Exception as e:
                st.error(f"Launch failed: {e}")

# Main execution
if __name__ == "__main__":
    if show_auth_page():
        redirect_to_app()