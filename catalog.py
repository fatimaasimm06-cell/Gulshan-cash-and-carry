"""Product cards and product grid, shared by the Groceries and Wholesale pages."""
import streamlit as st

import ui


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
            with st.container(key=f"pcrow_{prefix}_{sku}", horizontal=True, vertical_alignment="bottom",
                              gap="small"):
                st.number_input("Qty", min_value=1, max_value=limit, value=1, step=1,
                                key=f"{prefix}_q_{sku}", label_visibility="collapsed", width=110)
                st.button("Add", key=f"{prefix}_add_{sku}", type="primary", width="stretch",
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
    """Product cards: 4 per row on a computer, 2 per row on a phone (see layout.py CSS)."""
    with st.container(key=f"gcc-grid-{prefix}"):
        rows = [df.iloc[i:i + cols] for i in range(0, len(df), cols)]
        for chunk in rows:
            columns = st.columns(cols, gap="medium")
            for col, (_, p) in zip(columns, chunk.iterrows()):
                with col:
                    product_card(p, prefix)
