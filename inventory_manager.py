"""
Ibrahim Apparel & Trading - Inventory Manager v2
Full Python practice project - with proper UI (Streamlit, no CLI)

HOW TO RUN - Streamlit Community Cloud (free, no install):
1. Push this file + requirements.txt to a public GitHub repo
2. Go to share.streamlit.io, sign in with GitHub, Create app
3. Pick the repo, branch main, main file inventory_manager.py, Deploy
4. Every push to GitHub auto-redeploys in 1-2 minutes

WHAT'S NEW IN v2:
- Demo data: 8 real Ibrahim products, Load / Clear in one tap
- Sales history log: every sale is recorded with date, qty, amount, profit
- Charts: stock value and profit by category
- Edit product: change price, cost, stock, size after adding
- CSV import: upload many products at once
- Low-stock dashboard: all low items + how many to order

WHAT YOU LEARN:
- lists & dictionaries, functions, file handling (CSV)
- if/else, loops, sorting, filtering, groupby with pandas
- Streamlit UI: forms, file_uploader, bar_chart, dataframe, download_button
"""

import csv
import os
from datetime import datetime
import streamlit as st
import pandas as pd

CSV_FILE = "inventory.csv"
SALES_FILE = "sales.csv"

CATEGORIES = [
    "Jackets", "Hoodie", "Sweaters", "Sweat Shirts",
    "Shirts", "Pants", "Jeans", "Korean Trousers",
    "Ladies", "Shawls", "Co-ord Sets", "Kurtis", "Other"
]

# ---------- Demo data (8 products, as agreed) ----------
DEMO_PRODUCTS = [
    {"sku": "IAT-00001", "name": "Midnight Puffer Jacket", "category": "Jackets", "size": "L", "cost": 5200.0, "price": 8999.0, "qty": 12, "low_stock": 5},
    {"sku": "IAT-00002", "name": "Olive Hoodie", "category": "Hoodie", "size": "M", "cost": 1800.0, "price": 2999.0, "qty": 20, "low_stock": 5},
    {"sku": "IAT-00003", "name": "Camel Wool Sweater", "category": "Sweaters", "size": "L", "cost": 2200.0, "price": 3999.0, "qty": 5, "low_stock": 5},
    {"sku": "IAT-00004", "name": "Navy Mock Neck Sweatshirt", "category": "Sweat Shirts", "size": "M", "cost": 1500.0, "price": 2699.0, "qty": 15, "low_stock": 5},
    {"sku": "IAT-00005", "name": "White Formal Shirt", "category": "Shirts", "size": "L", "cost": 1200.0, "price": 2199.0, "qty": 18, "low_stock": 5},
    {"sku": "IAT-00006", "name": "Black Straight Fit Jeans", "category": "Jeans", "size": "32", "cost": 2000.0, "price": 3499.0, "qty": 10, "low_stock": 5},
    {"sku": "IAT-00007", "name": "Maroon Shawl", "category": "Shawls", "size": "One Size", "cost": 1400.0, "price": 2499.0, "qty": 3, "low_stock": 5},
    {"sku": "IAT-00008", "name": "Grey Kurti", "category": "Kurtis", "size": "M", "cost": 1600.0, "price": 2799.0, "qty": 7, "low_stock": 5},
]
DEMO_SKUS = {p["sku"] for p in DEMO_PRODUCTS}


# ---------- Data functions (pure Python - core logic) ----------

def load_products():
    """Load products from CSV file. Returns a list of dicts."""
    if not os.path.exists(CSV_FILE):
        return []
    products = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["cost"] = float(row["cost"])
            row["price"] = float(row["price"])
            row["qty"] = int(row["qty"])
            row["low_stock"] = int(row["low_stock"])
            products.append(row)
    return products


def save_products(products):
    fieldnames = ["sku", "name", "category", "size", "cost", "price", "qty", "low_stock"]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            writer.writerow(p)


