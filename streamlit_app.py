import sqlite3
import streamlit as st

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
            notes TEXT
        )
    ''')
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
    cursor.execute('''
        UPDATE items
        SET url = ?, decision = ?, source = ?, title = ?, description = ?, tags = ?, notes = ?
        WHERE id = ?
    ''', (url, decision, source, title, description, tags, notes, item_id))
    conn.commit()
    conn.close()

# Main Streamlit app
setup_database()
st.title("Database Management App")

# Search Form
st.write("### Search the Database")
query = st.text_input("Enter a keyword to search")
if st.button("Search"):
    results = search_items(query)
    if results:
        st.write("### Search Results")
        for item in results:
            with st.expander(f"Item ID: {item[0]} - {item[4]}"):
                with st.form(f"edit_form_{item[0]}"):
                    url = st.text_input("URL", value=item[1])
                    decision = st.text_input("Decision", value=item[2])
                    source = st.text_input("Source", value=item[3])
                    title = st.text_input("Title", value=item[4])
                    description = st.text_area("Description", value=item[5])
                    tags = st.text_input("Tags", value=item[6])
                    notes = st.text_area("Notes", value=item[7])
                    submitted = st.form_submit_button("Save Changes")
                    if submitted:
                        update_item(item[0], url, decision, source, title, description, tags, notes)
                        st.success(f"Item ID {item[0]} updated successfully!")
    else:
        st.warning("No items found.")

# Footer
st.write("Use the form above to search and edit database items.")
