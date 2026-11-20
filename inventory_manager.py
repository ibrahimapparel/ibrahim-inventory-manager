"""
Ibrahim Apparel & Trading - Inventory Manager v3
Full Python practice project - with proper UI (Streamlit, no CLI)

HOW TO RUN - Streamlit Community Cloud (free, no install):
1. Push this file + requirements.txt to a public GitHub repo
2. Go to share.streamlit.io, sign in with GitHub, Create app
3. Pick the repo, branch main, main file inventory_manager.py, Deploy
4. Every push to GitHub auto-redeploys in 1-2 minutes

WHAT'S NEW IN v3 (all v2 features kept):
1. Barcode + Price Tag: CODE128 barcode per product, download a price-tag PNG
2. Product Photos: upload a photo in Add / Edit, shown in Product Detail
3. WhatsApp Order: link to wa.me/923275084710 with product details prefilled
4. Supplier + Purchase Orders: supplier per product, create POs, Mark Received
5. Monthly Sales Report + PDF: current month totals, best sellers, PDF download
6. Discount / Sale Price: sale_price (0 = no sale), effective price used everywhere

WHAT'S NEW IN v5:
- Proper icons: Streamlit Material Symbols (no emojis) on headings, buttons and section titles

WHAT'S NEW IN v4:
- Accounting format: money shows as e.g. Rs 8,999.00 / $32.14, negatives in parentheses, 2 decimals
- Multi-currency display: PKR (base, stored in PKR), USD, EUR, GBP, AED, SAR, INR
- Editable exchange rates in Currency Settings (approximate as of Nov 2026, not live rates)

WHAT YOU LEARN:
- lists & dictionaries, functions, file handling (CSV)
- if/else, loops, sorting, filtering, groupby with pandas
- Streamlit UI: forms, file_uploader, bar_chart, dataframe, download_button
- try/except for optional libraries, image handling with Pillow, PDF with fpdf2
"""

import csv
import io
import os
import urllib.parse
from datetime import datetime
import streamlit as st
import pandas as pd

CSV_FILE = "inventory.csv"
SALES_FILE = "sales.csv"
PO_FILE = "purchase_orders.csv"
PHOTOS_DIR = "photos"
WHATSAPP_NUMBER = "923275084710"

# ---------- Currency: base is PKR, all costs/prices stored in PKR ----------
# Symbol per currency. Multi-letter symbols (Rs, AED, SAR) get a space
# before the amount, single-character symbols ($, Euro, GBP, INR) do not.
CURRENCIES = {"PKR": "Rs", "USD": "$", "EUR": "\u20ac", "GBP": "\u00a3",
              "AED": "AED", "SAR": "SAR", "INR": "\u20b9"}
# PKR per 1 unit of the currency. Editable in Currency Settings.
DEFAULT_RATES = {"PKR": 1.0, "USD": 280.0, "EUR": 325.0, "GBP": 375.0,
                 "AED": 76.0, "SAR": 75.0, "INR": 3.15}

CATEGORIES = [
    "Jackets", "Hoodie", "Sweaters", "Sweat Shirts",
    "Shirts", "Pants", "Jeans", "Korean Trousers",
    "Ladies", "Shawls", "Co-ord Sets", "Kurtis", "Other"
]

