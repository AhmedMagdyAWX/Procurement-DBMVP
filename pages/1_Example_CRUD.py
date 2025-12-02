# pages/1_Example_CRUD.py
import streamlit as st
from db import get_db
from services import create_example_item, list_example_items, delete_example_item

st.title("Example CRUD Page")

st.markdown("This is just a demo to prove the DB + ORM + Streamlit stack is working.")


# --- Create form ---
st.subheader("Create new item")

with st.form("create_item_form"):
    name = st.text_input("Name", max_chars=255)
    description = st.text_area("Description", max_chars=1000)
    submitted = st.form_submit_button("Create")

    if submitted:
        if not name.strip():
            st.error("Name is required.")
        else:
            db = next(get_db())
            item = create_example_item(db, name=name.strip(), description=description.strip() or None)
            st.success(f"Created item with ID {item.id}")


# --- List items ---
st.subheader("Existing items")

db = next(get_db())
items = list_example_items(db)

if not items:
    st.info("No items yet. Create one above.")
else:
    for item in items:
        with st.expander(f"[{item.id}] {item.name}"):
            st.write(f"**Description:** {item.description or '-'}")
            st.write(f"**Created at:** {item.created_at}")

            if st.button(f"Delete #{item.id}", key=f"delete_{item.id}"):
                if delete_example_item(db, item.id):
                    st.success("Item deleted. Please refresh the page.")
                else:
                    st.error("Could not delete item (maybe already deleted).")
