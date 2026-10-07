from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt6.QtGui import QFont

class BenchmarkDialog(QDialog):
    def __init__(self, results_table):
        super().__init__()
        self.setWindowTitle("Sorting Algorithms Benchmark (Side-by-Side Comparison)")
        self.resize(750, 400)
        
        # Dark Theme Styling for Dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #0F172A;
            }
            QLabel {
                color: #F8FAFC;
                font-weight: bold;
                font-size: 15px;
            }
            QTableWidget {
                background-color: #1E293B;
                border: 1px solid #334155;
                gridline-color: #334155;
                border-radius: 8px;
                color: #F8FAFC;
                selection-background-color: #0284C7;
            }
            QHeaderView::section {
                background-color: #0F172A;
                color: #38BDF8;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #334155;
            }
        """)

        layout = QVBoxLayout()
        
        title_label = QLabel("📊 Comparative Performance Benchmark")
        layout.addWidget(title_label)

        self.table = QTableWidget()
        self.table.setRowCount(len(results_table))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Algorithm", "Time (ms)", "Comparisons", "Swaps", "Complexity", "Stable"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for row_idx, res in enumerate(results_table):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(res["algo"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(res["time"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(res["comps"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(res["swaps"])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(res["complexity"])))
            self.table.setItem(row_idx, 5, QTableWidgetItem("Yes" if res["stable"] else "No"))

        layout.addWidget(self.table)
        self.setLayout(layout)