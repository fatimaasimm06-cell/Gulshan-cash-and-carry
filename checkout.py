import streamlit as st

from core import db, ui

version = ui.live_catalog()
s = ui.cfg()
products = db.load_products(version)
sectors = db.load_sectors(version)
sector = None

ui.header("Basket & checkout", "Cash on delivery · we confirm by phone before dispatch")

# ---------------------------------------------------------------- confirmation after placing
last = st.session_state.get("last_order")
if last and not ui.cart():
    st.success(f"Order **{last['order_id']}** placed! Total {ui.rs(last['total'])}, paid in cash on delivery.")
    st.markdown("**Last step:** send the order to the store on WhatsApp so they can start packing right away.")
    st.link_button("📲 Send order on WhatsApp", ui.wa_link(s["store_whatsapp"], ui.order_message(last)),
                   type="primary", width="stretch")
    with st.container(border=True):
        st.markdown(f"**{last['customer_name']}** · {last['phone']}  \n{last['address']}, {last['sector_name']}  \n"
                    f"Slot: {last['slot']}")
        for it in last["items"]:
            st.markdown(f"- {it['name']} × {it['qty']} — {ui.rs(it['line_total'])}")
        st.markdown(f"Delivery: {'Free' if last['delivery_fee'] == 0 else ui.rs(last['delivery_fee'])}  \n"
                    f"**Total: {ui.rs(last['total'])}**")
    st.caption(f"Save your order ID **{last['order_id']}** to track it on the Track order page.")
    c1, c2 = st.columns(2)
    c1.page_link("views/track.py", label="Track this order", icon="🚚")
    if c2.button("Start a new order", width="stretch"):
        st.session_state.pop("last_order", None)
        st.switch_page("views/shop.py")
    st.stop()

lines, subtotal, savings = ui.basket_lines(products)
if not lines:
    st.info("Your basket is empty.")
    st.page_link("views/shop.py", label="Browse groceries", icon="🛍️")
    st.stop()


def _set_qty(sku: str) -> None:
    q = int(st.session_state.get(f"bq_{sku}") or 0)
    if q <= 0:
        ui.cart().pop(sku, None)
    else:
        ui.cart()[sku] = q


def _remove(sku: str) -> None:
    ui.cart().pop(sku, None)


left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Your basket")
    for ln in lines:
        with st.container(border=True):
            a, b, c, d = st.columns([4, 2, 2, 1], vertical_alignment="center")
            a.markdown(f"**{ln['name']}**  \n<span class='gcc-unit'>{ln['unit']} · {ui.rs(ln['price'])} each</span>",
                       unsafe_allow_html=True)
            limit = max(1, min(ln["max_qty"], ln["stock"]))
            if ln["qty"] > limit:  # stock dropped since it was added
                ui.cart()[ln["sku"]] = limit
                ln["qty"] = limit
                st.warning(f"Only {limit} of {ln['name']} available — quantity adjusted.")
            b.number_input("Qty", min_value=0, max_value=limit, value=ln["qty"], step=1,
                           key=f"bq_{ln['sku']}", on_change=_set_qty, args=(ln["sku"],),
                           label_visibility="collapsed")
            c.markdown(f"**{ui.rs(ln['price'] * ln['qty'])}**")
            d.button("✕", key=f"rm_{ln['sku']}", on_click=_remove, args=(ln["sku"],), help="Remove")
    lines, subtotal, savings = ui.basket_lines(products)

with right:
    sector = ui.sector_picker(sectors, where=st)
    st.subheader("Summary")
    fee = ui.delivery_fee(subtotal, sector.fee if sector is not None else 0, s)
    free_over = float(s.get("free_delivery_threshold") or 0)
    min_order = float(s.get("min_order") or 0)
    with st.container(border=True):
        st.markdown(f"Subtotal: **{ui.rs(subtotal)}**")
        if savings:
            st.markdown(f"You save: **{ui.rs(savings)}** vs MRP")
        st.markdown(f"Delivery to {sector['name'] if sector is not None else '—'}: "
                    f"**{'Free' if fee == 0 else ui.rs(fee)}**")
        st.markdown(f"### Total: {ui.rs(subtotal + fee)}")
        if free_over and sector is not None and sector.fee and subtotal < free_over:
            st.progress(min(subtotal / free_over, 1.0),
                        text=f"Add {ui.rs(free_over - subtotal)} more for free delivery")
    below_min = subtotal < min_order
    if below_min:
        st.warning(f"Minimum order is {ui.rs(min_order)}. Add {ui.rs(min_order - subtotal)} more to check out.")

    st.subheader("Delivery details")
    slots = [x.strip() for x in s.get("delivery_slots", "").splitlines() if x.strip()] or ["Any time"]
    saved = st.session_state.get("customer", {})
    with st.form("checkout"):
        name = st.text_input("Full name", value=saved.get("name", ""))
        phone = st.text_input("Mobile / WhatsApp number", value=saved.get("phone", ""), placeholder="03XX-XXXXXXX")
        address = st.text_area("House / street / block", value=saved.get("address", ""),
                               placeholder="House 14-B, Street 32, G-10/2")
        slot = st.selectbox("Delivery slot", slots)
        notes = st.text_area("Notes for the store (optional)", placeholder="e.g. call on arrival, ring bell twice")
        st.caption("💵 Payment: cash on delivery")
        submitted = st.form_submit_button("Place order", type="primary", width="stretch", disabled=below_min)

    if submitted:
        clean = ui.clean_phone(phone)
        problems = []
        if not name.strip():
            problems.append("Please enter your name.")
        if not clean:
            problems.append("Enter a valid Pakistani mobile number, e.g. 0300-1234567.")
        if len(address.strip()) < 6:
            problems.append("Please enter your full address.")
        if sector is None:
            problems.append("Please choose your delivery area.")
        if problems:
            for p in problems:
                st.error(p)
        else:
            customer = {"name": name.strip(), "phone": clean, "address": address.strip()}
            st.session_state["customer"] = customer
            try:
                order = db.place_order(dict(ui.cart()), customer, st.session_state["sector_id"], slot, notes.strip())
            except db.OrderError as e:
                st.error(str(e))
            else:
                st.session_state["cart"] = {}
                st.session_state["last_order"] = order
                st.rerun()
