from typing import Optional
from pydantic import BaseModel

class Journey(BaseModel):
    operator: str
    origin: str
    destination: str
    departure: str
    arrival: str
    duration: str
    price: Optional[float]
    currency: str = "MAD" # Moroccan dirham
    available_seats: Optional[int]
    amenities: list[str] = []
    brand: Optional[str] = None
    for_sale: bool = True