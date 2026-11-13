"""Gulshan Cash & Carry — CUSTOMER website (Streamlit).

The admin portal is a separate app (admin_app.py) with its own web address.
Nothing in this app links to it or can open it.

Run locally:   streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Gulshan Cash & Carry · G-10 Markaz Islamabad",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import db  # noqa: E402
import layout  # noqa: E402
import ui  # noqa: E402

try:
    db.get_engine()  # creates tables and sample data on first run
except db.DatabaseUnavailable:
    st.error("We can't reach the store's database right now. Please try again in a few minutes.")
    st.caption("Store owner: open Manage app → logs and look for “DATABASE CONNECTION FAILED”.")
    st.stop()
ui.setup_page()
layout.apply_css()

version = ui.live_catalog()  # reloads within seconds of any admin change
s = db.get_settings(version)
products = db.load_products(version)
sectors = db.load_sectors(version)

shop = st.Page("shop.py", title="Groceries", icon="🛍️", default=True)
pages = [
    shop,
    st.Page("checkout.py", title="Basket & checkout", icon="🛒"),
    st.Page("track.py", title="Track order", icon="🚚"),
]
pg = st.navigation(pages, position="hidden")

# Shared header: on every page, and widgets here keep their value across pages.
layout.topbar(s, sectors)
layout.navbar(s, products, sectors)
if pg.title == shop.title:
    layout.hero(s, sectors)

with st.container(key="gcc-page"):
    pg.run()
    if pg.title == shop.title:
        layout.delivery_rates(s, sectors)
        layout.store_info(s)

layout.footer(s, products, sectors)

# Header/footer links that jump to another page
goto = st.session_state.pop("_goto", None)
if goto and not (goto == "shop.py" and pg.title == shop.title):
    st.switch_page(shop if goto == "shop.py" else goto)
