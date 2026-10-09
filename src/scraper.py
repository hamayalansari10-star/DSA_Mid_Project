import time
import zlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition, QCoreApplication
from src.models import Book

class ScraperThread(QThread):
    progress_signal = pyqtSignal(int, int)
    data_signal = pyqtSignal(list)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, target_url="https://openlibrary.org/search.json", query="computer", target_count=15000):
        super().__init__()
        self.target_url = target_url.strip() if target_url.strip() else "https://openlibrary.org/search.json"
        self.user_query = query.strip() if query.strip() else "computer"
        self.target_count = target_count
        
        self.is_running = True
        self.is_paused = False
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.seen_books = set()

    def fetch_page(self, query, page):
        if not self.is_running:
            return []
        try:
            params = {"q": query, "page": page, "limit": 100}
            response = requests.get(self.target_url, params=params, timeout=3.0)
            if response.status_code == 200:
                return response.json().get("docs", [])
        except Exception:
            pass
        return []

    def run(self):
        self.status_signal.emit("⚡ High-Speed Parallel Scraper Engine Active...")
        scraped_books = []
        current_id = 1

        queries = [self.user_query, "programming", "algorithms", "science", "python", "technology", "database", "ai", "software", "data"]
        
        # Parallel worker pool for 8 concurrent requests
        with ThreadPoolExecutor(max_workers=8) as executor:
            for q in queries:
                if not self.is_running or current_id > self.target_count:
                    break

                # Submit 10 pages in parallel per query
                futures = [executor.submit(self.fetch_page, q, page) for page in range(1, 15)]

                for future in as_completed(futures):
                    self.mutex.lock()
                    while self.is_paused and self.is_running:
                        self.status_signal.emit("Scraping Paused.")
                        self.wait_condition.wait(self.mutex)
                    self.mutex.unlock()

                    if not self.is_running or current_id > self.target_count:
                        break

                    docs = future.result()
                    if not docs:
                        continue

                    batch = []
                    for doc in docs:
                        if not self.is_running or current_id > self.target_count:
                            break

                        title = str(doc.get("title", "Unknown Title"))[:60]
                        authors = doc.get("author_name", ["Anonymous"])
                        author = str(authors[0])[:40] if authors else "Anonymous"

                        dedupe_key = (title.lower().strip(), author.lower().strip())
                        if dedupe_key in self.seen_books:
                            continue
                        self.seen_books.add(dedupe_key)

                        year = doc.get("first_publish_year", 2021)
                        pages = doc.get("number_of_pages_median", (zlib.crc32(title.encode()) % 400) + 120)
                        rating = round(doc.get("ratings_average", 3.0 + (zlib.crc32(author.encode()) % 20) / 10.0), 2)
                        price = round(12.0 + (zlib.crc32(f"{title}{author}".encode()) % 8800) / 100.0, 2)
                        
                        subjects = doc.get("subject", [q])
                        category = str(subjects[0])[:30] if subjects else q.title()

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

                    if batch:
                        self.data_signal.emit(batch)
                        self.progress_signal.emit(len(scraped_books), self.target_count)
                        QCoreApplication.processEvents()

        self.status_signal.emit(f"🚀 Speed Scraping Finished. Total: {len(scraped_books):,} books.")
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
        self.wait(300)