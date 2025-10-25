import pandas as pd
from utils import *


def classification_page():
    # Keep big header/subtitle removed
    setup_page_layout(
        "",
        "",
        csv_path="classification.csv",
        result_column="Classification",
    )

    # Styles: nuke top padding, better nav title, status belt width, vertical separators, centering helpers
    st.markdown("""
        <style>
            /* Remove all space above nav/content */
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stAppViewContainer"] .main { padding-top: 0 !important; }
            .block-container { padding-top: 0 !important; margin-top: 0 !important; }

            /* Nav title – clear and readable */
            .nav-title {
                display: inline-block;
                font-size: 1.2rem; font-weight: 700; letter-spacing: .2px;
                padding: .25rem .6rem; border-radius: .5rem;
                background: linear-gradient(90deg, #f8fafc, #eef2ff);
                border: 1px solid #e2e8f0;
            }

            /* Status belt exactly 256px wide (matches image col) */
            .status-belt { width: 256px; margin: 0 0 8px 0; text-align: center;
                           padding: 6px 8px; border-radius: 8px; font-weight: 600; }
            .status-green { background: #ecfdf5; border: 1px solid #10b981; color: #065f46; }
            .status-blue  { background: #eff6ff; border: 1px solid #3b82f6; color: #1e40af; }

            /* Vertical separator column visual */
            .v-sep {
                width: 2px; min-height: 340px;
                background: linear-gradient(180deg, rgba(0,0,0,0), #cbd5e1, rgba(0,0,0,0));
                border-radius: 2px;
            }

            /* Center helpers */
            .center-col { display: flex; flex-direction: column; align-items: center; justify-content: center; }
            .center-text { text-align: center; }

            /* Compact button paddings + tighter gaps (Streamlit >=1.25 supports gap="small") */
            .btn-compact button { padding: .4rem .6rem !important; width: auto !important; }

            /* Compact + centered reset button */
            .reset-center { display: flex; justify-content: center; }
            .reset-center button { width: auto !important; }

            /* Center Streamlit metrics horizontally */
            .stats-wrap [data-testid="stMetric"] * { text-align: center !important; }
        </style>
    """, unsafe_allow_html=True)

    # Initialize Supabase
    supabase = init_supabase()

    # Load data once per task
    if not st.session_state.data_loaded:
        st.session_state.df = load_data(csv_path="classification.csv")

        if st.session_state.df is not None:
            try:
                response = supabase.table("classifications").select("*").eq(
                    "reader_id", st.session_state.reader_id
                ).execute()
                existing = {str(item["case_id"]): {
                    "classification": item["classification"],
                    "image_path": item.get("image_path", "")
                } for item in response.data or []}

                for idx, row in st.session_state.df.iterrows():
                    cid = str(row["CaseID"])
                    if cid in existing:
                        st.session_state.df.at[idx, "Classification"] = existing[cid]["classification"]
            except Exception as e:
                st.warning(f"Could not load data from Supabase: {e}")
                st.info("Make sure the classifications table has been updated for multi-reader support")

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

        # Top Navigation Menu (compact)
        col1_nav, col2_nav, col3_nav, col4_nav, col5_nav = st.columns([2, 1, 1, 1, 1])
        with col1_nav:
            st.markdown('<div class="nav-title">Image Classification</div>', unsafe_allow_html=True)
        with col2_nav:
            if st.button("Home", use_container_width=True):
                st.switch_page("pages/Reader_Dashboard.py")
        with col3_nav:
            if st.button("Realistic Appearance", use_container_width=True):
                st.switch_page("pages/Realistic_Appearance.py")
        with col4_nav:
            if st.button("Anatomic Correctness", use_container_width=True):
                st.switch_page("pages/Anatomic_Correctness.py")
        with col5_nav:
            if st.button("Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        st.markdown("---")

        # ====== 5-column layout with real separators: Image | Sep | Controls | Sep | Stats ======
        # Use vertical_alignment="center" to vertically center contents in each column.
        col_img, col_sep12, col_ctrl, col_sep23, col_stats = st.columns(
            [3, 0.2, 7, 0.2, 2],
            vertical_alignment="center"
        )

        # Left image column (256x256 image + status belt)
        with col_img:
            if current_result:
                st.markdown(
                    f'<div class="status-belt status-blue">🔄 <b>Currently classified as: {current_result}</b></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="status-belt status-green">🆕 <b>New image to classify</b></div>',
                    unsafe_allow_html=True
                )
            image, error = load_and_display_image(image_path, subfolder="classification")
            if error:
                st.error(error)
            else:
                st.image(image, caption=f"Case: {case_id}", width=256)

        # Vertical separator between col 1 and 2
        with col_sep12:
            st.markdown('<div class="v-sep"></div>', unsafe_allow_html=True)

        # Middle controls column (radio + tighter Back/Skip/Save row + confirmation + reset centered)
        with col_ctrl:
            st.subheader(f"Image {current_index + 1} of {len(df)}")

            default_index = 0 if (current_result and current_result.lower() == "real") else (1 if current_result else 0)
            classification_choice = st.radio(
                "Is this image:",
                ["Real", "Synthetic"],
                index=default_index,
                key=f"class_radio_{case_id}",
            )

            # Tighter button row (gap="small") and compact buttons (not full width)
            st.markdown('<div class="btn-compact">', unsafe_allow_html=True)
            bcol1, bcol2, bcol3 = st.columns(3, gap="small")
            with bcol1:
                if current_index > 0 and st.button("← Back", use_container_width=False, key=f"back_{case_id}"):
                    st.session_state.current_index = current_index - 1
                    st.rerun()
            with bcol2:
                if current_index < len(df) - 1 and st.button("Skip →", use_container_width=False,
                                                             key=f"skip_{case_id}"):
                    st.session_state.current_index = current_index + 1
                    st.rerun()
            with bcol3:
                is_last_image = current_index == len(df) - 1
                button_label = "Save" if is_last_image else ("Update & Next" if current_result else "Save & Next")
                if st.button(button_label, type="primary", use_container_width=False, key=f"save_{case_id}"):
                    try:
                        case_id_norm = str(case_id).strip()
                        class_norm = str(classification_choice).strip()
                        image_path_norm = str(image_path).strip()

                        # Save to Supabase with ImagePath
                        supabase.table("classifications").upsert({
                            "case_id": case_id_norm,
                            "reader_id": st.session_state.reader_id,
                            "classification": class_norm,
                            "image_path": image_path_norm  # Store ImagePath in database
                        }).execute()

                        st.session_state.df.at[current_index, "Classification"] = class_norm

                        if is_last_image:
                            st.session_state["next_task_confirm"] = True
                            st.rerun()
                        else:
                            st.session_state.current_index = current_index + 1
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save to database: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Inline confirmation after LAST save (Reset-style)
            if st.session_state.get("next_task_confirm", False):
                st.warning("Would you like to move to next task (Realistic Appearance)?")
                c1, c2 = st.columns(2, gap="small")
                with c1:
                    if st.button("✅ Yes, go to Realistic Appearance Task", use_container_width=True,
                                 key="confirm_yes_next_task"):
                        st.session_state["next_task_confirm"] = False
                        st.switch_page("pages/Realistic_Appearance.py")
                with c2:
                    if st.button("❌ No, stay here", use_container_width=True, key="confirm_no_next_task"):
                        st.session_state["next_task_confirm"] = False
                        st.rerun()

            # ---- Reset My Labels (compact & centered) ----
            st.markdown("---")
            reset_key = f"reset_confirm_{current_index}"
            if st.session_state.get(reset_key, False):
                st.warning("⚠️ Are you sure you want to reset ALL your classifications? This action cannot be undone!")
                rc1, rc2 = st.columns(2, gap="small")
                with rc1:
                    if st.button("✅ Yes, Reset Everything", type="primary", use_container_width=True):
                        try:
                            supabase.table("classifications").delete().eq(
                                "reader_id", st.session_state.reader_id
                            ).execute()
                            st.session_state.df["Classification"] = ""
                            st.session_state.current_index = 0
                            if reset_key in st.session_state:
                                del st.session_state[reset_key]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to reset: {e}")
                with rc2:
                    if st.button("❌ Cancel", use_container_width=True):
                        if reset_key in st.session_state:
                            del st.session_state[reset_key]
                        st.rerun()
            else:
                # Centered reset button using columns approach
                left_space, center_col, right_space = st.columns([1, 2, 1])
                with center_col:
                    if st.button("🔄 Reset all Labels", type="secondary", use_container_width=True):
                        st.session_state[reset_key] = True
                        st.rerun()

        # Vertical separator between col 2 and 3  (this is the one you asked for)
        with col_sep23:
            st.markdown('<div class="v-sep"></div>', unsafe_allow_html=True)

        # Right stats column (centered vertically & horizontally)
        with col_stats:
            classified_count = len(df[df["Classification"].notna() & (df["Classification"] != "")])
            total_count = len(df)
            remaining = total_count - classified_count
            progress = (classified_count / total_count) if total_count > 0 else 0.0

            st.markdown('<div class="center-col stats-wrap center-text">', unsafe_allow_html=True)
            st.metric("Total", total_count)
            st.metric("Classified", classified_count)
            st.metric("Remaining", remaining)
            st.metric("Progress", f"{progress:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Data viewer + quick navigation (unchanged)
        with st.expander("View All Images", expanded=True):
            fresh_df = load_data(csv_path="classification.csv")
            try:
                response = supabase.table("classifications").select("*").eq(
                    "reader_id", st.session_state.reader_id
                ).execute()
                current_map = {str(item["case_id"]): {
                    "classification": item["classification"],
                    "image_path": item.get("image_path", "")
                } for item in response.data or []}

                display_df = fresh_df.copy()
                for idx, r in display_df.iterrows():
                    cid = str(r["CaseID"])
                    if cid in current_map:
                        display_df.at[idx, "Classification"] = current_map[cid]["classification"]

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


if __name__ == "__main__":
    classification_page()