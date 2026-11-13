"""Store admin portal. Locked behind a username + password from Streamlit secrets."""
import hashlib
import hmac
import io
import time
from datetime import datetime

import pandas as pd
import streamlit as st

import db
import ui
from seed import CATEGORIES

SESSION_HOURS = 12
MAX_TRIES = 5
LOCK_SECONDS = 300


# ---------------------------------------------------------------- login

def _creds():
    return db._secret("ADMIN_USERNAME"), db._secret("ADMIN_PASSWORD_SHA256"), db._secret("ADMIN_PASSWORD")


def _check(user: str, pw: str) -> bool:
    exp_user, exp_hash, exp_pw = _creds()
    ok_user = hmac.compare_digest(user.strip().lower().encode(), str(exp_user).strip().lower().encode())
    if exp_hash:
        ok_pw = hmac.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), str(exp_hash).strip().lower())
    else:
        ok_pw = hmac.compare_digest(pw.encode(), str(exp_pw).encode())
    return ok_user and ok_pw


def login_gate() -> None:
    signed_at = st.session_state.get("admin_at")
    if signed_at and time.time() - signed_at < SESSION_HOURS * 3600:
        return
    st.session_state.pop("admin_at", None)

    ui.header("Store admin", "Sign in to manage orders, products and prices")
    exp_user, exp_hash, exp_pw = _creds()
    if not exp_user or not (exp_hash or exp_pw):
        st.error("Admin login is not set up. Add ADMIN_USERNAME and ADMIN_PASSWORD_SHA256 "
                 "(or ADMIN_PASSWORD) to the app's secrets — see README.")
        st.stop()

    locked_until = st.session_state.get("admin_locked_until", 0)
    if time.time() < locked_until:
        st.error(f"Too many wrong attempts. Try again in {int(locked_until - time.time())} seconds.")
        st.stop()

    with st.form("admin_login"):
        user = st.text_input("Username", autocomplete="username")
        pw = st.text_input("Password", type="password", autocomplete="current-password")
        ok = st.form_submit_button("Sign in", type="primary")
    if ok:
        if _check(user, pw):
            st.session_state["admin_at"] = time.time()
            st.session_state["admin_tries"] = 0
            st.rerun()
        else:
            time.sleep(1)  # slows down guessing
            tries = st.session_state.get("admin_tries", 0) + 1
            st.session_state["admin_tries"] = tries
            if tries >= MAX_TRIES:
                st.session_state["admin_locked_until"] = time.time() + LOCK_SECONDS
                st.session_state["admin_tries"] = 0
            st.error("Wrong username or password.")
    st.stop()


login_gate()

# ---------------------------------------------------------------- signed in
version = db.catalog_version()
s = db.get_settings(version)

with st.sidebar:
    st.success("Signed in as store admin")
    if st.button("Sign out", width="stretch"):
        st.session_state.pop("admin_at", None)
        st.rerun()
    store_url = db._secret("STORE_URL") or s.get("store_url", "")
    if store_url:
        st.link_button("🛍️ Open the store", store_url, width="stretch", type="primary")
    else:
        st.caption("Add the store's web address in ⚙️ Settings to get an “Open the store” button here.")
    if db.using_sqlite():
        st.warning("Using a local SQLite file. On Streamlit Cloud this is wiped on restart — "
                   "set DATABASE_URL to a Postgres database before going live.")

ui.header("Store admin", "Every save goes live in the store within a few seconds")
if store_url:
    st.link_button("🛍️ Open the customer store in a new tab", store_url)
t_orders, t_scan, t_all, t_import, t_settings = st.tabs(
    ["📦 Orders", "🔎 Scan / add product", "📋 All products", "⬆️ Import / export", "⚙️ Settings"])


