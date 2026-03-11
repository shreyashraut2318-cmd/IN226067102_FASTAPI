from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ── Temporary Data (Database) ─────────────────────────

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]

orders = []
feedback = []

# ── Home Endpoint ─────────────────────────

@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API"}

# ── Get All Products ──────────────────────

@app.get("/products")
def get_all_products():
    return {"products": products, "total": len(products)}

# ── Filter Products ───────────────────────

@app.get("/products/filter")
def filter_products(
        category: Optional[str] = Query(None),
        max_price: Optional[int] = Query(None),
        min_price: Optional[int] = Query(None, description="Minimum price"),
        in_stock: Optional[bool] = Query(None)
):

    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {"filtered_products": result, "count": len(result)}

# ── Category Products ─────────────────────

@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):

    result = [p for p in products if p["category"].lower() == category_name.lower()]

    if not result:
        return {"error": "No products found"}

    return {"category": category_name, "products": result}

# ── In Stock Products ─────────────────────

@app.get("/products/instock")
def get_instock_products():

    instock = [p for p in products if p["in_stock"]]

    return {"in_stock_products": instock, "count": len(instock)}

# ── Store Summary ─────────────────────────

@app.get("/store/summary")
def store_summary():

    total = len(products)
    instock = sum(p["in_stock"] for p in products)
    out = total - instock
    categories = list({p["category"] for p in products})

    return {
        "store_name": "My E-commerce Store",
        "total_products": total,
        "in_stock": instock,
        "out_of_stock": out,
        "categories": categories
    }

# ── Search Products ───────────────────────

@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    result = [p for p in products if keyword.lower() in p["name"].lower()]

    return {"results": result, "count": len(result)}

# ── Deals Endpoint ────────────────────────

@app.get("/products/deals")
def get_deals():

    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {"best_deal": cheapest, "premium_pick": expensive}

# ================= DAY 2 ===========================

# ── Product Summary Dashboard ──────────────────────

@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }

# ── Get Only Price of Product ──────────────────────

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}

    return {"error": "Product not found"}

# ── Get Full Product ─────────────────────

@app.get("/products/{product_id}")
def get_product(product_id: int):

    for p in products:
        if p["id"] == product_id:
            return {"product": p}

    return {"error": "Product not found"}

# ── Feedback Model ───────────────────────

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

# ── Submit Feedback ──────────────────────

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }

# ── Bulk Order Models ─────────────────────

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

# ── Bulk Order Endpoint ───────────────────

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})

        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})

        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# ================= BONUS ============================

class OrderRequest(BaseModel):
    product_id: int
    quantity: int

# ── Place Order ──────────────────────────

@app.post("/orders")
def place_order(order: OrderRequest):

    product = next((p for p in products if p["id"] == order.product_id), None)

    if not product:
        return {"error": "Product not found"}

    new_order = {
        "order_id": len(orders) + 1,
        "product": product["name"],
        "quantity": order.quantity,
        "status": "pending"
    }

    orders.append(new_order)

    return {"message": "Order placed", "order": new_order}

# ── Get Order ────────────────────────────

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}

# ── Confirm Order ────────────────────────

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}

    return {"error": "Order not found"}