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
import validators

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('Good', 'Bad'))
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
        upload_db_to_drive()
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

# Function to manage words lists
def manage_words_lists():
    create_table()
    st.subheader("Manage Words Lists")
    conn = create_connection()
    cursor = conn.cursor()

    # Add a word
    with st.form("add_word_form"):
        word = st.text_input("Word")
        word_type = st.selectbox("Type", ["Good", "Bad"])
        submit = st.form_submit_button("Add Word")
        if submit:
            cursor.execute("INSERT INTO words_lists (word, type) VALUES (?, ?)", (word, word_type))
            conn.commit()
            st.success("Word added successfully!")
            upload_db_to_drive()

    # View existing words
    cursor.execute("SELECT * FROM words_lists")
    words = cursor.fetchall()
    df = pd.DataFrame(words, columns=["ID", "Word", "Type"])
    st.dataframe(df)

    # Edit or delete words
    for row in words:
        with st.expander(f"Edit/Delete Word ID: {row[0]}"):
            new_word = st.text_input("Word", value=row[1], key=f"word_{row[0]}")
            new_type = st.selectbox("Type", ["Good", "Bad"], index=["Good", "Bad"].index(row[2]), key=f"type_{row[0]}")
            if st.button(f"Update Word ID {row[0]}", key=f"update_{row[0]}"):
                cursor.execute("UPDATE words_lists SET word = ?, type = ? WHERE id = ?", (new_word, new_type, row[0]))
                conn.commit()
                st.success("Word updated successfully!")
                upload_db_to_drive()
            if st.button(f"Delete Word ID {row[0]}", key=f"delete_{row[0]}"):
                cursor.execute("DELETE FROM words_lists WHERE id = ?", (row[0],))
                conn.commit()
                st.warning("Word deleted!")
                upload_db_to_drive()

    conn.close()
    
# Function to fetch good and bad words from the database
def fetch_good_bad_words():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word, type FROM words_lists")
    words = cursor.fetchall()
    conn.close()
    
    good_words = [word[0] for word in words if word[1] == 'Good']
    bad_words = [word[0] for word in words if word[1] == 'Bad']
    return good_words, bad_words
    
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
    good_words, bad_words = fetch_good_bad_words()
    try:
        analyzed_data = analyze_url(url, good_words, bad_words)
        if analyzed_data:
            title, description, translated_title, translated_description, languages, decision, reason = analyzed_data
            
            st.session_state["title"] = title
            st.session_state["description"] = description
            st.session_state["title_translated"] = translated_title
            st.session_state["description_translated"] = translated_description
            st.session_state["languages"] = ", ".join(languages)
            st.session_state["decision"] = decision
            st.session_state["decision_reason"] = reason
            st.session_state["notes"] = "Automatically analyzed"
            st.rerun()
    except Exception as e:
        st.error(f"Error analyzing URL: {e}")

# Function to add a new item via a form
def add_new_item_form():
    st.subheader("Add a New Item to the Database")

    if "title" not in st.session_state:
        st.session_state["title"] = ""
        st.session_state["description"] = ""
        st.session_state["title_translated"] = ""
        st.session_state["description_translated"] = ""
        st.session_state["languages"] = ""
        st.session_state["decision"] = "Maybe"
        st.session_state["decision_reason"] = ""
        st.session_state["notes"] = ""

    with st.form(key="new_item_form"):
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            url = st.text_input("URL")
        with col2:
            analyze_button = st.form_submit_button("Analyze")            
        col1, col2 = st.columns(2)
        with col1:
            decision = st.selectbox("Decision", ["Yes", "Maybe", "No"], index=["Yes", "Maybe", "No"].index(st.session_state["decision"]))
        with col2:
            decision_reason = st.text_input("Decision Reason", value=st.session_state["decision_reason"])          
        source = st.text_input("Source")
        title = st.text_input("Title", value=st.session_state["title"])
        description = st.text_area("Description", value=st.session_state["description"])
        title_translated = st.text_input("Title (Translated)", value=st.session_state["title_translated"])
        description_translated = st.text_area("Description (Translated)", value=st.session_state["description_translated"])
        tags = st.text_input("Tags")
        notes = st.text_area("Notes", value=st.session_state["notes"])
        languages = st.text_input("Languages (comma separated)", value=st.session_state["languages"])

        col1, col2, col3 = st.columns(3)
        with col1:
            add_item_submitted = st.form_submit_button("Add Item")
        with col2:
            analyze_button_bottom = st.form_submit_button("Analyze?")  
        with col3:
            clear_button = st.form_submit_button("Clear")
        
        if analyze_button or analyze_button_bottom:
            with st.spinner('Analyzing...'):
                update_form_with_analysis(url)

        if add_item_submitted:
            if not validators.url(url):
                st.error("Invalid URL. Please enter a valid URL.")
            else:
                add_item(
                    url, decision, decision_reason, source, title, description,
                    title_translated, description_translated, tags, notes, languages
                )
                st.success("New item added successfully!")
                st.session_state.clear()
                st.rerun()

        if clear_button:
            st.session_state.clear()
            st.rerun()
            
