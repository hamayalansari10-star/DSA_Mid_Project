import time
import zlib
import requests
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from src.models import Book

class ScraperThread(QThread):
    progress_signal = pyqtSignal(int, int)
    data_signal = pyqtSignal(list)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, target_url="https://openlibrary.org/search.json", query="programming", target_count=15000):
        super().__init__()
        self.target_url = target_url.strip() if target_url.strip() else "https://openlibrary.org/search.json"
        self.query_list = [query.strip()] if query.strip() else ["computer", "programming", "science", "python", "algorithms", "history"]
        self.target_count = target_count
        
        self.is_running = True
        self.is_paused = False
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.seen_books = set()

    def run(self):
        self.status_signal.emit("Connecting to Open Library API...")
        scraped_books = []
        page = 1
        current_id = 1
        query_idx = 0

        categories = ["Computer Science", "Algorithms", "Software", "Technology", "Database", "AI"]
        current_query = self.query_list[0]

        batch = []

        while self.is_running and current_id <= self.target_count:
            self.mutex.lock()
            while self.is_paused:
                self.status_signal.emit("Scraping Paused.")
                self.wait_condition.wait(self.mutex)
            self.mutex.unlock()

            if not self.is_running:
                break

            try:
                params = {"q": current_query, "page": page, "limit": 100}
                response = requests.get(self.target_url, params=params, timeout=8)
                
                if response.status_code == 429:
                    self.status_signal.emit("Rate limit encountered. Waiting 3 seconds...")
                    time.sleep(3.0)
                    continue

                if response.status_code != 200:
                    page += 1
                    time.sleep(1.0)
                    continue

                data = response.json()
                docs = data.get("docs", [])

                if not docs:
                    query_idx = (query_idx + 1) % len(categories)
                    current_query = categories[query_idx]
                    page = 1
                    time.sleep(0.5)
                    continue

                for doc in docs:
                    if not self.is_running or current_id > self.target_count:
                        break

                    title = str(doc.get("title", "Unknown Title"))[:60]
                    authors = doc.get("author_name", ["Anonymous"])
                    author = str(authors[0])[:40] if authors else "Anonymous"

                    # Deduplication
                    dedupe_key = (title.lower().strip(), author.lower().strip())
                    if dedupe_key in self.seen_books:
                        continue
                    self.seen_books.add(dedupe_key)

                    year = doc.get("first_publish_year", 2021)
                    pages = doc.get("number_of_pages_median", (zlib.crc32(title.encode()) % 400) + 120)
                    rating = round(doc.get("ratings_average", 3.0 + (zlib.crc32(author.encode()) % 20) / 10.0), 2)
                    
                    # Deterministic price calculation using zlib.crc32
                    price = round(12.0 + (zlib.crc32(f"{title}{author}".encode()) % 8800) / 100.0, 2)
                    
                    subjects = doc.get("subject", [current_query])
                    category = str(subjects[0])[:30] if subjects else current_query.title()

                    book = Book(
                        id=current_id,
                        title=title,
                        author=author,
                        price=price,
                        rating=rating,
                        year=int(year) if str(year).isdigit() else 2020,
                        pages=int(pages),
                        category=category
                    )
                    batch.append(book)
                    scraped_books.append(book)

                    current_id += 1
                    if len(batch) >= 50 or current_id > self.target_count:
                        self.data_signal.emit(batch)
                        self.progress_signal.emit(len(scraped_books), self.target_count)
                        batch = []

                page += 1
                time.sleep(0.15)

            except Exception as e:
                self.status_signal.emit(f"Network delay/retry... ({str(e)[:30]})")
                time.sleep(1.5)

        # Flush any remaining items in batch to prevent lost records
        if batch:
            self.data_signal.emit(batch)
            self.progress_signal.emit(len(scraped_books), self.target_count)

        self.status_signal.emit(f"Scraping Completed. Total Items: {len(scraped_books):,}")
        self.finished_signal.emit(len(scraped_books))

    def pause(self):
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()

    def resume(self):
        self.mutex.lock()
        self.is_paused = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def stop(self):
        self.is_running = False
        if self.is_paused:
            self.resume()
        self.wait(2000)