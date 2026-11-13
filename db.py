"""Database layer: one place for every read and write.

Works with SQLite (local testing) and Postgres (production on Streamlit Cloud).
Set DATABASE_URL in Streamlit secrets to use Postgres; without it a local
SQLite file is used, which Streamlit Cloud WIPES on every restart.
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, LargeBinary, MetaData,
    String, Table, Text, create_engine, delete, func, insert, select, update,
)

import seed

PKT = timezone(timedelta(hours=5))  # Pakistan time for order timestamps
STATUSES = ["pending", "packing", "out_for_delivery", "delivered", "cancelled"]
STATUS_LABEL = {
    "pending": "Pending",
    "packing": "Packing",
    "out_for_delivery": "Out for delivery",
    "delivered": "Delivered",
    "cancelled": "Cancelled",
}

metadata = MetaData()

products = Table(
    "products", metadata,
    Column("sku", String(64), primary_key=True),
    Column("barcode", String(64), unique=True, nullable=True),
    Column("name", String(200), nullable=False),
    Column("urdu_name", String(200), default=""),
    Column("brand", String(100), default=""),
    Column("category", String(100), default=""),
    Column("unit", String(100), default=""),
    Column("description", Text, default=""),
    Column("price", Float, nullable=False, default=0),
    Column("mrp", Float, default=0),
    Column("stock", Integer, default=0),
    Column("is_deal", Boolean, default=False),
    Column("max_qty", Integer, default=50),
    Column("image_url", String(500), default=""),
    Column("image_data", LargeBinary, nullable=True),
    Column("active", Boolean, default=True),
    Column("updated_at", DateTime),
)

sectors = Table(
    "sectors", metadata,
    Column("id", String(64), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("zone", String(64), default=""),
    Column("fee", Float, default=0),
    Column("eta", String(64), default=""),
    Column("free_over", Float, default=0),  # 0 = never free
    Column("active", Boolean, default=True),
    Column("sort", Integer, default=0),
)

orders = Table(
    "orders", metadata,
    Column("order_id", String(20), primary_key=True),
    Column("customer_name", String(200), nullable=False),
    Column("phone", String(20), nullable=False, index=True),
    Column("sector_id", String(64)),
    Column("sector_name", String(200)),
    Column("address", Text),
    Column("slot", String(100)),
    Column("notes", Text, default=""),
    Column("subtotal", Float),
    Column("discount", Float),
    Column("delivery_fee", Float),          # NULL while the store is still pricing an unlisted area
    Column("fee_pending", Boolean, default=False),
    Column("total", Float),
    Column("payment_method", String(20), default="cod"),
    Column("status", String(20), default="pending", index=True),
    Column("created_at", DateTime, index=True),
    Column("updated_at", DateTime),
)

order_items = Table(
    "order_items", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", String(20), ForeignKey("orders.order_id"), index=True),
    Column("sku", String(64)),
    Column("name", String(200)),
    Column("unit", String(100)),
    Column("unit_price", Float),
    Column("mrp", Float),
    Column("qty", Integer),
    Column("line_total", Float),
)

settings = Table(
    "settings", metadata,
    Column("key", String(64), primary_key=True),
    Column("value", Text),
)


class OrderError(Exception):
    """Shown to the shopper when an order can't be placed."""


def now() -> datetime:
    return datetime.now(PKT).replace(tzinfo=None)


