import streamlit as st
from backend import init_db, get_user_by_username
from pages.Login import render_login
from pages.Register import render_register

st.set_page_config(page_title='Mental Health Chatbot', layout='wide')
init_db()

if 'user' not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    st.experimental_rerun()

st.title('🧠 Mental Health Chatbot (Auth)')

if st.session_state.user:
    user = get_user_by_username(st.session_state.user)
    st.sidebar.success(f'Logged in as {user["username"]}')
    st.sidebar.button('Logout', on_click=logout)
    # Show chatbot page
    from pages.Chatbot import render_chatbot
    render_chatbot()
else:
    col1, col2 = st.columns(2)
    with col1:
        if render_login():
            st.experimental_rerun()
    with col2:
        render_register()
