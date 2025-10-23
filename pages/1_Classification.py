import streamlit as st
import pandas as pd
import os
from utils import *


def classification_page():
    setup_page_layout(
        "Image Classification",
        "Classify images as Real or Synthetic",
        csv_path='classification.csv',  # Fixed: consistent CSV name
        result_column='Classification'  # Fixed: consistent column name
    )

    # Load data
    if not st.session_state.data_loaded:
        st.session_state.df = load_data(csv_path="classification.csv")
        if st.session_state.df is not None:
            # Add Classification column if not exists
            if 'Classification' not in st.session_state.df.columns:
                st.session_state.df['Classification'] = ''
            st.session_state.current_index = find_first_unclassified_index(st.session_state.df,'Classification')
            st.session_state.data_loaded = True

    # Handle navigation
    if st.session_state.jump_to_case is not None and st.session_state.df is not None:
        st.session_state.current_index = find_case_index(st.session_state.df, st.session_state.jump_to_case)
        st.session_state.jump_to_case = None
        st.rerun()

    # Main interface
    if st.session_state.df is not None and len(st.session_state.df) > 0:
        df = st.session_state.df
        current_index = st.session_state.current_index

        row = df.iloc[current_index]
        case_id = str(row["CaseID"])
        image_path = str(row["ImagePath"])
        current_result = str(row["Classification"]) if pd.notna(row["Classification"]) and row["Classification"] != '' else ""

        # Statistics at top
        classified_count = len(df[df['Classification'].notna() & (df['Classification'] != '')])
        total_count = len(df)

        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("Total Images", total_count)
        with col_stat2:
            st.metric("Classified", classified_count)
        with col_stat3:
            st.metric("Remaining", total_count - classified_count)
        with col_stat4:
            progress = classified_count / total_count if total_count > 0 else 0
            st.metric("Progress", f"{progress:.1%}")

        st.markdown("---")

        # Current image info
        st.subheader(f"Image {current_index + 1} of {len(df)}")
        st.write(f"**Case ID:** {case_id}")

        if current_result:
            st.info(f"🔄 **Currently classified as:** **{current_result}**")
        else:
            st.success("🆕 **New image to classify**")

        # Image and controls
        col1, col2 = st.columns([2, 1])

        with col1:
            image, error = load_and_display_image(image_path)
            if error:
                st.error(error)
            else:
                st.image(image, caption=f"Case: {case_id}", width=300)

        with col2:
            st.subheader("Classification")

            # Classification options
            if current_result:
                default_index = 0 if current_result.lower() == "real" else 1
            else:
                default_index = 0

            classification = st.radio(
                "Is this image:",
                ["Real", "Synthetic"],
                index=default_index,
                key=f"class_{current_index}"
            )

            # Navigation buttons
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

            with col_btn1:
                if current_index > 0 and st.button("← Back", key=f"back_{current_index}"):
                    st.session_state.current_index -= 1
                    st.rerun()

            with col_btn2:
                if current_index < len(df) - 1 and st.button("Skip →", key=f"skip_{current_index}"):
                    st.session_state.current_index += 1
                    st.rerun()

            with col_btn3:
                button_label = "Update" if current_result else "Save"
                if st.button(f"{button_label} →", type="primary", key=f"save_{current_index}"):
                    st.session_state.df.at[current_index, 'Classification'] = classification
                    st.session_state.df.to_csv("classification.csv", index=False)

                    if not current_result and current_index < len(df) - 1:
                        next_unclassified = find_first_unclassified_index(df,'Classification')
                        if next_unclassified is not None:
                            st.session_state.current_index = next_unclassified

                    st.success(f"Classification saved as: {classification}")
                    st.rerun()

        # CSV viewer
        with st.expander("View All Images", expanded=True):
            fresh_df = load_data(csv_path='classification.csv')
            st.dataframe(fresh_df[['CaseID', 'ImagePath', 'Classification']])

            st.write("### Quick Navigation")
            cols = st.columns(4)
            for idx, (case_id, result) in enumerate(zip(fresh_df['CaseID'], fresh_df['Classification'])):
                col_idx = idx % 4
                case_str = str(case_id)
                result_str = str(result) if pd.notna(result) and result != '' else "Unclassified"
                with cols[col_idx]:
                    if st.button(f"{case_str} ({result_str})", key=f"jump_{case_str}"):
                        st.session_state.jump_to_case = case_str
                        st.rerun()

    else:
        st.info("No data available. Please check the CSV file.")

    # Reset button in sidebar
    with st.sidebar:
        st.header("Controls")
        if st.button("🔄 Reset All Labels", type="secondary"):
            if st.session_state.df is not None:
                st.session_state.df['Classification'] = ''
                st.session_state.df.to_csv("classification.csv", index=False)
                st.session_state.current_index = 0
                st.session_state.show_celebration = False
                st.success("All labels reset!")
                st.rerun()

        if st.button("🏠 Back to Home"):
            st.switch_page("Main.py")


if __name__ == "__main__":
    classification_page()