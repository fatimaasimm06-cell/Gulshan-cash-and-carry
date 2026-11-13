import streamlit as st

import db
import layout
import ui

OTHER = "__other__"

version = ui.version()
s = ui.cfg()
products = db.load_products(version)
sectors = db.load_sectors(version)

layout.section_title("Cash on delivery · we confirm by phone before dispatch", "Basket & checkout")


# ---------------------------------------------------------------- confirmation after placing
def bill_lines(order: dict) -> str:
    if order.get("fee_pending"):
        return (f"Items: **{ui.rs(order['subtotal'])}**  \n"
                f"Delivery to {order['sector_name']}: **⏳ the store is adding the charge**  \n"
                f"Total: shown here as soon as the store adds the delivery charge")
    return (f"Items: {ui.rs(order['subtotal'])}  \nDelivery: {ui.fee_text(order['delivery_fee'])}  \n"
            f"### Total: {ui.rs(order['total'])}")


@st.fragment(run_every=10)
def live_bill(order_id: str, phone: str) -> None:
    """Re-reads the order so a delivery charge added by the store shows up without a refresh."""
    order = db.get_order(order_id, phone) or st.session_state["last_order"]
    was_pending = st.session_state["last_order"].get("fee_pending")
    if was_pending and not order.get("fee_pending"):
        st.toast(f"The store added the delivery charge: {ui.fee_text(order['delivery_fee'])}", icon="🚚")
    st.session_state["last_order"].update({k: order[k] for k in ("delivery_fee", "fee_pending", "total")})
    with st.container(border=True):
        st.markdown(f"**{order['customer_name']}** · {order['phone']}  \n{order['address']}, "
                    f"{order['sector_name']}  \nSlot: {order['slot']}")
        for it in order["items"]:
            st.markdown(f"- {it['name']} × {it['qty']} — {ui.rs(it['line_total'])}")
        st.markdown(bill_lines(order))


last = st.session_state.get("last_order")
if last and not ui.cart():
    if last.get("fee_pending"):
        st.success(f"Order **{last['order_id']}** placed! Your area isn't on our delivery list yet, so the store "
                   "will add the delivery charge to your bill. This page updates by itself.")
    else:
        st.success(f"Order **{last['order_id']}** placed! Total {ui.rs(last['total'])}, paid in cash on delivery.")
    st.markdown("**Last step:** send the order to the store on WhatsApp so they can start packing right away.")
    st.link_button("📲 Send order on WhatsApp", ui.wa_link(s["store_whatsapp"], ui.order_message(last)),
                   type="primary", width="stretch")
    live_bill(last["order_id"], last["phone"])
    st.caption(f"Save your order ID **{last['order_id']}** to track it on the Track order page.")
    c1, c2 = st.columns(2)
    c1.page_link("track.py", label="Track this order", icon="🚚")
    if c2.button("Start a new order", width="stretch"):
        st.session_state.pop("last_order", None)
        st.switch_page("shop.py")
    st.stop()

lines, subtotal, savings = ui.basket_lines(products)
if not lines:
    st.info("Your basket is empty.")
    st.page_link("shop.py", label="Browse groceries", icon="🛍️")
    st.stop()


def _set_qty(sku: str) -> None:
    q = int(st.session_state.get(f"bq_{sku}") or 0)
    if q <= 0:
        ui.cart().pop(sku, None)
    else:
        ui.cart()[sku] = q


def _remove(sku: str) -> None:
    ui.cart().pop(sku, None)


