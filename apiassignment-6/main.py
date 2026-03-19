from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# -------------------------------
# DATA
# -------------------------------
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "USB Cable", "price": 199, "category": "Electronics", "in_stock": False},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]

feedback = []
orders = []

# -------------------------------
# MODELS
# -------------------------------
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

# NEW MODEL (for POST products)
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

# -------------------------------
# HELPER
# -------------------------------
def find_product(product_id):
    for p in products:
        if p["id"] == product_id:
            return p
    return None

# -------------------------------
# BASIC ROUTES
# -------------------------------
@app.get("/")
def home():
    return {"message": "FastAPI Store API Running"}

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]
    if not result:
        return {"error": "No products found in this category"}
    return {"category": category_name, "products": result, "total": len(result)}

@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"]]
    return {"in_stock_products": available, "count": len(available)}

@app.get("/store/summary")
def store_summary():
    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count
    categories = list(set([p["category"] for p in products]))

    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories
    }

@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    results = [p for p in products if keyword.lower() in p["name"].lower()]
    if not results:
        return {"message": "No products matched your search"}
    return {"keyword": keyword, "results": results, "total_matches": len(results)}

@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {"best_deal": cheapest, "premium_pick": expensive}

@app.get("/products/filter")
def filter_products(category: str = None, max_price: int = None, min_price: int = Query(None)):
    result = products
    if category:
        result = [p for p in result if p["category"] == category]
    if max_price:
        result = [p for p in result if p["price"] <= max_price]
    if min_price:
        result = [p for p in result if p["price"] >= min_price]
    return {"products": result}

# -------------------------------
# 🆕 CRUD APIs (ASSIGNMENT)
# -------------------------------

@app.post("/products", status_code=201)
def add_product(new_product: NewProduct):
    for p in products:
        if p["name"].lower() == new_product.name.lower():
            return {"error": "Product already exists"}

    new_id = max(p["id"] for p in products) + 1
    product_dict = new_product.dict()
    product_dict["id"] = new_id

    products.append(product_dict)

    return {"message": "Product added", "product": product_dict}

@app.put("/products/{product_id}")
def update_product(product_id: int, price: int = None, in_stock: bool = None):
    product = find_product(product_id)

    if not product:
        return {"error": "Product not found"}

    if price is not None:
        product["price"] = price

    if in_stock is not None:
        product["in_stock"] = in_stock

    return {"message": "Product updated", "product": product}

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    product = find_product(product_id)

    if not product:
        return {"error": "Product not found"}

    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}

# -------------------------------
# 🆕 AUDIT (IMPORTANT ABOVE dynamic route)
# -------------------------------
@app.get("/products/audit")
def product_audit():
    in_stock_list = [p for p in products if p["in_stock"]]
    out_stock_list = [p for p in products if not p["in_stock"]]

    stock_value = sum(p["price"] * 10 for p in in_stock_list)
    priciest = max(products, key=lambda p: p["price"])

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p["name"] for p in out_stock_list],
        "total_stock_value": stock_value,
        "most_expensive": {
            "name": priciest["name"],
            "price": priciest["price"]
        }
    }

# -------------------------------
# 🆕 BONUS
# -------------------------------
@app.put("/products/discount")
def bulk_discount(category: str = Query(...), discount_percent: int = Query(..., ge=1, le=99)):
    updated = []

    for p in products:
        if p["category"] == category:
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": f"No products found in category: {category}"}

    return {
        "message": f"{discount_percent}% discount applied to {category}",
        "updated_count": len(updated),
        "updated_products": updated
    }

# -------------------------------
# 🆕 DAY 6 - SEARCH, SORT, PAGINATION
# -------------------------------

# Q1 - Search with query param (case-insensitive)
@app.get("/products/search")
def search_products_query(keyword: str = Query(...)):
    results = [p for p in products if keyword.lower() in p["name"].lower()]

    if not results:
        return {"message": f"No products found for: {keyword}"}

    return {
        "keyword": keyword,
        "total_found": len(results),
        "products": results
    }


# Q2 - Sort products
@app.get("/products/sort")
def sort_products(sort_by: str = Query("price"), order: str = Query("asc")):

    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    reverse = (order == "desc")

    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_products
    }


# Q3 - Pagination
@app.get("/products/page")
def paginate_products(page: int = Query(1, ge=1), limit: int = Query(2, ge=1)):

    total = len(products)
    start = (page - 1) * limit
    paged = products[start:start + limit]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": -(-total // limit),
        "products": paged
    }


# Q4 - Orders search (works with your existing orders list)
@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):

    results = [
        o for o in orders
        if customer_name.lower() in o.get("company_name", "").lower()
    ]

    if not results:
        return {"message": f"No orders found for: {customer_name}"}

    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results
    }


# Q5 - Sort by category then price
@app.get("/products/sort-by-category")
def sort_by_category():

    result = sorted(products, key=lambda p: (p["category"], p["price"]))

    return {
        "products": result,
        "total": len(result)
    }


# Q6 - Combined: Search + Sort + Pagination
@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20),
):

    result = products

    # Search
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # Sort
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # Pagination
    total = len(result)
    start = (page - 1) * limit
    paged = result[start:start + limit]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": -(-total // limit),
        "products": paged
    }


# BONUS - Orders pagination
@app.get("/orders/page")
def paginate_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20),
):

    total = len(orders)
    start = (page - 1) * limit

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": -(-total // limit),
        "orders": orders[start:start + limit]
    }

# -------------------------------
# EXISTING ROUTES (KEEP LAST)
# -------------------------------
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    product = find_product(product_id)
    if product:
        return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }

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

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:
        product = find_product(item.product_id)

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