import streamlit as st
from streamlit_option_menu import option_menu
import validators
from tools import analyze_url

# Mock functions for database operations
def add_item(url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    st.info("Item added to database")

def update_item(item_id, url, decision, decision_reason, source, title, description, title_translated, description_translated, tags, notes, languages):
    st.info(f"Item {item_id} updated in database")

def search_items(search_term):
    return []  # Mock search results

def get_all_items():
    return []  # Mock database items

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

def main():
    # Sidebar menu
    with st.sidebar:
        selected = option_menu(
            "Menu",
            ["Add New Item", "Edit Item", "View Database"],
            icons=["plus", "pencil", "table"],
            menu_icon="menu",
            default_index=0
        )

    # Add New Item
    if selected == "Add New Item":
        st.write("### Add a New Item")

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

    # Edit Item
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

    # View Database
    elif selected == "View Database":
        st.write("### Database View")

        items = get_all_items()
        if items:
            for item in items:
                st.write(f"ID: {item[0]}, Title: {item[5]}, URL: {item[1]}")
        else:
            st.info("No items in the database.")

if __name__ == "__main__":
    main()
