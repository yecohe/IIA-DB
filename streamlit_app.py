import sqlite3
import streamlit as st
from datetime import datetime
import validators  # For URL validation
import pandas as pd  # For displaying the database as a table
from streamlit_option_menu import option_menu  # For sidebar menu

# Database connection
def get_connection():
    return sqlite3.connect('items.db')

# Create the table if it doesn't exist
def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            decision TEXT,
            source TEXT,
            title TEXT,
            description TEXT,
            tags TEXT,
            notes TEXT,
            last_edit TEXT
        )
    ''')
    # Add the last_edit column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE items ADD COLUMN last_edit TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()
    conn.close()

# Add a new item to the database
def add_item(url, decision, source, title, description, tags, notes):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO items (url, decision, source, title, description, tags, notes, last_edit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (url, decision, source, title, description, tags, notes, timestamp))
    conn.commit()
    conn.close()

# Fetch all items from the database
def fetch_all_items():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items')
    data = cursor.fetchall()
    conn.close()
    return data

# Fetch items based on a general or advanced search query
def search_items(query, fields=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # If fields are provided, construct a WHERE clause for those fields
    if fields:
        where_clause = ' OR '.join([f"{field} LIKE ?" for field in fields])
        query_params = [f'%{query}%' for _ in fields]
    else:
        # Default: search across all fields
        where_clause = "title LIKE ? OR description LIKE ? OR url LIKE ? OR decision LIKE ? OR source LIKE ? OR tags LIKE ? OR notes LIKE ?"
        query_params = [f'%{query}%'] * 7  # One for each field
    
    cursor.execute(f'SELECT * FROM items WHERE {where_clause}', query_params)
    data = cursor.fetchall()
    conn.close()
    return data

# Update an item in the database
def update_item(item_id, url, decision, source, title, description, tags, notes):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE items
        SET url = ?, decision = ?, source = ?, title = ?, description = ?, tags = ?, notes = ?, last_edit = ?
        WHERE id = ?
    ''', (url, decision, source, title, description, tags, notes, timestamp, item_id))
    conn.commit()
    conn.close()

# Main Streamlit app
setup_database()

# Sidebar menu using streamlit_option_menu
selected = option_menu(
    menu_title=None,
    options=["View Database", "Search and Edit", "Add New Item"],
    icons=["table", "search", "plus"],
    default_index=0,
    orientation="vertical",
    menu_icon="cast"
)

# View Database
if selected == "View Database":
    st.write("### All Items in the Database")
    items = fetch_all_items()
    if items:
        # Convert the data to a pandas DataFrame for better display
        df = pd.DataFrame(items, columns=["ID", "URL", "Decision", "Source", "Title", "Description", "Tags", "Notes", "Last Edit"])
        st.dataframe(df)
    else:
        st.write("No items found in the database.")

# Search and Edit
elif selected == "Search and Edit":
    st.write("### Search the Database")

    # Search options (General vs Advanced)
    search_type = st.selectbox("Select search type", ["General Search (All Fields)", "Advanced Search (Specific Fields)"])

    query = st.text_input("Enter a keyword to search")

    if search_type == "General Search (All Fields)" and query:
        results = search_items(query)
        if results:
            st.write("### Search Results")
            for item in results:
                with st.expander(f"Item ID: {item[0]} - {item[4]} (Last Edit: {item[8]})"):
                    with st.form(f"edit_form_{item[0]}"):
                        url = st.text_input("URL", value=item[1])
                        decision = st.selectbox("Decision", ["Yes", "Maybe", "No"], index=["Yes", "Maybe", "No"].index(item[2]))
                        source = st.text_input("Source", value=item[3])
                        title = st.text_input("Title", value=item[4])
                        description = st.text_area("Description", value=item[5])
                        tags = st.text_input("Tags", value=item[6])
                        notes = st.text_area("Notes", value=item[7])
                        submitted = st.form_submit_button("Save Changes")
                        if submitted:
                            if not validators.url(url):
                                st.error("Invalid URL. Please enter a valid URL.")
                            else:
                                update_item(item[0], url, decision, source, title, description, tags, notes)
                                st.success(f"Item ID {item[0]} updated successfully!")

    elif search_type == "Advanced Search (Specific Fields)" and query:
        fields_to_search = []
        if st.checkbox("Search in URL"):
            fields_to_search.append("url")
        if st.checkbox("Search in Decision"):
            fields_to_search.append("decision")
        if st.checkbox("Search in Source"):
            fields_to_search.append("source")
        if st.checkbox("Search in Title"):
            fields_to_search.append("title")
        if st.checkbox("Search in Description"):
            fields_to_search.append("description")
        if st.checkbox("Search in Tags"):
            fields_to_search.append("tags")
        if st.checkbox("Search in Notes"):
            fields_to_search.append("notes")

        if fields_to_search:
            results = search_items(query, fields=fields_to_search)
            if results:
                st.write("### Search Results")
                for item in results:
                    with st.expander(f"Item ID: {item[0]} - {item[4]} (Last Edit: {item[8]})"):
                        with st.form(f"edit_form_{item[0]}"):
                            url = st.text_input("URL", value=item[1])
                            decision = st.selectbox("Decision", ["Yes", "Maybe", "No"], index=["Yes", "Maybe", "No"].index(item[2]))
                            source = st.text_input("Source", value=item[3])
                            title = st.text_input("Title", value=item[4])
                            description = st.text_area("Description", value=item[5])
                            tags = st.text_input("Tags", value=item[6])
                            notes = st.text_area("Notes", value=item[7])
                            submitted = st.form_submit_button("Save Changes")
                            if submitted:
                                if not validators.url(url):
                                    st.error("Invalid URL. Please enter a valid URL.")
                                else:
                                    update_item(item[0], url, decision, source, title, description, tags, notes)
                                    st.success(f"Item ID {item[0]} updated successfully!")
            else:
                st.warning("No items found.")
        else:
            st.warning("Please select at least one field to search.")

# Add New Item
elif selected == "Add New Item":
    st.write("### Add a New Item")
    with st.form("add_item_form"):
        url = st.text_input("URL")
        decision = st.selectbox("Decision", ["Yes", "Maybe", "No"])
        source = st.text_input("Source")
        title = st.text_input("Title")
        description = st.text_area("Description")
        tags = st.text_input("Tags (comma-separated)")
        notes = st.text_area("Notes")
        add_item_submitted = st.form_submit_button("Add Item")
        if add_item_submitted:
            if not validators.url(url):
                st.error("Invalid URL. Please enter a valid URL.")
            else:
                add_item(url, decision, source, title, description, tags, notes)
                st.success("New item added successfully!")

# Footer
st.write("Use the menu on the left sidebar to navigate between viewing the database, searching/editing items, or adding a new item.")
