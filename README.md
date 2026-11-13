# Gulshan Cash & Carry — Online Grocery (Streamlit)

Online ordering for Gulshan Cash & Carry, G-10 Markaz, Islamabad. *Bachat Aur Quality Sath Sath.*

Shoppers browse the catalog, pick their sector, and place cash-on-delivery orders that land on the
store's admin board and in the store's WhatsApp. The admin manages orders, products, pictures,
barcodes and prices; every admin save shows up in open store pages within about 5 seconds.

## What's inside

| Page | What it does |
| --- | --- |
| **Shop** | Catalog with search (English, Urdu, brand, barcode), category chips, deals filter, sorting, sector picker with delivery fee and ETA |
| **Basket & checkout** | Change quantities, free-delivery progress, minimum order check, delivery details, cash on delivery, "Send on WhatsApp" button with the full itemised order |
| **Track order** | Order ID + phone shows live status (auto-refresh), one-tap re-order |
| **Admin** (login required) | Orders board with new-order alerts and status updates · barcode scan to find or add a product · add/edit/delete products with picture upload or camera photo, Urdu name and description · quick-edit table for prices and stock · Excel/CSV import and export · store settings and delivery areas/fees |

```
gulshan-streamlit/
├── app.py                 # entry point + page navigation
├── views/                 # shop.py, checkout.py, track.py, admin.py
├── core/
│   ├── db.py              # all database reads/writes (SQLite or Postgres)
│   ├── ui.py              # styling, basket, images, WhatsApp, real-time watcher
│   └── seed.py            # sample products, sectors and settings (first run only)
├── assets/logo.png
├── .streamlit/config.toml # brand colours
├── .streamlit/secrets.toml.example
└── requirements.txt
```

## Run it on your computer

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit it
streamlit run app.py
```

Without `DATABASE_URL` the app makes `data/gulshan.db` (SQLite) and fills it with sample products.

## Admin login

The Admin page asks for a username **and** password. Both live only in Streamlit secrets, never in the code.

```toml
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_SHA256 = "…64-character hash…"
```

Make the hash (type your password when asked; it is not shown):

```bash
python -c "import hashlib,getpass;print(hashlib.sha256(getpass.getpass().encode()).hexdigest())"
```

Five wrong attempts lock the form for 5 minutes. A sign-in lasts 12 hours or until the browser tab is
closed/refreshed.

## Barcode reader

Any USB or Bluetooth barcode scanner works — they type the code like a keyboard and press Enter.

1. Admin → **Scan / add product** (the cursor is already in the scan box).
2. Scan. If the barcode exists, that product opens for editing. If not, a new-product form opens with
   the barcode filled in.
3. Fill in name, price, picture etc. and press **Save product**. It is live in the store within ~5 s.

Barcodes are unique: saving one that another product already uses is blocked and names that product.

## Pictures

Upload JPG/PNG/WEBP from the device, take a photo with the phone/laptop camera, or paste an image link.
Uploads are straightened, padded to a white square, shrunk to 800 px and stored **in the database**,
so they survive app restarts.

## How "real-time" works

Every admin save (product, price, stock, picture, settings, delivery areas, and each new order's stock
change) increases a `catalog_version` number. Each open store page checks that number every 5 seconds
and reloads its data only when it changed. The admin orders board refreshes every 15 seconds and pops a
🔔 alert when a new order arrives.

## Deploy on Streamlit Community Cloud

> **Use a hosted database.** Streamlit Cloud deletes local files whenever the app restarts or
> redeploys, so with SQLite you would lose orders and products. A free Postgres from
> [Supabase](https://supabase.com) or [Neon](https://neon.tech) fixes this.

1. Create a free Postgres database (Supabase: *Project → Connect → Session pooler* connection string;
   Neon: *Connection string*). It looks like `postgresql://user:password@host:5432/dbname`.
2. Push this folder to a GitHub repository. `.gitignore` already keeps `secrets.toml` and `data/` out.
   ```bash
   git init && git add . && git commit -m "Gulshan Cash & Carry Streamlit app"
   git branch -M main
   git remote add origin https://github.com/<you>/gulshan-streamlit.git
   git push -u origin main
   ```
3. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **Create app**,
   choose the repo, branch `main`, main file `app.py`.
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   ADMIN_USERNAME = "admin"
   ADMIN_PASSWORD_SHA256 = "…your hash…"
   DATABASE_URL = "postgresql://user:password@host:5432/dbname"
   ```
5. Click **Deploy**. The first start creates the tables and loads the sample catalog.
6. Sign in to **Admin → Settings**: set the real store WhatsApp number, helpline, delivery fees,
   free-delivery threshold and minimum order. Then load your real price list from **Import / export**.
7. Every `git push` to `main` redeploys automatically. Data stays in Postgres.

## Before going live — please confirm

- Store WhatsApp number (sample: `923008501234`).
- Delivery fee and ETA per sector, free-delivery threshold (sample Rs 5,000) and minimum order
  (sample Rs 1,000).
- Real prices and stock — the sample catalog prices are placeholders.

## Price list columns (Excel/CSV import)

`sku, barcode, name, urdu_name, brand, category, unit, description, price, mrp, stock, is_deal, max_qty, image_url, active`

Only `name` and `price` are required. Rows match existing products by barcode, then SKU. *Merge* updates
and adds; *Replace* also hides products missing from the file. Download a ready template from the Admin page.
