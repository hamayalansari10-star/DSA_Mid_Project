import csv
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QFileDialog, QHeaderView)
from PyQt6.QtCore import Qt
from src.sorting import SortingEngine

class BenchmarkDialog(QDialog):
    def __init__(self, dataset, col_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Algorithmic Performance Benchmark — [{col_name}]")
        self.resize(850, 500)
        self.dataset = dataset
        self.col_name = col_name

        self.setup_ui()
        self.run_benchmark()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(f"⚡ Running 8 Sorting Algorithms on <b>{len(self.dataset)} Records</b> (Column: <i>{self.col_name}</i>)")
        info_lbl.setStyleSheet("font-size: 14px; color: #38bdf8; padding: 5px;")
        layout.addWidget(info_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Algorithm", "Time (ms)", "Comparisons", "Swaps / Moves", "Complexity", "Stability"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #0f172a; color: #f8fafc; gridline-color: #334155; }
            QHeaderView::section { background-color: #1e293b; color: #38bdf8; font-weight: bold; }
        """)
        layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        export_btn = QPushButton("💾 Export CSV Report")
        export_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 15px;")
        export_btn.clicked.connect(self.export_csv)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #475569; color: white; padding: 8px 15px;")
        close_btn.clicked.connect(self.accept)

        btn_box.addWidget(export_btn)
        btn_box.addStretch()
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

    def run_benchmark(self):
        key_fn = lambda x: getattr(x, self.col_name.lower())
        
        # If dataset > 3000, skip slow O(n^2) algorithms to avoid UI crash
        too_large = len(self.dataset) > 3000

        algos = [
            ("Bubble Sort", SortingEngine.bubble_sort, too_large),
            ("Selection Sort", SortingEngine.selection_sort, too_large),
            ("Insertion Sort", SortingEngine.insertion_sort, too_large),
            ("Shell Sort", SortingEngine.shell_sort, False),
            ("Merge Sort", SortingEngine.merge_sort, False),
            ("Quick Sort", SortingEngine.quick_sort, False),
            ("Heap Sort", SortingEngine.heap_sort, False),
            ("TimSort", SortingEngine.tim_sort, False),
        ]

        self.results = []
        self.table.setRowCount(len(algos))

        fastest_time = float('inf')
        fastest_row = -1

        for row, (name, fn, skip) in enumerate(algos):
            if skip:
                res_tuple = (name, "Skipped (>3k)", "-", "-", "O(n²)", "Unstable")
            else:
                res = fn(self.dataset, key_fn=key_fn)
                res_tuple = (name, res.time_ms, res.comparisons, res.swaps, res.complexity, res.stability)
                if res.time_ms < fastest_time:
                    fastest_time = res.time_ms
                    fastest_row = row

            self.results.append(res_tuple)
            for col, val in enumerate(res_tuple):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

        if fastest_row != -1:
            for c in range(6):
                self.table.item(fastest_row, c).setBackground(Qt.GlobalColor.darkGreen)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Benchmark", "", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Algorithm", "Time (ms)", "Comparisons", "Swaps", "Complexity", "Stability"])
                for r in self.results:
                    writer.writerow(r)