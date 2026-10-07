import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QProgressBar, QTableView, QComboBox, QLabel,
    QRadioButton, QGroupBox, QHeaderView
)
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QFont

from src.scraper import ScraperThread
from src.sorting import SortingEngine
from src.searching import SearchEngine
from ui.benchmark_dialog import BenchmarkDialog

class PandasModel(QAbstractTableModel):
    def __init__(self, data=pd.DataFrame()):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSA Mid Project — Modern Algorithmic Data Engine")
        self.resize(1280, 850)

        self.raw_data = []
        self.displayed_df = pd.DataFrame()
        self.scraper_thread = None

        self.apply_global_styles()
        self.init_ui()

    def apply_global_styles(self):
        """ Modern Dark Theme & Premium QSS Design """
        qss = """
        QMainWindow {
            background-color: #0F172A;
        }
        QWidget {
            color: #F8FAFC;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 13px;
        }
        QGroupBox {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 10px;
            margin-top: 12px;
            font-weight: bold;
            font-size: 14px;
            color: #38BDF8;
            padding: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            background-color: #1E293B;
            border-radius: 4px;
        }
        QLineEdit, QComboBox {
            background-color: #0F172A;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 6px 12px;
            color: #F1F5F9;
            selection-background-color: #0284C7;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #38BDF8;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QPushButton {
            background-color: #2563EB;
            color: #FFFFFF;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #1D4ED8;
        }
        QPushButton:pressed {
            background-color: #1E40AF;
        }
        QPushButton#btn_pause {
            background-color: #D97706;
        }
        QPushButton#btn_pause:hover {
            background-color: #B45309;
        }
        QPushButton#btn_stop {
            background-color: #DC2626;
        }
        QPushButton#btn_stop:hover {
            background-color: #B91C1C;
        }
        QPushButton#btn_benchmark {
            background-color: #7C3AED;
        }
        QPushButton#btn_benchmark:hover {
            background-color: #6D28D9;
        }
        QPushButton#btn_reset {
            background-color: #475569;
        }
        QPushButton#btn_reset:hover {
            background-color: #334155;
        }
        QProgressBar {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 6px;
            text-align: center;
            color: #F8FAFC;
            font-weight: bold;
            height: 18px;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06B6D4, stop:1 #3B82F6);
            border-radius: 5px;
        }
        QTableView {
            background-color: #1E293B;
            border: 1px solid #334155;
            gridline-color: #334155;
            border-radius: 8px;
            selection-background-color: #0284C7;
            selection-color: #FFFFFF;
        }
        QHeaderView::section {
            background-color: #0F172A;
            color: #38BDF8;
            font-weight: bold;
            padding: 6px;
            border: 1px solid #334155;
        }
        QRadioButton {
            color: #CBD5E1;
            spacing: 6px;
        }
        QRadioButton::indicator::checked {
            background-color: #38BDF8;
            border: 2px solid #0F172A;
            border-radius: 6px;
        }
        QLabel#status_bar {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: 600;
            color: #38BDF8;
        }
        """
        self.setStyleSheet(qss)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header Title
        title_label = QLabel("⚡ DSA Mid-Term Algorithmic Workbench & Scraper")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #F8FAFC; margin-bottom: 2px;")
        main_layout.addWidget(title_label)

        # --- 1. Scraping Controls Box ---
        scrape_group = QGroupBox("1. Web Scraping Engine (Target: 15,000 Entities)")
        scrape_layout = QHBoxLayout()

        self.url_input = QLineEdit("http://books.toscrape.com")
        self.btn_start = QPushButton("▶ Start")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setObjectName("btn_pause")
        self.btn_resume = QPushButton("⏯ Resume")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("btn_stop")

        self.btn_start.clicked.connect(self.start_scraping)
        self.btn_pause.clicked.connect(self.pause_scraping)
        self.btn_resume.clicked.connect(self.resume_scraping)
        self.btn_stop.clicked.connect(self.stop_scraping)

        scrape_layout.addWidget(QLabel("Seed URL:"))
        scrape_layout.addWidget(self.url_input, stretch=2)
        scrape_layout.addWidget(self.btn_start)
        scrape_layout.addWidget(self.btn_pause)
        scrape_layout.addWidget(self.btn_resume)
        scrape_layout.addWidget(self.btn_stop)
        scrape_group.setLayout(scrape_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 15000)

        # --- 2. Searching & Filter Box ---
        search_group = QGroupBox("2. Advanced Composite Search (AND / OR / NOT Logic)")
        search_layout = QHBoxLayout()

        self.col1_combo = QComboBox()
        self.col1_combo.addItems(["Title", "Author", "Category", "ID"])
        self.type1_combo = QComboBox()
        self.type1_combo.addItems(["Contains", "Starts With", "Ends With", "Exact Match"])
        self.query1_input = QLineEdit()
        self.query1_input.setPlaceholderText("Filter 1...")

        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["NONE", "AND", "OR", "NOT"])

        self.col2_combo = QComboBox()
        self.col2_combo.addItems(["Category", "Author", "Title", "ID"])
        self.type2_combo = QComboBox()
        self.type2_combo.addItems(["Contains", "Starts With", "Ends With", "Exact Match"])
        self.query2_input = QLineEdit()
        self.query2_input.setPlaceholderText("Filter 2...")

        self.btn_search = QPushButton("🔍 Filter")
        self.btn_reset_search = QPushButton("🔄 Reset")
        self.btn_reset_search.setObjectName("btn_reset")
        self.btn_search.clicked.connect(self.execute_search)
        self.btn_reset_search.clicked.connect(self.reset_search)

        search_layout.addWidget(self.col1_combo)
        search_layout.addWidget(self.type1_combo)
        search_layout.addWidget(self.query1_input)
        search_layout.addWidget(self.operator_combo)
        search_layout.addWidget(self.col2_combo)
        search_layout.addWidget(self.type2_combo)
        search_layout.addWidget(self.query2_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_reset_search)
        search_group.setLayout(search_layout)

        # --- 3. Sorting Box ---
        sort_group = QGroupBox("3. Algorithmic Sorting Engine & Benchmark Scope")
        sort_layout = QHBoxLayout()

        self.sort_col_combo = QComboBox()
        self.sort_col_combo.addItems(["ID", "Title", "Author", "Price", "Rating", "Year", "Pages", "Category"])

        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["Bubble Sort", "Insertion Sort", "Selection Sort", "Merge Sort", "Shell Sort", "TimSort"])

        self.radio_full = QRadioButton("Full Dataset")
        self.radio_filtered = QRadioButton("Filtered Results")
        self.radio_full.setChecked(True)

        self.btn_sort = QPushButton("⇅ Sort")
        self.btn_benchmark = QPushButton("📊 Benchmark All")
        self.btn_benchmark.setObjectName("btn_benchmark")
        self.btn_sort.clicked.connect(self.execute_sort)
        self.btn_benchmark.clicked.connect(self.execute_benchmark)

        sort_layout.addWidget(QLabel("Target Column:"))
        sort_layout.addWidget(self.sort_col_combo)
        sort_layout.addWidget(QLabel("Algorithm:"))
        sort_layout.addWidget(self.algo_combo)
        sort_layout.addWidget(self.radio_full)
        sort_layout.addWidget(self.radio_filtered)
        sort_layout.addWidget(self.btn_sort)
        sort_layout.addWidget(self.btn_benchmark)
        sort_group.setLayout(sort_layout)

        # --- 4. Main Table View ---
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # --- 5. Status & Metrics Footer Bar ---
        self.status_label = QLabel("Status: Idle | Scraped Records: 0 | Time: - ms | Comparisons: - | Swaps: -")
        self.status_label.setObjectName("status_bar")

        main_layout.addWidget(scrape_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(search_group)
        main_layout.addWidget(sort_group)
        main_layout.addWidget(self.table_view)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def start_scraping(self):
        url = self.url_input.text()
        self.raw_data.clear()
        self.scraper_thread = ScraperThread(url, 15000)
        self.scraper_thread.progress_signal.connect(self.update_progress)
        self.scraper_thread.entity_scraped.connect(self.add_entity)
        self.scraper_thread.start()

    def pause_scraping(self):
        if self.scraper_thread: self.scraper_thread.pause()

    def resume_scraping(self):
        if self.scraper_thread: self.scraper_thread.resume()

    def stop_scraping(self):
        if self.scraper_thread: self.scraper_thread.stop()

    def update_progress(self, current, total):
        self.progress_bar.setValue(current)

    def add_entity(self, entity_dict):
        self.raw_data.append(entity_dict)
        if len(self.raw_data) % 500 == 0 or len(self.raw_data) == 15000:
            self.displayed_df = pd.DataFrame(self.raw_data)
            self.table_view.setModel(PandasModel(self.displayed_df))
            self.status_label.setText(f"Status: Scraping in progress... | Scraped Records: {len(self.raw_data)}")

    def execute_search(self):
        if not self.raw_data: return
        rule1 = {
            "column": self.col1_combo.currentText(),
            "type": self.type1_combo.currentText(),
            "query": self.query1_input.text()
        }
        rule2 = {
            "column": self.col2_combo.currentText(),
            "type": self.type2_combo.currentText(),
            "query": self.query2_input.text()
        }
        operator = self.operator_combo.currentText()

        filtered = SearchEngine.composite_search(self.raw_data, rule1, operator, rule2)
        self.displayed_df = pd.DataFrame(filtered)
        self.table_view.setModel(PandasModel(self.displayed_df))
        self.status_label.setText(f"Status: Filter Applied | Showing {len(filtered)} / {len(self.raw_data)} records")

    def reset_search(self):
        self.displayed_df = pd.DataFrame(self.raw_data)
        self.table_view.setModel(PandasModel(self.displayed_df))
        self.status_label.setText(f"Status: Filters Reset | Displaying all {len(self.raw_data)} records")

    def execute_sort(self):
        if self.displayed_df.empty: return
        col = self.sort_col_combo.currentText()
        algo_name = self.algo_combo.currentText()

        target_list = self.raw_data if self.radio_full.isChecked() else self.displayed_df.to_dict('records')
        key_fn = lambda x: x[col]

        if algo_name == "Bubble Sort":
            res = SortingEngine.bubble_sort(target_list[:2000], key_fn)
        elif algo_name == "Insertion Sort":
            res = SortingEngine.insertion_sort(target_list[:2000], key_fn)
        elif algo_name == "Selection Sort":
            res = SortingEngine.selection_sort(target_list[:2000], key_fn)
        elif algo_name == "Merge Sort":
            res = SortingEngine.merge_sort(target_list, key_fn)
        elif algo_name == "Shell Sort":
            res = SortingEngine.shell_sort(target_list, key_fn)
        else:
            res = SortingEngine.tim_sort(target_list, key_fn)

        self.displayed_df = pd.DataFrame(res.data)
        self.table_view.setModel(PandasModel(self.displayed_df))
        self.status_label.setText(
            f"Metrics -> Algo: {algo_name} | Time: {res.time_ms} ms | "
            f"Comparisons: {res.comparisons} | Swaps: {res.swaps} | Complexity: {res.complexity} | Stable: {res.is_stable}"
        )

    def execute_benchmark(self):
        if not self.raw_data: return
        col = self.sort_col_combo.currentText()
        target_list = self.raw_data[:1000]
        key_fn = lambda x: x[col]

        algos = [
            ("Bubble Sort", SortingEngine.bubble_sort),
            ("Insertion Sort", SortingEngine.insertion_sort),
            ("Selection Sort", SortingEngine.selection_sort),
            ("Merge Sort", SortingEngine.merge_sort),
            ("Shell Sort", SortingEngine.shell_sort),
            ("TimSort", SortingEngine.tim_sort),
        ]

        results = []
        for name, fn in algos:
            res = fn(target_list, key_fn)
            results.append({
                "algo": name,
                "time": res.time_ms,
                "comps": res.comparisons,
                "swaps": res.swaps,
                "complexity": res.complexity,
                "stable": res.is_stable
            })

        dialog = BenchmarkDialog(results)
        dialog.exec()