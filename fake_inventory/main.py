"""
Fake Inventory Service — simulates a real inventory system using Faker.

Runs on port 8001. GET /products returns products with randomly
mutated quantities/prices on each call to simulate real changes.
"""
import random

from faker import Faker
from fastapi import FastAPI

app = FastAPI(title="Fake Inventory", version="0.1.0")

fake = Faker()
Faker.seed(42)  # reproducible product names across restarts
random.seed(None)  # but mutations are truly random

# Generate stable product catalog at startup
_products: list[dict] = [
    {
        "product_id": f"P{str(i + 1).zfill(3)}",
        "name": fake.unique.word().capitalize() + " " + fake.lexify("??").upper(),
        "quantity": random.randint(50, 500),
        "price": round(random.uniform(1.99, 199.99), 2),
        "warehouse": fake.city(),
    }
    for i in range(10)
]


@app.get("/products")
def get_products() -> list[dict]:
    """
    Return all products. Randomly mutates 1-3 products on each call
    to simulate real inventory changes over time.
    """
    to_mutate = random.sample(_products, k=random.randint(1, 3))
    for product in to_mutate:
        product["quantity"] = max(0, product["quantity"] + random.randint(-30, 30))
        product["price"] = round(product["price"] + random.uniform(-0.5, 0.5), 2)

    return [dict(p) for p in _products]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
