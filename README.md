# 🛒 Gulshan Cash & Carry: Online Grocery Store

**Bachat Aur Quality Sath Sath**

The online ordering website for **Gulshan Cash & Carry, G-10 Markaz, Islamabad**. Customers browse groceries at wholesale prices, choose their sector, and order with **cash on delivery**. The store manages everything from a password-protected **Admin** page, and every change appears in the store within seconds.

Built with [Streamlit](https://streamlit.io) (Python) and hosted free on **Streamlit Community Cloud**, with a free **Supabase** database.

---

## ✨ Features

### For customers
- **Shop:** browse the full catalog with pictures, prices, MRP and savings.
- **Search:** in English or Urdu, or by brand or barcode (e.g. *atta*, *چاول*, *Dalda*).
- **Filters:** browse by category, show **Deals only**, and sort by price or biggest savings.
- **Delivery area:** choose an Islamabad sector to see the delivery fee and time.
- **Basket:** change quantities, see the total, and a progress bar shows how much more is needed for free delivery.
- **Checkout:** enter name, mobile number, address, delivery slot and notes, then pay **cash on delivery**.
- **WhatsApp:** after ordering, one tap sends the full itemised order to the store's WhatsApp.
- **Track order:** enter the order ID and phone number to see live status (Pending → Packing → Out for delivery → Delivered).
- **Re-order:** add a past order's items back to the basket in one tap.

### For the store admin
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
- ⚙️ **Settings:**
  - Store WhatsApp number, helpline, address and timings.
  - Free-delivery limit, minimum order and delivery slots.
  - Delivery areas and the fee for each.

### ⚡ Real-time updates
Every change the admin saves (price, stock, picture, new product or setting) shows up on every open customer page **within about 5 seconds**, with no refresh needed. Stock goes down automatically when an order is placed, and goes back up if the order is cancelled.

---

## 📁 Files

All files sit together in one folder, with no sub-folders.

| File | What it is |
| --- | --- |
| `app.py` | Starts the website and sets up the menu |
| `shop.py` | The Shop page |
| `checkout.py` | The Basket & checkout page |
| `track.py` | The Track order page |
| `admin.py` | The Admin page |
| `db.py` | Saves and loads everything from the database |
| `ui.py` | Design, basket, pictures, WhatsApp messages, live updates |
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

### Step 3: Publish the website (Streamlit)

1. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, and click **Create app**.
2. Choose **Deploy a public app from GitHub** and fill in:
   - **Repository:** `your-name/gulshan-streamlit`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** choose a name, e.g. `gulshan-cash-carry`
3. Open **Advanced settings**, choose **Python 3.12**, and paste this into **Secrets** with your own values:

```toml
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "choose-a-long-password"
DATABASE_URL = "postgresql://postgres.xxxx:YourPassword123@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
```

4. Click **Deploy**. The first start takes 2–4 minutes. The website creates its database tables and loads sample products automatically.

Your site is now live at `https://your-app-name.streamlit.app` 🎉

### Step 4: Set up the store

Open the site, click **Admin** in the menu, and sign in.

1. In **⚙️ Settings**, set the real store WhatsApp number, helpline, delivery fees, free-delivery limit and minimum order.
2. Load your real price list:
   - Either go to **⬆️ Import / export**, download the template, fill it in Excel, and upload it.
   - Or scan products one by one in **🔎 Scan / add product**.
3. Delete or hide sample products you don't sell.

> ⚠️ The sample products, prices, delivery fees and WhatsApp number are **placeholders**. Change them before sharing the link with customers.

---

## 🧑‍💼 Admin guide

### Signing in
Click **Admin** in the menu and enter the username and password from the Streamlit secrets. You stay signed in until you close or refresh the page. To change the password, edit `ADMIN_PASSWORD` in **Streamlit → your app → Settings → Secrets**.

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

Then start it:

```bash
streamlit run app.py
```

Without `DATABASE_URL`, it uses a local test database file (`data/gulshan.db`).

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
| "Admin login is not set up" | Add `ADMIN_USERNAME` and `ADMIN_PASSWORD` in Streamlit → Settings → Secrets, then reboot the app. |
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
