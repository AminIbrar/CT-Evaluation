# main.py
import streamlit as st



# Initialize ALL session state variables here
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'reader_id' not in st.session_state:
        st.session_state.reader_id = None
    if 'reader_name' not in st.session_state:
        st.session_state.reader_name = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    # Module-specific session states
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'jump_to_case' not in st.session_state:
        st.session_state.jump_to_case = None
    if 'show_celebration' not in st.session_state:
        st.session_state.show_celebration = False
    if 'current_csv_path' not in st.session_state:
        st.session_state.current_csv_path = ""
    if 'current_result_column' not in st.session_state:
        st.session_state.current_result_column = ""

# Initialize session state
init_session_state()

# Hide sidebar on login page
st.set_page_config(initial_sidebar_state="collapsed")

# Redirect to login page
st.switch_page("pages/login.py")