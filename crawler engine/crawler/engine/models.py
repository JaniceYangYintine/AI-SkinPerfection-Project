# engine/models.py
from dataclasses import dataclass

@dataclass
class Product:
    brand: str
    category: str
    name: str
    price: str | None
    description: str
    url: str
    crawled_at: str  # e.g. "2025-12-28 21:30:00"
    image_url: str | None = None
