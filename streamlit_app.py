import streamlit as st
import sqlite3
import pandas as pd
from streamlit_option_menu import option_menu
from tools import analyze_url
import validators
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

# Google Drive Setup
def authenticate_google_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Local webserver for authentication
    return GoogleDrive(gauth)

def download_db_from_drive(drive, file_id):
    """Download the database file from Google Drive."""
    try:
        file = drive.CreateFile({'id': file_id})
        file.GetContentFile('database.db')  # Save as 'database.db' locally
        st.success("Database downloaded successfully from Google Drive!")
    except Exception as e:
        st.error(f"Error downloading database from Google Drive: {e}")

def upload_db_to_drive(drive, file_id):
    """Upload the database file back to Google Drive."""
    try:
        file = drive.CreateFile({'id': file_id})
        file.SetContentFile('database.db')  # Upload 'database.db' to Google Drive
        file.Upload()
        st.success("Database uploaded successfully to Google Drive!")
    except Exception as e:
        st.error(f"Error uploading database to Google Drive: {e}")

# SQLite3 Database setup
def create_connection():
    conn = sqlite3.connect('database.db')
    return conn

# Create the items table if it doesn't exist
def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
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
    )''')
    conn.commit()
    conn.close()

# Add item function
def add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO items (
        url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages))
    conn.commit()
    conn.close()

# Main Streamlit app
def main():
    # Initialize the database and create the table
    create_table()

    # Google Drive Authentication
    st.sidebar.subheader("Google Drive Settings")
    drive_auth_button = st.sidebar.button("Authenticate Google Drive")
    if "drive" not in st.session_state:
        st.session_state.drive = None

    if drive_auth_button:
        st.session_state.drive = authenticate_google_drive()
        st.success("Authenticated with Google Drive!")

    drive_file_id = st.sidebar.text_input("Google Drive File ID", help="Enter the file ID of the database file on Google Drive.")
    if st.sidebar.button("Download Database from Drive"):
        if st.session_state.drive and drive_file_id:
            download_db_from_drive(st.session_state.drive, drive_file_id)

    if st.sidebar.button("Upload Database to Drive"):
        if st.session_state.drive and drive_file_id:
            upload_db_to_drive(st.session_state.drive, drive_file_id)

    # Main Menu
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=["View Database", "Add New Item", "Edit Item"],
            icons=["view-list", "plus-circle", "pencil"],
            default_index=0,
        )

    if selected == "View Database":
        st.write("### View Database")
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM items')
        items = cursor.fetchall()
        conn.close()
        if items:
            df = pd.DataFrame(items, columns=[
                'ID', 'URL', 'Decision', 'Decision Reason', 'Source',
                'Title', 'Description', 'Translated Title', 'Translated Description',
                'Tags', 'Notes', 'Languages'
            ])
            st.dataframe(df)
        else:
            st.info("No items in the database.")

    elif selected == "Add New Item":
        st.write("### Add a New Item")
        with st.form("add_item_form"):
            url = st.text_input("URL")
            decision = st.selectbox("Decision", ["Yes", "Maybe", "No"])
            decision_reason = st.text_input("Decision Reason")
            source = st.text_input("Source")
            title = st.text_input("Title")
            description = st.text_area("Description")
            title_translated = st.text_input("Translated Title")
            description_translated = st.text_area("Translated Description")
            tags = st.text_input("Tags (comma-separated)")
            languages = st.text_input("Languages (comma-separated)")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Add Item")
            if submitted:
                if not validators.url(url):
                    st.error("Invalid URL. Please enter a valid URL.")
                else:
                    add_item(url, decision, decision_reason, source, title, description,
                             title_translated, description_translated, tags, notes, languages)
                    st.success("New item added successfully!")

if __name__ == "__main__":
    main()
