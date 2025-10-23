# realistic_appearance.py
import streamlit as st
import pandas as pd
from utils import *  # uses: setup_page_layout, init_supabase, load_data, find_first_unclassified_index, find_case_index, load_and_display_image


# IMPORTANT:
# - Make sure your Supabase table "realistic_appearance" has a UNIQUE constraint on (case_id).
#   Example in SQL editor:
#   ALTER TABLE realistic_appearance ALTER COLUMN case_id TYPE text; -- if needed
#   ALTER TABLE realistic_appearance ADD CONSTRAINT realistic_appearance_case_id_key UNIQUE (case_id)


def realistic_appearance_page():
    setup_page_layout(
        "Realistic Appearance Assessment",
        "Evaluate the visual quality and realism of CT images",
        csv_path="realistic_appearance.csv",
        result_column="Assessment",
    )

    # Initialize Supabase
    supabase = init_supabase()

    # Load data once per task
    if not st.session_state.data_loaded:
        st.session_state.df = load_data(csv_path="realistic_appearance.csv")

        if st.session_state.df is not None:
            # Add temporary columns for session state (not in CSV)
            if "Assessment" not in st.session_state.df.columns:
                st.session_state.df["Assessment"] = ""
            if "Comment" not in st.session_state.df.columns:
                st.session_state.df["Comment"] = ""

            # Load existing assessments from Supabase and merge into DF
            try:
                response = supabase.table("realistic_appearance").select("*").execute()
                existing = {str(item["case_id"]): {
                    "assessment": item["assessment"],
                    "comment": item.get("comment", "")
                } for item in response.data or []}

                for idx, row in st.session_state.df.iterrows():
                    cid = str(row["CaseID"])
                    if cid in existing:
                        st.session_state.df.at[idx, "Assessment"] = existing[cid]["assessment"]
                        st.session_state.df.at[idx, "Comment"] = existing[cid]["comment"]
            except Exception as e:
                st.warning(f"Could not load data from Supabase: {e}")
                st.info("Check SUPABASE_URL and SUPABASE_KEY in utils.py")

            # Jump to first unassessed (for when user returns to app)
            first_uncl = find_first_unclassified_index(st.session_state.df, "Assessment")
            st.session_state.current_index = 0 if first_uncl is None else first_uncl
            st.session_state.data_loaded = True

    # Handle jump request (from quick nav)
    if st.session_state.jump_to_case is not None and st.session_state.df is not None:
        st.session_state.current_index = find_case_index(st.session_state.df, st.session_state.jump_to_case)
        st.session_state.jump_to_case = None
        st.rerun()

    # Main UI
    if st.session_state.df is not None and len(st.session_state.df) > 0:
        df = st.session_state.df
        current_index = max(0, min(st.session_state.current_index, len(df) - 1))

        row = df.iloc[current_index]
        case_id = str(row["CaseID"])
        image_path = str(row["ImagePath"])
        current_assessment = (
            str(row["Assessment"]) if pd.notna(row["Assessment"]) and row["Assessment"] != "" else ""
        )
        current_comment = (
            str(row["Comment"]) if pd.notna(row["Comment"]) and row["Comment"] != "" else ""
        )

        # Stats
        assessed_count = len(df[df["Assessment"].notna() & (df["Assessment"] != "")])
        total_count = len(df)
        remaining = total_count - assessed_count
        progress = (assessed_count / total_count) if total_count > 0 else 0.0

        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        col_stat1.metric("Total Images", total_count)
        col_stat2.metric("Assessed", assessed_count)
        col_stat3.metric("Remaining", remaining)
        col_stat4.metric("Progress", f"{progress:.1%}")

        st.markdown("---")

        # Current image section
        if current_assessment:
            st.info(f"🔄 **Current assessment:** **{current_assessment}**")
        else:
            st.success("🆕 **New image to assess**")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Load image from realistic_appearance subfolder
            image, error = load_and_display_image(image_path, subfolder="realistic_appearance")
            if error:
                st.error(error)
            else:
                st.image(image, caption=f"Case: {case_id}", width=300)

        with col2:
            st.subheader(f"Image {current_index + 1} of {len(df)}")

            # Assessment options
            options = [
                "Not recognizable as CT",
                "Recognizable as CT, but overall unrealistic",
                "Mostly realistic with only minor unrealistic areas",
                "Overall realistic"
            ]

            # Find current selection index
            if current_assessment:
                try:
                    default_index = options.index(current_assessment)
                except ValueError:
                    default_index = 0
            else:
                default_index = 0

            # Use a stable key per CASE ID (not per index)
            assessment_choice = st.radio(
                "Select the most appropriate description:",
                options,
                index=default_index,
                key=f"realistic_radio_{case_id}",
            )

            # Comment box
            comment_choice = st.text_area(
                "Additional Comments (optional):",
                value=current_comment,
                height=100,
                key=f"comment_{case_id}",
                placeholder="Add any additional observations about image realism..."
            )

            # Navigation buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if current_index > 0 and st.button("← Back", key=f"back_{case_id}"):
                    st.session_state.current_index = current_index - 1
                    st.rerun()

            with col_btn2:
                if current_index < len(df) - 1 and st.button("Skip →", key=f"skip_{case_id}"):
                    st.session_state.current_index = current_index + 1
                    st.rerun()

            with col_btn3:
                # Determine button label and behavior
                is_last_image = current_index == len(df) - 1

                if is_last_image:
                    button_label = "Restart" if current_assessment else "Save & Restart"
                    button_type = "secondary"
                else:
                    button_label = "Update & Next" if current_assessment else "Save & Next"
                    button_type = "primary"

                if st.button(button_label, type=button_type, key=f"save_{case_id}"):
                    try:
                        case_id_norm = str(case_id).strip()
                        assessment_norm = str(assessment_choice).strip()
                        comment_norm = str(comment_choice).strip()

                        # Save to Supabase
                        supabase.table("realistic_appearance").upsert({
                            "case_id": case_id_norm,
                            "assessment": assessment_norm,
                            "comment": comment_norm
                        }).execute()

                        # Update local session state
                        st.session_state.df.at[current_index, "Assessment"] = assessment_norm
                        st.session_state.df.at[current_index, "Comment"] = comment_norm

                        # Handle navigation after save
                        if is_last_image:
                            # Restart from beginning
                            st.session_state.current_index = 0
                            st.success(f"Assessment saved: {assessment_norm}. Restarting from first image.")
                        else:
                            # Move to next image (not first unassessed)
                            st.session_state.current_index = current_index + 1
                            st.success(f"Assessment saved: {assessment_norm}. Moving to next image.")

                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save to database: {e}")

        # Data viewer + quick navigation
        with st.expander("View All Images", expanded=True):
            fresh_df = load_data(csv_path="realistic_appearance.csv")

            try:
                response = supabase.table("realistic_appearance").select("*").execute()
                current_map = {str(item["case_id"]): {
                    "assessment": item["assessment"],
                    "comment": item.get("comment", "")
                } for item in response.data or []}

                # Create display dataframe with assessment data
                display_df = fresh_df.copy()
                display_df["Assessment"] = ""
                display_df["Comment"] = ""

                for idx, r in display_df.iterrows():
                    cid = str(r["CaseID"])
                    if cid in current_map:
                        display_df.at[idx, "Assessment"] = current_map[cid]["assessment"]
                        display_df.at[idx, "Comment"] = current_map[cid]["comment"]

                # Show relevant columns
                st.dataframe(display_df[["CaseID", "ImagePath", "Assessment", "Comment"]])

                st.write("### Quick Navigation")
                nav_cols = st.columns(4)
                for idx, (cid, assessment) in enumerate(
                        zip(display_df["CaseID"], display_df["Assessment"])):  # type: ignore
                    col_idx = idx % 4
                    cid_str = str(cid)
                    assessment_str = str(assessment) if pd.notna(assessment) and assessment != "" else "Unassessed"
                    with nav_cols[col_idx]:
                        if st.button(f"{cid_str} ({assessment_str})", key=f"jump_{cid_str}"):
                            st.session_state.jump_to_case = cid_str
                            st.rerun()
            except Exception as e:
                st.error(f"Could not load data: {e}")

    else:
        st.info("No data available. Please check the CSV file.")

    # Sidebar controls
    with st.sidebar:
        st.header("Controls")
        if st.button("🔄 Reset All Assessments", type="secondary"):
            if st.session_state.df is not None:
                try:
                    supabase.table("realistic_appearance").delete().gte("case_id", "").execute()
                    st.session_state.df["Assessment"] = ""
                    st.session_state.df["Comment"] = ""
                    st.session_state.current_index = 0
                    st.session_state.show_celebration = False
                    st.success("All assessments reset!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to reset: {e}")

        if st.button("🏠 Back to Home"):
            st.switch_page("main.py")


if __name__ == "__main__":
    realistic_appearance_page()