# ---------- Demo data (8 products, prices unchanged from v2) ----------
DEMO_PRODUCTS = [
    {"sku": "IAT-00001", "name": "Midnight Puffer Jacket", "category": "Jackets", "size": "L", "cost": 5200.0, "price": 8999.0, "qty": 12, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
    {"sku": "IAT-00002", "name": "Olive Hoodie", "category": "Hoodie", "size": "M", "cost": 1800.0, "price": 2999.0, "qty": 20, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
    {"sku": "IAT-00003", "name": "Camel Wool Sweater", "category": "Sweaters", "size": "L", "cost": 2200.0, "price": 3999.0, "qty": 5, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
    {"sku": "IAT-00004", "name": "Navy Mock Neck Sweatshirt", "category": "Sweat Shirts", "size": "M", "cost": 1500.0, "price": 2699.0, "qty": 15, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
    {"sku": "IAT-00005", "name": "White Formal Shirt", "category": "Shirts", "size": "L", "cost": 1200.0, "price": 2199.0, "qty": 18, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
    {"sku": "IAT-00006", "name": "Black Straight Fit Jeans", "category": "Jeans", "size": "32", "cost": 2000.0, "price": 3499.0, "qty": 10, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
    {"sku": "IAT-00007", "name": "Maroon Shawl", "category": "Shawls", "size": "One Size", "cost": 1400.0, "price": 2499.0, "qty": 3, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
    {"sku": "IAT-00008", "name": "Grey Kurti", "category": "Kurtis", "size": "M", "cost": 1600.0, "price": 2799.0, "qty": 7, "low_stock": 5, "photo": "", "supplier": "", "sale_price": 0.0},
]
DEMO_SKUS = {p["sku"] for p in DEMO_PRODUCTS}


# ---------- Small helpers for safe number/text conversion ----------

def _to_float(value, default=0.0):
    try:
        if value is None or str(value).strip() == "" or str(value).lower() == "nan":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def _to_int(value, default=0):
    try:
        if value is None or str(value).strip() == "" or str(value).lower() == "nan":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def _to_text(value, default=""):
    if value is None or str(value).lower() == "nan":
        return default
    return str(value)


def _current_currency():
    """Display currency code from session state, PKR if not set yet."""
    try:
        return st.session_state.get("display_currency", "PKR")
    except Exception:
        return "PKR"


def _current_rates():
    """Exchange rates (PKR per 1 unit) from session state."""
    try:
        return st.session_state.get("currency_rates", dict(DEFAULT_RATES))
    except Exception:
        return dict(DEFAULT_RATES)


def convert_from_pkr(amount_pkr, currency_code=None):
    """Convert an amount stored in PKR to the display currency (numeric)."""
    code = currency_code or _current_currency()
    rate = _current_rates().get(code, 1.0) or 1.0
    return _to_float(amount_pkr) / rate


def format_money(amount_pkr, currency_code=None):
    """Accounting-style money text for an amount stored in PKR.

    Examples: 8999 PKR in PKR -> "Rs 8,999.00", in USD at 280 -> "$32.14",
    -1200 PKR in PKR -> "(Rs 1,200.00)", 0 -> "Rs 0.00" (symbol follows
    the selected currency). Display only - CSVs keep plain PKR numbers.
    """
    code = currency_code or _current_currency()
    symbol = CURRENCIES.get(code, "Rs")
    converted = convert_from_pkr(amount_pkr, code)
    if len(symbol) > 1:
        body = f"{symbol} {abs(converted):,.2f}"
    else:
        body = f"{symbol}{abs(converted):,.2f}"
    if converted < 0:
        return f"({body})"
    return body


# ---------- Data functions (pure Python - core logic) ----------

def load_products():
    """Load products from CSV. Backward compatible: old CSVs without
    photo / supplier / sale_price get defaults."""
    if not os.path.exists(CSV_FILE):
        return []
    products = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                "sku": _to_text(row.get("sku")),
                "name": _to_text(row.get("name")),
                "category": _to_text(row.get("category"), "Other"),
                "size": _to_text(row.get("size")),
                "cost": _to_float(row.get("cost")),
                "price": _to_float(row.get("price")),
                "qty": _to_int(row.get("qty")),
                "low_stock": _to_int(row.get("low_stock"), 5),
                "photo": _to_text(row.get("photo")),
                "supplier": _to_text(row.get("supplier")),
                "sale_price": _to_float(row.get("sale_price")),
            })
    return products


def save_products(products):
    fieldnames = ["sku", "name", "category", "size", "cost", "price",
                  "qty", "low_stock", "photo", "supplier", "sale_price"]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            writer.writerow({
                "sku": p.get("sku", ""), "name": p.get("name", ""),
                "category": p.get("category", "Other"),
                "size": p.get("size", ""), "cost": p.get("cost", 0),
                "price": p.get("price", 0), "qty": p.get("qty", 0),
                "low_stock": p.get("low_stock", 5),
                "photo": p.get("photo", ""),
                "supplier": p.get("supplier", ""),
                "sale_price": p.get("sale_price", 0),
            })


def load_sales():
    if not os.path.exists(SALES_FILE):
        return []
    sales = []
    with open(SALES_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sales.append({
                "date": _to_text(row.get("date")),
                "sku": _to_text(row.get("sku")),
                "name": _to_text(row.get("name")),
                "qty": _to_int(row.get("qty")),
                "amount": _to_float(row.get("amount")),
                "profit": _to_float(row.get("profit")),
            })
    return sales


def save_sale(sku, name, qty, amount, profit):
    exists = os.path.exists(SALES_FILE)
    with open(SALES_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "sku", "name", "qty", "amount", "profit"])
        if not exists:
            writer.writeheader()
        writer.writerow({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sku": sku, "name": name, "qty": qty,
            "amount": amount, "profit": profit,
        })


def load_purchase_orders():
    if not os.path.exists(PO_FILE):
        return []
    pos = []
    with open(PO_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pos.append({
                "po_id": _to_text(row.get("po_id")),
                "date": _to_text(row.get("date")),
                "supplier": _to_text(row.get("supplier")),
                "sku": _to_text(row.get("sku")),
                "name": _to_text(row.get("name")),
                "qty": _to_int(row.get("qty")),
                "cost_each": _to_float(row.get("cost_each")),
                "total_cost": _to_float(row.get("total_cost")),
                "status": _to_text(row.get("status"), "Ordered"),
            })
    return pos


def save_purchase_orders(pos):
    fieldnames = ["po_id", "date", "supplier", "sku", "name",
                  "qty", "cost_each", "total_cost", "status"]
    with open(PO_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for po in pos:
            writer.writerow(po)


def make_po_id(pos):
    nums = []
    for po in pos:
        try:
            nums.append(int(str(po["po_id"]).replace("PO-", "")))
        except ValueError:
            pass
    return f"PO-{max(nums, default=0) + 1:03d}"


def make_sku(products):
    # Next number after the highest existing IAT- number
    nums = [int(p["sku"].split("-")[1]) for p in products
            if p["sku"].startswith("IAT-") and len(p["sku"].split("-")) > 1
            and p["sku"].split("-")[1].isdigit()]
    return f"IAT-{max(nums, default=0) + 1:05d}"


def effective_price(product):
    """Sale price if one is set, otherwise the normal price."""
    sale = _to_float(product.get("sale_price"), 0)
    if sale > 0:
        return sale
    return _to_float(product.get("price"), 0)


def discount_percent(product):
    price = _to_float(product.get("price"), 0)
    sale = _to_float(product.get("sale_price"), 0)
    if sale > 0 and price > 0 and sale < price:
        return (price - sale) / price * 100
    return 0.0


def discount_label(product):
    pct = discount_percent(product)
    if pct > 0:
        return f"{pct:.0f}% OFF"
    return "-"


def profit_per_item(product):
    return effective_price(product) - _to_float(product.get("cost"), 0)


def margin_percent(product):
    cost = _to_float(product.get("cost"), 0)
    if cost == 0:
        return 0
    return profit_per_item(product) / cost * 100


def is_low_stock(product):
    return _to_int(product.get("qty"), 0) <= _to_int(product.get("low_stock"), 5)


def restock_suggestion(product, target=15):
    """How many to order to bring stock up to target (15)."""
    return max(0, target - _to_int(product.get("qty"), 0))


def save_uploaded_photo(uploaded_file, sku):
    """Save an uploaded photo to photos/<SKU>.<ext> and return the filename.
    Returns "" if no file was uploaded."""
    if uploaded_file is None:
        return ""
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    if ext == ".jpeg":
        ext = ".jpg"
    filename = f"{sku}{ext}"
    path = os.path.join(PHOTOS_DIR, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filename


# Official WhatsApp logo (Simple Icons path, viewBox 0 0 24 24).
# White glyph on the green #25D366 button - no emoji, no generic chat icon.
WHATSAPP_LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'width="20" height="20" style="vertical-align: middle; margin-right: 8px;" '
    'role="img" aria-label="WhatsApp"><path fill="#ffffff" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967'
    "-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463"
    "-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52"
    ".149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5"
    "-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 "
    "1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 "
    "1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347"
    "m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 "
    "0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 "
    "6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 "
    "11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 "
    '11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'
)


def whatsapp_order_link(product):
    """Build a wa.me link with product details prefilled."""
    message = (
        f"Hello Ibrahim Apparel & Trading, I want to order "
        f"{product.get('name', '')} (SKU {product.get('sku', '')}), "
        f"Size {product.get('size', '')}, "
        f"Price Rs {effective_price(product):,.0f}. "
        f"Please confirm availability."
    )
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={urllib.parse.quote(message)}"


def make_barcode_png(sku):
    """Return CODE128 barcode image bytes for a SKU.
    Raises ImportError if python-barcode / Pillow is missing."""
    from barcode import Code128
    from barcode.writer import ImageWriter
    buffer = io.BytesIO()
    Code128(sku, writer=ImageWriter()).write(
        buffer,
        options={"module_width": 0.35, "module_height": 15,
                 "font_size": 10, "text_distance": 5, "quiet_zone": 2},
    )
    return buffer.getvalue()


def make_price_tag_png(product):
    """Return a price-tag PNG (name, price, SKU, barcode) as bytes.
    Raises ImportError if python-barcode / Pillow is missing."""
    from PIL import Image, ImageDraw
    barcode_bytes = make_barcode_png(product.get("sku", ""))
    barcode_img = Image.open(io.BytesIO(barcode_bytes)).convert("RGB")
    tag = Image.new("RGB", (600, 460), "white")
    draw = ImageDraw.Draw(tag)
    draw.text((30, 20), "IBRAHIM APPAREL & TRADING", fill="black")
    draw.text((30, 60), str(product.get("name", "")), fill="black")
    draw.text((30, 100), f"Size: {product.get('size', '')}    SKU: {product.get('sku', '')}", fill="black")
    if discount_percent(product) > 0:
        draw.text((30, 135), f"Price: {format_money(effective_price(product), 'PKR')}  (was {format_money(_to_float(product.get('price'), 0), 'PKR')}, {discount_label(product)})", fill="black")
    else:
        draw.text((30, 135), f"Price: {format_money(effective_price(product), 'PKR')}", fill="black")
    barcode_img.thumbnail((540, 220))
    tag.paste(barcode_img, (30, 180))
    draw.text((30, 420), "Scan to order on WhatsApp: 0327-5084710", fill="black")
    out = io.BytesIO()
    tag.save(out, format="PNG")
    return out.getvalue()


def build_monthly_report_pdf(month_label, total_amount, total_profit,
                             sale_count, best_by_qty, best_by_profit):
    """Return a simple monthly report PDF as bytes.
    Raises ImportError if fpdf2 is not installed."""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Ibrahim Apparel & Trading", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Monthly Sales Report - {month_label}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Totals", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Number of sales: {sale_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total sales amount: {format_money(total_amount)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total profit: {format_money(total_profit)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Best Sellers by Quantity", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    if best_by_qty:
        for name, qty in best_by_qty:
            pdf.cell(0, 8, f"{name}: {qty} sold", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, "No sales this month.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Best Sellers by Profit", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    if best_by_profit:
        for name, profit in best_by_profit:
            pdf.cell(0, 8, f"{name}: {format_money(profit)} profit", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, "No sales this month.", new_x="LMARGIN", new_y="NEXT")
    output = pdf.output()
    return bytes(output) if isinstance(output, (bytearray, bytes)) else output.encode("latin-1")


# ---------- App state ----------

st.set_page_config(page_title="Ibrahim Inventory Manager", page_icon=None, layout="wide")

if "products" not in st.session_state:
    st.session_state.products = load_products()
if "sales" not in st.session_state:
    st.session_state.sales = load_sales()
if "purchase_orders" not in st.session_state:
    st.session_state.purchase_orders = load_purchase_orders()
if "display_currency" not in st.session_state:
    st.session_state.display_currency = "PKR"
if "currency_rates" not in st.session_state:
    st.session_state.currency_rates = dict(DEFAULT_RATES)

products = st.session_state.products
sales = st.session_state.sales
purchase_orders = st.session_state.purchase_orders

# ---------- Header ----------

st.title(":material/checkroom: Ibrahim Apparel & Trading")
st.subheader(":material/store: Inventory Manager — Full Python Project")
st.write("Add products, track stock, see profit. Data saves to inventory.csv.")

# ---------- Display currency selector + editable rates ----------
_cur_col1, _cur_col2 = st.columns([1, 2])
with _cur_col1:
    st.selectbox(
        "Display Currency",
        list(CURRENCIES.keys()),
        format_func=lambda code: f"{code} ({CURRENCIES[code]})",
        key="display_currency",
    )
with _cur_col2:
    st.write(
        "All prices are stored in PKR. Amounts below are shown in the "
        "selected currency. Quantities stay as whole numbers."
    )

with st.expander(":material/currency_exchange: Currency Settings"):
    st.write("Rates are approximate as of Nov 2026 and editable - not live rates.")
    st.write("Each rate is PKR per 1 unit of that currency. Change a rate and "
             "every amount in the app updates. Base currency is PKR (rate 1.0).")
    _rates = st.session_state.currency_rates
    _rate_cols = st.columns(3)
    for _i, _code in enumerate(["USD", "EUR", "GBP", "AED", "SAR", "INR"]):
        with _rate_cols[_i % 3]:
            _rates[_code] = st.number_input(
                f"PKR per 1 {_code}", min_value=0.01,
                value=float(_rates.get(_code, DEFAULT_RATES[_code])),
                step=1.0, key=f"rate_{_code}",
            )
    if st.button("Reset Rates to Defaults", icon=":material/restart_alt:"):
        st.session_state.currency_rates = dict(DEFAULT_RATES)
        st.rerun()

# ---------- Demo data buttons ----------

col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    if st.button("Load Demo Data (8 products)", icon=":material/download:"):
        existing_skus = {p["sku"] for p in products}
        added = 0
        for demo in DEMO_PRODUCTS:
            if demo["sku"] not in existing_skus:
                products.append(dict(demo))
                added += 1
        save_products(products)
        st.success(f"Demo data loaded — {added} new product(s) added.")
        st.rerun()
with col_d2:
    if st.button("Clear Demo Data", icon=":material/clear_all:"):
        products[:] = [p for p in products if p["sku"] not in DEMO_SKUS]
        save_products(products)
        st.success("Demo products removed. Your own products are kept.")
        st.rerun()
with col_d3:
    st.write("Demo = 8 products: Puffer Jacket, Hoodie, Sweater, Sweatshirt, Shirt, Jeans, Shawl, Kurti.")

# ---------- Dashboard (uses effective price everywhere) ----------

total_units = sum(_to_int(p.get("qty")) for p in products)
stock_cost_value = sum(_to_float(p.get("cost")) * _to_int(p.get("qty")) for p in products)
stock_price_value = sum(effective_price(p) * _to_int(p.get("qty")) for p in products)
total_profit = stock_price_value - stock_cost_value
low_items = [p for p in products if is_low_stock(p)]
sales_total = sum(s["amount"] for s in sales)
sales_profit = sum(s["profit"] for s in sales)

st.markdown("### :material/dashboard: Dashboard")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Products", len(products))
c2.metric("Units in Stock", total_units)
c3.metric("Stock Value", format_money(stock_price_value))
c4.metric("Potential Profit", format_money(total_profit))
c5.metric("Sales So Far", format_money(sales_total), f"Profit {format_money(sales_profit)}")

if low_items:
    st.warning(f"Low stock: {len(low_items)} item(s) — " +
               ", ".join(f"{p['name']} ({p['qty']} left)" for p in low_items))

st.divider()

# ---------- Charts: by category (effective price) ----------

st.header(":material/bar_chart: Insights — By Category")
if products:
    _code = _current_currency()
    df_all = pd.DataFrame([{
        "Category": p["category"],
        f"Stock Value ({_code})": convert_from_pkr(effective_price(p) * _to_int(p.get("qty"))),
        f"Profit ({_code})": convert_from_pkr(profit_per_item(p) * _to_int(p.get("qty"))),
        "Units": _to_int(p.get("qty")),
    } for p in products])
    grouped = df_all.groupby("Category").sum(numeric_only=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.write("Stock Value by Category")
        st.bar_chart(grouped[f"Stock Value ({_code})"])
    with cc2:
        st.write("Potential Profit by Category")
        st.bar_chart(grouped[f"Profit ({_code})"])
    st.dataframe(grouped, use_container_width=True)
else:
    st.info("Load demo data or add a product to see charts.")

st.divider()

# ---------- Low-stock dashboard ----------

st.header(":material/warning: Low Stock — What to Order")
if not low_items:
    st.success("All good — no low-stock items right now.")
else:
    rows = [{
        "SKU": p["sku"], "Name": p["name"], "Category": p["category"],
        "In Stock": p["qty"], "Alert At": p["low_stock"],
        "Order This Many (to reach 15)": restock_suggestion(p),
        "Cost to Restock": format_money(restock_suggestion(p) * _to_float(p.get("cost"))),
    } for p in low_items]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

# ---------- Add Product Form (now with photo, supplier, sale price) ----------

st.header(":material/add_circle: Add New Product")
with st.form("add_product"):
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Product Name *", placeholder="e.g. Midnight Puffer Jacket")
    category = c2.selectbox("Category", CATEGORIES)
    size = c3.text_input("Size", placeholder="M / L / XL")
    c4, c5, c6, c7 = st.columns(4)
    cost = c4.number_input("Cost Price (Rs)", min_value=0.0, step=100.0)
    price = c5.number_input("Selling Price (Rs)", min_value=0.0, step=100.0)
    qty = c6.number_input("Quantity", min_value=0, step=1)
    low_stock = c7.number_input("Low Stock Alert At", min_value=0, value=5, step=1)
    c8, c9 = st.columns(2)
    supplier = c8.text_input("Supplier", placeholder="e.g. Faisalabad Textiles")
    sale_price = c9.number_input("Sale Price (Rs, 0 = no sale)", min_value=0.0, step=100.0)
    sku_input = st.text_input("SKU (leave blank for auto)", placeholder="IAT-00001")
    photo_file = st.file_uploader("Product Photo (jpg/png)", type=["jpg", "jpeg", "png"])

    submitted = st.form_submit_button("Add Product", icon=":material/add_circle:")
    if submitted:
        if not name:
            st.error("Product name is required.")
        elif price < cost:
            st.error("Selling price should be more than cost, otherwise loss!")
        elif sale_price > 0 and sale_price < cost:
            st.error("Sale price should not be below cost.")
        elif sale_price > 0 and sale_price >= price:
            st.error("Sale price should be less than the normal price.")
        else:
            sku = sku_input.strip() or make_sku(products)
            photo_name = save_uploaded_photo(photo_file, sku) if photo_file else ""
            new_product = {
                "sku": sku, "name": name, "category": category,
                "size": size, "cost": cost, "price": price,
                "qty": int(qty), "low_stock": int(low_stock),
                "photo": photo_name, "supplier": supplier,
                "sale_price": float(sale_price),
            }
            products.append(new_product)
            save_products(products)
            st.success(f"Added {name} — Profit per item: {format_money(profit_per_item(new_product))} "
                       f"({margin_percent(new_product):.1f}% margin)")
            st.rerun()

st.divider()

# ---------- CSV Import (new fields supported) ----------

st.header(":material/upload_file: Import Products from CSV")
st.write("Upload a CSV with columns: sku,name,category,size,cost,price,qty,low_stock,photo,supplier,sale_price — blank SKU = auto. Only name, category, cost, price, qty are required.")
st.download_button("Download CSV Template", icon=":material/download:",
                   data="sku,name,category,size,cost,price,qty,low_stock,photo,supplier,sale_price\n,Test Jacket,Jackets,L,5000,8999,10,5,,Faisalabad Textiles,0\n",
                   file_name="inventory_template.csv", mime="text/csv")
uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
if uploaded is not None:
    try:
        df_up = pd.read_csv(uploaded)
        needed = {"name", "category", "cost", "price", "qty"}
        if not needed.issubset(set(df_up.columns)):
            st.error(f"CSV must have at least: {', '.join(sorted(needed))}")
        else:
            added = 0
            for _, row in df_up.iterrows():
                sku = _to_text(row.get("sku")).strip()
                if not sku or sku.lower() == "nan":
                    sku = make_sku(products)
                products.append({
                    "sku": sku,
                    "name": _to_text(row.get("name")),
                    "category": _to_text(row.get("category"), "Other"),
                    "size": _to_text(row.get("size")),
                    "cost": _to_float(row.get("cost")),
                    "price": _to_float(row.get("price")),
                    "qty": _to_int(row.get("qty")),
                    "low_stock": _to_int(row.get("low_stock"), 5),
                    "photo": _to_text(row.get("photo")),
                    "supplier": _to_text(row.get("supplier")),
                    "sale_price": _to_float(row.get("sale_price")),
                })
                added += 1
            save_products(products)
            st.success(f"Imported {added} product(s).")
            st.rerun()
    except Exception as e:
        st.error(f"Could not read that CSV: {e}")

st.divider()

# ---------- Search / Filter / List (with Discount column) ----------

st.header(":material/inventory_2: Inventory")

search = st.text_input(":material/search: Search by name or SKU", "")
filter_cat = st.selectbox("Filter by Category", ["All"] + CATEGORIES)
show_only_low = st.checkbox("Show low stock only")

filtered = products
if search:
    filtered = [p for p in filtered
                if search.lower() in p["name"].lower() or search.lower() in p["sku"].lower()]
if filter_cat != "All":
    filtered = [p for p in filtered if p["category"] == filter_cat]
if show_only_low:
    filtered = [p for p in filtered if is_low_stock(p)]

if not filtered:
    st.info("No products yet. Click 'Load Demo Data' above, or add your first product.")
else:
    rows = []
    for p in filtered:
        _sale = _to_float(p.get("sale_price"), 0)
        rows.append({
            "SKU": p["sku"], "Name": p["name"], "Category": p["category"],
            "Size": p["size"], "Cost": format_money(p["cost"]),
            "Price": format_money(p["price"]),
            "Sale Price": format_money(_sale) if _sale > 0 else "-",
            "Effective Price": format_money(effective_price(p)),
            "Discount": discount_label(p),
            "Profit / item": format_money(profit_per_item(p)), "Qty": p["qty"],
            "Stock Value": format_money(effective_price(p) * _to_int(p.get("qty"))),
            "Supplier": p.get("supplier", ""),
            "Status": "LOW" if is_low_stock(p) else "OK",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download Inventory as CSV", icon=":material/download:",
                       data=df.to_csv(index=False).encode("utf-8"),
                       file_name="ibrahim_inventory.csv", mime="text/csv")

st.divider()

# ---------- Product Detail: photo, barcode, price tag, WhatsApp ----------

st.header(":material/package_2: Product Detail")
if not products:
    st.write("Add a product first.")
else:
    detail_names = [f"{p['sku']} — {p['name']}" for p in products]
    detail_sel = st.selectbox("Select product to view", detail_names, key="detail_sel")
    detail_idx = detail_names.index(detail_sel)
    dp = products[detail_idx]

    d1, d2 = st.columns(2)
    with d1:
        st.subheader(dp["name"])
        st.write(f"SKU: {dp['sku']} | Category: {dp['category']} | Size: {dp['size']}")
        st.write(f"Supplier: {dp.get('supplier', '') or '-'}")
        st.write(f"Cost: {format_money(dp.get('cost', 0))}")
        if discount_percent(dp) > 0:
            st.write(f"Price: {format_money(dp.get('price', 0))}  |  Sale Price: {format_money(effective_price(dp))}  ({discount_label(dp)})")
        else:
            st.write(f"Price: {format_money(effective_price(dp))}")
        st.write(f"Profit per item: {format_money(profit_per_item(dp))} ({margin_percent(dp):.1f}% margin)")
        st.write(f"Original: {format_money(effective_price(dp), 'PKR')}")
        st.write(f"In stock: {dp['qty']}  |  Status: {'LOW' if is_low_stock(dp) else 'OK'}")
        # WhatsApp Order button - official WhatsApp logo, green button.
        # Same wa.me link and prefilled message as before (name, effective
        # price, size, SKU), opens in a new tab.
        _wa_url = whatsapp_order_link(dp)
        st.markdown(
            f'<a href="{_wa_url}" target="_blank" rel="noopener" '
            'style="display: inline-flex; align-items: center; '
            'background-color: #25D366; color: #ffffff; '
            'text-decoration: none; font-weight: 600; '
            'padding: 10px 18px; border-radius: 8px; '
            'font-size: 15px; line-height: 1;">'
            f"{WHATSAPP_LOGO_SVG}Order on WhatsApp</a>",
            unsafe_allow_html=True,
        )
        st.write("WhatsApp: 0327-5084710 — message is prefilled with name, price, size and SKU.")
    with d2:
        photo_name = dp.get("photo", "")
        photo_path = os.path.join(PHOTOS_DIR, photo_name) if photo_name else ""
        if photo_name and os.path.exists(photo_path):
            st.image(photo_path, caption=dp["name"], use_container_width=True)
        else:
            st.info("No product photo yet. Add one in Edit Product.")

    # Barcode + Price Tag
    st.subheader(":material/barcode: Barcode and Price Tag")
    try:
        barcode_bytes = make_barcode_png(dp["sku"])
        st.image(barcode_bytes, caption=f"CODE128 — {dp['sku']}", width=320)
        try:
            tag_bytes = make_price_tag_png(dp)
            st.download_button("Download Price Tag (PNG)", icon=":material/download:",
                               data=tag_bytes,
                               file_name=f"{dp['sku']}_price_tag.png",
                               mime="image/png")
        except Exception as e:
            st.error(f"Could not make the price tag: {e}")
    except ImportError:
        st.info("Barcode is not available: install python-barcode and pillow "
                "(they are in requirements.txt) and redeploy to see it.")
    except Exception as e:
        st.error(f"Could not make the barcode: {e}")

st.divider()

# ---------- Edit Product (photo, supplier, sale price) ----------

st.header(":material/edit: Edit Product")
if not products:
    st.write("Add a product first.")
else:
    edit_names = [f"{p['sku']} — {p['name']}" for p in products]
    edit_sel = st.selectbox("Select product to edit", edit_names, key="edit_sel")
    edit_idx = edit_names.index(edit_sel)
    ep = products[edit_idx]
    with st.form("edit_product"):
        e1, e2, e3 = st.columns(3)
        e_name = e1.text_input("Name", value=ep["name"])
        e_cat = e2.selectbox("Category", CATEGORIES, index=CATEGORIES.index(ep["category"]) if ep["category"] in CATEGORIES else 0)
        e_size = e3.text_input("Size", value=ep["size"])
        e4, e5, e6, e7 = st.columns(4)
        e_cost = e4.number_input("Cost (Rs)", min_value=0.0, value=float(ep["cost"]), step=100.0)
        e_price = e5.number_input("Price (Rs)", min_value=0.0, value=float(ep["price"]), step=100.0)
        e_qty = e6.number_input("Quantity", min_value=0, value=int(ep["qty"]), step=1)
        e_low = e7.number_input("Low Stock Alert At", min_value=0, value=int(ep["low_stock"]), step=1)
        e8, e9 = st.columns(2)
        e_supplier = e8.text_input("Supplier", value=ep.get("supplier", ""))
        e_sale = e9.number_input("Sale Price (Rs, 0 = no sale)", min_value=0.0, value=float(ep.get("sale_price", 0)), step=100.0)
        e_photo = st.file_uploader("New Product Photo (jpg/png, leave empty to keep current)", type=["jpg", "jpeg", "png"])
        if st.form_submit_button("Save Changes", icon=":material/save:"):
            if e_price < e_cost:
                st.error("Price should be more than cost.")
            elif e_sale > 0 and e_sale < e_cost:
                st.error("Sale price should not be below cost.")
            elif e_sale > 0 and e_sale >= e_price:
                st.error("Sale price should be less than the normal price.")
            else:
                photo_name = ep.get("photo", "")
                if e_photo is not None:
                    photo_name = save_uploaded_photo(e_photo, ep["sku"])
                ep.update({"name": e_name, "category": e_cat, "size": e_size,
                           "cost": e_cost, "price": e_price,
                           "qty": int(e_qty), "low_stock": int(e_low),
                           "supplier": e_supplier, "sale_price": float(e_sale),
                           "photo": photo_name})
                save_products(products)
                st.success(f"Updated {e_name}.")
                st.rerun()

st.divider()

# ---------- Sell / Restock (sells at effective price) ----------

st.header(":material/shopping_cart: Sell / Restock")
if not products:
    st.write("Add a product first.")
else:
    names = [f"{p['sku']} — {p['name']} ({p['qty']} in stock)" for p in products]
    selected = st.selectbox("Select Product", names)
    idx = names.index(selected)
    product = products[idx]

    st.write(f"**{product['name']}** — Price {format_money(effective_price(product))}, "
             f"Profit {format_money(profit_per_item(product))} per item, Stock: {product['qty']}")
    if discount_percent(product) > 0:
        st.write(f"On sale: was {format_money(product.get('price', 0))}, now {format_money(effective_price(product))} ({discount_label(product)})")

    c1, c2 = st.columns(2)
    sell_qty = c1.number_input("Sell Quantity", min_value=1, max_value=max(1, product["qty"]), step=1)
    if c1.button("Sell", icon=":material/shopping_cart:"):
        if sell_qty > product["qty"]:
            st.error("Not enough stock!")
        else:
            product["qty"] -= sell_qty
            save_products(products)
            amount = sell_qty * effective_price(product)
            profit = sell_qty * profit_per_item(product)
            save_sale(product["sku"], product["name"], int(sell_qty), amount, profit)
            st.session_state.sales = load_sales()
            st.success(f"Sold {sell_qty} x {product['name']} — Earned {format_money(amount)}, Profit {format_money(profit)}")
            st.rerun()

    add_qty = c2.number_input("Restock Quantity", min_value=1, step=1)
    if c2.button("Add Stock", icon=":material/add_box:"):
        product["qty"] += add_qty
        save_products(products)
        st.success(f"Added {add_qty} to {product['name']}. New stock: {product['qty']}")
        st.rerun()

    if st.button("Delete This Product", icon=":material/delete:"):
        products.pop(idx)
        save_products(products)
        st.success("Product deleted.")
        st.rerun()

st.divider()

# ---------- Supplier & Purchase Orders ----------

st.header(":material/local_shipping: Supplier & Purchase Orders")
if not products:
    st.write("Add a product first, then create a purchase order for it.")
else:
    with st.form("create_po"):
        po_names = [f"{p['sku']} — {p['name']}" for p in products]
        po_sel = st.selectbox("Product", po_names)
        po_idx = po_names.index(po_sel)
        po_product = products[po_idx]
        po_supplier = st.text_input("Supplier", value=po_product.get("supplier", ""))
        po_c1, po_c2 = st.columns(2)
        po_qty = po_c1.number_input("Quantity to Order", min_value=1, value=10, step=1)
        po_cost = po_c2.number_input("Cost per Unit (Rs)", min_value=0.0, value=float(po_product.get("cost", 0)), step=100.0)
        if st.form_submit_button("Create Purchase Order", icon=":material/local_shipping:"):
            if not po_supplier:
                st.error("Supplier name is required for a purchase order.")
            else:
                new_po = {
                    "po_id": make_po_id(purchase_orders),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "supplier": po_supplier,
                    "sku": po_product["sku"],
                    "name": po_product["name"],
                    "qty": int(po_qty),
                    "cost_each": float(po_cost),
                    "total_cost": float(po_qty) * float(po_cost),
                    "status": "Ordered",
                }
                purchase_orders.append(new_po)
                save_purchase_orders(purchase_orders)
                st.success(f"Created {new_po['po_id']} — {po_qty} x {po_product['name']} from {po_supplier}, total {format_money(new_po['total_cost'])}")
                st.rerun()

    if not purchase_orders:
        st.info("No purchase orders yet.")
    else:
        _po_rows = [{
            "PO": po["po_id"], "Date": po["date"], "Supplier": po["supplier"],
            "SKU": po["sku"], "Name": po["name"], "Qty": po["qty"],
            "Cost Each": format_money(po["cost_each"]),
            "Total Cost": format_money(po["total_cost"]),
            "Status": po["status"],
        } for po in purchase_orders]
        st.dataframe(pd.DataFrame(_po_rows), use_container_width=True, hide_index=True)
        ordered = [po for po in purchase_orders if po.get("status") == "Ordered"]
        if ordered:
            po_labels = [f"{po['po_id']} — {po['name']} x {po['qty']} from {po['supplier']}" for po in ordered]
            po_choice = st.selectbox("Mark a purchase order as received", po_labels)
            if st.button("Mark Received", icon=":material/check_circle:"):
                chosen = ordered[po_labels.index(po_choice)]
                match = [p for p in products if p["sku"] == chosen["sku"]]
                if not match:
                    st.error("That product no longer exists in inventory, so stock cannot be added.")
                else:
                    match[0]["qty"] = _to_int(match[0].get("qty")) + _to_int(chosen.get("qty"))
                    chosen["status"] = "Received"
                    save_products(products)
                    save_purchase_orders(purchase_orders)
                    st.success(f"Received {chosen['po_id']}: added {chosen['qty']} to {chosen['name']}. New stock: {match[0]['qty']}")
                    st.rerun()

st.divider()

# ---------- Sales History ----------

st.header(":material/receipt_long: Sales History")
sales = st.session_state.sales
if not sales:
    st.info("No sales yet. Sell something above and it will appear here with date, amount and profit.")
else:
    df_sales = pd.DataFrame(sales)
    st.dataframe(df_sales, use_container_width=True, hide_index=True)
    st.write(f"**Total sales:** {format_money(sum(s['amount'] for s in sales))} &nbsp;|&nbsp; "
             f"**Total profit from sales:** {format_money(sum(s['profit'] for s in sales))}")
    st.download_button("Download Sales as CSV", icon=":material/download:",
                       data=df_sales.to_csv(index=False).encode("utf-8"),
                       file_name="ibrahim_sales.csv", mime="text/csv")

st.divider()

# ---------- Monthly Report + PDF ----------

st.header(":material/assessment: Monthly Report")
current_month = datetime.now().strftime("%Y-%m")
month_sales = [s for s in sales if str(s.get("date", ""))[:7] == current_month]
month_total = sum(s["amount"] for s in month_sales)
month_profit = sum(s["profit"] for s in month_sales)
month_count = len(month_sales)

m1, m2, m3 = st.columns(3)
m1.metric("Sales This Month", format_money(month_total))
m2.metric("Profit This Month", format_money(month_profit))
m3.metric("Number of Sales", month_count)

best_by_qty = []
best_by_profit = []
if month_sales:
    df_month = pd.DataFrame(month_sales)
    by_name = df_month.groupby("name").agg({"qty": "sum", "amount": "sum", "profit": "sum"}).reset_index()
    st.write("Best sellers this month:")
    _best_display = by_name.sort_values("qty", ascending=False).copy()
    _best_display["amount"] = _best_display["amount"].apply(lambda v: format_money(v))
    _best_display["profit"] = _best_display["profit"].apply(lambda v: format_money(v))
    st.dataframe(_best_display, use_container_width=True, hide_index=True)
    best_by_qty = [(row["name"], int(row["qty"])) for _, row in by_name.sort_values("qty", ascending=False).head(5).iterrows()]
    best_by_profit = [(row["name"], float(row["profit"])) for _, row in by_name.sort_values("profit", ascending=False).head(5).iterrows()]
else:
    st.info(f"No sales in {current_month} yet. Sell something and it will appear here.")

if st.button("Generate Monthly Report PDF", icon=":material/picture_as_pdf:"):
    try:
        pdf_bytes = build_monthly_report_pdf(
            current_month, month_total, month_profit, month_count,
            best_by_qty, best_by_profit)
        st.download_button("Download Monthly Report (PDF)", icon=":material/download:",
                           data=pdf_bytes,
                           file_name=f"ibrahim_monthly_report_{current_month}.pdf",
                           mime="application/pdf")
    except ImportError:
        st.info("PDF is not available: install fpdf2 (it is in requirements.txt) and redeploy to generate the PDF.")
    except Exception as e:
        st.error(f"Could not make the PDF: {e}")

st.divider()
st.caption("Practice task: add a filter to Sales History by date, or a chart of sales profit per day. "
           "Both use the same groupby idea as the category charts above.")
