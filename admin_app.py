"""Gulshan Cash & Carry — ADMIN portal (Streamlit).

Deploy this as a SEPARATE Streamlit app (main file: admin_app.py) with its own
web address. Customers use app.py and never see this one.

It must use the SAME DATABASE_URL as the customer app so that orders arrive
here and product changes reach the store.

Run locally:   streamlit run admin_app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Gulshan Cash & Carry · Store admin",
    page_icon="logo.png",
    layout="wide",
)

import db  # noqa: E402
import ui  # noqa: E402

db.get_engine()
ui.setup_page()

# One page only, no menu. Search engines are asked not to list it.
st.html('<meta name="robots" content="noindex, nofollow">')
st.navigation([st.Page("admin.py", title="Store admin", icon="🔒", default=True)], position="hidden").run()
