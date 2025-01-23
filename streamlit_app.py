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
        download_db_from_drive()

# Download the database from Google Drive
def download_db_from_drive():
    try:
        service = build('drive', 'v3', credentials=credentials)
        file_id = st.secrets["db_id"]
        request = service.files().get_media(fileId=file_id)
        with open('iiadb.db', 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")
    except Exception as e:
        st.error(f"Error downloading the database: {e}")
        raise

# Upload the database to Google Drive
def upload_db_to_drive():
    try:
        service = build('drive', 'v3', credentials=credentials)
        file_id = st.secrets["db_id"]
        media = MediaFileUpload('iiadb.db', mimetype='application/x-sqlite3')
        request = service.files().update(fileId=file_id, media_body=media)
        request.execute()
        st.success("Database saved to Google Drive.")
    except Exception as e:
        st.error(f"Error uploading the database: {e}")
        raise

# Create the items table
def create_table():
    download_db_if_needed()
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

# Add item to the database
def add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    download_db_if_needed()
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO items (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages))
        conn.commit()
        upload_db_to_drive()
        st.success("Item added to the database.")
    except Exception as e:
        st.error(f"Error adding item: {e}")
    finally:
        conn.close()

# View all items
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

# Save to Google Drive
def save_to_drive():
    try:
        upload_db_to_drive()
        download_db_from_drive()
        st.success("Database saved and reloaded.")
    except Exception as e:
        st.error(f"Error saving to Drive: {e}")

# Add new item via form
def add_new_item_form():
    st.subheader("Add a New Item")
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

        submitted = st.form_submit_button("Add Item")
        if submitted:
            add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)

# Search and Edit
def search_and_edit_items():
    download_db_if_needed()
    st.subheader("Search and Edit Items")
    conn = create_connection()
    cursor = conn.cursor()

    keyword = st.text_input("Search by keyword:")
    if st.button("Search"):
        query = "SELECT * FROM items WHERE url LIKE ? OR title LIKE ? OR description LIKE ?"
        cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=[
                "ID", "URL", "Decision", "Decision Reason", "Source", "Title",
                "Description", "Title Translated", "Description Translated",
                "Tags", "Notes", "Languages"
            ])
            st.dataframe(df)
        else:
            st.info("No matching results found.")

    conn.close()

# Sidebar and app selection
apps = {
    "View Database": view_db,
    "Add a New Item": add_new_item_form,
    "Search and Edit": search_and_edit_items,
    "Save to Google Drive": save_to_drive
}

with st.sidebar:
    st.header("Israeli Internet Archive")
    selected = option_menu("Menu", options=list(apps.keys()), icons=["database", "plus", "search", "save"])

# Run selected app
if selected in apps:
    apps[selected]()
