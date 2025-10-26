import streamlit as st
from backend import authenticate_user

def render_login():
    st.header('Login')
    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')
        if submitted:
            if not username or not password:
                st.error('Please provide both username and password.')
                return False
            if authenticate_user(username, password):
                st.session_state.user = username
                st.success('Login successful!')
                return True
            else:
                st.error('Invalid username or password.')
                return False
    return False
