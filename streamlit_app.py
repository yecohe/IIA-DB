import sqlite3
import streamlit as st
from datetime import datetime
import validators  # For URL validation
import pandas as pd  # For displaying the database as a table
from streamlit_option_menu import option_menu  # For sidebar menu
from tools import analyze_url  # Assuming you have this function to analyze URL

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
            decision_reason TEXT,
            source TEXT,
            title TEXT,
            description TEXT,
            title_translated TEXT,
            description_translated TEXT,
            tags TEXT,
            notes TEXT,
            languages TEXT,
            last_edit TEXT
        )
    ''')
    # Add the last_edit column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE items ADD COLUMN languages TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()
    conn.close()

# Add a new item to the database
def add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO items (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages, last_edit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages, timestamp))
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
def search_items(query, fields=None, conditions=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # If conditions are provided, construct a WHERE clause for those conditions
    where_clause = ""
    query_params = []
    
    if fields and conditions:
        where_clauses = []
        for field, condition in zip(fields, conditions):
            if condition:
                where_clauses.append(f"{field} LIKE ?")
                query_params.append(f"%{condition}%")
        where_clause = " AND ".join(where_clauses)
    elif query:
        # Default: search across all fields
        where_clause = "title LIKE ? OR description LIKE ? OR url LIKE ? OR decision LIKE ? OR source LIKE ? OR tags LIKE ? OR notes LIKE ? OR decision_reason LIKE ? OR title_translated LIKE ? OR description_translated LIKE ? OR languages LIKE ?"
        query_params = [f'%{query}%'] * 11  # One for each field

    cursor.execute(f'SELECT * FROM items WHERE {where_clause}', query_params)
    data = cursor.fetchall()
    conn.close()
    return data

# Update an item in the database
def update_item(item_id, url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE items
        SET url = ?, decision = ?, decision_reason = ?, source = ?, title = ?, description = ?, title_translated = ?, description_translated = ?, tags = ?, notes = ?, languages = ?, last_edit = ?
        WHERE id = ?
    ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages, timestamp, item_id))
    conn.commit()
    conn.close()

# Format ID to always be 5 digits
def format_id(id):
    return f"{id:05}"

# Main Streamlit app
setup_database()

# Sidebar menu using streamlit_option_menu
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["View Database", "Search and Edit", "Add New Item"],
        icons=["table", "search", "plus"],
        default_index=0,
        orientation="vertical",
        menu_icon="cast",
        key="main_menu"  # Ensuring it works well in the sidebar
    )

# View Database
if selected == "View Database":
    st.write("### All Items in the Database")
    items = fetch_all_items()
    if items:
        # Convert the data to a pandas DataFrame for better display
        df = pd.DataFrame(items, columns=["ID", "URL", "Decision", "Reason", "Source", "Title", "Description", "Translated Title", "Translated Description", "Tags", "Notes", "Languages", "Last Edit"])
        df["ID"] = df["ID"].apply(format_id)  # Format ID to 5 digits
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
                item_id = format_id(item[0])  # Format the ID
                with st.expander(f"Item ID: {item_id} - {item[5]} (Last Edit: {item[12]})"):
                    with st.form(f"edit_form_{item[0]}"):
                        url = st.text_input("URL", value=item[1])
                        decision = st.selectbox("Decision", ["Yes", "Maybe", "No"], index=["Yes", "Maybe", "No"].index(item[2]))
                        decision_reason = st.text_input("Decision Reason", value=item[3])
                        source = st.text_input("Source", value=item[4])
                        title = st.text_input("Title", value=item[5])
                        description = st.text_area("Description", value=item[6])
                        title_translated = st.text_input("Translated Title", value=item[7])
                        description_translated = st.text_area("Translated Description", value=item[8])
                        tags = st.text_input("Tags", value=item[9])
                        languages = st.text_input("Languages (comma-separated)", value=item[11])
                        notes = st.text_area("Notes", value=item[10])  # Notes should be last
                        submitted = st.form_submit_button("Save Changes")
                        if submitted:
                            if not validators.url(url):
                                st.error("Invalid URL. Please enter a valid URL.")
                            else:
                                update_item(item[0], url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
                                st.success(f"Item ID {item_id} updated successfully!")

    elif search_type == "Advanced Search (Specific Fields)" and query:
        fields_to_search = []
        conditions = []
        if st.checkbox("Search in URL"):
            fields_to_search.append("url")
            conditions.append(st.text_input("Search in URL"))
        if st.checkbox("Search in Decision"):
            fields_to_search.append("decision")
            conditions.append(st.text_input("Search in Decision"))
        if st.checkbox("Search in Source"):
            fields_to_search.append("source")
            conditions.append(st.text_input("Search in Source"))
        if st.checkbox("Search in Title"):
            fields_to_search.append("title")
            conditions.append(st.text_input("Search in Title"))
        if st.checkbox("Search in Description"):
            fields_to_search.append("description")
            conditions.append(st.text_input("Search in Description"))
        if st.checkbox("Search in Translated Title"):
            fields_to_search.append("title_translated")
            conditions.append(st.text_input("Search in Translated Title"))
        if st.checkbox("Search in Translated Description"):
            fields_to_search.append("description_translated")
            conditions.append(st.text_input("Search in Translated Description"))
        if st.checkbox("Search in Tags"):
            fields_to_search.append("tags")
            conditions.append(st.text_input("Search in Tags"))
        if st.checkbox("Search in Notes"):
            fields_to_search.append("notes")
            conditions.append(st.text_input("Search in Notes"))
        if st.checkbox("Search in Decision Reason"):
            fields_to_search.append("decision_reason")
            conditions.append(st.text_input("Search in Decision Reason"))
        if st.checkbox("Search in Languages"):
            fields_to_search.append("languages")
            conditions.append(st.text_input("Search in Languages"))

        if fields_to_search and all(conditions):
            results = search_items(query, fields=fields_to_search, conditions=conditions)
            if results:
                st.write("### Search Results")
                for item in results:
                    item_id = format_id(item[0])  # Format the ID
                    with st.expander(f"Item ID: {item_id} - {item[5]} (Last Edit: {item[12]})"):
                        with st.form(f"edit_form_{item[0]}"):
                            url = st.text_input("URL", value=item[1])
                            decision = st.selectbox("Decision", ["Yes", "Maybe", "No"], index=["Yes", "Maybe", "No"].index(item[2]))
                            decision_reason = st.text_input("Decision Reason", value=item[3])
                            source = st.text_input("Source", value=item[4])
                            title = st.text_input("Title", value=item[5])
                            description = st.text_area("Description", value=item[6])
                            title_translated = st.text_input("Translated Title", value=item[7])
                            description_translated = st.text_area("Translated Description", value=item[8])
                            tags = st.text_input("Tags", value=item[9])
                            languages = st.text_input("Languages (comma-separated)", value=item[11])
                            notes = st.text_area("Notes", value=item[10])  # Notes should be last
                            submitted = st.form_submit_button("Save Changes")
                            if submitted:
                                if not validators.url(url):
                                    st.error("Invalid URL. Please enter a valid URL.")
                                else:
                                    update_item(item[0], url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
                                    st.success(f"Item ID {item_id} updated successfully!")
            else:
                st.warning("No items found.")
        else:
            st.warning("Please enter search criteria for at least one field.")

# Add New Item
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
        languages = st.text_input("Languages (comma-separated)")  # Before notes
        notes = st.text_area("Notes")
        analyze_button = st.form_submit_button("Analyze")
        add_item_submitted = st.form_submit_button("Add Item")
        
        if analyze_button:
            if validators.url(url):
                analyzed_title, analyzed_description = analyze_url(url)
                title = analyzed_title
                description = analyzed_description
                st.success(f"Title and Description populated from the URL: {title}")
            else:
                st.error("Please enter a valid URL to analyze.")
        
        if add_item_submitted:
            if not validators.url(url):
                st.error("Invalid URL. Please enter a valid URL.")
            else:
                add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
                st.success("New item added successfully!")

# Footer
st.write("Use the menu on the left sidebar to navigate between viewing the database, searching/editing items, or adding a new item.")
