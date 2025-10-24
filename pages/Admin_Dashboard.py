# pages/Admin_Dashboard.py
import streamlit as st
import pandas as pd
from utils import init_supabase

import streamlit as st

import streamlit as st


def admin_dashboard():
    st.set_page_config(
        page_title="Admin Dashboard - User Management",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Hide the default Streamlit sidebar navigation completely
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

    # Check if user is admin
    if not st.session_state.get('is_admin', False):
        st.error("⛔ Access denied. Admin privileges required.")
        st.switch_page("pages/Reader_Dashboard.py")
        return

    supabase = init_supabase()

    # Header with logout button at top right
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("👥 User Management Dashboard")
    with col2:

        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("🚪 Logout", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


    st.markdown("---")

    # Tabs for different admin functions
    tab1, tab2 = st.tabs(["📋 Manage Users", "➕ Add New User"])

    with tab1:
        manage_users_tab(supabase)

    with tab2:
        add_user_tab(supabase)


def manage_users_tab(supabase):
    st.header("📋 Current Users")

    try:
        # Get all readers
        response = supabase.table("readers").select("*").order("created_at").execute()
        readers = response.data

        if not readers:
            st.info("No users found in the system.")
            return

        # Convert to DataFrame for display
        df = pd.DataFrame(readers)

        # Format the dataframe for better display
        display_df = df[['reader_id', 'username', 'reader_name', 'is_active', 'created_at', 'last_login']].copy()
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['last_login'] = pd.to_datetime(display_df['last_login']).dt.strftime('%Y-%m-%d %H:%M') if display_df[
            'last_login'].notna().any() else 'Never'

        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", len(readers))
        with col2:
            active_users = len([r for r in readers if r['is_active']])
            st.metric("Active Users", active_users)
        with col3:
            inactive_users = len([r for r in readers if not r['is_active']])
            st.metric("Inactive Users", inactive_users)
        with col4:
            logged_in_users = len([r for r in readers if r['last_login']])
            st.metric("Users Logged In", logged_in_users)

        st.markdown("---")

        # Display users table with actions
        st.subheader("User List")

        for reader in readers:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])

                with col1:
                    st.write(f"**{reader['reader_name']}**")
                    st.write(f"Username: `{reader['username']}`")

                with col2:
                    st.write(f"ID: `{reader['reader_id']}`")
                    st.write(f"Created: {reader['created_at'][:10]}")

                with col3:
                    status = "🟢 Active" if reader['is_active'] else "🔴 Inactive"
                    st.write(f"Status: {status}")
                    if reader['last_login']:
                        st.write(f"Last Login: {reader['last_login'][:16]}")
                    else:
                        st.write("Last Login: Never")

                with col4:
                    # Toggle active status
                    if reader['is_active']:
                        if st.button("🚫 Deactivate", key=f"deactivate_{reader['reader_id']}"):
                            deactivate_user(supabase, reader['reader_id'])
                            st.rerun()
                    else:
                        if st.button("✅ Activate", key=f"activate_{reader['reader_id']}"):
                            activate_user(supabase, reader['reader_id'])
                            st.rerun()

                with col5:
                    # Delete user button
                    if st.button("🗑️ Delete", key=f"delete_{reader['reader_id']}"):
                        if delete_user(supabase, reader['reader_id']):
                            st.success(f"User {reader['username']} deleted successfully!")
                            st.rerun()

                st.markdown("---")

    except Exception as e:
        st.error(f"Error loading users: {e}")


def add_user_tab(supabase):
    st.header("➕ Add New User")

    with st.form("add_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("👤 Username", placeholder="Enter unique username")
            new_reader_name = st.text_input("📛 Full Name", placeholder="Enter reader's full name")

        with col2:
            new_password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm password")

        is_active = st.checkbox("✅ Activate user immediately", value=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button("👥 Create User", use_container_width=True)

    if submit_button:
        # Validate form
        if not all([new_username, new_reader_name, new_password, confirm_password]):
            st.error("❌ Please fill in all fields")
            return

        if new_password != confirm_password:
            st.error("❌ Passwords do not match")
            return

        if len(new_password) < 4:
            st.error("❌ Password must be at least 4 characters long")
            return

        # Create new user
        if create_new_user(supabase, new_username, new_reader_name, new_password, is_active):
            st.success(f"✅ User '{new_username}' created successfully!")
            st.rerun()


def create_new_user(supabase, username, reader_name, password, is_active=True):
    """Create a new reader user"""
    try:
        # Check if username already exists
        response = supabase.table("readers").select("username").eq("username", username).execute()
        if response.data:
            st.error(f"❌ Username '{username}' already exists")
            return False

        # Generate reader ID
        reader_id = f"reader_{len(supabase.table('readers').select('*').execute().data) + 1:03d}"

        # Insert new user
        response = supabase.table("readers").insert({
            "reader_id": reader_id,
            "username": username,
            "reader_name": reader_name,
            "password_hash": password,  # Plain text as requested
            "is_active": is_active,
            "created_by": st.session_state.get('reader_id', 'admin')
        }).execute()

        return True

    except Exception as e:
        st.error(f"❌ Error creating user: {e}")
        return False


def deactivate_user(supabase, reader_id):
    """Deactivate a user"""
    try:
        supabase.table("readers").update({
            "is_active": False
        }).eq("reader_id", reader_id).execute()
        st.success("✅ User deactivated successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error deactivating user: {e}")
        return False


def activate_user(supabase, reader_id):
    """Activate a user"""
    try:
        supabase.table("readers").update({
            "is_active": True
        }).eq("reader_id", reader_id).execute()
        st.success("✅ User activated successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error activating user: {e}")
        return False


def delete_user(supabase, reader_id):
    """Delete a user"""
    try:
        supabase.table("readers").delete().eq("reader_id", reader_id).execute()
        st.success("✅ User deleted successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error deleting user: {e}")
        return False


if __name__ == "__main__":
    admin_dashboard()