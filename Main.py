import streamlit as st
# 🏠 Home
st.set_page_config(
    page_title="CT Image Evaluation",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def main():
    # Custom CSS for styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 3.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #666;
            text-align: center;
            margin-bottom: 3rem;
        }
        .button-container {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 3rem;
        }
        .stButton button {
            width: 250px;
            height: 80px;
            font-size: 1.2rem;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="main-header">🏥 CT Image Evaluation Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive assessment of CT image quality and authenticity</div>',
                unsafe_allow_html=True)

    # Center the buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎯 Classification\nReal vs Synthetic", use_container_width=True):
            st.switch_page("pages/1_Classification.py")

    with col2:
        if st.button("🖼️ Realistic Appearance\nImage Quality Assessment", use_container_width=True):
            st.switch_page("pages/2_Realistic_Appearance.py")

    with col3:
        if st.button("🔍 Anatomic Correctness\nStructural Accuracy", use_container_width=True):
            st.switch_page("pages/3_Anatomic_Correctness.py")

    # Additional information
    st.markdown("---")
    st.markdown("""
    ### About This Tool

    This platform provides comprehensive evaluation of medical images through three specialized modules:

    - **Classification**: Determine if images are real or synthetically generated
    - **Realistic Appearance**: Assess the visual quality and realism of CT images  
    - **Anatomic Correctness**: Evaluate the anatomical accuracy and structural integrity

    Select a module above to begin your evaluation.
    """)


if __name__ == "__main__":
    main()