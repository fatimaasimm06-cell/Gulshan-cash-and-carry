import streamlit as st

import db
import layout
import ui

version = ui.version()
s = db.get_settings(version)
products = db.load_products(version)
sectors = db.load_sectors(version)


def _add(sku: str, qkey: str, info: dict) -> None:
    qty = int(st.session_state.get(qkey, 1) or 1)
    ui.add_to_cart(sku, qty, info)


def product_card(p, prefix: str) -> None:
    sku = p.sku
    in_cart = ui.cart().get(sku, 0)
    with st.container(key=f"pc_{prefix}_{sku}"):
        ui.product_image(p)
        st.markdown(f'<div class="gcc-name">{p["name"]}</div>', unsafe_allow_html=True)
        if p.urdu_name:
            st.markdown(f'<div class="gcc-urdu">{p.urdu_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="gcc-unit">{p.brand} · {p.unit}</div>', unsafe_allow_html=True)
        mrp = f'<span class="gcc-mrp">{ui.rs(p.mrp)}</span>' if p.mrp and p.mrp > p.price else ""
        save = (f'<br><span class="gcc-save">Save {ui.rs(p.mrp - p.price)}</span>'
                if p.mrp and p.mrp > p.price else "")
        st.markdown(f'<span class="gcc-price">{ui.rs(p.price)}</span>{mrp}{save or "<br>&nbsp;"}',
                    unsafe_allow_html=True)

        limit = int(min(p.max_qty or 50, p.stock or 0))
        if limit <= 0:
            st.markdown('<span class="gcc-oos">Out of stock</span>', unsafe_allow_html=True)
        else:
            c1, c2 = st.columns([1, 1], vertical_alignment="bottom")
            c1.number_input("Qty", min_value=1, max_value=limit, value=1, step=1,
                            key=f"{prefix}_q_{sku}", label_visibility="collapsed")
            c2.button("Add", key=f"{prefix}_add_{sku}", type="primary", width="stretch",
                      on_click=_add, args=(sku, f"{prefix}_q_{sku}",
                                           {"name": p["name"], "max_qty": p.max_qty, "stock": p.stock}))
        if in_cart:
            st.caption(f"✅ {in_cart} in basket")
        with st.popover("Details", width="stretch"):
            st.markdown(f"**{p['name']}**  \n{p.brand} · {p.unit}")
            if p.description:
                st.write(p.description)
            st.caption(f"Category: {p.category}" + (f" · Barcode: {p.barcode}" if p.barcode else ""))
            st.caption(f"Max {p.max_qty} per order · {int(p.stock)} in stock")


def grid(df, prefix: str, cols: int = 4) -> None:
    rows = [df.iloc[i:i + cols] for i in range(0, len(df), cols)]
    for chunk in rows:
        columns = st.columns(cols, gap="medium")
        for col, (_, p) in zip(columns, chunk.iterrows()):
            with col:
                product_card(p, prefix)


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

no_filters = (st.session_state["cat"] == "All" and not st.session_state["deals_only"]
              and not st.session_state["search"].strip())

# ---------------------------------------------------------------- deals
deals = products[products.is_deal & (products.stock > 0)].head(4)
if no_filters and not deals.empty:
    layout.section_title("Weekly Markaz savings", "Featured wholesale deals in G-10", anchor="deals")
    grid(deals, "deal")
    st.html('<div style="height:24px"></div>')

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
layout.scroll_if_requested("catalog")

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
    grid(df.head(shown), "cat")
    if len(df) > shown:
        if st.button(f"Show more ({len(df) - shown} left)", width="stretch"):
            st.session_state["show_n"] = shown + page_size
            st.rerun()
