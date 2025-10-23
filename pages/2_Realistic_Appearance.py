import streamlit as st
import pandas as pd
import os
from utils import *


def realistic_appearance_page():
    setup_page_layout(
        "Realistic Appearance Assessment",
        "Evaluate the visual quality and realism of CT images",
        csv_path='realistic_appearance.csv',
        result_column='Realistic Appearance'
    )

    # Load data
    if not st.session_state.data_loaded:
        st.session_state.df = load_data(csv_path='realistic_appearance.csv')
        if st.session_state.df is not None:
            # Add result column if not exists
            if 'Realistic Appearance' not in st.session_state.df.columns:
                st.session_state.df['Realistic Appearance'] = ''
            # Add comment column if not exists
            if 'Comment' not in st.session_state.df.columns:
                st.session_state.df['Comment'] = ''
            st.session_state.current_index = find_first_unclassified_index(st.session_state.df, 'Realistic Appearance')
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
        current_result = str(row["Realistic Appearance"]) if pd.notna(row["Realistic Appearance"]) and row[
            "Realistic Appearance"] != '' else ""
        current_comment = str(row["Comment"]) if pd.notna(row["Comment"]) else ""

        # Statistics at top
        classified_count = len(df[df['Realistic Appearance'].notna() & (df['Realistic Appearance'] != '')])
        total_count = len(df)

        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("Total Images", total_count)
        with col_stat2:
            st.metric("Assessed", classified_count)
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
            st.info(f"🔄 **Current assessment:** **{current_result}**")
        else:
            st.success("🆕 **New image to assess**")

        # Image and controls
        col1, col2 = st.columns([2, 1])

        with col1:
            image, error = load_and_display_image(image_path)
            if error:
                st.error(error)
            else:
                st.image(image, caption=f"Case: {case_id}", width=300)

        with col2:
            st.subheader("Realistic Appearance")

            # Realistic Appearance options
            options = [
                "Not recognizable as CT",
                "Recognizable as CT, but overall unrealistic",
                "Mostly realistic with only minor unrealistic areas",
                "Overall realistic"
            ]

            # Find current selection index
            if current_result:
                try:
                    default_index = options.index(current_result)
                except ValueError:
                    default_index = 0
            else:
                default_index = 0

            realistic_appearance = st.radio(
                "Select the most appropriate description:",
                options,
                index=default_index,
                key=f"realistic_{current_index}"
            )

            # Comment box
            comment = st.text_area(
                "Additional Comments (optional):",
                value=current_comment,
                height=100,
                key=f"Comment_{current_index}",
                placeholder="Add any additional observations about image realism..."
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
                    st.session_state.df.at[current_index, 'Realistic Appearance'] = realistic_appearance
                    st.session_state.df.at[current_index, 'Comment'] = comment
                    st.session_state.df.to_csv("realistic_appearance.csv", index=False)

                    if not current_result and current_index < len(df) - 1:
                        next_unclassified = find_first_unclassified_index(df, 'Realistic Appearance')
                        if next_unclassified is not None:
                            st.session_state.current_index = next_unclassified

                    st.success(f"Assessment saved: {realistic_appearance}")
                    st.rerun()

        # CSV viewer with simplified navigation
        with st.expander("View All Images and Quick Navigation", expanded=True):
            fresh_df = load_data(csv_path='realistic_appearance.csv')

            # Display the dataframe with comment column
            st.dataframe(fresh_df[['CaseID', 'ImagePath', 'Realistic Appearance', 'Comment']])

            # Simplified navigation - just case numbers
            st.write("### Quick Navigation - Jump to Case:")

            # Create buttons in a grid
            num_cols = 6  # More columns to fit more buttons
            cols = st.columns(num_cols)

            for idx, case_id in enumerate(fresh_df['CaseID']):
                col_idx = idx % num_cols
                case_str = str(case_id)

                # Get current assessment status for color coding
                current_assessment = fresh_df.iloc[idx]['Realistic Appearance']
                if pd.isna(current_assessment) or current_assessment == '':
                    button_label = f"Case {case_str}"
                    button_type = "secondary"
                else:
                    button_label = f"Case {case_str} ✓"
                    button_type = "primary"

                with cols[col_idx]:
                    if st.button(button_label, key=f"jump_{case_str}", type=button_type):
                        st.session_state.jump_to_case = case_str
                        st.rerun()

            # Legend for button colors
            st.caption("🎯 **Legend:** Blue = Assessed, Gray = Not Assessed")

    else:
        st.info("No data available. Please check the CSV file.")

    # Reset button in sidebar
    with st.sidebar:
        st.header("Controls")
        if st.button("🔄 Reset All Assessments", type="secondary"):
            if st.session_state.df is not None:
                st.session_state.df['Realistic Appearance'] = ''
                st.session_state.df['Comment'] = ''
                st.session_state.df.to_csv("realistic_appearance.csv", index=False)
                st.session_state.current_index = 0
                st.session_state.show_celebration = False
                st.success("All assessments and comments reset!")
                st.rerun()

        if st.button("🏠 Back to Home"):
            st.switch_page("Main.py")


if __name__ == "__main__":
    realistic_appearance_page()