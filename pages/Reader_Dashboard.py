# pages/Reader_Dashboard.py
import streamlit as st
#new



def reader_dashboard():
    st.set_page_config(
        page_title="Medical Image Evaluation - Reader Dashboard",
        page_icon="🏥",
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

    # Check authentication and ensure user is NOT admin
    if not st.session_state.get('authenticated', False):
        st.warning("Please log in to access the application")
        st.switch_page("pages/login.py")
        return

    if st.session_state.get('is_admin', False):
        st.switch_page("pages/Admin_Dashboard.py")
        return

    # Header with user info and logout button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏥 Medical Image Evaluation Platform")
        st.markdown("### Comprehensive assessment of CT image quality and authenticity")
    with col2:
        st.write("")  # Spacer
        st.markdown(f"**👤 Logged in as:**  **{st.session_state.reader_name}**")
        if st.button("🚪 Logout", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


    st.markdown("---")

    # Center the module buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎯 Classification\n\nReal vs Synthetic", use_container_width=True,
                     help="Determine if images are real or synthetically generated"):
            st.switch_page("pages/Classification.py")

    with col2:
        if st.button("🖼️ Realistic Appearance\n\nImage Quality Assessment", use_container_width=True,
                     help="Assess the visual quality and realism of CT images"):
            st.switch_page("pages/Realistic_Appearance.py")

    with col3:
        if st.button("🔍 Anatomic Correctness\n\nStructural Accuracy", use_container_width=True,
                     help="Evaluate the anatomical accuracy and structural integrity"):
            st.switch_page("pages/Anatomic_Correctness.py")

    # Additional information
    st.markdown("---")
    st.markdown("""
    ### About This Tool

    This platform provides comprehensive evaluation of medical images through three specialized modules:

    - **🎯 Classification**: Determine if images are real or synthetically generated
    - **🖼️ Realistic Appearance**: Assess the visual quality and realism of CT images  
    - **🔍 Anatomic Correctness**: Evaluate the anatomical accuracy and structural integrity

    Select a module above to begin your evaluation.
    """)


if __name__ == "__main__":
    reader_dashboard()