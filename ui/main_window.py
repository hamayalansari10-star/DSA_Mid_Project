import os
import csv
import pandas as pd
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, 
                             QTableView, QComboBox, QRadioButton, QGroupBox, 
                             QMessageBox, QHeaderView, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from src.scraper import ScraperThread
from src.sorting import SortingEngine
from src.searching import SearchingEngine
from src.models import Book
from ui.benchmark_dialog import BenchmarkDialog


class BookTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self._headers = ["ID", "Title", "Author", "Price ($)", "Rating ★", "Year", "Pages", "Category"]

    def rowCount(self, parent=QModelIndex()): return len(self._data)
    def columnCount(self, parent=QModelIndex()): return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            book = self._data[index.row()]
            col_attr = ["id", "title", "author", "price", "rating", "year", "pages", "category"][index.column()]
            val = getattr(book, col_attr)
            if col_attr == "price":
                return f"${val:.2f}"
            if col_attr == "rating":
                return f"{val:.1f} ★"
            return str(val)
        
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in [0, 3, 4, 5, 6]:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def update_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class SortingWorker(QThread):
    finished_signal = pyqtSignal(object)

    def __init__(self, algo_fn, data, key_fn, reverse=False):
        super().__init__()
        self.algo_fn = algo_fn
        self.data = data
        self.key_fn = key_fn
        self.reverse = reverse

    def run(self):
        res = self.algo_fn(self.data, key_fn=self.key_fn, reverse=self.reverse)
        self.finished_signal.emit(res)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Algorithmic Book Analytics Engine — Executive Suite")
        self.resize(1350, 880)

        # Data states
        self.full_data = []
        self.filtered_data = []
        self.view_data = []

        self.rules_widgets = []
        self.setup_stylesheet()
        self.setup_ui()
        self.load_persisted_csv()

    def setup_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #090d16, stop:1 #0f172a);
            }
            QWidget {
                color: #f1f5f9;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                background-color: rgba(30, 41, 59, 0.7);
                border: 1px solid #334155;
                border-radius: 10px;
                font-weight: 700;
                font-size: 13px;
                margin-top: 12px;
                padding: 14px;
                color: #38bdf8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                background-color: #0f172a;
                border: 1px solid #0284c7;
                border-radius: 5px;
                color: #38bdf8;
            }
            QLineEdit, QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                color: #f8fafc;
                selection-background-color: #0284c7;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #38bdf8;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QRadioButton {
                color: #cbd5e1;
                font-weight: 600;
                spacing: 6px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }
            
            /* Buttons Styling */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0284c7, stop:1 #0369a1);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #38bdf8, stop:1 #0284c7);
            }
            QPushButton:pressed {
                background-color: #0c4a6e;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
                border: 1px solid #334155;
            }

            /* Custom Button Colors */
            QPushButton#btn_start {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #047857);
            }
            QPushButton#btn_start:hover {
                background: #34d399;
            }
            QPushButton#btn_pause {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f59e0b, stop:1 #b45309);
            }
            QPushButton#btn_pause:hover {
                background: #fbbf24;
            }
            QPushButton#btn_resume {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #06b6d4, stop:1 #0e7490);
            }
            QPushButton#btn_resume:hover {
                background: #22d3ee;
            }
            QPushButton#btn_stop {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #b91c1c);
            }
            QPushButton#btn_stop:hover {
                background: #f87171;
            }
            QPushButton#btn_benchmark {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8b5cf6, stop:1 #6d28d9);
            }
            QPushButton#btn_benchmark:hover {
                background: #a78bfa;
            }

            /* Progress Bar */
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 6px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                background-color: #0f172a;
                height: 22px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #10b981);
                border-radius: 5px;
            }

            /* Table View */
            QTableView {
                background-color: #0b1329;
                border: 1px solid #1e293b;
                border-radius: 8px;
                gridline-color: #1e293b;
                selection-background-color: #0284c7;
                selection-color: #ffffff;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #38bdf8;
                padding: 8px;
                font-weight: 700;
                border: none;
                border-bottom: 2px solid #0284c7;
                border-right: 1px solid #334155;
            }
        """)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title Banner
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #0f172a);
                border-radius: 10px;
                border-left: 5px solid #38bdf8;
                padding: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        title_lbl = QLabel("📚 Algorithmic Book Analytics Engine")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        sub_lbl = QLabel("DSA Mid-Term Evaluation Suite • PyQt6 Multithreaded Engine")
        sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; font-weight: 500;")
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(sub_lbl)
        layout.addWidget(header_frame)

        # 1. Scraper Control Panel
        scrape_box = QGroupBox("⚡ Real-Time Multi-Threaded Scraper Engine")
        scrape_layout = QHBoxLayout(scrape_box)
        scrape_layout.setSpacing(10)

        self.url_input = QLineEdit("https://openlibrary.org/search.json")
        self.query_input = QLineEdit("computer")
        self.query_input.setPlaceholderText("Keyword (e.g. Science)")

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setObjectName("btn_start")
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setObjectName("btn_pause")
        self.resume_btn = QPushButton("⏯ Resume")
        self.resume_btn.setObjectName("btn_resume")
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setObjectName("btn_stop")

        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        self.start_btn.clicked.connect(self.start_scraping)
        self.pause_btn.clicked.connect(self.pause_scraping)
        self.resume_btn.clicked.connect(self.resume_scraping)
        self.stop_btn.clicked.connect(self.stop_scraping)

        scrape_layout.addWidget(QLabel("Target URL:"))
        scrape_layout.addWidget(self.url_input, 3)
        scrape_layout.addWidget(QLabel("Keyword:"))
        scrape_layout.addWidget(self.query_input, 2)
        scrape_layout.addWidget(self.start_btn)
        scrape_layout.addWidget(self.pause_btn)
        scrape_layout.addWidget(self.resume_btn)
        scrape_layout.addWidget(self.stop_btn)

        layout.addWidget(scrape_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("0 / 15,000 entities scraped (0%)")
        layout.addWidget(self.progress_bar)

        # 2. Controls Panel (Searching & Sorting)
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)

        # Search Panel
        search_box = QGroupBox("🔍 Search & Composite Logical Filtering")
        self.search_vbox = QVBoxLayout(search_box)
        self.search_vbox.setSpacing(8)

        algo_choice_layout = QHBoxLayout()
        algo_choice_layout.addWidget(QLabel("Mode:"))
        self.search_algo_combo = QComboBox()
        self.search_algo_combo.addItems(["Composite Rules", "Linear Search", "Binary Search (Exact)"])
        algo_choice_layout.addWidget(self.search_algo_combo, 2)

        add_rule_btn = QPushButton("+ Add Rule")
        add_rule_btn.setStyleSheet("background-color: #334155; color: #38bdf8; border: 1px solid #0284c7;")
        add_rule_btn.clicked.connect(self.add_search_rule)
        algo_choice_layout.addWidget(add_rule_btn, 1)

        self.search_vbox.addLayout(algo_choice_layout)
        self.add_search_rule()  # Initial rule row

        search_btn_layout = QHBoxLayout()
        apply_search_btn = QPushButton("🔍 Filter Results")
        apply_search_btn.clicked.connect(self.execute_search)
        reset_search_btn = QPushButton("🔄 Reset Filters")
        reset_search_btn.setStyleSheet("background-color: #475569;")
        reset_search_btn.clicked.connect(self.reset_filters)

        search_btn_layout.addWidget(apply_search_btn)
        search_btn_layout.addWidget(reset_search_btn)
        self.search_vbox.addLayout(search_btn_layout)

        ctrl_layout.addWidget(search_box, 3)

        # Sort Control Panel
        sort_box = QGroupBox("🎯 Algorithmic Sorting & Benchmarking")
        sort_vbox = QVBoxLayout(sort_box)
        sort_vbox.setSpacing(8)

        scope_layout = QHBoxLayout()
        self.radio_full = QRadioButton("Full Dataset (15k)")
        self.radio_filtered = QRadioButton("Filtered Results")
        self.radio_full.setChecked(True)
        scope_layout.addWidget(QLabel("Scope:"))
        scope_layout.addWidget(self.radio_full)
        scope_layout.addWidget(self.radio_filtered)
        sort_vbox.addLayout(scope_layout)

        algo_sel_layout = QHBoxLayout()
        self.sort_col_combo = QComboBox()
        self.sort_col_combo.addItems(["ID", "Title", "Author", "Price", "Rating", "Year", "Pages", "Category"])
        self.sort_algo_combo = QComboBox()
        self.sort_algo_combo.addItems(["Merge Sort", "Quick Sort", "Heap Sort", "TimSort", "Shell Sort", "Bubble Sort", "Selection Sort", "Insertion Sort"])

        algo_sel_layout.addWidget(self.sort_col_combo, 1)
        algo_sel_layout.addWidget(self.sort_algo_combo, 2)
        sort_vbox.addLayout(algo_sel_layout)

        sort_btn_layout = QHBoxLayout()
        exec_sort_btn = QPushButton("⚡ Sort Column")
        exec_sort_btn.clicked.connect(self.execute_sort)
        
        benchmark_btn = QPushButton("📊 Benchmark All")
        benchmark_btn.setObjectName("btn_benchmark")
        benchmark_btn.clicked.connect(self.open_benchmark)

        sort_btn_layout.addWidget(exec_sort_btn)
        sort_btn_layout.addWidget(benchmark_btn)
        sort_vbox.addLayout(sort_btn_layout)

        ctrl_layout.addWidget(sort_box, 2)
        layout.addLayout(ctrl_layout)

        # 3. Main Entity Table
        self.table_model = BookTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.horizontalHeader().sectionClicked.connect(self.handle_header_click)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_view)

        # Status Footer Bar
        self.status_lbl = QLabel("Ready • Engine initialized.")
        self.status_lbl.setStyleSheet("""
            QLabel {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                color: #38bdf8;
                font-weight: 600;
                padding: 8px 12px;
            }
        """)
        layout.addWidget(self.status_lbl)

    def add_search_rule(self):
        row_layout = QHBoxLayout()
        col_combo = QComboBox()
        col_combo.addItems(["Title", "Author", "Price", "Rating", "Year", "Pages", "Category"])
        op_combo = QComboBox()
        op_combo.addItems(["Contains", "Starts With", "Ends With", "Exact Match", "=", ">", ">=", "<", "<="])
        val_input = QLineEdit()
        val_input.setPlaceholderText("Value...")
        logic_combo = QComboBox()
        logic_combo.addItems(["AND", "OR"])

        row_layout.addWidget(col_combo)
        row_layout.addWidget(op_combo)
        row_layout.addWidget(val_input)
        row_layout.addWidget(logic_combo)

        self.search_vbox.insertLayout(self.search_vbox.count() - 1, row_layout)
        self.rules_widgets.append((col_combo, op_combo, val_input, logic_combo))

    def start_scraping(self):
        target_url = self.url_input.text()
        query = self.query_input.text()

        self.scraper_thread = ScraperThread(target_url=target_url, query=query, target_count=15000)
        self.scraper_thread.data_signal.connect(self.handle_scraped_data)
        self.scraper_thread.progress_signal.connect(self.update_progress)
        self.scraper_thread.status_signal.connect(self.status_lbl.setText)
        self.scraper_thread.finished_signal.connect(self.finish_scraping)

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.scraper_thread.start()

    def pause_scraping(self):
        self.scraper_thread.pause()
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)

    def resume_scraping(self):
        self.scraper_thread.resume()
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)

    def stop_scraping(self):
        self.scraper_thread.stop()

    def finish_scraping(self, total):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.save_to_csv()

    def handle_scraped_data(self, batch):
        self.full_data.extend(batch)
        if not self.filtered_data:
            self.view_data = list(self.full_data)
            self.table_model.update_data(self.view_data)

    def update_progress(self, current, total):
        pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"{current:,} / {total:,} entities scraped ({pct}%)")

    def execute_search(self):
        rules = []
        for col_c, op_c, val_i, log_c in self.rules_widgets:
            val = val_i.text().strip()
            if val:
                rules.append({
                    "col": col_c.currentText(),
                    "op": op_c.currentText(),
                    "val": val,
                    "logic": log_c.currentText()
                })

        if not rules:
            self.reset_filters()
            return

        res = SearchingEngine.composite_search(self.full_data, rules)
        self.filtered_data = res.data
        self.view_data = list(self.filtered_data)
        self.table_model.update_data(self.view_data)
        self.status_lbl.setText(f"🔍 Search Complete: Found {len(res.data)} matching books in {res.time_ms} ms ({res.comparisons:,} comparisons).")

    def reset_filters(self):
        self.filtered_data = []
        self.view_data = list(self.full_data)
        self.table_model.update_data(self.view_data)
        self.status_lbl.setText(f"Filters reset. Displaying full dataset ({len(self.full_data):,} records).")

    def execute_sort(self):
        col_name = self.sort_col_combo.currentText()
        algo_name = self.sort_algo_combo.currentText()
        
        target_list = self.filtered_data if (self.radio_filtered.isChecked() and self.filtered_data) else self.full_data

        if not target_list:
            QMessageBox.warning(self, "No Data", "Dataset is empty!")
            return

        algo_map = {
            "Merge Sort": SortingEngine.merge_sort,
            "Quick Sort": SortingEngine.quick_sort,
            "Heap Sort": SortingEngine.heap_sort,
            "TimSort": SortingEngine.tim_sort,
            "Shell Sort": SortingEngine.shell_sort,
            "Bubble Sort": SortingEngine.bubble_sort,
            "Selection Sort": SortingEngine.selection_sort,
            "Insertion Sort": SortingEngine.insertion_sort,
        }

        fn = algo_map[algo_name]
        key_fn = lambda x: getattr(x, col_name.lower().replace(" ($)", "").replace(" ★", ""))

        self.status_lbl.setText(f"⚡ Running {algo_name} on {len(target_list):,} records...")
        
        self.sort_worker = SortingWorker(fn, target_list, key_fn)
        self.sort_worker.finished_signal.connect(self.on_sort_finished)
        self.sort_worker.start()

    def on_sort_finished(self, res):
        self.view_data = res.data
        self.table_model.update_data(self.view_data)
        self.status_lbl.setText(f"✅ Sorted in {res.time_ms} ms | Comparisons: {res.comparisons:,} | Swaps: {res.swaps:,} | Complexity: {res.complexity} | Stability: {res.stability}")

    def handle_header_click(self, logical_index):
        headers = ["ID", "Title", "Author", "Price", "Rating", "Year", "Pages", "Category"]
        col_name = headers[logical_index]
        self.sort_col_combo.setCurrentText(col_name)
        self.execute_sort()

    def open_benchmark(self):
        target_list = self.filtered_data if (self.radio_filtered.isChecked() and self.filtered_data) else self.full_data
        col_name = self.sort_col_combo.currentText().replace(" ($)", "").replace(" ★", "")

        if not target_list:
            QMessageBox.warning(self, "No Data", "Dataset is empty!")
            return

        dlg = BenchmarkDialog(target_list, col_name, self)
        dlg.exec()

    def save_to_csv(self):
        os.makedirs("data", exist_ok=True)
        path = "data/scraped_books.csv"
        if self.full_data:
            df = pd.DataFrame([b.to_dict() for b in self.full_data])
            df.to_csv(path, index=False)

    def load_persisted_csv(self):
        path = "data/scraped_books.csv"
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                for _, row in df.iterrows():
                    book = Book(
                        id=int(row['id']),
                        title=str(row['title']),
                        author=str(row['author']),
                        price=float(row['price']),
                        rating=float(row['rating']),
                        year=int(row['year']),
                        pages=int(row['pages']),
                        category=str(row['category'])
                    )
                    self.full_data.append(book)
                self.view_data = list(self.full_data)
                self.table_model.update_data(self.view_data)
                self.status_lbl.setText(f"Loaded {len(self.full_data):,} records from CSV cache.")
            except Exception as e:
                print("CSV Load Error:", e)