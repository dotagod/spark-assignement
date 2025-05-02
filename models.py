from pydantic import BaseModel
from typing import List

class Location(BaseModel):
    lat: float
    lon: float

class Profile(BaseModel):
    id: str
    age: int
    gender: str
    location: Location
    interests: List[str]
