import streamlit as st
import validators
import sqlite3
import pandas as pd

# Function to create the database and table
def create_table():
    conn = sqlite3.connect("items.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            url TEXT,
            decision TEXT,
            decision_reason TEXT,
            source TEXT,
            title TEXT,
            description TEXT,
            translated_title TEXT,
            translated_description TEXT,
            tags TEXT,
            notes TEXT,
            languages TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to create a database connection
def create_connection():
    conn = sqlite3.connect("items.db")
    return conn

# Function to add a new item to the database
def add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO items (url, decision, decision_reason, source, title, description, translated_title, translated_description, tags, notes, languages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages))
    conn.commit()
    conn.close()

# Function to update an existing item in the database
def update_item(item_id, url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE items SET
            url = ?, decision = ?, decision_reason = ?, source = ?, title = ?, description = ?, translated_title = ?, translated_description = ?, tags = ?, notes = ?, languages = ?
        WHERE id = ?
    ''', (url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages, item_id))
    conn.commit()
    conn.close()

# Function to update form with analysis results (assuming analyze_url is a working function)
def update_form_with_analysis(url):
    try:
        title, description, translated_title, translated_description, languages = analyze_url(url)

        # Ensure session state is updated correctly
        st.session_state.title = title
        st.session_state.description = description
        st.session_state.title_translated = translated_title
        st.session_state.description_translated = translated_description
        st.session_state.languages = ', '.join(languages)

    except Exception as e:
        st.error(f"Error during analysis: {e}")

# Function to analyze the URL (replace this with actual URL analysis logic)
def analyze_url(url):
    # Placeholder implementation, replace with real logic
    title = "Sample Title"
    description = "Sample Description"
    translated_title = "Sample Translated Title"
    translated_description = "Sample Translated Description"
    languages = ["English"]
    return title, description, translated_title, translated_description, languages

# Main Streamlit app
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
        
        # Fetch only the necessary columns (avoiding the rowid)
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, url, decision, decision_reason, source, title, description, translated_title, translated_description, tags, notes, languages FROM items')
        items = cursor.fetchall()
        conn.close()

        if items:
            # Create a pandas DataFrame with the expected columns
            df = pd.DataFrame(items, columns=[
                'ID', 'URL', 'Decision', 'Decision Reason', 'Source',
                'Title', 'Description', 'Translated Title', 'Translated Description',
                'Tags', 'Notes', 'Languages'
            ])
            # Display the table
            st.dataframe(df)
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

        search_option = st.radio("Select Search Option", ["Regular Search", "Advanced Search"])

        if search_option == "Regular Search":
            search_term = st.text_input("Enter a search term")
            search_button = st.button("Search")

            if search_button:
                results = regular_search(search_term)
            else:
                results = []

        elif search_option == "Advanced Search":
            st.write("### Advanced Search")
            url_query = st.text_input("URL")
            title_query = st.text_input("Title")
            description_query = st.text_input("Description")
            tags_query = st.text_input("Tags")
            languages_query = st.text_input("Languages")
            search_button = st.button("Search")

            if search_button:
                queries = {
                    "url": url_query,
                    "title": title_query,
                    "description": description_query,
                    "tags": tags_query,
                    "languages": languages_query,
                }
                results = advanced_search(queries)
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


# Running the main function to start the app
if __name__ == "__main__":
    main()
