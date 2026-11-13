"""Shared look, basket helpers and the real-time catalog watcher."""
from __future__ import annotations

import io
import re
import urllib.parse

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

import db
from seed import CATEGORY_EMOJI

BRAND = "#001089"
LOGO = "logo.png"
POLL_SECONDS = 5

CSS = f"""
<style>
.block-container {{ padding-top: 1.2rem; max-width: 1200px; }}
.gcc-header {{ background:{BRAND}; color:#fff; border-radius:14px; padding:18px 22px; margin-bottom:14px; }}
.gcc-header h1 {{ color:#fff; font-size:1.55rem; margin:0; line-height:1.2; }}
.gcc-header p {{ color:#c9d1ff; margin:4px 0 0; font-size:.95rem; }}
.gcc-price {{ font-size:1.15rem; font-weight:700; color:{BRAND}; }}
.gcc-mrp {{ color:#8a8a8a; text-decoration:line-through; font-size:.85rem; margin-left:6px; }}
.gcc-save {{ display:inline-block; white-space:nowrap; background:#fff4d6; color:#7a4b00; border-radius:6px; padding:1px 7px; font-size:.75rem; font-weight:600; }}
.gcc-oos {{ background:#fde2e2; color:#9b1c1c; border-radius:6px; padding:1px 7px; font-size:.75rem; font-weight:600; }}
.gcc-name {{ font-weight:600; line-height:1.25; min-height:2.5em; }}
.gcc-urdu {{ color:#666; font-size:.9rem; direction:rtl; }}
.gcc-unit {{ color:#666; font-size:.8rem; }}
.gcc-ph {{ aspect-ratio:1/1; width:100%; display:flex; align-items:center; justify-content:center;
          font-size:3.2rem; background:#eef0fb; border-radius:10px; }}
.gcc-live {{ color:#1a7f37; font-size:.75rem; }}
/* brand blue even without .streamlit/config.toml */
[data-testid^="stBaseButton-primary"], [data-testid^="stBaseLinkButton-primary"] {{
  background:{BRAND} !important; border-color:{BRAND} !important; color:#fff !important; }}
[data-testid^="stBaseButton-primary"]:hover, [data-testid^="stBaseLinkButton-primary"]:hover {{
  background:#000c66 !important; border-color:#000c66 !important; }}
@media (max-width: 640px) {{
  .gcc-ph {{ max-height:150px; font-size:2.6rem; }}
  div[data-testid="stImage"] img {{ max-height:170px; }}
  .gcc-header h1 {{ font-size:1.25rem; }}
}}
div[data-testid="stImage"] img {{ border-radius:10px; aspect-ratio:1/1; object-fit:contain; background:#fff; }}
</style>
"""


def setup_page() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    try:
        st.logo(LOGO, size="large")
    except Exception:
        pass


def rs(v: float) -> str:
    return f"Rs {v:,.0f}"


def header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="gcc-header"><h1>{title}</h1>{f"<p>{subtitle}</p>" if subtitle else ""}</div>',
        unsafe_allow_html=True,
    )


def cfg() -> dict:
    return db.get_settings(db.catalog_version())


# ---------------------------------------------------------------- real-time sync

def live_catalog() -> int:
    """Return the current catalog version and keep this page in sync with admin edits.

    A tiny fragment re-runs every few seconds, checks the version number the admin
    bumps on each save, and reloads the page only when something changed.
    """
    v = db.catalog_version()
    st.session_state["_catalog_v"] = v
    _watch_catalog()
    return v


@st.fragment(run_every=POLL_SECONDS)
def _watch_catalog() -> None:
    if db.catalog_version() != st.session_state.get("_catalog_v"):
        st.rerun(scope="app")


# ---------------------------------------------------------------- images

def process_image(raw: bytes, size: int = 800) -> bytes:
    """Fix rotation, pad to a white square, shrink to max `size` px, save as JPEG."""
    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(bg, img).convert("RGB")
    side = max(img.size)
    square = Image.new("RGB", (side, side), (255, 255, 255))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    square.thumbnail((size, size))
    out = io.BytesIO()
    square.save(out, "JPEG", quality=82, optimize=True)
    return out.getvalue()


