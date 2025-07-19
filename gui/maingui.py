import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QTableWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6 import uic
from gui.dashboard import Dashboard



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        
        self.dashboard = Dashboard()
        self.collapseSidebarButton.clicked.connect(self.toggle_sidebar)
        
        self.setup_dashboard()

    def toggle_sidebar(self):
        visible = self.sidebarFrame.isVisible()
        self.sidebarFrame.setVisible(not visible)
        
    def setup_dashboard(self):
        table_data, headers, status = self.dashboard.get_table_data()
        color_data = self.dashboard.get_color_data()
        
        table_widget = self.dashboardTableWidget
        
        table_widget.setRowCount(len(table_data))
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                
                # Right-align numeric columns
                if col_idx in [2, 3, 4, 5, 6]:  # Last Close, Prev Close, Change ($), Change (%), Volume
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Apply colors
                ticker = row_data[0]  # First column is ticker
                if ticker in color_data:
                    color_info = color_data[ticker]
                    
                    # Color the change columns
                    if col_idx == 4:  # Change ($)
                        if color_info['dollar_color'] == 'green':
                            item.setForeground(QColor(0, 128, 0))
                        elif color_info['dollar_color'] == 'red':
                            item.setForeground(QColor(255, 0, 0))
                    
                    elif col_idx == 5:  # Change (%)
                        if color_info['percent_color'] == 'green':
                            item.setForeground(QColor(0, 128, 0))
                        elif color_info['percent_color'] == 'red':
                            item.setForeground(QColor(255, 0, 0))
                    
                    # Special formatting for SPY
                    if color_info['is_spy']:
                        item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                        if color_info['row_background'] == 'lightblue':
                            item.setBackground(QColor(240, 248, 255))
                
                table_widget.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        table_widget.resizeColumnsToContents()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
