import streamlit as st
import runpy
import os

def render_chatbot():
    st.header('Chatbot')
    st.info('The chatbot UI is provided by chat.py (executed unchanged). If chat.py depends on absolute file paths, see README for guidance.')
    # Execute chat.py in-place so its Streamlit UI appears here.
    chat_path = os.path.join(os.path.dirname(__file__), '..', 'chat.py')
    chat_path = os.path.abspath(chat_path)
    try:
        runpy.run_path(chat_path, run_name='__main__')
    except Exception as e:
        st.error(f'Error running chat.py: {e}')
