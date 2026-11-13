"""Gulshan Cash & Carry — online grocery ordering (Streamlit).

Run locally:   streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Gulshan Cash & Carry · G-10 Markaz",
    page_icon="logo.png",
    layout="wide",
)

import db
import ui  # noqa: E402  (after set_page_config)

db.get_engine()  # creates tables and sample data on first run
ui.setup_page()

pages = [
    st.Page("shop.py", title="Shop", icon="🛍️", default=True),
    st.Page("checkout.py", title="Basket & checkout", icon="🛒"),
    st.Page("track.py", title="Track order", icon="🚚"),
    st.Page("admin.py", title="Admin", icon="🔒"),
]
st.navigation(pages).run()
