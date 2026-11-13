"""Gulshan Cash & Carry — online grocery ordering (Streamlit).

Run locally:   streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Gulshan Cash & Carry · G-10 Markaz",
    page_icon="assets/logo.png",
    layout="wide",
)

from core import db, ui  # noqa: E402  (after set_page_config)

db.get_engine()  # creates tables and sample data on first run
ui.setup_page()

pages = [
    st.Page("views/shop.py", title="Shop", icon="🛍️", default=True),
    st.Page("views/checkout.py", title="Basket & checkout", icon="🛒"),
    st.Page("views/track.py", title="Track order", icon="🚚"),
    st.Page("views/admin.py", title="Admin", icon="🔒"),
]
st.navigation(pages).run()