def product_image(p) -> None:
    data = p.get("image_data") if isinstance(p, dict) else p["image_data"]
    url = p.get("image_url") if isinstance(p, dict) else p["image_url"]
    if data:
        st.image(data, width="stretch")
    elif url:
        st.image(url, width="stretch")
    else:
        emoji = CATEGORY_EMOJI.get(p["category"], "🛒")
        st.markdown(f'<div class="gcc-ph">{emoji}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- basket

def cart() -> dict[str, int]:
    return st.session_state.setdefault("cart", {})


def add_to_cart(sku: str, qty: int, p) -> None:
    c = cart()
    limit = int(min(p["max_qty"] or 50, p["stock"] or 0))
    new = c.get(sku, 0) + qty
    if new > limit:
        new = limit
        st.toast(f"Limit reached: max {limit} of {p['name']}", icon="⚠️")
    else:
        st.toast(f"Added {p['name']}", icon="🛒")
    if new > 0:
        c[sku] = new


def basket_lines(products: pd.DataFrame) -> tuple[list[dict], float, float]:
    """Basket priced from the live catalog. Drops items that vanished."""
    c = cart()
    by_sku = products.set_index("sku") if not products.empty else None
    lines, subtotal, savings = [], 0.0, 0.0
    for sku in list(c):
        if by_sku is None or sku not in by_sku.index:
            c.pop(sku)
            continue
        p = by_sku.loc[sku]
        qty = c[sku]
        subtotal += p.price * qty
        savings += max((p.mrp or 0) - p.price, 0) * qty
        lines.append({"sku": sku, "name": p["name"], "unit": p.unit, "price": p.price,
                      "qty": qty, "stock": int(p.stock), "max_qty": int(p.max_qty),
                      "line_total": p.price * qty})
    return lines, subtotal, savings


def delivery_fee(subtotal: float, sector) -> float:
    """Delivery charge for a listed area: its fee, or free once the basket reaches its limit."""
    free_over = float(sector.free_over or 0)
    return 0.0 if db.free_delivery_applies(subtotal, free_over) else float(sector.fee or 0)


def fee_text(fee) -> str:
    return "Free" if fee == 0 else rs(fee)


def sector_picker(sectors: pd.DataFrame, where=st.sidebar, compact: bool = False) -> pd.Series | None:
    if sectors.empty:
        where.warning("No delivery areas set up yet.")
        return None
    ids = sectors["id"].tolist()
    current = st.session_state.get("sector_id")
    if st.session_state.get("sector_select") not in ids:  # area removed by admin, or first visit
        st.session_state["sector_select"] = current if current in ids else ids[0]
    if compact:
        labels = {r.id: f"📍 {r['name']} · {'Free' if r.fee == 0 else rs(r.fee)}" for _, r in sectors.iterrows()}
        choice = where.selectbox("Deliver to", ids, format_func=labels.get, key="sector_select",
                                 label_visibility="collapsed", width=215)
    else:
        labels = {r.id: f"{r['name']} — {'Free' if r.fee == 0 else rs(r.fee)} · {r.eta}" for _, r in sectors.iterrows()}
        choice = where.selectbox("📍 Deliver to", ids, format_func=labels.get, key="sector_select")
    st.session_state["sector_id"] = choice
    return sectors.set_index("id").loc[choice]


def current_sector(sectors: pd.DataFrame) -> pd.Series | None:
    """The area the customer picked (Delivery rates table or checkout), or None if not picked yet."""
    sid = st.session_state.get("sector_id")
    if sectors.empty or not sid:
        return None
    by_id = sectors.set_index("id")
    return by_id.loc[sid] if sid in by_id.index else None


def version() -> int:
    """Catalog version for this run (set by the entry point's live watcher)."""
    return st.session_state.get("_catalog_v") or db.catalog_version()


def sidebar_basket(products: pd.DataFrame) -> None:
    lines, subtotal, _ = basket_lines(products)
    count = sum(l["qty"] for l in lines)
    with st.sidebar:
        st.markdown(f"### 🛒 Basket · {count} item{'s' if count != 1 else ''}")
        st.markdown(f"**{rs(subtotal)}**")
        if count:
            st.page_link("checkout.py", label="Go to basket & checkout →", icon="✅")


# ---------------------------------------------------------------- phone & WhatsApp

PHONE_RE = re.compile(r"^03\d{9}$")


def clean_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("92") and len(digits) == 12:
        digits = "0" + digits[2:]
    return digits if PHONE_RE.match(digits) else None


def wa_number(local_or_intl: str) -> str:
    d = re.sub(r"\D", "", local_or_intl or "")
    if d.startswith("0"):
        d = "92" + d[1:]
    return d


def order_message(order: dict) -> str:
    lines = [
        f"🛒 *New order {order['order_id']}*",
        f"Name: {order['customer_name']}",
        f"Phone: {order['phone']}",
        f"Area: {order['sector_name']}",
        f"Address: {order['address']}",
        f"Slot: {order['slot']}",
        "",
        "*Items*",
    ]
    for it in order["items"]:
        lines.append(f"• {it['name']} ({it.get('unit') or ''}) × {it['qty']} = {rs(it['line_total'])}")
    lines += [
        "",
        f"Items: {rs(order['subtotal'])}",
    ]
    if order.get("fee_pending"):
        lines += [
            "Delivery: ⚠️ area not on the delivery list. Please add the delivery charge.",
            f"*Items total (cash on delivery): {rs(order['total'])} + delivery*",
        ]
    else:
        lines += [
            f"Delivery: {fee_text(order['delivery_fee'])}",
            f"*Total (cash on delivery): {rs(order['total'])}*",
    ]
    if order.get("notes"):
        lines += ["", f"Notes: {order['notes']}"]
    return "\n".join(lines)


def wa_link(number: str, text: str) -> str:
    return f"https://wa.me/{wa_number(number)}?text={urllib.parse.quote(text)}"