def _secret(name: str, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # no secrets file at all
        pass
    return os.environ.get(name, default)


@st.cache_resource(show_spinner=False)
def _describe_url(url: str) -> list[str]:
    """Plain-English checks on DATABASE_URL for the logs. Never prints the password itself."""
    from sqlalchemy.engine import make_url
    notes = []
    raw = url.strip()
    if raw != url:
        notes.append("DATABASE_URL has spaces or line breaks at the start or end.")
    try:
        u = make_url(raw)
    except Exception as e:  # unparseable link
        return notes + [f"DATABASE_URL is not a valid link ({type(e).__name__}). Copy it again from Supabase."]
    pw = u.password or ""
    notes.append(f"user = {u.username}  |  host = {u.host}  |  port = {u.port}  |  database = {u.database}")
    notes.append(f"password length = {len(pw)} characters")
    for bad in ("YOUR-PASSWORD", "NEW-PASSWORD", "PASSWORD-HERE", "PASTE-HERE"):
        if bad.lower() in pw.lower():
            notes.append(f"PROBLEM: the password still contains the placeholder text '{bad}'. Type your real password.")
            break
    if any(ch in pw for ch in "[]"):
        notes.append("PROBLEM: the password contains [ or ]. Remove the square brackets around it.")
    if any(ch.isspace() for ch in pw):
        notes.append("PROBLEM: the password contains a space.")
    if raw.count("@") > 1:
        notes.append("PROBLEM: the link has more than one '@'. Your password probably contains '@'; "
                     "reset it in Supabase to letters and numbers only.")
    if not pw:
        notes.append("PROBLEM: no password found between ':' and '@'.")
    if u.username and "." not in u.username and "pooler.supabase.com" in (u.host or ""):
        notes.append("PROBLEM: with the Session pooler the user must look like 'postgres.<project-code>'.")
    return notes


class DatabaseUnavailable(Exception):
    """Raised (with a plain-English hint) when DATABASE_URL is set but the database refuses us."""


def get_engine():
    url = _secret("DATABASE_URL")
    if url:
        url = url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        engine = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)
        try:
            with engine.connect():
                pass
        except Exception as e:
            reason = str(getattr(e, "orig", e)).strip().splitlines()[-1] if str(e).strip() else type(e).__name__
            lines = ["", "=" * 70, "DATABASE CONNECTION FAILED", f"Supabase says: {reason}"]
            lines += ["Checks on DATABASE_URL (password hidden):"] + [f"  - {n}" for n in _describe_url(url)]
            if "password authentication failed" in reason:
                lines.append("  -> The password in DATABASE_URL does not match the database password in "
                             "Supabase (Project Settings > Database). Compare the length above with yours.")
            lines.append("=" * 70)
            print("\n".join(lines), flush=True)
            engine.dispose()
            raise DatabaseUnavailable(reason) from None
    else:
        os.makedirs("data", exist_ok=True)
        engine = create_engine("sqlite:///data/gulshan.db", connect_args={"check_same_thread": False})
    metadata.create_all(engine)
    _migrate(engine)
    _seed_if_empty(engine)
    with engine.connect() as conn:
        n_all = conn.execute(select(func.count()).select_from(products)).scalar()
        n_live = conn.execute(select(func.count()).select_from(products).where(products.c.active.is_(True))).scalar()
        n_areas = conn.execute(select(func.count()).select_from(sectors)).scalar()
    print(f"DATABASE OK ({engine.dialect.name}): {n_all} products ({n_live} visible in the store), "
          f"{n_areas} delivery areas", flush=True)
    return engine


def _migrate(engine) -> None:
    """Add columns introduced after a database was first created (safe to run every start)."""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    want = {
        "sectors": {"zone": "VARCHAR(64) DEFAULT ''", "free_over": "FLOAT DEFAULT 0"},
        "orders": {"fee_pending": "BOOLEAN DEFAULT FALSE"},
    }
    reseed_sectors = False
    with engine.begin() as conn:
        for table, cols in want.items():
            have = {c["name"] for c in insp.get_columns(table)}
            for col, ddl in cols.items():
                if col not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
                    if table == "sectors":
                        reseed_sectors = True
        if reseed_sectors:  # old sample areas -> the store's real delivery zones
            conn.execute(delete(sectors))


def using_sqlite() -> bool:
    return get_engine().dialect.name == "sqlite"


def _seed_if_empty(engine) -> None:
    with engine.begin() as conn:
        if conn.execute(select(func.count()).select_from(settings)).scalar() == 0:
            conn.execute(insert(settings), [{"key": k, "value": v} for k, v in seed.SETTINGS.items()])
        if conn.execute(select(func.count()).select_from(sectors)).scalar() == 0:
            conn.execute(insert(sectors), [
                {"id": i, "name": n, "zone": z, "fee": f, "eta": e, "free_over": fo, "active": True, "sort": idx}
                for idx, (i, n, z, f, e, fo) in enumerate(seed.SECTORS)
            ])
        if conn.execute(select(func.count()).select_from(products)).scalar() == 0:
            ts = now()
            conn.execute(insert(products), [
                {"sku": p[0], "barcode": None, "name": p[1], "urdu_name": p[2], "brand": p[3],
                 "category": p[4], "unit": p[5], "price": p[6], "mrp": p[7], "stock": p[8],
                 "is_deal": p[9], "description": p[10], "max_qty": 50, "image_url": "",
                 "image_data": None, "active": True, "updated_at": ts}
                for p in seed.PRODUCTS
            ])


# ---------------------------------------------------------------- settings / version