# ================================================================ ORDERS
@st.fragment(run_every=15)
def orders_board() -> None:
    c1, c2, c3 = st.columns([2, 2, 1])
    status = c1.selectbox("Status", ["all"] + db.STATUSES, format_func=lambda x: "All" if x == "all"
                          else db.STATUS_LABEL[x], key="o_status")
    days = c2.selectbox("Period", [1, 7, 30, 90], index=1, format_func=lambda d: f"Last {d} day(s)", key="o_days")
    c3.caption(f"Auto-refresh 15 s  \n{datetime.now(db.PKT):%I:%M:%S %p}")

    df = db.list_orders(status, days)
    all_recent = db.list_orders("all", 1)
    # New-order alert
    newest = all_recent.created_at.max() if not all_recent.empty else None
    seen = st.session_state.get("o_seen")
    if newest is not None and seen is not None and newest > seen:
        st.toast("🔔 New order received!", icon="🛒")
    if newest is not None:
        st.session_state["o_seen"] = newest

    # Orders from areas not on the delivery list: the store must add the delivery charge
    need_fee = db.list_orders("all", 30)
    need_fee = need_fee[need_fee.fee_pending.fillna(False).astype(bool) & (need_fee.status != "cancelled")]
    seen_fee = st.session_state.get("o_seen_fee", set())
    for oid_ in set(need_fee.order_id) - seen_fee:
        if "o_seen_fee" in st.session_state:  # don't toast on first load
            st.toast(f"🔔 {oid_}: area not on the delivery list. Add the delivery charge.", icon="🚚")
    st.session_state["o_seen_fee"] = set(need_fee.order_id)
    if not need_fee.empty:
        st.error(f"🚚 **{len(need_fee)} order(s) need a delivery charge** (area not on your list): "
                 + ", ".join(f"{r.order_id} ({r.sector_name})" for r in need_fee.itertuples())
                 + ". Open the order below and add the charge. The customer's bill updates by itself.")

    live = all_recent[all_recent.status != "cancelled"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Orders (24 h)", len(live))
    m2.metric("Sales (24 h)", ui.rs(live.total.sum() if not live.empty else 0))
    m3.metric("Waiting (pending)", int((all_recent.status == "pending").sum()) if not all_recent.empty else 0)
    m4.metric("Need delivery charge", len(need_fee))

    if df.empty:
        st.info("No orders in this period.")
        return
    view = df[["order_id", "created_at", "customer_name", "phone", "sector_name", "total", "status"]].copy()
    view["status"] = view.status.map(db.STATUS_LABEL)
    pend = df.fee_pending.fillna(False).astype(bool)
    view.loc[pend, "status"] = "⚠️ Needs delivery charge · " + view.loc[pend, "status"]
    st.dataframe(view, hide_index=True, width="stretch", column_config={
        "order_id": "Order", "created_at": st.column_config.DatetimeColumn("Placed", format="DD MMM, hh:mm a"),
        "customer_name": "Customer", "phone": "Phone", "sector_name": "Area",
        "total": st.column_config.NumberColumn("Total (Rs)", format="%d"), "status": "Status"})

    labels = {r.order_id: f"{'⚠️ ' if r.fee_pending else ''}{r.order_id} · {r.customer_name} · {ui.rs(r.total)}"
                          f" · {db.STATUS_LABEL[r.status]}" for r in df.itertuples()}
    if "o_open" in st.session_state and st.session_state["o_open"] not in labels:
        del st.session_state["o_open"]
    oid = st.selectbox("Open order", list(labels), format_func=labels.get, key="o_open")
    order = db.get_order(oid)
    if not order:
        return
    with st.container(border=True):
        a, b = st.columns([3, 2])
        with a:
            st.markdown(f"**{order['customer_name']}** · {order['phone']}  \n"
                        f"{order['address']}, {order['sector_name']}  \nSlot: {order['slot']}")
            if order["notes"]:
                st.info(f"Notes: {order['notes']}")
            items = pd.DataFrame(order["items"])[["name", "unit", "qty", "unit_price", "line_total"]]
            st.dataframe(items, hide_index=True, width="stretch", column_config={
                "name": "Item", "unit": "Pack", "qty": "Qty",
                "unit_price": st.column_config.NumberColumn("Price", format="%d"),
                "line_total": st.column_config.NumberColumn("Line total", format="%d")})
            if order.get("fee_pending"):
                st.warning(f"**{order['sector_name']}** is not on your delivery list. Items {ui.rs(order['subtotal'])}"
                           " + delivery charge (not added yet).")
                with st.form(f"fee_{oid}"):
                    fee = st.number_input("Delivery charge for this order (Rs)", min_value=0, step=50, value=400)
                    save = st.checkbox(f"Also add “{order['sector_name']}” to the delivery list", value=True,
                                       help="Future customers from this area then see the charge automatically.")
                    c1, c2, c3 = st.columns(3)
                    zone = c1.text_input("Zone", value="Zone 3 (Outer)")
                    eta = c2.text_input("Delivery time", value="60–90 mins")
                    free_over = c3.number_input("Free delivery over (Rs, 0 = never)", min_value=0, step=500, value=0)
                    if st.form_submit_button("Add charge to the bill", type="primary"):
                        db.set_delivery_fee(oid, fee, {"zone": zone, "eta": eta, "free_over": free_over}
                                            if save else None)
                        st.toast(f"Added {ui.fee_text(fee)} delivery to {oid}. New total "
                                 f"{ui.rs(order['subtotal'] + fee)}.", icon="✅")
                        st.rerun()
            else:
                st.markdown(f"Delivery {ui.fee_text(order['delivery_fee'])} · **Total {ui.rs(order['total'])}** (cash)")
                with st.popover("Change delivery charge"):
                    fee = st.number_input("Delivery charge (Rs)", min_value=0, step=50,
                                          value=int(order["delivery_fee"] or 0), key=f"chg_{oid}")
                    if st.button("Update bill", key=f"chgb_{oid}", type="primary"):
                        db.set_delivery_fee(oid, fee)
                        st.rerun()
        with b:
            new_status = st.selectbox("Status", db.STATUSES, index=db.STATUSES.index(order["status"]),
                                      format_func=db.STATUS_LABEL.get, key=f"st_{oid}")
            if st.button("Update status", type="primary", width="stretch", key=f"upd_{oid}"):
                db.update_order_status(oid, new_status)
                st.toast(f"{oid} → {db.STATUS_LABEL[new_status]}")
                st.rerun(scope="fragment")
            total_txt = (f"items {ui.rs(order['total'])}, delivery charge to be added" if order.get("fee_pending")
                         else f"total {ui.rs(order['total'])} incl. delivery {ui.fee_text(order['delivery_fee'])}")
            msg = (f"Assalam o Alaikum {order['customer_name']}, your Gulshan Cash & Carry order "
                   f"{oid} ({total_txt}) is now: {db.STATUS_LABEL[new_status]}.")
            st.link_button("💬 WhatsApp customer", ui.wa_link(order["phone"], msg), width="stretch")
            st.link_button("📞 Call customer", f"tel:{order['phone']}", width="stretch")


with t_orders:
    orders_board()


# ================================================================ SCAN / ADD
def _on_scan() -> None:
    code = (st.session_state.get("scan_code") or "").strip()
    st.session_state["scan_code"] = ""  # ready for the next scan
    if not code:
        return
    found = db.find_by_barcode(code)
    if found:
        st.session_state["edit_sku"] = found["sku"]
        st.session_state["scan_msg"] = ("ok", f"Found “{found['name']}” — edit it below.")
    else:
        st.session_state["edit_sku"] = "__new__"
        st.session_state["new_barcode"] = code
        st.session_state["new_n"] = st.session_state.get("new_n", 0) + 1
        st.session_state["scan_msg"] = ("new", f"Barcode {code} is not in the catalog — add the new product below.")


def _start_new() -> None:
    st.session_state["edit_sku"] = "__new__"
    st.session_state["new_barcode"] = ""
    st.session_state["new_n"] = st.session_state.get("new_n", 0) + 1


def product_editor(p: dict | None) -> None:
    is_new = p is None
    if is_new:
        p = {"sku": "", "barcode": st.session_state.get("new_barcode", ""), "name": "", "urdu_name": "",
             "brand": "", "category": "", "unit": "", "description": "", "price": 0.0, "mrp": 0.0,
             "stock": 0, "is_deal": False, "max_qty": 50, "image_url": "", "image_data": None, "active": True}
        k = f"new{st.session_state.get('new_n', 0)}"
    else:
        stamp = p["updated_at"].timestamp() if p.get("updated_at") else 0
        k = f"{p['sku']}_{int(stamp)}"  # fresh widgets after every save

    st.markdown("#### " + ("➕ New product" if is_new else f"✏️ {p['name']}"))
    left, right = st.columns([3, 2], gap="large")
    with left:
        c1, c2 = st.columns(2)
        name = c1.text_input("Product name *", p["name"], key=f"name_{k}")
        urdu = c2.text_input("Urdu name", p["urdu_name"], key=f"urdu_{k}")
        c1, c2, c3 = st.columns(3)
        brand = c1.text_input("Brand", p["brand"], key=f"brand_{k}")
        cats = sorted(set(CATEGORIES) | set(db.load_products(version, True).category.dropna()) - {""})
        cat_opts = cats + ["➕ New category…"]
        cat_idx = cat_opts.index(p["category"]) if p["category"] in cat_opts else 0
        cat = c2.selectbox("Category", cat_opts, index=cat_idx, key=f"cat_{k}")
        if cat == "➕ New category…":
            cat = c2.text_input("New category name", key=f"newcat_{k}")
        unit = c3.text_input("Pack size / unit", p["unit"], placeholder="e.g. 5 kg bag", key=f"unit_{k}")
        desc = st.text_area("Description", p["description"], height=110, key=f"desc_{k}",
                            placeholder="What it is, size, best use — shown on the product's Details popup")
        c1, c2, c3, c4 = st.columns(4)
        price = c1.number_input("Price (Rs) *", min_value=0.0, value=float(p["price"]), step=5.0, key=f"price_{k}")
        mrp = c2.number_input("MRP (Rs)", min_value=0.0, value=float(p["mrp"] or 0), step=5.0, key=f"mrp_{k}",
                              help="Printed price. If higher than Price, the store shows the saving.")
        stock = c3.number_input("Stock", min_value=0, value=int(p["stock"]), step=1, key=f"stock_{k}")
        max_qty = c4.number_input("Max per order", min_value=1, value=int(p["max_qty"] or 50), step=1,
                                  key=f"max_{k}")
        c1, c2, c3 = st.columns([2, 1, 1])
        barcode = c1.text_input("Barcode", p["barcode"] or "", key=f"bc_{k}",
                                help="Click here and scan with the barcode reader, or type it.")
        is_deal = c2.checkbox("🔥 Deal", value=bool(p["is_deal"]), key=f"deal_{k}")
        active = c3.checkbox("Visible in store", value=bool(p["active"]), key=f"active_{k}")
        sku = st.text_input("SKU (internal code)", p["sku"], disabled=not is_new, key=f"sku_{k}",
                            help="Leave blank to generate one automatically.")
    with right:
        st.markdown("**Picture**")
        if p["image_data"] or p["image_url"]:
            ui.product_image(p)
        else:
            st.caption("No picture yet.")
        upload = st.file_uploader("Upload picture", type=["jpg", "jpeg", "png", "webp"], key=f"up_{k}")
        use_cam = st.toggle("📷 Take photo with camera", key=f"camtog_{k}")
        cam = st.camera_input("Photo", key=f"cam_{k}", label_visibility="collapsed") if use_cam else None
        image_url = st.text_input("…or image link (URL)", p["image_url"], key=f"url_{k}")
        remove_img = False
        if p["image_data"]:
            remove_img = st.checkbox("Remove uploaded picture", key=f"rmimg_{k}")

    b1, b2, _ = st.columns([1, 1, 2])
    if b1.button("💾 Save product", type="primary", width="stretch", key=f"save_{k}"):
        raw = (upload.getvalue() if upload else None) or (cam.getvalue() if cam else None)
        try:
            img = ui.process_image(raw) if raw else None
            saved_sku = db.save_product({
                "sku": sku if is_new else p["sku"], "barcode": barcode, "name": name, "urdu_name": urdu,
                "brand": brand, "category": cat, "unit": unit, "description": desc, "price": price,
                "mrp": mrp, "stock": stock, "is_deal": is_deal, "max_qty": max_qty,
                "image_url": image_url, "active": active,
            }, image_bytes=img, remove_image=remove_img)
        except ValueError as e:
            st.error(str(e))
        except Exception as e:  # unreadable image etc.
            st.error(f"Could not save: {e}")
        else:
            st.session_state["edit_sku"] = saved_sku
            st.session_state["scan_msg"] = ("ok", f"Saved “{name}”. It is live in the store.")
            st.rerun()
    if not is_new:
        with b2.popover("🗑️ Delete", width="stretch"):
            st.write(f"Delete **{p['name']}** permanently? Old orders keep their records.")
            if st.button("Yes, delete", type="primary", key=f"del_{k}"):
                db.delete_product(p["sku"])
                st.session_state.pop("edit_sku", None)
                st.session_state["scan_msg"] = ("ok", f"Deleted “{p['name']}”.")
                st.rerun()


with t_scan:
    st.text_input("Scan barcode", key="scan_code", on_change=_on_scan,
                  placeholder="Click here, then scan with the barcode reader (or type the code and press Enter)")
    # Put the cursor in the scan box so the scanner works straight away.
    st.html("""<script>
      setTimeout(() => {
        const box = document.querySelector('input[aria-label="Scan barcode"]');
        if (box) { box.focus(); }
      }, 300);
    </script>""", unsafe_allow_javascript=True)
    kind_msg = st.session_state.pop("scan_msg", None)
    if kind_msg:
        (st.success if kind_msg[0] == "ok" else st.info)(kind_msg[1])

    allp = db.load_products(version, include_inactive=True)
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    opts = [""] + allp.sku.tolist()
    names = dict(zip(allp.sku, allp["name"] + " · " + allp.unit + " · " + allp.sku))
    pick = c1.selectbox("…or pick a product to edit", opts, format_func=lambda x: names.get(x, "—"),
                        key="pick_sku")
    if pick and pick != st.session_state.get("_last_pick"):
        st.session_state["edit_sku"] = pick
    st.session_state["_last_pick"] = pick
    c2.button("➕ New product", on_click=_start_new, width="stretch")

    target = st.session_state.get("edit_sku")
    st.divider()
    if target == "__new__":
        product_editor(None)
    elif target:
        prod = db.get_product(target)
        if prod:
            product_editor(prod)
        else:
            st.session_state.pop("edit_sku", None)
    else:
        st.caption("Scan a barcode, pick a product, or click New product.")


# ================================================================ ALL PRODUCTS (quick edit)
with t_all:
    allp = db.load_products(version, include_inactive=True)
    q = st.text_input("Filter", placeholder="Name, brand, category or barcode", key="qe_filter")
    view = allp
    if q.strip():
        hay = (allp["name"] + " " + allp.brand + " " + allp.category + " " + allp.barcode).str.lower()
        view = allp[hay.str.contains(q.strip().lower(), regex=False)]
    cols = ["sku", "name", "unit", "category", "barcode", "price", "mrp", "stock", "max_qty", "is_deal", "active"]
    base = view[cols].assign(picture=view.image_data.notna() | (view.image_url != "")).reset_index(drop=True)
    st.caption(f"{len(base)} products · edit price, MRP, stock, limits, deal and visibility here, then Save. "
               "Use the Scan / add tab for names, descriptions, barcodes and pictures.")
    edited = st.data_editor(
        base, hide_index=True, width="stretch", key=f"qe_{version}",
        disabled=["sku", "name", "unit", "category", "barcode", "picture"],
        column_config={
            "sku": "SKU", "name": "Product", "unit": "Pack", "category": "Category", "barcode": "Barcode",
            "price": st.column_config.NumberColumn("Price (Rs)", min_value=0, step=5, format="%d"),
            "mrp": st.column_config.NumberColumn("MRP (Rs)", min_value=0, step=5, format="%d"),
            "stock": st.column_config.NumberColumn("Stock", min_value=0, step=1),
            "max_qty": st.column_config.NumberColumn("Max/order", min_value=1, step=1),
            "is_deal": "Deal", "active": "Visible", "picture": "Picture"})
    if st.button("💾 Save changes", type="primary"):
        diff_cols = ["price", "mrp", "stock", "max_qty", "is_deal", "active"]
        changed = []
        for (_, old), (_, new) in zip(base.iterrows(), edited.iterrows()):
            if any(old[c] != new[c] for c in diff_cols):
                row = {"sku": new.sku}
                for c in diff_cols:
                    row[c] = bool(new[c]) if c in ("is_deal", "active") else (
                        int(new[c]) if c in ("stock", "max_qty") else float(new[c]))
                changed.append(row)
        if any(r["price"] <= 0 for r in changed):
            st.error("Price must be more than 0.")
        elif changed:
            db.quick_update(changed)
            st.toast(f"Saved {len(changed)} product(s) — live in the store.", icon="✅")
            st.rerun()
        else:
            st.info("Nothing changed.")


# ================================================================ IMPORT / EXPORT
with t_import:
    st.markdown("**Update the catalog from an Excel or CSV price list.** Rows are matched by barcode, then SKU; "
                "new rows are added.")
    template = pd.DataFrame([{
        "sku": "ATTA-SR-10", "barcode": "8961234567890", "name": "Chakki Atta", "urdu_name": "چکی آٹا",
        "brand": "Sunridge", "category": "Atta & Flour", "unit": "10 kg bag",
        "description": "Stone-ground whole wheat flour", "price": 1450, "mrp": 1550, "stock": 120,
        "is_deal": "yes", "max_qty": 20, "image_url": "", "active": "yes"}], columns=db.IMPORT_COLUMNS)
    buf = io.BytesIO()
    template.to_excel(buf, index=False)
    st.download_button("⬇️ Download template (.xlsx)", buf.getvalue(), "gulshan_price_list_template.xlsx")

    up = st.file_uploader("Upload price list", type=["xlsx", "csv"], key="imp_file")
    if up:
        try:
            df = pd.read_csv(up, dtype={"barcode": str}) if up.name.lower().endswith(".csv") \
                else pd.read_excel(up, dtype={"barcode": str})
        except Exception as e:
            st.error(f"Could not read the file: {e}")
        else:
            st.dataframe(df.head(20), hide_index=True, width="stretch")
            st.caption(f"{len(df)} rows found (showing first 20).")
            mode = st.radio("Mode", ["merge", "replace"], horizontal=True, format_func={
                "merge": "Merge — update matching products, add new ones",
                "replace": "Replace — also hide products not in this file"}.get)
            if st.button("Import now", type="primary"):
                n, errors = db.bulk_import(df, mode)
                st.success(f"Imported {n} product(s). They are live in the store.")
                if errors:
                    st.warning(f"{len(errors)} row(s) skipped:")
                    st.code("\n".join(errors))

    st.divider()
    export = db.load_products(version, include_inactive=True)[db.IMPORT_COLUMNS]
    out = io.BytesIO()
    export.to_excel(out, index=False)
    st.download_button("⬇️ Export full catalog (.xlsx)", out.getvalue(),
                       f"gulshan_catalog_{datetime.now():%Y%m%d}.xlsx")
    orders_90 = db.list_orders("all", 90)
    st.download_button("⬇️ Export orders, last 90 days (.csv)", orders_90.to_csv(index=False).encode(),
                       f"gulshan_orders_{datetime.now():%Y%m%d}.csv")


# ================================================================ SETTINGS
with t_settings:
    with st.form("store_settings"):
        st.markdown("**Store details** (shown in the website's top bar, header, store cards and footer)")
        c1, c2 = st.columns(2)
        store_whatsapp = c1.text_input("Store WhatsApp number (orders go here)", s["store_whatsapp"],
                                       help="Format 923361142223 or 03361142223")
        store_helpline = c2.text_input("WhatsApp number as shown to customers", s["store_helpline"])
        store_landline = c1.text_input("Shop landline", s.get("store_landline", ""))
        store_email = c2.text_input("Email", s.get("store_email", ""))
        store_address = st.text_input("Address", s["store_address"])
        c1, c2 = st.columns(2)
        store_landmark = c1.text_input("Landmark", s.get("store_landmark", ""))
        store_timings = c2.text_input("Timings", s["store_timings"])
        store_url_in = st.text_input("Store website address (for the “Open the store” button)",
                                     s.get("store_url", ""), placeholder="https://….streamlit.app/")
        map_url = st.text_input("Google Maps link", s.get("map_url", ""),
                                help="Open your shop on Google Maps → Share → Copy link")
        c1, c2 = st.columns(2)
        local_eta = c1.text_input("Delivery time in G-10", s.get("local_eta", ""))
        other_eta = c2.text_input("Delivery time to other sectors", s.get("other_eta", ""))
        min_order = st.number_input("Minimum order (Rs)", min_value=0, value=int(float(s["min_order"] or 0)), step=100)
        slots = st.text_area("Delivery slots (one per line)", s["delivery_slots"], height=130)
        if st.form_submit_button("Save store settings", type="primary"):
            db.save_settings({"store_whatsapp": store_whatsapp.strip(), "store_helpline": store_helpline.strip(),
                              "store_landline": store_landline.strip(), "store_email": store_email.strip(),
                              "store_address": store_address.strip(), "store_landmark": store_landmark.strip(),
                              "store_timings": store_timings.strip(), "map_url": map_url.strip(),
                              "store_url": store_url_in.strip(),
                              "local_eta": local_eta.strip(), "other_eta": other_eta.strip(),
                              "min_order": min_order, "delivery_slots": slots})
            st.toast("Settings saved", icon="✅")
            st.rerun()

    st.markdown("**Delivery areas & fees** (shown in the store's Delivery rates table and used at checkout)")
    st.caption("Add a row for a new area, untick *Delivering* to hide one. Free delivery applies when the "
               "items total reaches the area's limit (0 = never free).")
    sec = db.load_sectors(version, active_only=False)[["id", "name", "zone", "fee", "eta", "free_over", "active"]]
    sec_edit = st.data_editor(sec, num_rows="dynamic", hide_index=True, width="stretch", key=f"sec_{version}",
                              column_config={
                                  "id": None,
                                  "name": st.column_config.TextColumn("Sector / area", required=True),
                                  "zone": "Zone",
                                  "fee": st.column_config.NumberColumn("Delivery fee (Rs)", min_value=0, step=50),
                                  "eta": "Delivery time",
                                  "free_over": st.column_config.NumberColumn("Free delivery over (Rs)", min_value=0,
                                                                             step=500),
                                  "active": "Delivering"})
    if st.button("Save delivery areas", type="primary"):
        db.save_sectors(sec_edit)
        st.toast("Delivery areas saved", icon="✅")
        st.rerun()
