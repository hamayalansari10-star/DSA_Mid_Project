from dataclasses import dataclass, asdict

@dataclass
class Book:
    id: int
    title: str
    author: str
    price: float
    rating: float
    year: int
    pages: int
    category: str

    def to_dict(self):
        return asdict(self)