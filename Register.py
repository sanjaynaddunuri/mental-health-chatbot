import streamlit as st
from backend import create_user

def render_register():
    st.header('Register')
    with st.form('register_form'):
        username = st.text_input('Choose a username')
        email = st.text_input('Email')
        password = st.text_input('Password', type='password')
        confirm = st.text_input('Confirm Password', type='password')
        submitted = st.form_submit_button('Create account')
        if submitted:
            if not username or not email or not password or not confirm:
                st.error('Please fill out all fields.')
                return
            if password != confirm:
                st.error('Passwords do not match.')
                return
            ok = create_user(username.strip(), email.strip(), password)
            if ok:
                st.success('Account created! You can now log in.')
            else:
                st.error('Username or email already exists. Try a different one.')