def catalog_version() -> int:
    """Cheap query the store polls every few seconds to spot admin changes."""
    with get_engine().connect() as conn:
        v = conn.execute(select(settings.c.value).where(settings.c.key == "catalog_version")).scalar()
    return int(v or 1)


def _bump_version(conn) -> None:
    cur = conn.execute(select(settings.c.value).where(settings.c.key == "catalog_version")).scalar()
    new = str(int(cur or 1) + 1)
    if cur is None:
        conn.execute(insert(settings).values(key="catalog_version", value=new))
    else:
        conn.execute(update(settings).where(settings.c.key == "catalog_version").values(value=new))


@st.cache_data(show_spinner=False, ttl=3600)
def get_settings(version: int) -> dict:
    with get_engine().connect() as conn:
        rows = conn.execute(select(settings)).all()
    out = dict(seed.SETTINGS)
    out.update({r.key: r.value for r in rows})
    return out


def save_settings(values: dict) -> None:
    with get_engine().begin() as conn:
        for k, v in values.items():
            exists = conn.execute(select(settings.c.key).where(settings.c.key == k)).first()
            if exists:
                conn.execute(update(settings).where(settings.c.key == k).values(value=str(v)))
            else:
                conn.execute(insert(settings).values(key=k, value=str(v)))
        _bump_version(conn)


# ---------------------------------------------------------------- products

def _to_bytes(v):
    if v is None:
        return None
    if isinstance(v, memoryview):
        return v.tobytes()
    return bytes(v)


@st.cache_data(show_spinner=False, ttl=3600)
def load_products(version: int, include_inactive: bool = False) -> pd.DataFrame:
    q = select(products).order_by(products.c.category, products.c.name)
    if not include_inactive:
        q = q.where(products.c.active.is_(True))
    with get_engine().connect() as conn:
        df = pd.read_sql(q, conn)
    if not df.empty:
        df["image_data"] = df["image_data"].map(_to_bytes)
        df["barcode"] = df["barcode"].fillna("")
        for col in ("urdu_name", "brand", "category", "unit", "description", "image_url"):
            df[col] = df[col].fillna("")
        df["mrp"] = df["mrp"].fillna(0)
        df["stock"] = df["stock"].fillna(0).astype(int)
        df["max_qty"] = df["max_qty"].fillna(50).astype(int)
        df["is_deal"] = df["is_deal"].fillna(False).astype(bool)
        df["active"] = df["active"].fillna(True).astype(bool)
    return df


def get_product(sku: str) -> dict | None:
    with get_engine().connect() as conn:
        row = conn.execute(select(products).where(products.c.sku == sku)).mappings().first()
    if not row:
        return None
    d = dict(row)
    d["image_data"] = _to_bytes(d["image_data"])
    return d


def find_by_barcode(code: str) -> dict | None:
    code = (code or "").strip()
    if not code:
        return None
    with get_engine().connect() as conn:
        row = conn.execute(select(products.c.sku).where(products.c.barcode == code)).first()
    return get_product(row.sku) if row else None


def new_sku() -> str:
    with get_engine().connect() as conn:
        while True:
            sku = f"SKU-{random.randint(100000, 999999)}"
            if not conn.execute(select(products.c.sku).where(products.c.sku == sku)).first():
                return sku


def save_product(data: dict, image_bytes: bytes | None = None, remove_image: bool = False) -> str:
    """Insert or update one product. Returns its SKU. Raises ValueError on bad input."""
    sku = (data.get("sku") or "").strip() or new_sku()
    barcode = (data.get("barcode") or "").strip() or None
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("Product name is required.")
    if float(data.get("price") or 0) <= 0:
        raise ValueError("Price must be more than 0.")

    values = {
        "barcode": barcode,
        "name": name,
        "urdu_name": (data.get("urdu_name") or "").strip(),
        "brand": (data.get("brand") or "").strip(),
        "category": (data.get("category") or "").strip(),
        "unit": (data.get("unit") or "").strip(),
        "description": (data.get("description") or "").strip(),
        "price": float(data.get("price") or 0),
        "mrp": float(data.get("mrp") or 0),
        "stock": int(data.get("stock") or 0),
        "is_deal": bool(data.get("is_deal")),
        "max_qty": int(data.get("max_qty") or 50),
        "image_url": (data.get("image_url") or "").strip(),
        "active": bool(data.get("active", True)),
        "updated_at": now(),
    }
    if image_bytes is not None:
        values["image_data"] = image_bytes
    elif remove_image:
        values["image_data"] = None

    with get_engine().begin() as conn:
        if barcode:
            clash = conn.execute(
                select(products.c.sku, products.c.name)
                .where(products.c.barcode == barcode, products.c.sku != sku)
            ).first()
            if clash:
                raise ValueError(f"Barcode {barcode} already belongs to “{clash.name}” ({clash.sku}).")
        exists = conn.execute(select(products.c.sku).where(products.c.sku == sku)).first()
        if exists:
            conn.execute(update(products).where(products.c.sku == sku).values(**values))
        else:
            values.setdefault("image_data", None)
            conn.execute(insert(products).values(sku=sku, **values))
        _bump_version(conn)
    return sku


