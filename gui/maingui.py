import sys
import os
from typing import Optional, List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QTableWidget, QSpinBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6 import uic
from gui.dashboard import Dashboard
from src.graphing.graphs import plot_rrg, plot_sector_relative_strength, plot_sector_relative_strength_momentum, plot_volatility_heatmap
from config.helper import get_sector_tickers, get_sector_config

sector_config = get_sector_config()
sector_etfs = sector_config['sector_etfs']
benchmark = sector_config['benchmark']

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        
        self.dashboard = Dashboard()
        
        self.intersectorBenchmarkComboBox.addItems(sector_etfs)
        self.intersectorBenchmarkComboBox.setCurrentText(sector_etfs[0])
        
        self.collapseSidebarButton.clicked.connect(self.toggle_sidebar)
        self.dashboardButton.clicked.connect(self.show_dashboard_page)
        self.sectorButton.clicked.connect(self.show_sector_page)
        self.plotButton.clicked.connect(self.sector_page_button_click)
        self.intersectorRelativePerformanceButton.clicked.connect(self.show_intersector_performance_page)
        self.relativeSectorPerformanceButton.clicked.connect(self.show_sector_page)
        self.intersectorPlotButton.clicked.connect(self.intersector_page_button_click)
        self.setup_dashboard()
        

    def sector_page_button_click(self):
        self.render_plot_to_webview(
            webview=self.sectorRRGWebEngineView,
            lookback_widget=self.lookbackSpinBox,
            momentum_widget=self.momentumSpinBox,
            timeframe_widget=self.timeframeComboBox,
            tickers=sector_etfs,
            benchmark=benchmark,
            plot_func=plot_rrg
        )
        self.render_plot_to_webview(
            webview=self.RSWebEngineViewer,
            lookback_widget=self.lookbackSpinBox,
            timeframe_widget=self.timeframeComboBox,
            tickers=sector_etfs,
            benchmark=benchmark,
            plot_func=plot_sector_relative_strength
        )
        self.render_plot_to_webview(
            webview=self.RSMomentumWebEngineViewer,
            lookback_widget=self.lookbackSpinBox,
            timeframe_widget=self.timeframeComboBox,
            momentum_widget=self.momentumSpinBox,
            tickers=sector_etfs,
            benchmark=benchmark,
            plot_func=plot_sector_relative_strength_momentum
        )
        self.render_plot_to_webview(
            webview=self.sectorVolatilityWebEngineView,
            lookback_widget=self.lookbackSpinBox,
            timeframe_widget=self.timeframeComboBox,
            tickers=sector_etfs,
            benchmark=benchmark,
            plot_func=plot_volatility_heatmap,
            normalize=True
        )
        
    def intersector_page_button_click(self):
        current_benchmark = self.intersectorBenchmarkComboBox.currentText()
        if self.intersectorDefaultTickersCheckBox.isChecked() and current_benchmark in sector_etfs:
            topholdingcount = self.topHoldingCountSpinBox.value()
            target_list = get_sector_tickers(current_benchmark, topholdingcount)
            target_list = [t.strip() for t in target_list if t.strip()]
        else:
            target_list = []
            
        text = self.Additionaltickers.toPlainText().strip()
        if text:
            addtickers = self.Additionaltickers.toPlainText().split(",")
            target_list.extend(addtickers)
        
        params = {
            'lookback_widget': self.intersectorLookbackSpinBox,
            'timeframe_widget': self.intersectorTimeframeComboBox,
            'tickers': target_list,
        }
        self.render_plot_to_webview(**params, plot_func=plot_rrg, webview=self.intersectorRRGGraph, momentum_widget=self.intersectorMomentumSpinBox, benchmark=current_benchmark)
        self.render_plot_to_webview(**params, plot_func=plot_volatility_heatmap, webview=self.intersectorVolatilityGraph, normalize=True)
        self.render_plot_to_webview(**params, plot_func=plot_sector_relative_strength_momentum, webview=self.intersectorRSmomentumGraph, momentum_widget=self.intersectorMomentumSpinBox, benchmark=current_benchmark)
        self.render_plot_to_webview(**params, plot_func=plot_sector_relative_strength, webview=self.intersectorRSGraph, benchmark=current_benchmark)

    def toggle_sidebar(self):
        visible = self.sidebarFrame.isVisible()
        self.sidebarFrame.setVisible(not visible)
        
    def show_dashboard_page(self):
        self.mainContentStackedWidget.setCurrentWidget(self.dashboardPage)
        self.topMenuWidget.setCurrentWidget(self.dashboardMenuPage)
        
    def show_sector_page(self):
        if (self.mainContentStackedWidget.currentWidget() != self.sectorPage or self.sectorPageStackedWidget.currentWidget() != self.relativeSectorPerformancePage):
            self.mainContentStackedWidget.setCurrentWidget(self.sectorPage)
            self.sectorPageStackedWidget.setCurrentWidget(self.relativeSectorPerformancePage)
            self.topMenuWidget.setCurrentWidget(self.sectorMenuPage)
            # Generate RRG plot when sector page is shown
            self.render_plot_to_webview(
                webview=self.sectorRRGWebEngineView,
                lookback_widget=self.lookbackSpinBox,
                momentum_widget=self.momentumSpinBox,
                timeframe_widget=self.timeframeComboBox,
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_rrg
            )
            self.render_plot_to_webview(
                webview=self.RSWebEngineViewer,
                lookback_widget=self.lookbackSpinBox,
                timeframe_widget=self.timeframeComboBox,
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_sector_relative_strength
            )
            self.render_plot_to_webview(
                webview=self.RSMomentumWebEngineViewer,
                lookback_widget=self.lookbackSpinBox,
                timeframe_widget=self.timeframeComboBox,
                momentum_widget=self.momentumSpinBox,
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_sector_relative_strength_momentum
            )
            self.render_plot_to_webview(
               webview=self.sectorVolatilityWebEngineView,
                lookback_widget=self.lookbackSpinBox,
                timeframe_widget=self.timeframeComboBox,
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_volatility_heatmap,
                normalize=True
            )
        
    def show_intersector_performance_page(self):
        if (self.mainContentStackedWidget.currentWidget() != self.sectorPage or self.sectorPageStackedWidget.currentWidget() != self.intersectorPerformancePage):
            self.sectorPageStackedWidget.setCurrentWidget(self.intersectorPerformancePage)
        
        current_benchmark = self.intersectorBenchmarkComboBox.currentText()
        if self.intersectorDefaultTickersCheckBox.isChecked() and current_benchmark in sector_etfs:
            topholdingcount = self.topHoldingCountSpinBox.value()
            target_list = get_sector_tickers(current_benchmark, topholdingcount)
            target_list = [t.strip() for t in target_list if t.strip()]
        else:
            target_list = []
        
        text = self.Additionaltickers.toPlainText().strip()
        if text:
            addtickers = self.Additionaltickers.toPlainText().split(",")
            target_list.extend(addtickers)
        
        params = {
            'lookback_widget': self.intersectorLookbackSpinBox,
            'timeframe_widget': self.intersectorTimeframeComboBox,
            'tickers': target_list,
        }
        self.render_plot_to_webview(**params, plot_func=plot_rrg, webview=self.intersectorRRGGraph, momentum_widget=self.intersectorMomentumSpinBox, benchmark=current_benchmark)
        self.render_plot_to_webview(**params, plot_func=plot_volatility_heatmap, webview=self.intersectorVolatilityGraph, normalize=True)
        self.render_plot_to_webview(**params, plot_func=plot_sector_relative_strength_momentum, webview=self.intersectorRSmomentumGraph, momentum_widget=self.intersectorMomentumSpinBox, benchmark=current_benchmark)
        self.render_plot_to_webview(**params, plot_func=plot_sector_relative_strength, webview=self.intersectorRSGraph, benchmark=current_benchmark)
            

        
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

    def render_plot_to_webview(self, webview, lookback_widget, timeframe_widget, plot_func, momentum_widget: Optional[QSpinBox] = None, benchmark: Optional[str] = None, tickers: Optional[List[str]] = None, normalize: Optional[bool] = None):
        try:
            lookback = lookback_widget.value()
            timeframe = timeframe_widget.currentText()
            
            print(f"Generating plot with: lookback={lookback}, momentum={momentum_widget.value() if momentum_widget is not None else None}, timeframe={timeframe}")
            
            # Build parameters dictionary dynamically
            params = {
                'lookback_days': lookback,
                'timeframe': timeframe,
            }
            
            # Add normalize parameter only for volatility heatmap
            if normalize is not None and plot_func.__name__ == 'plot_volatility_heatmap':
                params['normalize'] = normalize
            
            # Add optional parameters only if they exist
            if tickers is not None:
                params['tickers'] = tickers
            if benchmark is not None and plot_func.__name__ != 'plot_volatility_heatmap':
                params['benchmark'] = benchmark
            if momentum_widget is not None:
                params['momentum_window'] = momentum_widget.value()
            
            # Call the function with unpacked parameters
            html_content = plot_func(**params)
            # Wrap in HTML with dark background to match theme
            html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        margin: 0;
                        background-color: #26282C; /* match Qt dark background */
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """

            print("Plot generated successfully, setting HTML...")
            webview.setHtml(html)
            print("HTML set successfully")
            
        except Exception as e:
            print(f"Error generating plot: {e}")
            # Set a simple error message in the WebEngineView
            error_html = f"""
            <html>
            <body>
                <h2>Error Generating Plot</h2>
                <p>{str(e)}</p>
                <p>Please check your data files and try again.</p>
            </body>
            </html>
            """
            webview.setHtml(error_html)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())