import os
import pandas as pd
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, 
                             QTableView, QComboBox, QRadioButton, QGroupBox, 
                             QMessageBox, QHeaderView, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, pyqtSignal

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
            if col_attr == "price": return f"${val:.2f}"
            if col_attr == "rating": return f"{val:.1f} ★"
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
        self.resize(1380, 900)

        self.full_data = []
        self.filtered_data = []
        self.view_data = []
        self.rules_widgets = []
        self.sort_directions = {} # Header toggle tracking

        self.setup_stylesheet()
        self.setup_ui()
        self.load_persisted_csv()

    def setup_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #090d16; }
            QWidget { color: #f1f5f9; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
            QGroupBox { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; font-weight: bold; margin-top: 10px; padding: 10px; color: #38bdf8; }
            QLineEdit, QComboBox { background-color: #0f172a; border: 1px solid #334155; border-radius: 5px; padding: 6px; color: #f8fafc; }
            QPushButton { background-color: #0284c7; color: white; border: none; border-radius: 5px; padding: 7px 14px; font-weight: bold; }
            QPushButton:hover { background-color: #0369a1; }
            QPushButton:disabled { background-color: #334155; color: #64748b; }
            QProgressBar { border: 1px solid #334155; border-radius: 5px; text-align: center; color: white; background-color: #0f172a; }
            QProgressBar::chunk { background-color: #10b981; }
            QTableView { background-color: #0b1329; gridline-color: #1e293b; selection-background-color: #0284c7; }
            QHeaderView::section { background-color: #1e293b; color: #38bdf8; padding: 6px; font-weight: bold; border-bottom: 2px solid #0284c7; }
        """)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Clean Title Bar
        header = QFrame()
        header.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 8px;")
        h_layout = QHBoxLayout(header)
        h_title = QLabel("📚 Algorithmic Book Analytics Engine")
        h_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8;")
        h_sub = QLabel("OpenLibrary API Scraper & Real-Time Data Analytics Engine")
        h_sub.setStyleSheet("color: #94a3b8; font-size: 12px;")
        h_layout.addWidget(h_title)
        h_layout.addStretch()
        h_layout.addWidget(h_sub)
        layout.addWidget(header)

        # 1. Scraper Control Panel
        scrape_box = QGroupBox("🚀 Live Multi-Threaded Scraper")
        s_layout = QHBoxLayout(scrape_box)

        self.url_input = QLineEdit("https://openlibrary.org/search.json")
        self.query_input = QLineEdit("computer")

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("background-color: #10b981;")
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet("background-color: #f59e0b;")
        self.resume_btn = QPushButton("⏯ Resume")
        self.resume_btn.setStyleSheet("background-color: #06b6d4;")
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet("background-color: #ef4444;")

        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        self.start_btn.clicked.connect(self.start_scraping)
        self.pause_btn.clicked.connect(self.pause_scraping)
        self.resume_btn.clicked.connect(self.resume_scraping)
        self.stop_btn.clicked.connect(self.stop_scraping)

        s_layout.addWidget(QLabel("URL:"))
        s_layout.addWidget(self.url_input, 2)
        s_layout.addWidget(QLabel("Keyword:"))
        s_layout.addWidget(self.query_input, 1)
        s_layout.addWidget(self.start_btn)
        s_layout.addWidget(self.pause_btn)
        s_layout.addWidget(self.resume_btn)
        s_layout.addWidget(self.stop_btn)

        layout.addWidget(scrape_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("0 / 15,000 entities scraped (0%)")
        layout.addWidget(self.progress_bar)

        # 2. Controls Panel (Searching & Sorting)
        ctrl_layout = QHBoxLayout()

        # Search Panel
        search_box = QGroupBox("🔍 Search & Composite Logic Filters")
        self.search_vbox = QVBoxLayout(search_box)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems(["Composite Rules", "Linear Search", "Binary Search (Exact)"])
        mode_layout.addWidget(self.search_mode_combo)

        add_rule_btn = QPushButton("+ Rule")
        add_rule_btn.clicked.connect(self.add_search_rule)
        mode_layout.addWidget(add_rule_btn)

        self.search_vbox.addLayout(mode_layout)
        self.add_search_rule()

        s_btn_layout = QHBoxLayout()
        apply_search_btn = QPushButton("🔍 Filter")
        apply_search_btn.clicked.connect(self.execute_search)
        reset_search_btn = QPushButton("🔄 Reset")
        reset_search_btn.setStyleSheet("background-color: #475569;")
        reset_search_btn.clicked.connect(self.reset_filters)

        s_btn_layout.addWidget(apply_search_btn)
        s_btn_layout.addWidget(reset_search_btn)
        self.search_vbox.addLayout(s_btn_layout)

        ctrl_layout.addWidget(search_box, 2)

        # Sort Control Panel
        sort_box = QGroupBox("🎯 Algorithmic Sorting Engine")
        sort_vbox = QVBoxLayout(sort_box)

        scope_layout = QHBoxLayout()
        self.radio_full = QRadioButton("Full Dataset")
        self.radio_filtered = QRadioButton("Filtered")
        self.radio_full.setChecked(True)
        scope_layout.addWidget(QLabel("Scope:"))
        scope_layout.addWidget(self.radio_full)
        scope_layout.addWidget(self.radio_filtered)
        sort_vbox.addLayout(scope_layout)

        algo_sel_layout = QHBoxLayout()
        self.sort_col_combo = QComboBox()
        self.sort_col_combo.addItems(["ID", "Title", "Author", "Price", "Rating", "Year", "Pages", "Category"])
        self.sort_algo_combo = QComboBox()
        
        # Algorithmic Badges in Dropdown
        self.sort_algo_combo.addItems([
            "Merge Sort [O(n log n) | Stable]",
            "Quick Sort [O(n log n) | Unstable]",
            "Heap Sort [O(n log n) | Unstable]",
            "TimSort [O(n log n) | Stable]",
            "Shell Sort [O(n²) | Unstable]",
            "Bubble Sort [O(n²) | Stable]",
            "Selection Sort [O(n²) | Unstable]",
            "Insertion Sort [O(n²) | Stable]"
        ])

        algo_sel_layout.addWidget(self.sort_col_combo)
        algo_sel_layout.addWidget(self.sort_algo_combo)
        sort_vbox.addLayout(algo_sel_layout)

        sort_btn_layout = QHBoxLayout()
        exec_sort_btn = QPushButton("⚡ Sort")
        exec_sort_btn.clicked.connect(self.execute_sort)

        # Multi-Level Sort Button
        multi_sort_btn = QPushButton("🔀 Multi-Level Sort")
        multi_sort_btn.setStyleSheet("background-color: #0e7490;")
        multi_sort_btn.clicked.connect(self.execute_multi_sort)

        benchmark_btn = QPushButton("📊 Benchmark All")
        benchmark_btn.setStyleSheet("background-color: #8b5cf6;")
        benchmark_btn.clicked.connect(self.open_benchmark)

        sort_btn_layout.addWidget(exec_sort_btn)
        sort_btn_layout.addWidget(multi_sort_btn)
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
        self.status_lbl = QLabel("System Ready.")
        self.status_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_lbl)

    def add_search_rule(self):
        row = QHBoxLayout()
        col_combo = QComboBox()
        col_combo.addItems(["Title", "Author", "Price", "Rating", "Year", "Pages", "Category", "ID"])
        
        op_combo = QComboBox()
        op_combo.addItems(["Contains", "Starts With", "Ends With", "Exact Match", "=", ">", ">=", "<", "<="])
        
        val_input = QLineEdit()
        val_input.setPlaceholderText("Val...")

        not_chk = QCheckBox("NOT")
        logic_combo = QComboBox()
        logic_combo.addItems(["AND", "OR"])

        del_btn = QPushButton("❌")
        del_btn.setStyleSheet("background-color: #ef4444; padding: 2px 6px;")

        row.addWidget(col_combo)
        row.addWidget(op_combo)
        row.addWidget(val_input)
        row.addWidget(not_chk)
        row.addWidget(logic_combo)
        row.addWidget(del_btn)

        self.search_vbox.insertLayout(self.search_vbox.count() - 1, row)
        rule_tuple = (col_combo, op_combo, val_input, not_chk, logic_combo, row)
        self.rules_widgets.append(rule_tuple)

        del_btn.clicked.connect(lambda: self.remove_search_rule(rule_tuple))

    def remove_search_rule(self, rule_tuple):
        if len(self.rules_widgets) > 1:
            row_layout = rule_tuple[5]
            while row_layout.count():
                item = row_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.rules_widgets.remove(rule_tuple)

    def start_scraping(self):
        if self.full_data and len(self.full_data) > 0:
            reply = QMessageBox.question(self, "Clear Dataset?", "Start scraping anew and clear existing records?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.full_data = []
                self.filtered_data = []
                self.view_data = []
                self.table_model.update_data([])

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
        pct = int((current / total) * 100) if total else 0
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"{current:,} / {total:,} entities scraped ({pct}%)")

    def execute_search(self):
        mode = self.search_mode_combo.currentText()
        target_list = self.full_data

        if mode == "Linear Search":
            rule = self.rules_widgets[0]
            col, op, val_in = rule[0].currentText(), rule[1].currentText(), rule[2].text()
            res = SearchingEngine.linear_search(target_list, col, op, val_in)
        elif mode == "Binary Search (Exact)":
            rule = self.rules_widgets[0]
            col, val_in = rule[0].currentText(), rule[2].text()
            res = SearchingEngine.binary_search(target_list, col, val_in)
        else:
            rules = []
            for col_c, op_c, val_i, not_chk, log_c, _ in self.rules_widgets:
                val = val_i.text().strip()
                if val:
                    rules.append({
                        "col": col_c.currentText(),
                        "op": op_c.currentText(),
                        "val": val,
                        "not": not_chk.isChecked(),
                        "logic": log_c.currentText()
                    })
            if not rules:
                self.reset_filters()
                return
            res = SearchingEngine.composite_search(target_list, rules)

        self.filtered_data = res.data
        self.view_data = list(self.filtered_data)
        self.table_model.update_data(self.view_data)
        self.status_lbl.setText(f"🔍 Search Mode [{mode}] Found {len(res.data)} items in {res.time_ms} ms ({res.comparisons:,} comps).")

    def reset_filters(self):
        self.filtered_data = []
        self.view_data = list(self.full_data)
        self.table_model.update_data(self.view_data)
        self.status_lbl.setText(f"Filters reset. Showing {len(self.full_data):,} records.")

    def execute_sort(self, reverse=False):
        col_name = self.sort_col_combo.currentText()
        algo_text = self.sort_algo_combo.currentText()
        algo_name = algo_text.split(" [")[0]

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
        clean_col = col_name.replace(" ($)", "").replace(" ★", "")
        key_fn = lambda x: getattr(x, clean_col.lower())

        self.status_lbl.setText(f"⚡ Sorting {len(target_list):,} records using {algo_name}...")
        
        self.sort_worker = SortingWorker(fn, target_list, key_fn, reverse=reverse)
        self.sort_worker.finished_signal.connect(self.on_sort_finished)
        self.sort_worker.start()

    def execute_multi_sort(self):
        target_list = self.filtered_data if (self.radio_filtered.isChecked() and self.filtered_data) else self.full_data
        if not target_list:
            QMessageBox.warning(self, "No Data", "Dataset is empty!")
            return

        rules = [("category", False), ("rating", True), ("price", False)]
        sorted_list = SortingEngine.multi_level_sort(target_list, rules)
        self.view_data = sorted_list
        self.table_model.update_data(self.view_data)
        self.status_lbl.setText("🔀 Multi-Level Sort Applied: [Category Asc -> Rating Desc -> Price Asc]")

    def on_sort_finished(self, res):
        self.view_data = res.data
        self.table_model.update_data(self.view_data)
        self.status_lbl.setText(f"✅ Sorted in {res.time_ms} ms | Comps: {res.comparisons:,} | Swaps: {res.swaps:,} | {res.complexity} | {res.stability}")

    def handle_header_click(self, logical_index):
        headers = ["ID", "Title", "Author", "Price", "Rating", "Year", "Pages", "Category"]
        col_name = headers[logical_index]
        
        rev = self.sort_directions.get(col_name, False)
        rev = not rev
        self.sort_directions[col_name] = rev

        self.sort_col_combo.setCurrentText(col_name)
        self.execute_sort(reverse=rev)

    def open_benchmark(self):
        target_list = self.filtered_data if (self.radio_filtered.isChecked() and self.filtered_data) else self.full_data
        col_name = self.sort_col_combo.currentText()

        if not target_list:
            QMessageBox.warning(self, "No Data", "Dataset is empty!")
            return

        dlg = BenchmarkDialog(target_list, col_name, self)
        dlg.exec()

    def save_to_csv(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        path = os.path.join(data_dir, "scraped_books.csv")

        if self.full_data:
            df = pd.DataFrame([b.to_dict() for b in self.full_data])
            df.to_csv(path, index=False)

    def load_persisted_csv(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "data", "scraped_books.csv")

        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                self.full_data = []
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
                self.status_lbl.setText(f"Loaded {len(self.full_data):,} records from CSV.")
            except Exception as e:
                self.status_lbl.setText(f"CSV Schema Reset: {str(e)}")

    def closeEvent(self, event):
        if hasattr(self, 'scraper_thread') and self.scraper_thread.isRunning():
            self.scraper_thread.stop()
        event.accept()