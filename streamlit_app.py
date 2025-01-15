import streamlit as st
import sqlite3
import validators
from tools import analyze_url
from streamlit_option_menu import option_menu

# SQLite3 Database setup
def create_connection():
    conn = sqlite3.connect('database.db')
    return conn

# Create the items table if it doesn't exist
def create_table():
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO items (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages))
    conn.commit()
    conn.close()

# Update an existing item in the database
def update_item(item_id, url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE items
        SET url = ?, decision = ?, decision_reason = ?, source = ?, title = ?, description = ?, title_translated = ?, description_translated = ?, tags = ?, notes = ?, languages = ?
        WHERE id = ?
    ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages, item_id))
    conn.commit()
    conn.close()

# Search for items in the database
def search_items(search_term):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM items WHERE title LIKE ? OR tags LIKE ?
    ''', ('%' + search_term + '%', '%' + search_term + '%'))
    results = cursor.fetchall()
    conn.close()
    return results

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

# Main Streamlit app
def main():
    # Initialize the database and create the table
    create_table()

    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=["View Database", "Add New Item", "Edit Item"],
            icons=["view-list", "plus-circle", "pencil"],
            default_index=0,
        )

    if selected == "View Database":
        st.write("### View Database")
        
        # Fetch all items from the database
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM items')
        items = cursor.fetchall()
        conn.close()

        if items:
            # Display the items in a table
            st.write("### Items List")
            table_data = []
            for item in items:
                table_data.append([
                    item[0],  # ID
                    item[1],  # URL
                    item[2],  # Decision
                    item[3],  # Decision Reason
                    item[4],  # Source
                    item[5],  # Title
                    item[6],  # Description
                    item[7],  # Translated Title
                    item[8],  # Translated Description
                    item[9],  # Tags
                    item[10],  # Notes
                    item[11],  # Languages
                ])
            st.dataframe(table_data, columns=[
                'ID', 'URL', 'Decision', 'Decision Reason', 'Source',
                'Title', 'Description', 'Translated Title', 'Translated Description',
                'Tags', 'Notes', 'Languages'
            ])
        else:
            st.info("No items in the database.")
        
        
    elif selected == "Add New Item":
        st.write("### Add a New Item")

        # Initialize session state variables for form
        if "title" not in st.session_state:
            st.session_state.title = ""
            st.session_state.description = ""
            st.session_state.title_translated = ""
            st.session_state.description_translated = ""
            st.session_state.languages = ""

        with st.form("add_item_form"):
            url = st.text_input("URL")
            decision = st.selectbox("Decision", ["Yes", "Maybe", "No"])
            decision_reason = st.text_input("Decision Reason")
            source = st.text_input("Source")
            title = st.text_input("Title", value=st.session_state.title)
            description = st.text_area("Description", value=st.session_state.description)
            title_translated = st.text_input("Translated Title", value=st.session_state.title_translated)
            description_translated = st.text_area("Translated Description", value=st.session_state.description_translated)
            tags = st.text_input("Tags (comma-separated)")
            languages = st.text_input("Languages (comma-separated)", value=st.session_state.languages)
            notes = st.text_area("Notes")

            analyze_button = st.form_submit_button("Analyze")
            add_item_submitted = st.form_submit_button("Add Item")

            if analyze_button:
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

    elif selected == "Edit Item":
        st.write("### Edit Existing Items")

        search_term = st.text_input("Search by keyword or tag")
        search_button = st.button("Search")

        if search_button:
            results = search_items(search_term)
        else:
            results = []

        if results:
            st.write("### Search Results")
            for item in results:
                item_id = item[0]
                if f"edit_{item_id}_url" not in st.session_state:
                    st.session_state[f"edit_{item_id}_title"] = item[5]
                    st.session_state[f"edit_{item_id}_description"] = item[6]
                    st.session_state[f"edit_{item_id}_title_translated"] = item[7]
                    st.session_state[f"edit_{item_id}_description_translated"] = item[8]
                    st.session_state[f"edit_{item_id}_languages"] = item[11]

                with st.expander(f"Item ID: {item_id} - {item[5]}"):
                    with st.form(f"edit_form_{item_id}"):
                        url = st.text_input("URL", value=item[1])
                        decision = st.selectbox("Decision", ["Yes", "Maybe", "No"], index=["Yes", "Maybe", "No"].index(item[2]))
                        decision_reason = st.text_input("Decision Reason", value=item[3])
                        source = st.text_input("Source", value=item[4])
                        title = st.text_input("Title", value=st.session_state[f"edit_{item_id}_title"])
                        description = st.text_area("Description", value=st.session_state[f"edit_{item_id}_description"])
                        title_translated = st.text_input("Translated Title", value=st.session_state[f"edit_{item_id}_title_translated"])
                        description_translated = st.text_area("Translated Description", value=st.session_state[f"edit_{item_id}_description_translated"])
                        tags = st.text_input("Tags", value=item[9])
                        languages = st.text_input("Languages (comma-separated)", value=st.session_state[f"edit_{item_id}_languages"])
                        notes = st.text_area("Notes", value=item[10])

                        analyze_button = st.form_submit_button("Analyze")
                        save_changes = st.form_submit_button("Save Changes")

                        if analyze_button:
                            update_form_with_analysis(url)

                        if save_changes:
                            if not validators.url(url):
                                st.error("Invalid URL. Please enter a valid URL.")
                            else:
                                update_item(
                                    item_id, url, decision, decision_reason, source, title,
                                    description, title_translated, description_translated,
                                    tags, notes, languages
                                )
                                st.success(f"Item ID {item_id} updated successfully!")

if __name__ == "__main__":
    main()
