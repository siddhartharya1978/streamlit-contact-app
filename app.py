
import streamlit as st
import pandas as pd
import json
import os
import re

CONTACT_FILE = "contacts.csv"
LISTS_FILE = "saved_lists.json"
MATRIX_FILE = "channel_matrix.xlsx"
DOC_FILE = "CHANNELS LIST.docx"

st.set_page_config(layout="wide", page_title="Skype Contact Manager")

# Load contacts
@st.cache_data
def load_contacts():
    df = pd.read_csv(CONTACT_FILE, encoding="ISO-8859-1")
    if "checkbox" not in df.columns:
        df["checkbox"] = False
    return df

# Extract +tags (case-insensitive, non-numeric)
@st.cache_data
def extract_tags(df):
    tags = set()
    for name in df["display_name"]:
        tokens = re.findall(r'\+\w+', str(name))
        tags.update([t.lower() for t in tokens if not re.match(r'\+\d+', t)])
    return sorted(tags)

# Load saved lists
def load_saved_lists():
    if os.path.exists(LISTS_FILE):
        with open(LISTS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save lists to file
def save_lists(lists):
    with open(LISTS_FILE, "w") as f:
        json.dump(lists, f, indent=2)

# UI – Filter tags
def tag_filter_ui(df):
    st.header("🔍 Filter Contacts by Tags")
    tags = extract_tags(df)

    filter_mode = st.radio("Filter Mode", ["AND", "OR"], horizontal=True)
    selected_tags = []
    cols = st.columns(6)
    for i, tag in enumerate(tags):
        if cols[i % 6].checkbox(tag):
            selected_tags.append(tag)

    if selected_tags:
        def match_tags(name):
            found = [t.lower() for t in re.findall(r'\+\w+', str(name)) if not re.match(r'\+\d+', t)]
            if filter_mode == "AND":
                return all(tag in found for tag in selected_tags)
            else:
                return any(tag in found for tag in selected_tags)

        df = df[df["display_name"].apply(match_tags)]
    return df, selected_tags

# UI – Select & Save lists
def select_and_save_ui(df, saved_lists):
    st.header("✅ Select Contacts & Save as List")
    selection_df = df[["display_name"]].copy()
    selection_df["checkbox"] = False
    edited_df = st.data_editor(selection_df, num_rows="fixed", use_container_width=True)

    # Save list
    list_name = st.text_input("List Name")
    if st.button("💾 Save Selected Contacts"):
        selected = edited_df[edited_df["checkbox"] == True]["display_name"].tolist()
        if list_name and selected:
            saved_lists[list_name] = selected
            save_lists(saved_lists)
            st.success(f"Saved list '{list_name}' with {len(selected)} contacts.")

    # Load existing list
    st.subheader("📂 Load or Edit Saved List")
    if saved_lists:
        selected_list = st.selectbox("Choose a Saved List", list(saved_lists.keys()))
        if selected_list:
            st.markdown(f"**📋 Contacts in '{selected_list}'**")
            selected = st.multiselect("Modify this list:", df["display_name"].tolist(), default=saved_lists[selected_list])
            if st.button("💾 Update List"):
                saved_lists[selected_list] = selected
                save_lists(saved_lists)
                st.success("List updated.")

            if st.button("🗑️ Delete List"):
                del saved_lists[selected_list]
                save_lists(saved_lists)
                st.warning(f"Deleted list: {selected_list}")

# UI – Edit contacts
def edit_contacts_ui(df):
    st.header("✍️ Edit Contacts Inline")
    editable_df = st.data_editor(df[["display_name"]], use_container_width=True, key="edit_contacts")
    if st.button("💾 Save Edited Contacts"):
        df["display_name"] = editable_df["display_name"]
        df.to_csv(CONTACT_FILE, index=False, encoding="ISO-8859-1")
        st.success("Contacts updated and saved.")

# UI – Add contact
def add_contact_ui(df):
    st.header("➕ Add New Contact")
    new_contact = st.text_input("Enter New Contact (with tags)")
    if st.button("➕ Add Contact"):
        if new_contact.strip():
            new_row = pd.DataFrame({"display_name": [new_contact]})
            for col in df.columns:
                if col not in new_row.columns:
                    new_row[col] = False if col == "checkbox" else ""
            df = pd.concat([df, new_row[df.columns]], ignore_index=True)
            df.to_csv(CONTACT_FILE, index=False, encoding="ISO-8859-1")
            st.success("Contact added. Please refresh to see the change.")
    return df

# UI – Channel Matrix
def channel_matrix_ui():
    st.header("🧭 Channel Matrix Viewer")
    try:
        matrix_df = pd.read_excel(MATRIX_FILE)
        matrix_df = matrix_df.rename(columns={matrix_df.columns[0]: "Operator"})
        charterers = list(matrix_df.columns[1:])
        selected = st.selectbox("Select a Charterer", charterers)

        yes_ops = matrix_df[matrix_df[selected].astype(str).str.upper() == "YES"]["Operator"].dropna()
        no_ops = matrix_df[matrix_df[selected].astype(str).str.upper() == "NO"]["Operator"].dropna()

        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ Operators Who Work With Us")
            st.dataframe(yes_ops, use_container_width=True)

        with col2:
            st.error("❌ Operators Who Don't Work With Us")
            st.dataframe(no_ops, use_container_width=True)

    except Exception as e:
        st.warning(f"Matrix load failed: {e}")

# UI – View Docx File
def docx_viewer_ui():
    st.header("📄 View CHANNELS LIST Document")
    try:
        import docx
        document = docx.Document(DOC_FILE)
        for para in document.paragraphs:
            st.markdown(para.text)
    except Exception as e:
        st.error(f"Could not load DOCX file: {e}")

# ========================== MAIN ==========================
df = load_contacts()
saved_lists = load_saved_lists()

tab1, tab2, tab3 = st.tabs(["📁 Contact Manager", "📊 Channel Matrix", "📄 New Channel List"])

with tab1:
    df, _ = tag_filter_ui(df)
    select_and_save_ui(df, saved_lists)
    edit_contacts_ui(df)
    df = add_contact_ui(df)

with tab2:
    channel_matrix_ui()

with tab3:
    docx_viewer_ui()
