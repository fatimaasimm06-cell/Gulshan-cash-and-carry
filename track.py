import streamlit as st

import db
import layout
import ui

version = ui.version()
products = db.load_products(version)

layout.section_title("Live order status", "Track your order", "Enter the order ID from your confirmation and your phone number.")

last = st.session_state.get("last_order") or {}
with st.form("track"):
    c1, c2 = st.columns(2)
    oid = c1.text_input("Order ID", value=last.get("order_id", ""), placeholder="GCC-123456")
    phone = c2.text_input("Phone number", value=last.get("phone", ""), placeholder="03XX-XXXXXXX")
    go = st.form_submit_button("Track", type="primary")

if go:
    st.session_state["track_query"] = (oid.strip().upper(), ui.clean_phone(phone))

query = st.session_state.get("track_query")
STEPS = ["pending", "packing", "out_for_delivery", "delivered"]
ICONS = {"pending": "🧾", "packing": "📦", "out_for_delivery": "🛵", "delivered": "✅"}


def _reorder(order: dict) -> None:
    live = products.set_index("sku") if not products.empty else None
    added, skipped = 0, 0
    for it in order["items"]:
        if live is not None and it["sku"] in live.index and live.loc[it["sku"]].stock > 0:
            p = live.loc[it["sku"]]
            ui.cart()[it["sku"]] = int(min(it["qty"], p.max_qty, p.stock))
            added += 1
        else:
            skipped += 1
    st.session_state.pop("last_order", None)
    st.session_state["reorder_msg"] = (added, skipped)


@st.fragment(run_every=15)
def show_status(order_id: str, phone: str) -> None:
    order = db.get_order(order_id, phone)
    if not order:
        st.error("Order not found. Check the order ID and the phone number used at checkout.")
        return
    status = order["status"]
    st.markdown(f"### {order['order_id']} · {db.STATUS_LABEL[status]}")
    st.caption(f"Placed {order['created_at']:%d %b %Y, %I:%M %p} · updates automatically")
    if status == "cancelled":
        st.error("This order was cancelled. Please call the store if this is unexpected.")
    else:
        reached = STEPS.index(status)
        steps_row = st.container(key="track_steps", horizontal=True, horizontal_alignment="distribute")
        for i, step in enumerate(STEPS):
            done = i <= reached
            steps_row.markdown(f"{ICONS[step] if done else '⚪'}  \n**{db.STATUS_LABEL[step]}**" if done
                         else f"⚪  \n<span style='color:#999'>{db.STATUS_LABEL[step]}</span>",
                         unsafe_allow_html=True)
        st.progress((reached + 1) / len(STEPS))
    with st.container(border=True):
        st.markdown(f"Deliver to: {order['address']}, {order['sector_name']} · {order['slot']}")
        for it in order["items"]:
            st.markdown(f"- {it['name']} × {it['qty']} — {ui.rs(it['line_total'])}")
        if order.get("fee_pending"):
            st.markdown(f"Items: {ui.rs(order['subtotal'])}  \n"
                        "Delivery: **⏳ the store is adding the charge for your area**  \n"
                        "Your total will show here automatically.")
        else:
            st.markdown(f"Items: {ui.rs(order['subtotal'])}  \nDelivery: {ui.fee_text(order['delivery_fee'])}  \n"
                        f"**Total (cash on delivery): {ui.rs(order['total'])}**")
    if st.button("🔁 Order these items again"):
        _reorder(order)
        st.rerun(scope="app")


if query:
    if not query[1]:
        st.error("Enter the 11-digit phone number used at checkout, e.g. 0300-1234567.")
    else:
        show_status(*query)

msg = st.session_state.pop("reorder_msg", None)
if msg:
    added, skipped = msg
    st.success(f"Added {added} item(s) to your basket." + (f" {skipped} are no longer available." if skipped else ""))
    st.page_link("checkout.py", label="Go to basket & checkout", icon="🛒")
