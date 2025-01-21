import os
import sqlite3
import pandas as pd
import json
from google.oauth2 import service_account
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import streamlit as st
from streamlit_option_menu import option_menu
from tools import analyze_url

# SQLite3 Database setup
def create_connection():
    conn = sqlite3.connect('iiadb.db')  # Local copy of the database
    return conn

# Check if the database is already downloaded
def download_db_if_needed():
    if not os.path.exists('iiadb.db'):
        download_db_from_drive()  # Download the database if not already present

# Download the database from Google Drive
def download_db_from_drive():
    try:
        service = build('drive', 'v3', credentials=credentials)
        file_id = st.secrets["db_id"]  # Your Google Drive file ID
        request = service.files().get_media(fileId=file_id)
        with open('iiadb.db', 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")
    except Exception as e:
        st.error(f"Error downloading the database from Google Drive: {e}")
        raise

# Function to upload the database back to Google Drive
def upload_db_to_drive():
    try:
        service = build('drive', 'v3', credentials=credentials)
        file_id = st.secrets["db_id"]  # Your Google Drive file ID
        media = MediaFileUpload('iiadb.db', mimetype='application/x-sqlite3')
        request = service.files().update(fileId=file_id, media_body=media)
        request.execute()
        st.success("Database successfully updated on Google Drive.")
    except Exception as e:
        st.error(f"Error uploading the database to Google Drive: {e}")
        raise

# Create the items table if it doesn't exist
def create_table():
    download_db_if_needed()  # Ensure the database is downloaded
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            decision TEXT,
            decision_reason TEXT,
            source TEXT,
            title TEXT,
            description TEXT,
            title_translated TEXT,
            description_translated TEXT,
            tags TEXT,
            notes TEXT,
            languages TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Add a new item to the database
def add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    download_db_if_needed()
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(''' 
            INSERT INTO items (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages))
        conn.commit()  # Save the changes
        st.success("Item successfully added to the database!")
    except Exception as e:
        st.error(f"An error occurred while adding the item: {e}")
    finally:
        conn.close()  # Ensure the connection is closed


# Update an existing item in the database
def update_item(item_id, url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    download_db_if_needed()
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(''' 
            UPDATE items
            SET url = ?, decision = ?, decision_reason = ?, source = ?, title = ?, description = ?, title_translated = ?, description_translated = ?, tags = ?, notes = ?, languages = ?
            WHERE id = ?
        ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages, item_id))
        conn.commit()
        conn.close()

    except Exception as e:
        st.error(f"Error while updating the item in the database: {e}")
        raise

# Function to view all items in the database
def view_db():
    download_db_if_needed()
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM items')
        rows = cursor.fetchall()
        conn.close()
    
        df = pd.DataFrame(rows, columns=[
            "ID", "URL", "Decision", "Decision Reason", "Source", "Title", 
            "Description", "Title Translated", "Description Translated", 
            "Tags", "Notes", "Languages"
        ])
        
        st.subheader("Database View")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error: {e}")
        raise

# Function to update form fields with analyzed data
def update_form_with_analysis(url):
    try:
        analyzed_data = analyze_url(url)
        if analyzed_data:
            title, description, translated_title, translated_description, languages = analyzed_data
            st.session_state.title = title
            st.session_state.description = description
            st.session_state.title_translated = translated_title
            st.session_state.description_translated = translated_description
            st.session_state.languages = ", ".join(languages)
    except Exception as e:
        st.error(f"Error analyzing URL: {e}")

# Function to add a new item via a form
def add_new_item_form():
    st.subheader("Add a New Item to the Database")

    with st.form(key="new_item_form"):
        url = st.text_input("URL")
        decision = st.text_input("Decision")
        decision_reason = st.text_input("Decision Reason")
        source = st.text_input("Source")
        title = st.text_input("Title")
        description = st.text_area("Description")
        title_translated = st.text_input("Title (Translated)")
        description_translated = st.text_area("Description (Translated)")
        tags = st.text_input("Tags")
        notes = st.text_area("Notes")
        languages = st.text_input("Languages (comma separated)")

        submit_button = st.form_submit_button(label="Add Item")

        if submit_button:
            if url:
                add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
                st.success("Item successfully added!")
            else:
                st.error("Please provide the URL for the new item.")

# Save to Google Drive function
def save_to_drive():
    try:
        upload_db_to_drive()  # Upload the updated database to Google Drive
    except Exception as e:
        st.error(f"Error saving to Google Drive: {e}")
        
# Initialize app options and authentication flag
apps = {}
authenticated = False
client = None

# Sidebar Header
with st.sidebar:
    st.header("Israeli Internet Archive")

# Handle credentials upload
if not authenticated:
    with st.sidebar:
        st.subheader("Upload Credentials File")
        credentials_file = st.file_uploader("Please upload your JSON credentials file", type="json")

        if credentials_file is not None:
            try:
                scope = [
                    "https://spreadsheets.google.com/feeds", 
                    "https://www.googleapis.com/auth/spreadsheets", 
                    "https://www.googleapis.com/auth/drive"
                ]

                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(credentials_file.read().decode("utf-8")), 
                    scopes=scope
                )

                client = gspread.authorize(credentials)
                st.sidebar.success("Credentials uploaded and authenticated successfully!")
                authenticated = True

                # Authenticate with Google API
                service = build('drive', 'v3', credentials=credentials)

                # Specify the file ID (replace with your own file ID)
                file_id = st.secrets["db_id"]
                request = service.files().get_media(fileId=file_id)
                with open("iiadb.db", 'wb') as file:
                    downloader = MediaIoBaseDownload(file, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        st.info(f"Download {int(status.progress() * 100)}% complete.")
            except Exception as e:
                st.sidebar.error(f"Error processing credentials: {e}")

# Define apps
apps = {
    "View Database": view_db,
    "Add a New Item": add_new_item_form,
    "Save to Google Drive": save_to_drive  
}

# Sidebar menu
if authenticated:
    with st.sidebar:
        selected_app_name = option_menu(
            "Tools Menu",
            options=list(apps.keys()),
            icons=["database", "link", "filter", "search", "save"], 
            menu_icon="tools",
            default_index=0,
            orientation="vertical"
        )

    # Render the selected app
    app_function = apps[selected_app_name]
    if callable(app_function):
        st.title(selected_app_name)
        app_function()  # Call the selected function (view_db for "View Database")
    else:
        st.error(f"The app '{selected_app_name}' is not callable.")
else:
    st.warning("Please upload the credentials file to access the tools.")
