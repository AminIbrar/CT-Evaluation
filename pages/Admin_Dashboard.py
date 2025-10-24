# pages/Admin_Dashboard.py
import pandas as pd
from utils import init_supabase
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
    tab1, tab2, tab3 = st.tabs(["📋 Manage Users", "➕ Add New User", "📊 Data"])

    with tab1:
        manage_users_tab(supabase)

    with tab2:
        add_user_tab(supabase)

    with tab3:
        data_tab(supabase)


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


def data_tab(supabase):
    st.header("📊 Assessment Data")
    st.markdown("View and download all assessment data from the system.")

    # Create tabs for each assessment type
    data_tab1, data_tab2, data_tab3 = st.tabs(
        [" Classification Data", "Realistic Appearance Data", "Anatomic Correctness Data"])

    with data_tab1:
        display_classification_data(supabase)

    with data_tab2:
        display_realistic_appearance_data(supabase)

    with data_tab3:
        display_anatomic_correctness_data(supabase)


def display_classification_data(supabase):
    st.subheader("Classification Data")

    try:
        # Get all classification data
        response = supabase.table("classifications").select("*").execute()

        if not response.data:
            st.info("No classification data found.")
            return

        # Create DataFrame
        df = pd.DataFrame(response.data)

        # Format datetime
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Show statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            unique_cases = df['case_id'].nunique() if 'case_id' in df.columns else 0
            st.metric("Unique Cases", unique_cases)
        with col3:
            unique_readers = df['reader_id'].nunique() if 'reader_id' in df.columns else 0
            st.metric("Unique Readers", unique_readers)
        with col4:
            real_count = len(df[df['classification'] == 'Real']) if 'classification' in df.columns else 0
            st.metric("Real Classifications", real_count)

        st.markdown("---")

        # Display data
        st.dataframe(df, use_container_width=True)

        # Action buttons - only show if data exists
        if response.data:
            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="classification_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col3:
                # Reset button with popup confirmation
                if st.button("🗑️ Reset Data", type="secondary", use_container_width=True,
                             key="reset_classification_btn"):
                    st.session_state.show_reset_confirm_classification = True

            # Confirmation dialog
            if st.session_state.get('show_reset_confirm_classification', False):
                st.markdown("---")
                st.warning("⚠️ **Confirm Data Deletion**")
                st.error("This will permanently delete ALL classification data. This action cannot be undone!")

                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✅ YES, DELETE EVERYTHING", type="primary", use_container_width=True,
                                 key="confirm_classification_delete"):
                        if reset_classification_data(supabase):
                            st.session_state.show_reset_confirm_classification = False
                            st.rerun()

                with col3:
                    if st.button("❌ Cancel", use_container_width=True, key="cancel_classification_delete"):
                        st.session_state.show_reset_confirm_classification = False
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading classification data: {e}")


def display_realistic_appearance_data(supabase):
    st.subheader(" Realistic Appearance Data")

    try:
        # Get all realistic appearance data
        response = supabase.table("realistic_appearance").select("*").execute()

        if not response.data:
            st.info("No realistic appearance data found.")
            return

        # Create DataFrame
        df = pd.DataFrame(response.data)

        # Format datetime
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Show statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            unique_cases = df['case_id'].nunique() if 'case_id' in df.columns else 0
            st.metric("Unique Cases", unique_cases)
        with col3:
            unique_readers = df['reader_id'].nunique() if 'reader_id' in df.columns else 0
            st.metric("Unique Readers", unique_readers)

        st.markdown("---")

        # Display data
        st.dataframe(df, use_container_width=True)

        # Action buttons - only show if data exists
        if response.data:
            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="realistic_appearance_data.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_realistic"
                )

            with col3:
                # Reset button with popup confirmation
                if st.button("🗑️ Reset Data", type="secondary", use_container_width=True, key="reset_realistic_btn"):
                    st.session_state.show_reset_confirm_realistic = True

            # Confirmation dialog
            if st.session_state.get('show_reset_confirm_realistic', False):
                st.markdown("---")
                st.warning("⚠️ **Confirm Data Deletion**")
                st.error("This will permanently delete ALL realistic appearance data. This action cannot be undone!")

                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✅ YES, DELETE EVERYTHING", type="primary", use_container_width=True,
                                 key="confirm_realistic_delete"):
                        if reset_realistic_appearance_data(supabase):
                            st.session_state.show_reset_confirm_realistic = False
                            st.rerun()

                with col3:
                    if st.button("❌ Cancel", use_container_width=True, key="cancel_realistic_delete"):
                        st.session_state.show_reset_confirm_realistic = False
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading realistic appearance data: {e}")


def display_anatomic_correctness_data(supabase):
    st.subheader(" Anatomic Correctness Data")

    try:
        # Get all anatomic correctness data
        response = supabase.table("anatomic_correctness").select("*").execute()

        if not response.data:
            st.info("No anatomic correctness data found.")
            return

        # Create DataFrame
        df = pd.DataFrame(response.data)

        # Format datetime
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Show statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            unique_cases = df['case_id'].nunique() if 'case_id' in df.columns else 0
            st.metric("Unique Cases", unique_cases)
        with col3:
            unique_readers = df['reader_id'].nunique() if 'reader_id' in df.columns else 0
            st.metric("Unique Readers", unique_readers)

        st.markdown("---")

        # Display data
        st.dataframe(df, use_container_width=True)

        # Action buttons - only show if data exists
        if response.data:
            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="anatomic_correctness_data.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_anatomic"
                )

            with col3:
                # Reset button with popup confirmation
                if st.button("🗑️ Reset Data", type="secondary", use_container_width=True, key="reset_anatomic_btn"):
                    st.session_state.show_reset_confirm_anatomic = True

            # Confirmation dialog
            if st.session_state.get('show_reset_confirm_anatomic', False):
                st.markdown("---")
                st.warning("⚠️ **Confirm Data Deletion**")
                st.error("This will permanently delete ALL anatomic correctness data. This action cannot be undone!")

                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✅ YES, DELETE EVERYTHING", type="primary", use_container_width=True,
                                 key="confirm_anatomic_delete"):
                        if reset_anatomic_correctness_data(supabase):
                            st.session_state.show_reset_confirm_anatomic = False
                            st.rerun()

                with col3:
                    if st.button("❌ Cancel", use_container_width=True, key="cancel_anatomic_delete"):
                        st.session_state.show_reset_confirm_anatomic = False
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading anatomic correctness data: {e}")


def reset_classification_data(supabase):
    """Delete all classification data"""
    try:
        supabase.table("classifications").delete().neq("case_id", "").execute()
        st.success("✅ All classification data deleted successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error deleting classification data: {e}")
        return False


def reset_realistic_appearance_data(supabase):
    """Delete all realistic appearance data"""
    try:
        supabase.table("realistic_appearance").delete().neq("case_id", "").execute()
        st.success("✅ All realistic appearance data deleted successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error deleting realistic appearance data: {e}")
        return False


def reset_anatomic_correctness_data(supabase):
    """Delete all anatomic correctness data"""
    try:
        supabase.table("anatomic_correctness").delete().neq("case_id", "").execute()
        st.success("✅ All anatomic correctness data deleted successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error deleting anatomic correctness data: {e}")
        return False


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