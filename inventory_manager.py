"""
Ibrahim Apparel & Trading - Inventory Manager
Full Python practice project - with proper UI (Streamlit, no CLI)

HOW TO RUN - without installing anything on your PC:
1. Go to replit.com -> Create Repl -> Python
2. Upload this file as main file, or paste this code
3. In Replit Shell, run:  pip install streamlit pandas
4. Then run:  streamlit run inventory_manager.py
5. Replit will show you a website link - open it, you get full UI

WHAT YOU LEARN FROM THIS PROJECT:
- lists & dictionaries (products are dicts in a list)
- functions (add_product, sell_product, restock, etc.)
- file handling (save/load from inventory.csv)
- if/else, loops, sorting & filtering
- Streamlit UI: text_input, number_input, button, metric, dataframe
"""

import csv
import os
import streamlit as st
import pandas as pd

CSV_FILE = "inventory.csv"

CATEGORIES = [
    "Jackets", "Hoodie", "Sweaters", "Sweat Shirts",
    "Shirts", "Pants", "Jeans", "Korean Trousers",
    "Ladies", "Shawls", "Co-ord Sets", "Kurtis", "Other"
]

# ---------- Data functions (pure Python - this is the core logic) ----------

def load_products():
    """Load products from CSV file. Returns a list of dicts."""
    if not os.path.exists(CSV_FILE):
        return []
    products = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numbers back from text
            row["cost"] = float(row["cost"])
            row["price"] = float(row["price"])
            row["qty"] = int(row["qty"])
            row["low_stock"] = int(row["low_stock"])
            products.append(row)
    return products


def save_products(products):
    """Save list of product dicts to CSV file."""
    fieldnames = ["sku", "name", "category", "size", "cost", "price", "qty", "low_stock"]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            writer.writerow(p)


def make_sku(products):
    """Auto SKU like IAT-00001, IAT-00002..."""
    return f"IAT-{len(products) + 1:05d}"


def profit_per_item(product):
    return product["price"] - product["cost"]


def margin_percent(product):
    if product["cost"] == 0:
        return 0
    return (product["price"] - product["cost"]) / product["cost"] * 100


def is_low_stock(product):
    return product["qty"] <= product["low_stock"]


# ---------- App state ----------

st.set_page_config(page_title="Ibrahim Inventory Manager", page_icon="🧥", layout="wide")

if "products" not in st.session_state:
    st.session_state.products = load_products()

products = st.session_state.products

# ---------- Header ----------

st.title("🧥 Ibrahim Apparel & Trading")
st.subheader("Inventory Manager — Full Python Project")
st.write("Add products, track stock, see profit. Data saves to `inventory.csv`.")

# ---------- Dashboard ----------

total_units = sum(p["qty"] for p in products)
stock_cost_value = sum(p["cost"] * p["qty"] for p in products)
stock_price_value = sum(p["price"] * p["qty"] for p in products)
total_profit = stock_price_value - stock_cost_value
low_items = [p for p in products if is_low_stock(p)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Products", len(products))
col2.metric("Units in Stock", total_units)
col3.metric("Stock Value (Rs)", f"{stock_price_value:,.0f}")
col4.metric("Potential Profit (Rs)", f"{total_profit:,.0f}")

if low_items:
    st.warning(f"⚠️ Low stock: {len(low_items)} item(s) — " +
               ", ".join(f"{p['name']} ({p['qty']} left)" for p in low_items))

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
    st.info("No products yet. Add your first product above — try a Jacket at Cost 5000, Price 8999.")
else:
    # Build table with calculated columns
    rows = []
    for p in filtered:
        rows.append({
            "SKU": p["sku"],
            "Name": p["name"],
            "Category": p["category"],
            "Size": p["size"],
            "Cost (Rs)": p["cost"],
            "Price (Rs)": p["price"],
            "Profit / item": profit_per_item(p),
            "Qty": p["qty"],
            "Stock Value": p["price"] * p["qty"],
            "Status": "🔴 LOW" if is_low_stock(p) else "🟢 OK",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Download as CSV
    st.download_button("⬇️ Download Inventory as CSV",
                       data=df.to_csv(index=False).encode("utf-8"),
                       file_name="ibrahim_inventory.csv", mime="text/csv")

st.divider()

# ---------- Sell / Restock ----------

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
            st.success(f"Sold {sell_qty} x {product['name']} — Earned Rs {sell_qty * product['price']:,.0f}")
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
st.caption("Practice task: try adding a function to calculate total profit for a category, "
           "or add a 'discount price' field. That is your next step after this works.")