def quick_update(rows: list[dict]) -> int:
    """Save edits from the admin quick-edit table (price, mrp, stock, deal, active)."""
    allowed = {"price", "mrp", "stock", "is_deal", "active", "max_qty"}
    with get_engine().begin() as conn:
        for r in rows:
            vals = {k: v for k, v in r.items() if k in allowed}
            if not vals:
                continue
            vals["updated_at"] = now()
            conn.execute(update(products).where(products.c.sku == r["sku"]).values(**vals))
        if rows:
            _bump_version(conn)
    return len(rows)


def delete_product(sku: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(delete(products).where(products.c.sku == sku))
        _bump_version(conn)


IMPORT_COLUMNS = ["sku", "barcode", "name", "urdu_name", "brand", "category", "unit",
                  "description", "price", "mrp", "stock", "is_deal", "max_qty", "image_url", "active"]


def _truthy(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in {"1", "yes", "y", "true", "t"}
    try:
        return bool(v) and not pd.isna(v)
    except TypeError:
        return bool(v)


def bulk_import(df: pd.DataFrame, mode: str = "merge") -> tuple[int, list[str]]:
    """Import a price list. Rows match existing products by barcode, then SKU.

    mode="merge" updates/adds; mode="replace" also hides products not in the file.
    Returns (rows saved, list of error messages).
    """
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    errors: list[str] = []
    saved = 0
    seen: set[str] = set()
    ts = now()
    with get_engine().begin() as conn:
        for i, r in df.iterrows():
            line = i + 2  # header is row 1 in Excel
            name = str(r.get("name") or "").strip()
            if not name or name.lower() == "nan":
                errors.append(f"Row {line}: missing name — skipped.")
                continue
            try:
                price = float(r.get("price"))
                if price <= 0 or pd.isna(price):
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"Row {line} ({name}): price must be a number above 0 — skipped.")
                continue

            def s(col):
                v = r.get(col)
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return ""
                if isinstance(v, float) and v.is_integer():
                    v = int(v)  # barcodes read from Excel arrive as floats
                return str(v).strip()

            barcode = s("barcode") or None
            sku = s("sku")
            existing = None
            if barcode:
                existing = conn.execute(select(products.c.sku).where(products.c.barcode == barcode)).first()
            if not existing and sku:
                existing = conn.execute(select(products.c.sku).where(products.c.sku == sku)).first()
            if existing:
                sku = existing.sku
            elif not sku:
                sku = f"SKU-{random.randint(100000, 999999)}"

            def num(col, default):
                try:
                    v = float(r.get(col))
                    return default if pd.isna(v) else v
                except (TypeError, ValueError):
                    return default

            vals = {
                "barcode": barcode, "name": name, "urdu_name": s("urdu_name"), "brand": s("brand"),
                "category": s("category"), "unit": s("unit"), "description": s("description"),
                "price": price, "mrp": num("mrp", price), "stock": int(num("stock", 0)),
                "is_deal": _truthy(r.get("is_deal")) if "is_deal" in df.columns else False,
                "max_qty": int(num("max_qty", 50)), "image_url": s("image_url"),
                "active": _truthy(r.get("active")) if "active" in df.columns and s("active") else True,
                "updated_at": ts,
            }
            if barcode:
                clash = conn.execute(select(products.c.sku).where(
                    products.c.barcode == barcode, products.c.sku != sku)).first()
                if clash:
                    errors.append(f"Row {line} ({name}): barcode {barcode} already used by {clash.sku} — skipped.")
                    continue
            if existing:
                conn.execute(update(products).where(products.c.sku == sku).values(**vals))
            else:
                conn.execute(insert(products).values(sku=sku, image_data=None, **vals))
            seen.add(sku)
            saved += 1
        if mode == "replace" and seen:
            conn.execute(update(products).where(products.c.sku.not_in(seen)).values(active=False))
        if saved:
            _bump_version(conn)
    return saved, errors


# ---------------------------------------------------------------- sectors

@st.cache_data(show_spinner=False, ttl=3600)
def load_sectors(version: int, active_only: bool = True) -> pd.DataFrame:
    q = select(sectors).order_by(sectors.c.sort, sectors.c.name)
    if active_only:
        q = q.where(sectors.c.active.is_(True))
    with get_engine().connect() as conn:
        df = pd.read_sql(q, conn)
    df["zone"] = df["zone"].fillna("")
    df["free_over"] = df["free_over"].fillna(0).astype(float)
    df["fee"] = df["fee"].fillna(0).astype(float)
    return df


def free_delivery_applies(subtotal: float, free_over: float) -> bool:
    return bool(free_over) and subtotal >= free_over


def _area_id(name: str) -> str:
    slug = "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return (slug or "area")[:50] + f"-{random.randint(100, 999)}"


def save_sectors(df: pd.DataFrame) -> None:
    with get_engine().begin() as conn:
        conn.execute(delete(sectors))
        rows = []
        for idx, r in enumerate(df.to_dict("records")):
            name = str(r.get("name") or "").strip()
            if not name:
                continue
            sid = str(r.get("id") or "").strip()
            if not sid or sid.lower() == "nan" or sid in {x["id"] for x in rows}:
                sid = _area_id(name)

            def num(v):
                try:
                    v = float(v)
                    return 0.0 if pd.isna(v) else v
                except (TypeError, ValueError):
                    return 0.0
            rows.append({"id": sid, "name": name, "zone": str(r.get("zone") or "").replace("nan", ""),
                         "fee": num(r.get("fee")), "eta": str(r.get("eta") or "").replace("nan", ""),
                         "free_over": num(r.get("free_over")), "active": bool(r.get("active", True)), "sort": idx})
        if rows:
            conn.execute(insert(sectors), rows)
        _bump_version(conn)


# ---------------------------------------------------------------- orders

def _new_order_id(conn) -> str:
    while True:
        oid = f"GCC-{random.randint(100000, 999999)}"
        if not conn.execute(select(orders.c.order_id).where(orders.c.order_id == oid)).first():
            return oid


def place_order(cart: dict[str, int], customer: dict, sector_id: str | None, slot: str, notes: str,
                custom_area: str | None = None) -> dict:
    """Validate against live prices/stock, save the order, reduce stock. All or nothing.

    Give either a listed `sector_id`, or `custom_area` for an area not on the delivery list:
    then the order is saved without a delivery charge and flagged for the store to price.
    """
    if not cart:
        raise OrderError("Your basket is empty.")
    cfg = get_settings(catalog_version())
    with get_engine().begin() as conn:
        sector = None
        if custom_area:
            custom_area = custom_area.strip()
            if len(custom_area) < 2:
                raise OrderError("Please type the name of your area or sector.")
        else:
            sector = conn.execute(select(sectors).where(sectors.c.id == sector_id,
                                                        sectors.c.active.is_(True))).first()
            if not sector:
                raise OrderError("Please choose your delivery area.")
        rows = {r.sku: r for r in conn.execute(select(products).where(products.c.sku.in_(list(cart)))).all()}

        lines, subtotal, mrp_total = [], 0.0, 0.0
        for sku, qty in cart.items():
            p = rows.get(sku)
            if not p or not p.active:
                raise OrderError("An item in your basket is no longer available. Please review your basket.")
            if qty > (p.max_qty or 50):
                raise OrderError(f"{p.name}: maximum {p.max_qty} per order.")
            if qty > (p.stock or 0):
                raise OrderError(f"{p.name}: only {p.stock} left in stock.")
            line_total = p.price * qty
            subtotal += line_total
            mrp_total += max(p.mrp or 0, p.price) * qty
            lines.append({"sku": sku, "name": p.name, "unit": p.unit, "unit_price": p.price,
                          "mrp": p.mrp, "qty": qty, "line_total": line_total})

        min_order = float(cfg.get("min_order") or 0)
        if subtotal < min_order:
            raise OrderError(f"Minimum order is Rs {min_order:,.0f}. Add Rs {min_order - subtotal:,.0f} more.")
        if sector is not None:
            fee = 0.0 if free_delivery_applies(subtotal, float(sector.free_over or 0)) else float(sector.fee or 0)
            total, pending = subtotal + fee, False
        else:
            fee, total, pending = None, subtotal, True  # store adds the charge from the admin portal

        # Reduce stock atomically; fails if someone else bought the last units meanwhile.
        for ln in lines:
            res = conn.execute(
                update(products)
                .where(products.c.sku == ln["sku"], products.c.stock >= ln["qty"])
                .values(stock=products.c.stock - ln["qty"], updated_at=now())
            )
            if res.rowcount != 1:
                raise OrderError(f"{ln['name']} just went out of stock. Please review your basket.")

        oid = _new_order_id(conn)
        ts = now()
        order = {
            "order_id": oid, "customer_name": customer["name"], "phone": customer["phone"],
            "sector_id": sector.id if sector is not None else None,
            "sector_name": sector.name if sector is not None else custom_area,
            "address": customer["address"],
            "slot": slot, "notes": notes, "subtotal": subtotal, "discount": mrp_total - subtotal,
            "delivery_fee": fee, "fee_pending": pending, "total": total, "payment_method": "cod", "status": "pending",
            "created_at": ts, "updated_at": ts,
        }
        conn.execute(insert(orders).values(**order))
        conn.execute(insert(order_items), [{"order_id": oid, **ln} for ln in lines])
        _bump_version(conn)  # stock changed
    order["items"] = lines
    return order


def get_order(order_id: str, phone: str | None = None) -> dict | None:
    q = select(orders).where(func.upper(orders.c.order_id) == order_id.strip().upper())
    if phone is not None:
        q = q.where(orders.c.phone == phone)
    with get_engine().connect() as conn:
        row = conn.execute(q).mappings().first()
        if not row:
            return None
        items = conn.execute(select(order_items).where(order_items.c.order_id == row["order_id"])
                             .order_by(order_items.c.id)).mappings().all()
    d = dict(row)
    d["items"] = [dict(i) for i in items]
    return d


def list_orders(status: str | None = None, days: int = 7) -> pd.DataFrame:
    q = select(orders).where(orders.c.created_at >= now() - timedelta(days=days)) \
        .order_by(orders.c.created_at.desc())
    if status and status != "all":
        q = q.where(orders.c.status == status)
    with get_engine().connect() as conn:
        return pd.read_sql(q, conn)


def set_delivery_fee(order_id: str, fee: float, save_area: dict | None = None) -> None:
    """Admin adds the delivery charge to an order (e.g. one from an unlisted area).

    The customer's bill updates on their confirmation / Track order page automatically.
    `save_area` = {"zone", "eta", "free_over"} also adds the area to the delivery list.
    """
    fee = max(float(fee), 0.0)
    with get_engine().begin() as conn:
        row = conn.execute(select(orders).where(orders.c.order_id == order_id)).first()
        if not row:
            raise ValueError("Order not found.")
        conn.execute(update(orders).where(orders.c.order_id == order_id).values(
            delivery_fee=fee, total=float(row.subtotal or 0) + fee, fee_pending=False, updated_at=now()))
        if save_area:
            name = (row.sector_name or "").strip()
            exists = conn.execute(select(sectors.c.id).where(func.lower(sectors.c.name) == name.lower())).first()
            if name and not exists:
                last = conn.execute(select(func.max(sectors.c.sort))).scalar() or 0
                conn.execute(insert(sectors).values(
                    id=_area_id(name), name=name, zone=save_area.get("zone", ""), fee=fee,
                    eta=save_area.get("eta", ""), free_over=float(save_area.get("free_over") or 0),
                    active=True, sort=last + 1))
                sid = conn.execute(select(sectors.c.id).where(sectors.c.name == name)).scalar()
                conn.execute(update(orders).where(orders.c.order_id == order_id).values(sector_id=sid))
            _bump_version(conn)


def update_order_status(order_id: str, status: str) -> None:
    if status not in STATUSES:
        raise ValueError(status)
    with get_engine().begin() as conn:
        cur = conn.execute(select(orders.c.status).where(orders.c.order_id == order_id)).scalar()
        if cur is None or cur == status:
            return
        conn.execute(update(orders).where(orders.c.order_id == order_id).values(status=status, updated_at=now()))
        # Put stock back when an order is cancelled (and take it again if un-cancelled).
        if status == "cancelled" or cur == "cancelled":
            sign = 1 if status == "cancelled" else -1
            for it in conn.execute(select(order_items).where(order_items.c.order_id == order_id)).all():
                conn.execute(update(products).where(products.c.sku == it.sku)
                             .values(stock=products.c.stock + sign * it.qty))
            _bump_version(conn)
