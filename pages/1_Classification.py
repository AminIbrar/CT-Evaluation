# classification.py
import streamlit as st
import pandas as pd
from utils import *  # uses: setup_page_layout, init_supabase, load_data, find_first_unclassified_index, find_case_index, load_and_display_image


# IMPORTANT:
# - Make sure your Supabase table "classifications" has a UNIQUE constraint on (case_id).
#   Example in SQL editor:
#   ALTER TABLE classifications ALTER COLUMN case_id TYPE text; -- if needed
#   ALTER TABLE classifications ADD CONSTRAINT classifications_case_id_key UNIQUE (case_id)


def classification_page():
    setup_page_layout(
        "Image Classification",
        "Classify images as Real or Synthetic",
        csv_path="classification.csv",
        result_column="Classification",
    )

    # Initialize Supabase
    supabase = init_supabase()

    # Load data once per task
    if not st.session_state.data_loaded:
        st.session_state.df = load_data(csv_path="classification.csv")

        if st.session_state.df is not None:
            # Load existing classifications from Supabase and merge into DF
            try:
                response = supabase.table("classifications").select("*").execute()
                existing = {str(item["case_id"]): item["classification"] for item in response.data or []}

                for idx, row in st.session_state.df.iterrows():
                    cid = str(row["CaseID"])
                    if cid in existing:
                        st.session_state.df.at[idx, "Classification"] = existing[cid]
            except Exception as e:
                st.warning(f"Could not load data from Supabase: {e}")
                st.info("Check SUPABASE_URL and SUPABASE_KEY in utils.py")

            # Jump to first unclassified (for when user returns to app)
            first_uncl = find_first_unclassified_index(st.session_state.df, "Classification")
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
        current_result = (
            str(row["Classification"]) if pd.notna(row["Classification"]) and row["Classification"] != "" else ""
        )

        # Stats
        classified_count = len(df[df["Classification"].notna() & (df["Classification"] != "")])
        total_count = len(df)
        remaining = total_count - classified_count
        progress = (classified_count / total_count) if total_count > 0 else 0.0

        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        col_stat1.metric("Total Images", total_count)
        col_stat2.metric("Classified", classified_count)
        col_stat3.metric("Remaining", remaining)
        col_stat4.metric("Progress", f"{progress:.1%}")

        st.markdown("---")

        # Current image section
        if current_result:
            st.info(f"🔄 **Currently classified as:** **{current_result}**")
        else:
            st.success("🆕 **New image to classify**")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Updated: Pass subfolder name
            image, error = load_and_display_image(image_path, subfolder="classification")
            if error:
                st.error(error)
            else:
                st.image(image, caption=f"Case: {case_id}", width=300)

        with col2:
            st.subheader(f"Image {current_index + 1} of {len(df)}")

            # Default selection mirrors current_result
            default_index = 0 if (current_result and current_result.lower() == "real") else (1 if current_result else 0)

            # Use a stable key per CASE ID (not per index)
            classification_choice = st.radio(
                "Is this image:",
                ["Real", "Synthetic"],
                index=default_index,
                key=f"class_radio_{case_id}",
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
                    button_label = "Restart" if current_result else "Save & Restart"
                    button_type = "secondary"
                else:
                    button_label = "Update & Next" if current_result else "Save & Next"
                    button_type = "primary"

                if st.button(button_label, type=button_type, key=f"save_{case_id}"):
                    try:
                        case_id_norm = str(case_id).strip()
                        class_norm = str(classification_choice).strip()

                        # Save to Supabase
                        supabase.table("classifications").upsert({
                            "case_id": case_id_norm,
                            "classification": class_norm
                        }).execute()

                        # Update local session state
                        st.session_state.df.at[current_index, "Classification"] = class_norm

                        # Handle navigation after save
                        if is_last_image:
                            # Restart from beginning
                            st.session_state.current_index = 0
                            st.success(f"Classification saved as: {class_norm}. Restarting from first image.")
                        else:
                            # Move to next image (not first unclassified)
                            st.session_state.current_index = current_index + 1
                            st.success(f"Classification saved as: {class_norm}. Moving to next image.")

                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save to database: {e}")

        # Data viewer + quick navigation
        with st.expander("View All Images", expanded=True):
            fresh_df = load_data(csv_path="classification.csv")

            try:
                response = supabase.table("classifications").select("*").execute()
                current_map = {str(item["case_id"]): item["classification"] for item in response.data or []}

                display_df = fresh_df.copy()
                for idx, r in display_df.iterrows():
                    cid = str(r["CaseID"])
                    if cid in current_map:
                        display_df.at[idx, "Classification"] = current_map[cid]

                st.dataframe(display_df[["CaseID", "ImagePath", "Classification"]])

                st.write("### Quick Navigation")
                nav_cols = st.columns(4)
                for idx, (cid, result) in enumerate(
                        zip(display_df["CaseID"], display_df["Classification"])):  # type: ignore
                    col_idx = idx % 4
                    cid_str = str(cid)
                    result_str = str(result) if pd.notna(result) and result != "" else "Unclassified"
                    with nav_cols[col_idx]:
                        if st.button(f"{cid_str} ({result_str})", key=f"jump_{cid_str}"):
                            st.session_state.jump_to_case = cid_str
                            st.rerun()
            except Exception as e:
                st.error(f"Could not load data: {e}")

    else:
        st.info("No data available. Please check the CSV file.")

    # Sidebar controls
with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Reset All Labels", type="secondary"):
        if st.session_state.df is not None:
            try:
                supabase.table("classifications").delete().gte("case_id", "").execute()
                st.session_state.df["Classification"] = ""
                st.session_state.current_index = 0
                st.session_state.show_celebration = False
                st.success("All labels reset!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reset: {e}")

    if st.button("🏠 Back to Home"):
        st.switch_page("main.py")


if __name__ == "__main__":
    classification_page()
