# 🛒 Gulshan Cash & Carry: Online Grocery Store

**Bachat Aur Quality Sath Sath**

The online ordering website for **Gulshan Cash & Carry, G-10 Markaz, Islamabad**. Customers browse groceries at wholesale prices, choose their sector, and order with **cash on delivery**. The store manages everything from a **separate, password-protected admin portal** with its own web address, which customers never see. Every admin change appears in the store within seconds.

Built with [Streamlit](https://streamlit.io) (Python) and hosted free on **Streamlit Community Cloud**, with a free **Supabase** database.

---

## ✨ Features

### For customers
- **Shop:** browse the full catalog with pictures, prices, MRP and savings.
- **Search:** in English or Urdu, or by brand or barcode (e.g. *atta*, *چاول*, *Dalda*).
- **Filters:** browse by category, show **Deals only**, and sort by price or biggest savings.
- **Delivery rates:** a sector-wise table (G-10 Local, Zone 1, Zone 2) with each area's fee, delivery time and free-delivery limit, plus a **Deliver here** button.
- **Basket:** change quantities, see the total, and a progress bar shows how much more is needed for free delivery.
- **Checkout:** the **total bill appears only after the customer picks their area and enters their address**. The delivery charge comes from the area, and is free once the basket reaches that area's limit. Then they add name, mobile number, slot and notes, and pay **cash on delivery**.
- **Area not on the list?** The customer can still order. The order is flagged for the store, the admin adds the delivery charge, and the customer's bill updates on its own.
- **WhatsApp:** after ordering, one tap sends the full itemised order to the store's WhatsApp.
- **Track order:** enter the order ID and phone number to see live status (Pending → Packing → Out for delivery → Delivered).
- **Re-order:** add a past order's items back to the basket in one tap.

### For the store admin
- 🚪 **Separate admin portal:** a second app at its own web address. The customer website has no Admin page or link, and typing `/admin` on the store only shows "page not found".
- 🔒 **Secure login:** username and password, with 5 wrong attempts locking the form for 5 minutes.
- 📦 **Orders board:**
  - New orders appear automatically, with a 🔔 alert.
  - Update an order's status, then WhatsApp or call the customer in one tap.
  - See the last 24 hours' orders and sales, and how many are waiting.
- 🔎 **Barcode scanning:** works with any USB or Bluetooth barcode reader. Scan a product to edit it, or scan a new barcode to add a new product.
- 🖼️ **Products:**
  - Add, edit or delete products.
  - Each product can have an English and Urdu name, brand, category, pack size, description, price, MRP, stock, a per-order limit and a "Deal" tag.
- 📷 **Pictures:** upload from the computer, take a photo with the camera, or paste an image link.
- 📋 **Quick edit:** change prices and stock for many products in one table.
- ⬆️ **Excel import and export:** update the whole price list from an Excel or CSV file, and download the catalog and orders.
- 🚚 **Delivery charges:**
  - Orders from areas that aren't on the list show a red alert, a 🔔 pop-up and a "Need delivery charge" count.
  - The admin types the charge and clicks **Add charge to the bill**. The customer's confirmation and Track order pages update within seconds.
  - One tick also saves that area, with its fee, to the delivery list for future customers.
  - The delivery charge on any order can be changed later.
- ⚙️ **Settings:**
  - Store WhatsApp number, helpline, address and timings.
  - Minimum order and delivery slots.
  - Delivery areas: sector, zone, fee, delivery time and free-delivery limit for each.

### ⚡ Real-time updates
Every change the admin saves (price, stock, picture, new product or setting) shows up on every open customer page **within about 5 seconds**, with no refresh needed. Stock goes down automatically when an order is placed, and goes back up if the order is cancelled.

---

## 📁 Files

All files sit together in one folder, with no sub-folders.

| File | What it is |
| --- | --- |
| `app.py` | Starts the **customer website** and its menu: Groceries, Wholesale Deals, Delivery Rates, Track Order, Store Info, Basket |
| `admin_app.py` | Starts the separate **admin portal** |
| `shop.py` | **Groceries** page: banner and the full catalog with search, categories and sorting |
| `wholesale.py` | **Wholesale Deals** page: this week's deals and the bulk/office order request |
| `rates.py` | **Delivery Rates** page: fee, time and free-delivery limit per area, with "Deliver here" |
| `track.py` | **Track Order** page |
| `store.py` | **Store Info** page: address, hours, contacts, map and how ordering works |
| `checkout.py` | **Basket** page: basket, delivery address, bill and order confirmation |
| `catalog.py` | Product cards and grid shared by Groceries and Wholesale Deals |
| `admin.py` | The admin portal's page (used only by `admin_app.py`) |
| `db.py` | Saves and loads everything from the database |
| `layout.py` | Website design for computers and phones: top bar, header, banner, delivery rates, store info, footer |
| `ui.py` | Basket, delivery charges, pictures, WhatsApp messages, live updates |
| `seed.py` | Sample products, delivery areas and settings, loaded on first start only |
| `logo.png` | Store logo |
| `requirements.txt` | List of Python packages Streamlit installs |
| `.gitignore` | Keeps private files off GitHub |

---

## 🚀 How to put the website online

You need three free accounts: **Supabase** (database), **GitHub** (stores the code) and **Streamlit** (runs the website).

### Step 1: Create the database (Supabase)

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and click **New project**.
2. Fill in the form:
   - **Name:** `gulshan-cash-carry`
   - **Database password:** letters and numbers only. Symbols like `@ # / :` break the connection link. **Write it down.**
   - **Region:** South Asia (Mumbai)
3. Click **Create new project** and wait 1–2 minutes.
4. Click **Connect** at the top and choose **URI** with **Session pooler**. Copy the link.
5. Replace `[YOUR-PASSWORD]` in the link with your password. Keep this link private.

```
postgresql://postgres.xxxx:YourPassword123@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
```

> ⚠️ Without a database, Streamlit stores data in a temporary file that is **deleted every time the app restarts**, so orders and products would be lost.

### Step 2: Upload the code (GitHub)

1. On [github.com](https://github.com), click **+ → New repository**, name it `gulshan-streamlit`, and click **Create repository**.
2. Click **uploading an existing file**, select **all the files** listed above, and click **Commit changes**.
3. Your repository's main page should show `app.py`, `shop.py`, `admin.py` and the other files directly. If they're inside another folder, see Troubleshooting.

### Step 3: Publish the customer website (Streamlit)

1. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, and click **Create app**.
2. Choose **Deploy a public app from GitHub** and fill in:
   - **Repository:** `your-name/gulshan-streamlit`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** the address customers will use, e.g. `gulshan-cash-carry`
3. Open **Advanced settings**, choose **Python 3.12**, and paste this into **Secrets**:

```toml
DATABASE_URL = "postgresql://postgres.xxxx:YourPassword123@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
```

4. Click **Deploy**. The first start takes 2–4 minutes. The website creates its database tables and loads sample products automatically.

The store is now live at `https://gulshan-cash-carry.streamlit.app` 🎉 This is the link you share with customers.

### Step 4: Publish the admin portal (a second Streamlit app)

1. On [share.streamlit.io](https://share.streamlit.io), click **Create app** again and choose the **same repository**.
2. Fill in:
   - **Branch:** `main`
   - **Main file path:** `admin_app.py`
   - **App URL:** something customers won't guess, e.g. `gcc-staff-g10-7341`. Don't use "gulshan-admin".
3. Open **Advanced settings**, choose **Python 3.12**, and paste into **Secrets**:

```toml
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "choose-a-long-password"
DATABASE_URL = "the SAME link as the customer app"
STORE_URL = "https://gulshan-cash-carry.streamlit.app"
```

4. Click **Deploy**. Bookmark this address and **share it only with staff**.

> ⚠️ Both apps **must use the same `DATABASE_URL`**. That shared database is how orders reach the admin portal and how product changes reach the store.
>
> The admin username and password live **only** in the admin app's secrets, so the customer app doesn't even know them.

### Step 5: Set up the store

Open the **admin portal** address and sign in.

1. In **⚙️ Settings**, check the store WhatsApp number, landline, address, timings and minimum order, and the **delivery areas** table (fee, zone, time and free-delivery limit per area).
2. Load your real price list:
   - Either go to **⬆️ Import / export**, download the template, fill it in Excel, and upload it.
   - Or scan products one by one in **🔎 Scan / add product**.
3. Delete or hide sample products you don't sell.

> ⚠️ The sample products, prices, delivery fees and WhatsApp number are **placeholders**. Change them before sharing the link with customers.

---

## 🧑‍💼 Admin guide

### Signing in
Open the admin portal's address (from Step 4) and enter the username and password from its Streamlit secrets. You stay signed in until you close or refresh the page. To change the password, edit `ADMIN_PASSWORD` in **Streamlit → the admin app → Settings → Secrets**.

> 🔐 **Extra security (optional):** instead of the plain password, store only a scrambled "hash" of it. Run this on any computer with Python, type your password, and copy the result:
> ```bash
> python -c "import hashlib,getpass;print(hashlib.sha256(getpass.getpass().encode()).hexdigest())"
> ```
> Then use `ADMIN_PASSWORD_SHA256 = "the-result"` in secrets instead of `ADMIN_PASSWORD`.

### Handling orders (📦 Orders tab)
1. New orders appear automatically, and the board refreshes every 15 seconds.
2. Open an order to see items, address and notes.
3. Change the status as you work: **Packing → Out for delivery → Delivered**.
4. Use **WhatsApp customer** or **Call customer** to confirm. Call first-time customers back before sending a rider.
5. **Cancelled** orders put their stock back automatically.

### Adding products with a barcode reader (🔎 Scan / add product tab)
1. Plug in the barcode reader. The cursor is already in the **Scan barcode** box.
2. Scan the product:
   - **Already in the catalog:** it opens so you can edit it.
   - **New barcode:** a new-product form opens with the barcode filled in.
3. Fill in the name, Urdu name, price, stock and description, and add a picture.
4. Click **💾 Save product**. It's live in the store within about 5 seconds.

No barcode reader? Type the number and press **Enter**. To add a product without a barcode, click **➕ New product**.

### Pictures
- **Upload picture:** JPG, PNG or WEBP from your computer or phone.
- **Take photo with camera:** turn on the switch and take the photo.
- **Image link:** paste a web address of a picture.

Uploaded pictures are automatically straightened, placed on a white square and made smaller, so they load fast.

### Delivery charges
- **Listed areas** are charged automatically from the **Delivery areas & fees** table in ⚙️ Settings. Each area has its own fee and its own free-delivery limit (e.g. G-10 Local: Rs 200, free over Rs 7,999; Zone 1: Rs 350; Zone 2: Rs 400; both free over Rs 10,000).
- **Unlisted areas:** when a customer chooses "My area is not in this list", the order arrives with **⚠️ Needs delivery charge**.
  1. Open the order on the 📦 Orders tab.
  2. Type the charge and click **Add charge to the bill**. The customer sees the new total within seconds.
  3. Leave "Also add … to the delivery list" ticked so the next customer from that area is charged automatically.
- To change the charge on any order, open it and use **Change delivery charge**.

### Changing many prices at once (📋 All products tab)
Edit price, MRP, stock, per-order limit, **Deal** and **Visible** directly in the table, then click **💾 Save changes**.

### Excel price list (⬆️ Import / export tab)
Download the template, fill it in, and upload it. These are the columns:

| Column | Required | Example |
| --- | --- | --- |
| `name` | ✅ | Chakki Atta |
| `price` | ✅ | 1450 |
| `sku` | | ATTA-SR-10 |
| `barcode` | | 8961234567890 |
| `urdu_name` | | چکی آٹا |
| `brand` | | Sunridge |
| `category` | | Atta & Flour |
| `unit` | | 10 kg bag |
| `description` | | Stone-ground whole wheat flour |
| `mrp` | | 1550 |
| `stock` | | 120 |
| `is_deal` | | yes / no |
| `max_qty` | | 20 |
| `image_url` | | https://… |
| `active` | | yes / no |

Rows are matched to existing products by **barcode**, then by **SKU**:
- **Merge** updates matching products and adds new ones.
- **Replace** does the same, and also hides products that aren't in the file.

Rows with mistakes are skipped and listed so you can fix them.

---

## 💻 Run it on your own computer (optional)

```bash
pip install -r requirements.txt
mkdir .streamlit
```

Create the file `.streamlit/secrets.toml` with at least:

```toml
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "test123"
```

Then start each app in its own terminal:

```bash
streamlit run app.py                       # customer website → http://localhost:8501
streamlit run admin_app.py --server.port 8502   # admin portal → http://localhost:8502
```

Without `DATABASE_URL`, both use the same local test database file (`data/gulshan.db`).

---

## 🎨 Store colours (optional)

The buttons already use the store's blue. To colour everything else too (category chips, switches):
1. On GitHub, click **Add file → Create new file**.
2. Type the name `.streamlit/config.toml`. The slash creates the folder automatically.
3. Paste the following and commit:

```toml
[theme]
primaryColor = "#001089"
backgroundColor = "#FAFAF9"
secondaryBackgroundColor = "#EEF0FB"
textColor = "#1C1917"
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError: No module named 'db'` | The files are inside a folder on GitHub. Set **Main file path** to `folder-name/app.py`, or re-upload the files to the top level. |
| "Admin login is not set up" | Add `ADMIN_USERNAME` and `ADMIN_PASSWORD` to the **admin app's** secrets (Streamlit → Settings → Secrets), then reboot it. |
| Orders don't show in the admin portal, or admin changes don't show in the store | The two apps use different databases. Copy the exact same `DATABASE_URL` into both apps' secrets. |
| Database connection error | Check `DATABASE_URL`: use the **Session pooler** link, replace `[YOUR-PASSWORD]`, and make sure the password has no symbols. |
| Orders or products disappeared | `DATABASE_URL` is missing, so the temporary file was wiped. Add the Supabase link to secrets. |
| "This app has gone to sleep" | Free Streamlit apps sleep after a period with no visitors. Click **Yes, get this app back up**; it takes about 30 seconds. |
| Supabase says the project is paused | Free projects pause after 7 days of very low use. Open Supabase and click **Resume project**. Your data is kept. |
| Changes on GitHub don't show | Streamlit redeploys automatically after each commit. Wait 1–2 minutes, or use **Reboot app** in the Streamlit menu. |

---

## 📞 Store contact

- **Address:** Shop #1-4, Ground Floor, Markaz G-10, Islamabad 44000
- **Helpline / WhatsApp:** 0300-8501234
- **Email:** gulshancashandcarryg10@gmail.com
- **Timings:** 8:00 AM – 12:00 Midnight, 7 days a week
