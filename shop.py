import streamlit as st

import catalog
import db
import layout
import ui

version = ui.version()
s = db.get_settings(version)
products = db.load_products(version)

if products.empty:
    st.info("The catalog is empty. The store will add products soon.")
    st.stop()

# ---------------------------------------------------------------- filter state (set by header/footer links too)
st.session_state.setdefault("cat", "All")
st.session_state.setdefault("deals_only", False)
st.session_state.setdefault("search", "")
cats = ["All"] + sorted(c for c in products.category.unique() if c)
if st.session_state["cat"] not in cats:
    st.session_state["cat"] = "All"


# ---------------------------------------------------------------- catalog
layout.section_title("Daily fresh inventory", "Browse grocery catalog",
                     "Wholesale cash & carry rates, delivered across Islamabad.", anchor="catalog")

search = st.text_input("Search", placeholder="Search atta, چاول, Dalda, tea …",
                       label_visibility="collapsed", key="search")
cat = st.pills("Category", cats, key="cat", label_visibility="collapsed") or "All"
f1, f2 = st.columns([1, 1], vertical_alignment="center")
deals_only = f1.toggle("🔥 Deals only", key="deals_only")
sort = f2.selectbox("Sort", ["Featured", "Price: low to high", "Price: high to low", "Biggest savings"],
                    key="sort", label_visibility="collapsed")

df = products
if cat != "All":
    df = df[df.category == cat]
if deals_only:
    df = df[df.is_deal]
if search.strip():
    q = search.strip().lower()
    hay = (df["name"] + " " + df.urdu_name + " " + df.brand + " " + df.description + " "
           + df.barcode + " " + df.category).str.lower()
    df = df[hay.str.contains(q, regex=False)]
if sort == "Price: low to high":
    df = df.sort_values("price")
elif sort == "Price: high to low":
    df = df.sort_values("price", ascending=False)
elif sort == "Biggest savings":
    df = df.assign(_s=(df.mrp - df.price).clip(lower=0)).sort_values("_s", ascending=False)
else:  # featured: in-stock deals first
    df = df.assign(_k=(df.stock > 0).astype(int) * 2 + df.is_deal.astype(int)).sort_values(
        ["_k", "category", "name"], ascending=[False, True, True])

if not (cat == "All" and not deals_only and not search.strip()):
    st.caption(f"{len(df)} item{'s' if len(df) != 1 else ''} found")
if df.empty:
    st.info("No products match. Try “atta”, “rice”, “oil” or “milk”.")
else:
    page_size = 24
    shown = st.session_state.get("show_n", page_size)
    catalog.grid(df.head(shown), "cat")
    if len(df) > shown:
        if st.button(f"Show more ({len(df) - shown} left)", width="stretch"):
            st.session_state["show_n"] = shown + page_size
            st.rerun()