# Save to Google Drive function
def save_to_drive():
    try:
        upload_db_to_drive()  # Upload the updated database to Google Drive
    except Exception as e:
        st.error(f"Error saving to Google Drive: {e}")

# Function to perform a search and allow editing
def search_and_edit_items(mode="simple"):
    """
    Perform a search in the database and allow users to edit fields.
    
    Args:
    - mode: 'simple' or 'advanced'. Default is 'simple'.
    """
    download_db_if_needed()
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Perform a search
        if mode == "simple":
            keyword = st.text_input("Enter a keyword to search:")
            if st.button("Search"):
                query = """
                    SELECT * FROM items 
                    WHERE url LIKE ? OR decision LIKE ? OR decision_reason LIKE ? 
                    OR source LIKE ? OR title LIKE ? OR description LIKE ? 
                    OR title_translated LIKE ? OR description_translated LIKE ? 
                    OR tags LIKE ? OR notes LIKE ? OR languages LIKE ?
                """
                params = tuple([f"%{keyword}%"] * 11)
                cursor.execute(query, params)
        elif mode == "advanced":
            st.write("Specify your search criteria:")
            fields = [
                "url", "decision", "decision_reason", "source", "title", 
                "description", "title_translated", "description_translated", 
                "tags", "notes", "languages"
            ]
            criteria = {}
            for field in fields:
                value = st.text_input(f"{field.capitalize()}:")
                if value:
                    criteria[field] = value
            
            if st.button("Search"):
                if criteria:
                    conditions = " AND ".join([f"{field} LIKE ?" for field in criteria.keys()])
                    query = f"SELECT * FROM items WHERE {conditions}"
                    params = tuple([f"%{value}%" for value in criteria.values()])
                    cursor.execute(query, params)
                else:
                    st.warning("Please provide at least one search criterion.")
        else:
            st.warning("Invalid search mode.")
            return
        
        # Fetch and display search results
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=[
                "ID", "URL", "Decision", "Decision Reason", "Source", "Title", 
                "Description", "Title Translated", "Description Translated", 
                "Tags", "Notes", "Languages"
            ])
            st.subheader("Search Results")
            st.dataframe(df)

            # Allow editing of each row
            for row in rows:
                with st.expander(f"Edit Item ID: {row[0]}"):
                    url = st.text_input("URL", value=row[1], key=f"url_{row[0]}")
                    decision = st.text_input("Decision", value=row[2], key=f"decision_{row[0]}")
                    decision_reason = st.text_input("Decision Reason", value=row[3], key=f"reason_{row[0]}")
                    source = st.text_input("Source", value=row[4], key=f"source_{row[0]}")
                    title = st.text_input("Title", value=row[5], key=f"title_{row[0]}")
                    description = st.text_area("Description", value=row[6], key=f"description_{row[0]}")
                    title_translated = st.text_input("Title (Translated)", value=row[7], key=f"title_trans_{row[0]}")
                    description_translated = st.text_area("Description (Translated)", value=row[8], key=f"description_trans_{row[0]}")
                    tags = st.text_input("Tags", value=row[9], key=f"tags_{row[0]}")
                    notes = st.text_area("Notes", value=row[10], key=f"notes_{row[0]}")
                    languages = st.text_input("Languages", value=row[11], key=f"languages_{row[0]}")

                    if st.button(f"Save Changes for ID {row[0]}", key=f"save_{row[0]}"):
                        try:
                            cursor.execute(''' 
                                UPDATE items
                                SET url = ?, decision = ?, decision_reason = ?, source = ?, title = ?, 
                                    description = ?, title_translated = ?, description_translated = ?, 
                                    tags = ?, notes = ?, languages = ?
                                WHERE id = ?
                            ''', (url, decision, decision_reason, source, title, description, 
                                  title_translated, description_translated, tags, notes, languages, row[0]))
                            conn.commit()
                            save_to_drive()
                            st.success(f"Item ID {row[0]} updated successfully!")
                        except Exception as e:
                            st.error(f"Error updating item ID {row[0]}: {e}")
        else:
            st.info("No results found.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        conn.close()

# Update search mode selector to include editing
def search_and_edit_mode_selector():
    st.subheader("Search and Edit the Database")
    mode = st.radio("Select search mode:", options=["Simple", "Advanced"], index=0)
    if mode == "Simple":
        search_and_edit_items(mode="simple")
    elif mode == "Advanced":
        search_and_edit_items(mode="advanced")




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
    "Search and Edit": search_and_edit_mode_selector,
    "Words Lists": manage_words_lists,
    "Save to Google Drive": save_to_drive  
}

# Sidebar menu
if authenticated:
    with st.sidebar:
        selected_app_name = option_menu(
            "Tools Menu",
            options=list(apps.keys()),
            icons=["database", "link", "filter", "search", "list", "save"], 
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
