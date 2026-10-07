class Book:
    def __init__(self, book_id, title, author, price, rating, year, pages, category):
        self.book_id = str(book_id)      # 1. String/ID
        self.title = str(title)          # 2. String
        self.author = str(author)        # 3. String
        self.price = float(price)        # 4. Numeric (Float)
        self.rating = float(rating)      # 5. Numeric (Float)
        self.year = int(year)            # 6. Numeric (Integer)
        self.pages = int(pages)          # 7. Numeric (Integer)
        self.category = str(category)    # 8. String

    def to_dict(self):
        return {
            "ID": self.book_id,
            "Title": self.title,
            "Author": self.author,
            "Price": self.price,
            "Rating": self.rating,
            "Year": self.year,
            "Pages": self.pages,
            "Category": self.category
        }