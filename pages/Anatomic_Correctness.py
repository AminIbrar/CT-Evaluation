import pandas as pd
from utils import *


def anatomic_correctness_page():
    # Keep big header/subtitle removed
    setup_page_layout(
        "",
        "",
        csv_path="anatomic_structure.csv",
        result_column="Assessment",
    )

    # Styles: nuke top padding, better nav title, status belt width, vertical separators, centering helpers
    st.markdown("""
        <style>
            /* Remove all space above nav/content */
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stAppViewContainer"] .main { padding-top: 0 !important; }
            .block-container { padding-top: 0 !important; margin-top: 0 !important; }

            /* Remove extra padding from the main container */
            .main .block-container {
                padding-top: 0.5rem !important;
                padding-bottom: 1rem !important;
            }

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
            .stats-wrap [data-testid="stMetric"] {
                text-align: center !important;
                justify-content: center !important;
            }
            .stats-wrap [data-testid="stMetric"] > div {
                justify-content: center !important;
                text-align: center !important;
            }
            .stats-wrap [data-testid="stMetric"] > div > div {
                text-align: center !important;
                justify-content: center !important;
            }
            .stats-wrap [data-testid="stMetricLabel"], 
            .stats-wrap [data-testid="stMetricValue"], 
            .stats-wrap [data-testid="stMetricDelta"] {
                justify-content: center !important;
                text-align: center !important;
                width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize Supabase
    supabase = init_supabase()

    # Load data once per task
    if not st.session_state.data_loaded:
        st.session_state.df = load_data(csv_path="anatomic_structure.csv")

        if st.session_state.df is not None:
            # Add temporary columns for session state (not in CSV)
            if "Assessment" not in st.session_state.df.columns:
                st.session_state.df["Assessment"] = ""
            if "Comment" not in st.session_state.df.columns:
                st.session_state.df["Comment"] = ""

            # Load existing assessments from Supabase for current reader
            try:
                response = supabase.table("anatomic_correctness").select("*").eq(
                    "reader_id", st.session_state.reader_id
                ).execute()
                existing = {str(item["case_id"]): {
                    "assessment": item["assessment"],
                    "comment": item.get("comment", ""),
                    "image_path": item.get("image_path", "")
                } for item in response.data or []}

                for idx, row in st.session_state.df.iterrows():
                    cid = str(row["CaseID"])
                    if cid in existing:
                        st.session_state.df.at[idx, "Assessment"] = existing[cid]["assessment"]
                        st.session_state.df.at[idx, "Comment"] = existing[cid]["comment"]
            except Exception as e:
                st.warning(f"Could not load data from Supabase: {e}")
                st.info("Make sure the anatomic_correctness table has been updated for multi-reader support")

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

        # Top Navigation Menu (compact)
        col1_nav, col2_nav, col3_nav, col4_nav, col5_nav = st.columns([2, 1, 1, 1, 1])
        with col1_nav:
            st.markdown('<div class="nav-title">Anatomic Correctness</div>', unsafe_allow_html=True)
        with col2_nav:
            if st.button("Home", use_container_width=True):
                st.switch_page("pages/Reader_Dashboard.py")
        with col3_nav:
            if st.button("Classification", use_container_width=True):
                st.switch_page("pages/Classification.py")
        with col4_nav:
            if st.button("Realistic Appearance", use_container_width=True):
                st.switch_page("pages/Realistic_Appearance.py")
        with col5_nav:
            if st.button("Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        st.markdown("---")

        # ====== 5-column layout with real separators: Image | Sep | Controls | Sep | Stats ======
        col_img, col_sep12, col_ctrl, col_sep23, col_stats = st.columns(
            [3, 0.2, 7, 0.2, 2],
            vertical_alignment="center"
        )

        # Left image column (256x256 image + status belt)
        with col_img:
            if current_assessment:
                st.markdown(
                    f'<div class="status-belt status-blue">🔄 <b>Current assessment: {current_assessment}</b></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="status-belt status-green">🆕 <b>New image to assess</b></div>',
                    unsafe_allow_html=True
                )
            image, error = load_and_display_image(image_path, subfolder="anatomic_structure")
            if error:
                st.error(error)
            else:
                st.image(image, caption=f"Case: {case_id}", width=256)

        # Vertical separator between col 1 and 2
        with col_sep12:
            st.markdown('<div class="v-sep"></div>', unsafe_allow_html=True)

        # Middle controls column (radio + comment + buttons + confirmation + reset centered)
        with col_ctrl:
            st.subheader(f"Image {current_index + 1} of {len(df)}")

            # Assessment options
            options = [
                "Anatomic region not recognizable",
                "Recognizable, but major parts show anatomic incorrectness",
                "Only minor anatomic incorrectness",
                "Anatomic features are correct"
            ]

            # Find current selection index
            if current_assessment:
                try:
                    default_index = options.index(current_assessment)
                except ValueError:
                    default_index = 0
            else:
                default_index = 0

            assessment_choice = st.radio(
                "Select the most appropriate description:",
                options,
                index=default_index,
                key=f"anatomic_radio_{case_id}",
            )

            # Comment box
            comment_choice = st.text_area(
                "Additional Comments (optional):",
                value=current_comment,
                height=120,
                key=f"comment_{case_id}",
                placeholder="Specify anatomical inaccuracies (e.g., organ shape/size/position, missing structures, abnormal morphology)..."
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
                button_label = "Save" if is_last_image else ("Update & Next" if current_assessment else "Save & Next")
                if st.button(button_label, type="primary", use_container_width=False, key=f"save_{case_id}"):
                    try:
                        case_id_norm = str(case_id).strip()
                        assessment_norm = str(assessment_choice).strip()
                        comment_norm = str(comment_choice).strip()
                        image_path_norm = str(image_path).strip()

                        # Save to Supabase with reader_id and ImagePath
                        supabase.table("anatomic_correctness").upsert({
                            "case_id": case_id_norm,
                            "reader_id": st.session_state.reader_id,
                            "assessment": assessment_norm,
                            "comment": comment_norm,
                            "image_path": image_path_norm  # Store ImagePath in database
                        }).execute()

                        # Update local session state
                        st.session_state.df.at[current_index, "Assessment"] = assessment_norm
                        st.session_state.df.at[current_index, "Comment"] = comment_norm

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
                st.warning("🎉 All tasks completed! You've finished all assessments.")
                c1, c2 = st.columns(2, gap="small")
                with c1:
                    if st.button("🏠 Return to Home", use_container_width=True, key="confirm_yes_next_task"):
                        st.session_state["next_task_confirm"] = False
                        st.switch_page("pages/Reader_Dashboard.py")
                with c2:
                    if st.button("🔄 Review Again", use_container_width=True, key="confirm_no_next_task"):
                        st.session_state["next_task_confirm"] = False
                        st.session_state.current_index = 0
                        st.rerun()

            # ---- Reset My Labels (compact & centered) ----
            st.markdown("---")
            reset_key = f"reset_confirm_{current_index}"
            if st.session_state.get(reset_key, False):
                st.warning("⚠️ Are you sure you want to reset ALL your assessments? This action cannot be undone!")
                rc1, rc2 = st.columns(2, gap="small")
                with rc1:
                    if st.button("✅ Yes, Reset Everything", type="primary", use_container_width=True):
                        try:
                            supabase.table("anatomic_correctness").delete().eq(
                                "reader_id", st.session_state.reader_id
                            ).execute()
                            st.session_state.df["Assessment"] = ""
                            st.session_state.df["Comment"] = ""
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
                    if st.button("🔄 Reset all Assessments", type="secondary", use_container_width=True):
                        st.session_state[reset_key] = True
                        st.rerun()

        # Vertical separator between col 2 and 3
        with col_sep23:
            st.markdown('<div class="v-sep"></div>', unsafe_allow_html=True)

        # Right stats column (centered vertically & horizontally)
        with col_stats:
            assessed_count = len(df[df["Assessment"].notna() & (df["Assessment"] != "")])
            total_count = len(df)
            remaining = total_count - assessed_count
            progress = (assessed_count / total_count) if total_count > 0 else 0.0

            st.markdown('<div class="stats-wrap">', unsafe_allow_html=True)
            st.metric("Total", total_count)
            st.metric("Assessed", assessed_count)
            st.metric("Remaining", remaining)
            st.metric("Progress", f"{progress:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Data viewer + quick navigation
        with st.expander("View All Images", expanded=True):
            fresh_df = load_data(csv_path="anatomic_structure.csv")

            try:
                response = supabase.table("anatomic_correctness").select("*").eq(
                    "reader_id", st.session_state.reader_id
                ).execute()
                current_map = {str(item["case_id"]): {
                    "assessment": item["assessment"],
                    "comment": item.get("comment", ""),
                    "image_path": item.get("image_path", "")
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


if __name__ == "__main__":
    anatomic_correctness_page()