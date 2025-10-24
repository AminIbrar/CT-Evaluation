# pages/login.py
import streamlit as st
from utils import init_supabase



def login_page():
    st.set_page_config(
        page_title="Medical Image Evaluation - Login",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"  # Hide sidebar on login
    )

    # Custom CSS for styling
    st.markdown("""
        <style>
        .main {
            max-width: 350px !important;
            padding: 2rem 1rem !important;
        }
        .main .block-container {
            max-width: 320px !important;
            padding: 1rem !important;
        }
        .login-header {
            text-align: center;
            color: #1f77b4;
            margin-bottom: 2rem;
        }
        .stButton button {
            width: 100%;
        }
        /* Hide sidebar on login page */
        section[data-testid="stSidebar"] {
            display: none;
        }
        .stApp > header {
            display: none;
        }
        /* Make the form container narrower */
        .stForm {
            max-width: 300px !important;
            margin: 0 auto !important;
        }
        /* Target the form content specifically */
        [data-testid="stForm"] {
            max-width: 300px !important;
            margin: 0 auto !important;
        }
        /* Make text inputs narrower */
        .stTextInput input {
            max-width: 280px !important;
        }
        /* Make the button container narrower */
        .stButton {
            max-width: 280px !important;
            margin: 0 auto !important;
        }
        </style>
    """, unsafe_allow_html=True)

    supabase = init_supabase()


    # Header
    st.markdown('<div class="login-header"><h1>🏥 Medical Image Evaluation</h1><h3>Please Login</h3></div>',
                unsafe_allow_html=True)

    # Login Form - using columns to constrain width
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")

            login_button = st.form_submit_button("🚀 Login", use_container_width=True)

    if login_button:
        if not username or not password:
            st.error("❌ Please enter both username and password")
        else:
            # Check if user exists and password is correct
            user = authenticate_user(supabase, username, password)

            if user:
                # Set session state
                st.session_state.authenticated = True
                st.session_state.reader_id = user['reader_id']
                st.session_state.reader_name = user['reader_name']
                st.session_state.username = username
                st.session_state.is_admin = user.get('is_admin', False)

                # Update last login time
                update_last_login(supabase, user['reader_id'])

                st.success(f"✅ Welcome, {user['reader_name']}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")


def authenticate_user(supabase, username, password):
    """Authenticate user against database"""
    try:
        # First check if it's a reader
        response = supabase.table("readers").select("*").eq("username", username).eq("is_active", True).execute()

        if response.data and len(response.data) > 0:
            reader = response.data[0]
            # Simple password check (plain text comparison)
            if reader['password_hash'] == password:
                return {
                    'reader_id': reader['reader_id'],
                    'reader_name': reader['reader_name'],
                    'is_admin': False
                }

        # Check if it's an admin user
        response = supabase.table("admin_users").select("*").eq("username", username).execute()

        if response.data and len(response.data) > 0:
            admin = response.data[0]
            # Simple password check (plain text comparison)
            if admin['password_hash'] == password:
                st.success("🔧 Admin privileges granted!")  # This is the new line
                return {
                    'reader_id': admin['admin_id'],
                    'reader_name': f"Admin ({admin['username']})",
                    'is_admin': True
                }

        return None

    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None


def update_last_login(supabase, user_id):
    """Update last login timestamp"""
    try:
        supabase.table("readers").update({
            "last_login": "now()"
        }).eq("reader_id", user_id).execute()
    except:
        pass  # Silently fail if it's an admin user


# Check if user is already authenticated - use get() to avoid KeyError
if st.session_state.get('authenticated', False):
    # Redirect based on user type
    if st.session_state.get('is_admin', False):
        st.switch_page("pages/Admin_Dashboard.py")
    else:
        st.switch_page("pages/Reader_Dashboard.py")
else:
    login_page()

