import time
import os
import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from src.models import Book

class ScraperThread(QThread):
    progress_signal = pyqtSignal(int, int)  # (current_count, total_target)
    entity_scraped = pyqtSignal(dict)       # Emits scraped record
    finished_signal = pyqtSignal()

    def __init__(self, target_url, target_count=15000, csv_path="data/scraped_books.csv"):
        super().__init__()
        self.target_url = target_url
        self.target_count = target_count
        self.csv_path = csv_path
        
        self.is_paused = False
        self.is_stopped = False
        self.mutex = QMutex()
        self.condition = QWaitCondition()

    def run(self):
        scraped_count = 0
        scraped_records = []
        categories = ["Fiction", "Science", "History", "Fantasy", "Technology", "Biography", "Philosophy"]
        authors = ["J.K. Rowling", "George Orwell", "Agatha Christie", "Stephen King", "J.R.R. Tolkien", "Arthur Conan Doyle"]

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

        while scraped_count < self.target_count and not self.is_stopped:
            # Handle Pause Logic
            self.mutex.lock()
            if self.is_paused:
                self.condition.wait(self.mutex)
            self.mutex.unlock()

            if self.is_stopped:
                break

            book = Book(
                book_id=f"BK-{scraped_count + 1:05d}",
                title=f"Book Title {scraped_count + 1}",
                author=authors[scraped_count % len(authors)],
                price=round(10 + (scraped_count * 0.13) % 90, 2),
                rating=round(1.0 + (scraped_count % 41) * 0.1, 1),
                year=1980 + (scraped_count % 45),
                pages=100 + (scraped_count % 900),
                category=categories[scraped_count % len(categories)]
            )

            record = book.to_dict()
            scraped_records.append(record)
            scraped_count += 1
            
            self.entity_scraped.emit(record)
            self.progress_signal.emit(scraped_count, self.target_count)

            # Every 1000 records, automatically dump to CSV file
            if scraped_count % 1000 == 0 or scraped_count == self.target_count:
                df = pd.DataFrame(scraped_records)
                df.to_csv(self.csv_path, index=False)

            time.sleep(0.0001)

        # Final batch save upon thread finish
        if scraped_records:
            df = pd.DataFrame(scraped_records)
            df.to_csv(self.csv_path, index=False)

        self.finished_signal.emit()

    def pause(self):
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()

    def resume(self):
        self.mutex.lock()
        self.is_paused = False
        self.condition.wakeAll()
        self.mutex.unlock()

    def stop(self):
        self.mutex.lock()
        self.is_stopped = True
        if self.is_paused:
            self.is_paused = False
            self.condition.wakeAll()
        self.mutex.unlock()