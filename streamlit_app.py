import sqlite3
import streamlit as st
from datetime import datetime
import validators  # For URL validation

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

# Fetch items based on a search query
def search_items(query):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM items WHERE title LIKE ? OR description LIKE ?', (f'%{query}%', f'%{query}%'))
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
st.title("Database Management App")

# Add Item Form
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

# Search Form
st.write("### Search the Database")
query = st.text_input("Enter a keyword to search")
if st.button("Search"):
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
    else:
        st.warning("No items found.")

# Footer
st.write("Use the forms above to add, search, and edit database items.")