def _area_changed() -> None:
    choice = st.session_state.get("co_area")
    st.session_state["sector_id"] = None if choice in (None, OTHER) else choice


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
    # ------------------------------------------------ 1. delivery address
    st.subheader("1 · Delivery address")
    saved = st.session_state.get("customer", {})
    ids = sectors["id"].tolist()
    names = dict(zip(sectors["id"], sectors["name"]))
    names[OTHER] = "My area is not in this list"
    if "co_area" not in st.session_state:  # first visit: use the area picked in Delivery rates, if any
        pre = st.session_state.get("sector_id")
        st.session_state["co_area"] = pre if pre in ids else None
    if st.session_state["co_area"] not in ids + [OTHER, None]:  # area removed by the store meanwhile
        st.session_state["co_area"] = None
    area = st.selectbox("Sector / area", ids + [OTHER], format_func=names.get, key="co_area",
                        placeholder="Choose your sector or area", on_change=_area_changed)
    custom_area = ""
    if area == OTHER:
        custom_area = st.text_input("Your area / sector / society", key="co_custom_area",
                                    placeholder="e.g. Bahria Town Phase 7, DHA Phase 2, G-14/4")
        st.caption("We'll still deliver. The store checks the distance and adds the delivery charge to your "
                   "bill, and you'll see it on the confirmation and Track order pages.")
    address = st.text_area("House / street / block", value=saved.get("address", ""), key="co_address",
                           placeholder="House 14-B, Street 32")
    sector = sectors.set_index("id").loc[area] if area in ids else None
    address_ok = len(address.strip()) >= 6 and (sector is not None or len(custom_area.strip()) >= 2)

    # ------------------------------------------------ 2. bill
    st.subheader("2 · Your bill")
    min_order = float(s.get("min_order") or 0)
    with st.container(border=True):
        st.markdown(f"Items ({sum(l['qty'] for l in lines)}): **{ui.rs(subtotal)}**")
        if savings:
            st.markdown(f"You save: **{ui.rs(savings)}** vs MRP")
        if not address_ok:
            st.info("Enter your area and address above to see the delivery charge and your total bill.")
        elif sector is not None:
            fee = ui.delivery_fee(subtotal, sector)
            st.markdown(f"Delivery to {sector['name']} ({sector.zone}): **{ui.fee_text(fee)}**  \n"
                        f"<span class='gcc-unit'>Arrives in about {sector.eta}</span>", unsafe_allow_html=True)
            st.markdown(f"### Total: {ui.rs(subtotal + fee)}")
            free_over = float(sector.free_over or 0)
            if free_over and fee:
                st.progress(min(subtotal / free_over, 1.0),
                            text=f"Add {ui.rs(free_over - subtotal)} more for free delivery to this area")
        else:
            st.markdown(f"Delivery to {custom_area.strip()}: **added by the store**")
            st.markdown(f"### Total: {ui.rs(subtotal)} + delivery")
            st.caption("Your final total appears as soon as the store adds the delivery charge.")
    below_min = subtotal < min_order
    if below_min:
        st.warning(f"Minimum order is {ui.rs(min_order)}. Add {ui.rs(min_order - subtotal)} more to check out.")

    # ------------------------------------------------ 3. contact + place order
    st.subheader("3 · Your details")
    slots = [x.strip() for x in s.get("delivery_slots", "").splitlines() if x.strip()] or ["Any time"]
    name = st.text_input("Full name", value=saved.get("name", ""), key="co_name")
    phone = st.text_input("Mobile / WhatsApp number", value=saved.get("phone", ""), placeholder="03XX-XXXXXXX",
                          key="co_phone")
    slot = st.selectbox("Delivery slot", slots, key="co_slot")
    notes = st.text_area("Notes for the store (optional)", placeholder="e.g. call on arrival, ring bell twice",
                         key="co_notes")
    st.caption("💵 Payment: cash on delivery")
    submitted = st.button("Place order", type="primary", width="stretch", disabled=below_min or not address_ok,
                          key="co_place")

    if submitted:
        clean = ui.clean_phone(phone)
        problems = []
        if not name.strip():
            problems.append("Please enter your name.")
        if not clean:
            problems.append("Enter a valid Pakistani mobile number, e.g. 0300-1234567.")
        if problems:
            for p in problems:
                st.error(p)
        else:
            customer = {"name": name.strip(), "phone": clean, "address": address.strip()}
            st.session_state["customer"] = customer
            try:
                order = db.place_order(dict(ui.cart()), customer, area if sector is not None else None,
                                       slot, notes.strip(),
                                       custom_area=custom_area.strip() if sector is None else None)
            except db.OrderError as e:
                st.error(str(e))
            else:
                st.session_state["cart"] = {}
                st.session_state["last_order"] = order
                st.rerun()