def load_sales():
    if not os.path.exists(SALES_FILE):
        return []
    sales = []
    with open(SALES_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["qty"] = int(row["qty"])
            row["amount"] = float(row["amount"])
            row["profit"] = float(row["profit"])
            sales.append(row)
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


def make_sku(products):
    # Next number after the highest existing IAT- number
    nums = [int(p["sku"].split("-")[1]) for p in products
            if p["sku"].startswith("IAT-") and p["sku"].split("-")[1].isdigit()]
    return f"IAT-{max(nums, default=0) + 1:05d}"


def profit_per_item(product):
    return product["price"] - product["cost"]


def margin_percent(product):
    if product["cost"] == 0:
        return 0
    return (product["price"] - product["cost"]) / product["cost"] * 100


def is_low_stock(product):
    return product["qty"] <= product["low_stock"]


def restock_suggestion(product, target=15):
    """How many to order to bring stock up to target (15)."""
    return max(0, target - product["qty"])


# ---------- App state ----------

st.set_page_config(page_title="Ibrahim Inventory Manager", page_icon="🧥", layout="wide")

if "products" not in st.session_state:
    st.session_state.products = load_products()
if "sales" not in st.session_state:
    st.session_state.sales = load_sales()

products = st.session_state.products
sales = st.session_state.sales

# ---------- Header ----------

st.title("🧥 Ibrahim Apparel & Trading")
st.subheader("Inventory Manager — Full Python Project")
st.write("Add products, track stock, see profit. Data saves to `inventory.csv`.")

# ---------- Demo data buttons ----------

col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    if st.button("📥 Load Demo Data (8 products)"):
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
    if st.button("🧹 Clear Demo Data"):
        products[:] = [p for p in products if p["sku"] not in DEMO_SKUS]
        save_products(products)
        st.success("Demo products removed. Your own products are kept.")
        st.rerun()
with col_d3:
    st.write("Demo = 8 products: Puffer Jacket, Hoodie, Sweater, Sweatshirt, Shirt, Jeans, Shawl, Kurti.")

# ---------- Dashboard ----------

total_units = sum(p["qty"] for p in products)
stock_cost_value = sum(p["cost"] * p["qty"] for p in products)
stock_price_value = sum(p["price"] * p["qty"] for p in products)
total_profit = stock_price_value - stock_cost_value
low_items = [p for p in products if is_low_stock(p)]
sales_total = sum(s["amount"] for s in sales)
sales_profit = sum(s["profit"] for s in sales)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Products", len(products))
c2.metric("Units in Stock", total_units)
c3.metric("Stock Value (Rs)", f"{stock_price_value:,.0f}")
c4.metric("Potential Profit (Rs)", f"{total_profit:,.0f}")
c5.metric("Sales So Far (Rs)", f"{sales_total:,.0f}", f"Profit Rs {sales_profit:,.0f}")

if low_items:
    st.warning(f"⚠️ Low stock: {len(low_items)} item(s) — " +
               ", ".join(f"{p['name']} ({p['qty']} left)" for p in low_items))

st.divider()

# ---------- Charts: by category ----------

st.header("📊 Insights — By Category")
if products:
    df_all = pd.DataFrame([{
        "Category": p["category"],
        "Stock Value (Rs)": p["price"] * p["qty"],
        "Profit (Rs)": profit_per_item(p) * p["qty"],
        "Units": p["qty"],
    } for p in products])
    grouped = df_all.groupby("Category").sum(numeric_only=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.write("Stock Value by Category")
        st.bar_chart(grouped["Stock Value (Rs)"])
    with cc2:
        st.write("Potential Profit by Category")
        st.bar_chart(grouped["Profit (Rs)"])
    st.dataframe(grouped, use_container_width=True)
else:
    st.info("Load demo data or add a product to see charts.")

st.divider()

# ---------- Low-stock dashboard ----------

st.header("🔴 Low Stock — What to Order")
if not low_items:
    st.success("All good — no low-stock items right now.")
else:
    rows = [{
        "SKU": p["sku"], "Name": p["name"], "Category": p["category"],
        "In Stock": p["qty"], "Alert At": p["low_stock"],
        "Order This Many (to reach 15)": restock_suggestion(p),
        "Cost to Restock (Rs)": restock_suggestion(p) * p["cost"],
    } for p in low_items]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

# ---------- Add Product Form ----------

st.header("➕ Add New Product")
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
    sku_input = st.text_input("SKU (leave blank for auto)", placeholder="IAT-00001")

    submitted = st.form_submit_button("Add Product")
    if submitted:
        if not name:
            st.error("Product name is required.")
        elif price < cost:
            st.error("Selling price should be more than cost, otherwise loss!")
        else:
            sku = sku_input.strip() or make_sku(products)
            new_product = {
                "sku": sku, "name": name, "category": category,
                "size": size, "cost": cost, "price": price,
                "qty": int(qty), "low_stock": int(low_stock),
            }
            products.append(new_product)
            save_products(products)
            st.success(f"Added {name} — Profit per item: Rs {profit_per_item(new_product):,.0f} "
                       f"({margin_percent(new_product):.1f}% margin)")
            st.rerun()

st.divider()

# ---------- CSV Import ----------

st.header("📤 Import Products from CSV")
st.write("Upload a CSV with columns: `sku,name,category,size,cost,price,qty,low_stock` — blank SKU = auto.")
st.download_button("⬇️ Download CSV Template",
                   data="sku,name,category,size,cost,price,qty,low_stock\n,Test Jacket,Jackets,L,5000,8999,10,5\n",
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
                sku = str(row.get("sku", "")).strip()
                if not sku or sku.lower() == "nan":
                    sku = make_sku(products)
                products.append({
                    "sku": sku,
                    "name": str(row["name"]),
                    "category": str(row.get("category", "Other")),
                    "size": str(row.get("size", "")),
                    "cost": float(row["cost"]),
                    "price": float(row["price"]),
                    "qty": int(row["qty"]),
                    "low_stock": int(row.get("low_stock", 5)),
                })
                added += 1
            save_products(products)
            st.success(f"Imported {added} product(s).")
            st.rerun()
    except Exception as e:
        st.error(f"Could not read that CSV: {e}")

st.divider()

# ---------- Search / Filter / List ----------

st.header("📦 Inventory")

search = st.text_input("🔍 Search by name or SKU", "")
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
        rows.append({
            "SKU": p["sku"], "Name": p["name"], "Category": p["category"],
            "Size": p["size"], "Cost (Rs)": p["cost"], "Price (Rs)": p["price"],
            "Profit / item": profit_per_item(p), "Qty": p["qty"],
            "Stock Value": p["price"] * p["qty"],
            "Status": "🔴 LOW" if is_low_stock(p) else "🟢 OK",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download Inventory as CSV",
                       data=df.to_csv(index=False).encode("utf-8"),
                       file_name="ibrahim_inventory.csv", mime="text/csv")

st.divider()

# ---------- Edit Product ----------

st.header("✏️ Edit Product")
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
        if st.form_submit_button("Save Changes"):
            if e_price < e_cost:
                st.error("Price should be more than cost.")
            else:
                ep.update({"name": e_name, "category": e_cat, "size": e_size,
                           "cost": e_cost, "price": e_price,
                           "qty": int(e_qty), "low_stock": int(e_low)})
                save_products(products)
                st.success(f"Updated {e_name}.")
                st.rerun()

st.divider()

# ---------- Sell / Restock (now logs sales) ----------

st.header("🛒 Sell / Restock")
if not products:
    st.write("Add a product first.")
else:
    names = [f"{p['sku']} — {p['name']} ({p['qty']} in stock)" for p in products]
    selected = st.selectbox("Select Product", names)
    idx = names.index(selected)
    product = products[idx]

    st.write(f"**{product['name']}** — Price Rs {product['price']:,.0f}, "
             f"Profit Rs {profit_per_item(product):,.0f} per item, Stock: {product['qty']}")

    c1, c2 = st.columns(2)
    sell_qty = c1.number_input("Sell Quantity", min_value=1, max_value=max(1, product["qty"]), step=1)
    if c1.button("Sell"):
        if sell_qty > product["qty"]:
            st.error("Not enough stock!")
        else:
            product["qty"] -= sell_qty
            save_products(products)
            amount = sell_qty * product["price"]
            profit = sell_qty * profit_per_item(product)
            save_sale(product["sku"], product["name"], int(sell_qty), amount, profit)
            st.session_state.sales = load_sales()
            st.success(f"Sold {sell_qty} x {product['name']} — Earned Rs {amount:,.0f}, Profit Rs {profit:,.0f}")
            st.rerun()

    add_qty = c2.number_input("Restock Quantity", min_value=1, step=1)
    if c2.button("Add Stock"):
        product["qty"] += add_qty
        save_products(products)
        st.success(f"Added {add_qty} to {product['name']}. New stock: {product['qty']}")
        st.rerun()

    if st.button("🗑️ Delete This Product"):
        products.pop(idx)
        save_products(products)
        st.success("Product deleted.")
        st.rerun()

st.divider()

# ---------- Sales History ----------

st.header("🧾 Sales History")
sales = st.session_state.sales
if not sales:
    st.info("No sales yet. Sell something above and it will appear here with date, amount and profit.")
else:
    df_sales = pd.DataFrame(sales)
    st.dataframe(df_sales, use_container_width=True, hide_index=True)
    st.write(f"**Total sales:** Rs {sum(s['amount'] for s in sales):,.0f} &nbsp;|&nbsp; "
             f"**Total profit from sales:** Rs {sum(s['profit'] for s in sales):,.0f}")
    st.download_button("⬇️ Download Sales as CSV",
                       data=df_sales.to_csv(index=False).encode("utf-8"),
                       file_name="ibrahim_sales.csv", mime="text/csv")

st.divider()
st.caption("Practice task: add a filter to Sales History by date, or a chart of sales profit per day. "
           "Both use the same groupby idea as the category charts above.")
