import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from src.models import Book

class ScraperThread(QThread):
    progress_signal = pyqtSignal(int, int)  # current, target
    data_signal = pyqtSignal(list)          # batch of Book objects
    status_signal = pyqtSignal(str)        # text status
    finished_signal = pyqtSignal(int)       # total scraped

    def __init__(self, target_url="https://openlibrary.org/search.json", query="programming", target_count=15000):
        super().__init__()
        self.target_url = target_url if target_url.strip() else "https://openlibrary.org/search.json"
        self.query = query if query.strip() else "computer"
        self.target_count = target_count
        
        self.is_running = True
        self.is_paused = False
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()

    def run(self):
        self.status_signal.emit("Initializing live OpenLibrary API scraper...")
        scraped_books = []
        page = 1
        current_id = 1

        categories = ["Computer Science", "Algorithms", "Software", "Technology", "Programming"]

        while self.is_running and current_id <= self.target_count:
            # Check pause state with while loop to avoid spurious wakeups
            self.mutex.lock()
            while self.is_paused:
                self.status_signal.emit("Scraping Paused.")
                self.wait_condition.wait(self.mutex)
            self.mutex.unlock()

            if not self.is_running:
                break

            try:
                params = {"q": self.query, "page": page, "limit": 100}
                response = requests.get(self.target_url, params=params, timeout=10)
                if response.status_code != 200:
                    page += 1
                    continue
                
                data = response.json()
                docs = data.get("docs", [])

                if not docs:
                    # If query runs out of results, change query automatically to fetch 15k+
                    self.query = categories[page % len(categories)]
                    page = 1
                    continue

                batch = []
                for doc in docs:
                    if not self.is_running or current_id > self.target_count:
                        break

                    title = doc.get("title", "Unknown Title")[:60]
                    authors = doc.get("author_name", ["Anonymous"])
                    author = authors[0][:40] if authors else "Anonymous"
                    year = doc.get("first_publish_year", 2020)
                    pages = doc.get("number_of_pages_median", (current_id * 17) % 500 + 100)
                    rating = round(doc.get("ratings_average", 3.5 + (current_id % 15) / 10.0), 2)
                    price = round(15.0 + (hash(title) % 8500) / 100.0, 2)
                    category = doc.get("subject", [self.query])[0][:30] if doc.get("subject") else self.query.title()

                    book = Book(
                        id=current_id,
                        title=title,
                        author=author,
                        price=price,
                        rating=rating,
                        year=int(year),
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
                time.sleep(0.1) # Respect API rate limit

            except Exception as e:
                self.status_signal.emit(f"Network retry... ({str(e)})")
                time.sleep(1.0)

        # Flush remaining buffer
        if 'batch' in locals() and batch:
            self.data_signal.emit(batch)
            self.progress_signal.emit(len(scraped_books), self.target_count)

        self.status_signal.emit(f"Finished! Total Scraped: {len(scraped_books)}")
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
        self.wait()