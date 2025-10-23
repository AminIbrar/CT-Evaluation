import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="Image Classification", layout="wide")

st.title("Image Classification App")
st.write("Classify images as Real or Synthetic")

# Initialize session state
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'df' not in st.session_state:
    st.session_state.df = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'jump_to_case' not in st.session_state:
    st.session_state.jump_to_case = None
if 'show_celebration' not in st.session_state:
    st.session_state.show_celebration = False

# Load CSV file
csv_path = "image_list.csv"  # CSV file in same directory


def load_data():
    """Load data without caching to always get fresh data"""
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # Create 'result' column if it doesn't exist
        if 'result' not in df.columns:
            df['result'] = ''
        return df
    else:
        st.error(f"CSV file '{csv_path}' not found in the current directory.")
        return None


def find_first_unclassified_index(df):
    """Find the index of the first unclassified image"""
    for idx, row in df.iterrows():
        if pd.isna(row['result']) or row['result'] == '':
            return idx
    return 0  # Return first index if all are classified


def find_case_index(df, case_id):
    """Find the index of a specific case ID"""
    for idx, row in df.iterrows():
        if str(row['CaseID']) == str(case_id):
            return idx
    return 0


# Load the data
if not st.session_state.data_loaded:
    st.session_state.df = load_data()
    if st.session_state.df is not None:
        st.session_state.current_index = find_first_unclassified_index(st.session_state.df)
        st.session_state.data_loaded = True

# Handle case jumping from CSV viewer
if st.session_state.jump_to_case is not None and st.session_state.df is not None:
    st.session_state.current_index = find_case_index(st.session_state.df, st.session_state.jump_to_case)
    st.session_state.jump_to_case = None
    st.rerun()

# Main classification interface
if st.session_state.df is not None and len(st.session_state.df) > 0:
    df = st.session_state.df
    current_index = st.session_state.current_index

    # Get current image data
    row = df.iloc[current_index]
    case_id = str(row["CaseID"])
    image_path = str(row["ImagePath"])
    current_result = str(row["result"]) if pd.notna(row["result"]) and row["result"] != '' else ""

    # Check if all images are classified (for celebration)
    classified_count = len(df[df['result'].notna() & (df['result'] != '')])
    total_count = len(df)
    all_classified = classified_count == total_count and total_count > 0

    # Show celebration only once when completion is first detected
    if all_classified and not st.session_state.show_celebration:
        st.session_state.show_celebration = True
        st.balloons()

    # Create main layout with top stats and main content
    # Top row for statistics
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

    st.markdown("---")  # Separator line

    # Display current progress with classification status
    st.subheader(f"Image {current_index + 1} of {len(df)}")
    st.write(f"**Case ID:** {case_id}")

    # Show classification status
    if current_result:
        st.info(f"🔄 **Revisiting classified image:** This image is currently classified as **{current_result}**")
    else:
        st.success("🆕 **New image to classify**")

    # Create columns for image and controls
    col1, col2 = st.columns([2, 1])

    with col1:
        # Load and display image with fixed 256x256 size
        try:
            full_image_path = os.path.join("images", image_path)
            if os.path.exists(full_image_path):
                image = Image.open(full_image_path)
                # Resize image to 256x256
                image_resized = image.resize((256, 256))
                st.image(image_resized, caption=f"Case: {case_id}", width=256)
            else:
                st.error(f"Image not found: {full_image_path}")
                st.info(f"Looking for image in: {os.path.abspath('images')}")
        except Exception as e:
            st.error(f"Error loading image: {e}")

    with col2:
        st.subheader("Classification")

        # Radio buttons for classification
        if current_result:
            # Pre-select based on existing result
            if current_result.lower() == "real":
                default_index = 0
            else:
                default_index = 1
        else:
            default_index = 0

        classification = st.radio(
            "Is this image:",
            ["Real", "Synthetic"],
            index=default_index,
            key=f"class_{current_index}"
        )

        # Navigation buttons - ALWAYS show Back and Skip when applicable
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

        with col_btn1:
            # Back button (always show except on first image)
            if current_index > 0:
                if st.button("← Back", key=f"back_{current_index}"):
                    st.session_state.current_index -= 1
                    st.rerun()
            else:
                st.write("")  # Empty space for layout

        with col_btn2:
            # Skip button (always show except on last image)
            if current_index < len(df) - 1:
                if st.button("Skip →", key=f"skip_{current_index}"):
                    # Move to next image
                    st.session_state.current_index += 1
                    st.rerun()
            else:
                st.write("")  # Empty space for layout

        with col_btn3:
            # Save/Update button - ALWAYS works
            button_label = "Update" if current_result else "Save"
            if st.button(f"{button_label} →", type="primary", key=f"save_{current_index}"):
                # Update the result in dataframe
                st.session_state.df.at[current_index, 'result'] = classification

                # Save to CSV
                st.session_state.df.to_csv(csv_path, index=False)

                # If this was an unclassified image and not last image, find next unclassified
                if not current_result and current_index < len(df) - 1:
                    next_unclassified = None
                    for idx in range(current_index + 1, len(df)):
                        if pd.isna(df.iloc[idx]['result']) or df.iloc[idx]['result'] == '':
                            next_unclassified = idx
                            break

                    if next_unclassified is not None:
                        st.session_state.current_index = next_unclassified

                st.success(f"Classification saved as: {classification}")
                st.rerun()

        # Show current result if exists
        if current_result:
            st.info(f"Current classification: **{current_result}**")

    # Show completion message if all images are classified
    if all_classified:
        st.success("🎉 All images have been classified!")

        # Show summary
        real_count = len(df[df['result'].str.lower() == 'real'])
        synthetic_count = len(df[df['result'].str.lower() == 'synthetic'])

        st.write("### Classification Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Real Images", real_count)
        with col2:
            st.metric("Synthetic Images", synthetic_count)

else:
    st.info("No data available. Please check the CSV file.")

# Reset button in sidebar
with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Reset All Labels", type="secondary"):
        if st.session_state.df is not None:
            # Reset all results to empty
            st.session_state.df['result'] = ''
            # Save to CSV
            st.session_state.df.to_csv(csv_path, index=False)
            # Reset to first image
            st.session_state.current_index = 0
            st.session_state.show_celebration = False
            st.success("All labels have been reset!")
            st.rerun()

# Display current CSV data for reference with clickable case IDs
if st.session_state.df is not None:
    with st.expander("View CSV Data"):
        # Always load fresh data for the viewer
        fresh_df = load_data()

        # Display the dataframe without the 'Action' column
        st.dataframe(fresh_df[['CaseID', 'ImagePath', 'result']], use_container_width=True)

        # Create clickable case IDs using buttons
        st.write("### Quick Navigation - Jump to Case:")
        cols = st.columns(4)  # Create 4 columns for the buttons

        for idx, (case_id, result) in enumerate(zip(fresh_df['CaseID'], fresh_df['result'])):
            col_idx = idx % 4
            case_str = str(case_id)
            result_str = str(result) if pd.notna(result) and result != '' else "Unclassified"
            button_label = f"{case_str} ({result_str})"

            with cols[col_idx]:
                if st.button(button_label, key=f"jump_{case_str}", use_container_width=True):
                    st.session_state.jump_to_case = case_str
                    st.rerun()