import streamlit as st
import pandas as pd
import os
from PIL import Image
from supabase import create_client, Client
import streamlit as st


# Initialize Supabase client
@st.cache_resource
def init_supabase():
    # For local development - we'll use secrets for deployment
    try:
        # Try to get from secrets (for Streamlit Cloud)
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except:
        # For local development - you'll replace these with your actual credentials
        url = "https://raajetcwgsyeesrdooap.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJhYWpldGN3Z3N5ZWVzcmRvb2FwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMjYzNjYsImV4cCI6MjA3NjgwMjM2Nn0.THWFJT8slo1r3bVz6TtXTbg1zESbiv1_-YzxaK4Gt0M"

    return create_client(url, key)


# Initialize session state
def init_session_state():
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
    if 'current_csv_path' not in st.session_state:
        st.session_state.current_csv_path = ""
    if 'current_result_column' not in st.session_state:
        st.session_state.current_result_column = ""


# Load CSV data (for initial image list only)
def load_data(csv_path=""):
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df
    else:
        st.error(f"CSV file '{csv_path}' not found in the current directory.")
        return None


def find_first_unclassified_index(df, result_column=''):
    for idx, row in df.iterrows():
        if pd.isna(row[result_column]) or row[result_column] == '':
            return idx
    return 0


def find_case_index(df, case_id):
    for idx, row in df.iterrows():
        if str(row['CaseID']) == str(case_id):
            return idx
    return 0


def load_and_display_image(image_path, subfolder="", size=(256, 256)):
    try:
        # Build the full image path with optional subfolder
        if subfolder:
            full_image_path = os.path.join("images", subfolder, image_path)
        else:
            full_image_path = os.path.join("images", image_path)

        if os.path.exists(full_image_path):
            image = Image.open(full_image_path)
            image_resized = image.resize(size)
            return image_resized, None
        else:
            return None, f"Image not found: {full_image_path}"
    except Exception as e:
        return None, f"Error loading image: {e}"


def setup_page_layout(title, description, csv_path="", result_column=""):
    st.set_page_config(page_title=title, layout="wide")
    st.title(title)
    st.write(description)

    # Initialize session state FIRST
    init_session_state()

    # THEN check for task switching
    if (st.session_state.current_csv_path != csv_path or
            st.session_state.current_result_column != result_column):
        st.session_state.data_loaded = False
        st.session_state.current_csv_path = csv_path
        st.session_state.current_result_column = result_column