import sys
import os
from typing import Optional, List
import pandas as pd
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
from src.process.relative_strength import get_relative_strength
from src.process.rs_momentum import get_relative_strength_momentum
from src.process.volatility import compute_volatility_for_timeframe

sector_config = get_sector_config()
sector_etfs = sector_config['sector_etfs']
benchmark = sector_config['benchmark']
alletfs = [benchmark] + sector_etfs

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        
        self.dashboard = Dashboard()

        self.intersectorBenchmarkComboBox.addItems(alletfs)
        self.comparisonBenchmarkComboBox.addItems(alletfs)
        self.comparisonBenchmarkComboBox.setCurrentText('XLK')
        self.intersectorBenchmarkComboBox.setCurrentText('XLK')
        
        self.sectorsChoice.toggled.connect(self.handle_intersector_buttongroup)
        self.intersectorChoice.toggled.connect(self.handle_intersector_buttongroup)
        self.RRGChoice.toggled.connect(self.handle_intersector_buttongroup)
        self.RSMomentumChoice.toggled.connect(self.handle_intersector_buttongroup)
        self.RSRatioChoice.toggled.connect(self.handle_intersector_buttongroup)
        
        self.comparisonBenchmarkComboBox.currentIndexChanged.connect(self.toggle_target_widget_combobox)
        self.intersectorBenchmarkComboBox.currentIndexChanged.connect(self.toggle_target_widget_combobox)
        self.intersectorDefaultTickersCheckBox.stateChanged.connect(self.toggle_target_widget_checkbox)
        
        self.collapseSidebarButton.clicked.connect(self.toggle_sidebar)
        self.dashboardButton.clicked.connect(self.show_dashboard_page)
        self.sectorButton.clicked.connect(self.show_sector_page)
        self.plotButton.clicked.connect(self.sector_page_button_click)
        self.intersectorRelativePerformanceButton.clicked.connect(self.show_intersector_performance_page)
        self.relativeSectorPerformanceButton.clicked.connect(self.show_sector_page)
        self.intersectorPlotButton.clicked.connect(self.intersector_page_button_click)
        self.timeframeComparisonButton.clicked.connect(self.show_timeframe_comparison_page)
        self.timeframeComparisonPlotButton.clicked.connect(self.timeframe_comparison_page_button_click)
        
        self.setup_dashboard()
    
    def handle_intersector_buttongroup(self):
        if self.sectorsChoice.isChecked():
            self.comparisonBenchmarkLabel.setDisabled(True)
            self.comparisonBenchmarkComboBox.setDisabled(True)
            self.comparisonIncludeDefaultCheck.setDisabled(True)
            self.comparisonNumHoldingsLabel.setDisabled(True)
            self.comparisonNumHoldingsSpinBox.setDisabled(True)
            self.comparisonCustomTickersLabel.setDisabled(True)
            self.comparisonCustomTickers.setDisabled(True)
        if self.intersectorChoice.isChecked():
            self.comparisonBenchmarkLabel.setDisabled(False)
            self.comparisonBenchmarkComboBox.setDisabled(False)
            self.comparisonIncludeDefaultCheck.setDisabled(False)
            self.comparisonNumHoldingsLabel.setDisabled(False)
            self.comparisonNumHoldingsSpinBox.setDisabled(False)
            self.comparisonCustomTickersLabel.setDisabled(False)
            self.comparisonCustomTickers.setDisabled(False)
        if self.RRGChoice.isChecked():
            self.comparisonWindowLabel.setDisabled(False)
            self.comparisonWindowSpinBox.setDisabled(False)
        if self.RSMomentumChoice.isChecked():
            self.comparisonWindowLabel.setDisabled(True)
            self.comparisonWindowSpinBox.setDisabled(True)
        if self.RSRatioChoice.isChecked():
            self.comparisonWindowLabel.setDisabled(False)
            self.comparisonWindowSpinBox.setDisabled(False)
    
    def toggle_target_widget_combobox(self, state):
        sender = self.sender()
        currenttext = sender.currentText()
        is_spy = (currenttext.upper() == "SPY")
        
        if (sender == self.intersectorBenchmarkComboBox):
            if is_spy:
                self.intersectorDefaultTickersCheckBox.setDisabled(True)
                self.numtopholdingLabel.setDisabled(True)
                self.topHoldingCountSpinBox.setDisabled(True)
            else:
                self.intersectorDefaultTickersCheckBox.setDisabled(False)
                self.numtopholdingLabel.setDisabled(False)
                self.topHoldingCountSpinBox.setDisabled(False)
        
        if (sender == self.comparisonBenchmarkComboBox):
            if is_spy:
                self.comparisonIncludeDefaultCheck.setDisabled(True)
                self.comparisonNumHoldingsSpinBox.setDisabled(True)
                self.comparisonNumHoldingsLabel.setDisabled(True)
            else:
                self.comparisonIncludeDefaultCheck.setDisabled(False)
                self.comparisonNumHoldingsSpinBox.setDisabled(False)
                self.comparisonNumHoldingsLabel.setDisabled(False)
                
    def toggle_target_widget_checkbox(self, state):
        sender = self.sender()
        is_checked = (state == Qt.CheckState.Checked)
        
        if sender == self.intersectorDefaultTickersCheckBox:
            self.numtopholdingLabel.setDisabled(is_checked)
            self.topHoldingCountSpinBox.setDisabled(is_checked)
        
    def show_timeframe_comparison_page(self):
        if (self.mainContentStackedWidget.currentWidget() != self.sectorPage or self.sectorPageStackedWidget.currentWidget() != self.timeframeComparisonPage):
            self.sectorPageStackedWidget.setCurrentWidget(self.timeframeComparisonPage)

        current_benchmark = self.comparisonBenchmarkComboBox.currentText()
        if self.comparisonIncludeDefaultCheck.isChecked() and current_benchmark in sector_etfs:
            topholdingcount = self.comparisonNumHoldingsSpinBox.value()
            target_list = get_sector_tickers(current_benchmark, topholdingcount)
        else:
            target_list = []

        text = self.comparisonCustomTickers.toPlainText()
        if text:
            tickers = [t.strip().upper() for t in text.split(",") if t.strip()]
            target_list.extend(tickers)
        
        params = {
            'lookback_widget': self.comparisonLookbackSpinBox,
            'tickers': target_list,
            'momentum_widget': self.comparisonWindowSpinBox,
            'benchmark': current_benchmark
        }
        
        if self.RRGChoice.isChecked():
            plottype = plot_rrg
        elif self.RSMomentumChoice.isChecked():
            plottype = plot_sector_relative_strength_momentum
        elif self.RSRatioChoice.isChecked():
            plottype = plot_sector_relative_strength
                    
        self.render_plot_to_webview(**params, plot_func=plottype, webview=self.comparisonDailyGraph, timeframe_widget="daily")
        self.render_plot_to_webview(**params, plot_func=plottype, webview=self.comparisonWeeklyGraph, timeframe_widget="weekly")
        self.render_plot_to_webview(**params, plot_func=plottype, webview=self.comparisonMonthlyGraph, timeframe_widget="monthly")
        tables_dict = {
            'daily': self.dailyComparisonTable,
            'weekly': self.weeklyComparisonTable,
            'monthly': self.monthlyComparisonTable
        }
        self.timeframe_comparison_tables(tickers=target_list, benchmark=current_benchmark, lookback=self.comparisonLookbackSpinBox.value(), momentum_window=self.comparisonWindowSpinBox.value(), tables_dict=tables_dict)
            
    
    def timeframe_comparison_page_button_click(self):
        if (self.mainContentStackedWidget.currentWidget() != self.sectorPage or self.sectorPageStackedWidget.currentWidget() != self.timeframeComparisonPage):
            self.sectorPageStackedWidget.setCurrentWidget(self.timeframeComparisonPage)

        current_benchmark = self.comparisonBenchmarkComboBox.currentText()
        if self.comparisonIncludeDefaultCheck.isChecked() and current_benchmark in sector_etfs:
            topholdingcount = self.comparisonNumHoldingsSpinBox.value()
            target_list = get_sector_tickers(current_benchmark, topholdingcount)
        else:
            target_list = []

        text = self.comparisonCustomTickers.toPlainText()
        if text:
            tickers = [t.strip().upper() for t in text.split(",") if t.strip()]
            target_list.extend(tickers)
        
        params = {
            'lookback_widget': self.comparisonLookbackSpinBox,
            'tickers': target_list,
            'benchmark': current_benchmark
        }
        
        if self.RRGChoice.isChecked():
            plottype = plot_rrg
            params['momentum_widget'] = self.comparisonWindowSpinBox
        elif self.RSMomentumChoice.isChecked():
            plottype = plot_sector_relative_strength_momentum
            params['momentum_widget'] = self.comparisonWindowSpinBox
        elif self.RSRatioChoice.isChecked():
            plottype = plot_sector_relative_strength
                    
        self.render_plot_to_webview(**params, plot_func=plottype, webview=self.comparisonDailyGraph, timeframe_widget="daily")
        self.render_plot_to_webview(**params, plot_func=plottype, webview=self.comparisonWeeklyGraph, timeframe_widget="weekly")
        self.render_plot_to_webview(**params, plot_func=plottype, webview=self.comparisonMonthlyGraph, timeframe_widget="monthly")
        
        tables_dict = {
            'daily': self.dailyComparisonTable,
            'weekly': self.weeklyComparisonTable,
            'monthly': self.monthlyComparisonTable
        }
        self.timeframe_comparison_tables(tickers=target_list, benchmark=current_benchmark, lookback=self.comparisonLookbackSpinBox.value(), momentum_window=self.comparisonWindowSpinBox.value(), tables_dict=tables_dict)
        
    def timeframe_comparison_tables(self, tickers, benchmark, lookback, momentum_window, tables_dict):
        metrics = ['Volatility', 'RS', 'Momentum']
        
        for tf, table in tables_dict.items():
            rows = []
            for ticker in tickers:
                try:
                    vol = compute_volatility_for_timeframe(ticker, timeframe=tf, window=lookback, raw_volatility=True)
                    rs_raw = get_relative_strength(target=ticker, benchmark=benchmark, timeframe=tf, lookback_days=lookback)
                    rs_series = pd.Series(rs_raw) if isinstance(rs_raw, list) else rs_raw
                    rs = rs_series.iloc[-1]
                    mom_raw = get_relative_strength_momentum(target=ticker, benchmark=benchmark, timeframe=tf, lookback_days=lookback, return_series=True)
                    mom_series = pd.Series(mom_raw) if isinstance(mom_raw, list) else mom_raw
                    mom = mom_series.iloc[-1]
                    rows.append((ticker, vol, rs, mom))
                except Exception as e:
                    print(f"Error for {ticker} @ {tf}: {e}")
            
            self.fill_table_with_rows(table, rows, metrics)


    def sector_page_button_click(self):
        self.render_plot_to_webview(
            webview=self.sectorRRGWebEngineView,
            lookback_widget=self.lookbackSpinBox,
            momentum_widget=self.momentumSpinBox,
            timeframe_widget=self.timeframeComboBox.currentText(),
            tickers=sector_etfs,
            benchmark=benchmark,
            plot_func=plot_rrg
        )
        self.render_plot_to_webview(
            webview=self.RSWebEngineViewer,
            lookback_widget=self.lookbackSpinBox,
            timeframe_widget=self.timeframeComboBox.currentText(),
            tickers=sector_etfs,
            benchmark=benchmark,
            plot_func=plot_sector_relative_strength
        )
        self.render_plot_to_webview(
            webview=self.RSMomentumWebEngineViewer,
            lookback_widget=self.lookbackSpinBox,
            timeframe_widget=self.timeframeComboBox.currentText(),
            momentum_widget=self.momentumSpinBox,
            tickers=sector_etfs,
            benchmark=benchmark,
            plot_func=plot_sector_relative_strength_momentum
        )
        self.render_plot_to_webview(
            webview=self.sectorVolatilityWebEngineView,
            lookback_widget=self.lookbackSpinBox,
            timeframe_widget=self.timeframeComboBox.currentText(),
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
        else:
            target_list = []
        
        text = self.Additionaltickers.toPlainText()
        if text:
            tickers = [t.strip().upper() for t in text.split(",") if t.strip()]
            target_list.extend(tickers)
        
        params = {
            'lookback_widget': self.intersectorLookbackSpinBox,
            'timeframe_widget': self.intersectorTimeframeComboBox.currentText(),
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
                timeframe_widget=self.timeframeComboBox.currentText(),
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_rrg
            )
            self.render_plot_to_webview(
                webview=self.RSWebEngineViewer,
                lookback_widget=self.lookbackSpinBox,
                timeframe_widget=self.timeframeComboBox.currentText(),
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_sector_relative_strength
            )
            self.render_plot_to_webview(
                webview=self.RSMomentumWebEngineViewer,
                lookback_widget=self.lookbackSpinBox,
                timeframe_widget=self.timeframeComboBox.currentText(),
                momentum_widget=self.momentumSpinBox,
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_sector_relative_strength_momentum
            )
            self.render_plot_to_webview(
               webview=self.sectorVolatilityWebEngineView,
                lookback_widget=self.lookbackSpinBox,
                timeframe_widget=self.timeframeComboBox.currentText(),
                tickers=sector_etfs,
                benchmark=benchmark,
                plot_func=plot_volatility_heatmap,
                normalize=True
            )
        
    def show_intersector_performance_page(self):
        self.sectorPageStackedWidget.setCurrentWidget(self.intersectorPerformancePage)
        
        current_benchmark = self.intersectorBenchmarkComboBox.currentText()
        if self.intersectorDefaultTickersCheckBox.isChecked() and current_benchmark in sector_etfs:
            topholdingcount = self.topHoldingCountSpinBox.value()
            target_list = get_sector_tickers(current_benchmark, topholdingcount)
        else:
            target_list = []
        
        text = self.Additionaltickers.toPlainText()
        if text:
            tickers = [t.strip().upper() for t in text.split(",") if t.strip()]
            target_list.extend(tickers)
        
        params = {
            'lookback_widget': self.intersectorLookbackSpinBox,
            'timeframe_widget': self.intersectorTimeframeComboBox.currentText(),
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
                    cleaned = (
                        cell_data.replace("$", "")
                        .replace("%", "")
                        .replace(",", "")
                        .strip()
                    )
                    sortableval = float(cleaned)
                    item.setData(Qt.ItemDataRole.EditRole, sortableval)
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
        table_widget.setSortingEnabled(True)

    def render_plot_to_webview(self, webview, lookback_widget, timeframe_widget, plot_func, momentum_widget: Optional[QSpinBox] = None, benchmark: Optional[str] = None, tickers: Optional[List[str]] = None, normalize: Optional[bool] = None):
        try:
            lookback = lookback_widget.value()
            timeframe = timeframe_widget
            
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
        
    def fill_table_with_rows(self, table, data_rows, metric_labels):
        table.setRowCount(len(data_rows))
        table.setColumnCount(len(metric_labels) + 1)
        table.setHorizontalHeaderLabels(['Ticker'] + metric_labels)

        col_values = list(zip(*[row[1:] for row in data_rows]))  # exclude ticker
        minmax = [(min(col), max(col)) for col in col_values]

        def get_color(metric_name, value, min_val, max_val):
            if metric_name.lower() == 'momentum':
                # Diverging around 0: red < 0 < green
                if value >= 0:
                    intensity = min(value / max_val, 1.0) if max_val > 0 else 0.0
                    return QColor(int(255 * (1 - intensity)), int(255 * intensity), 0, int(255 * 0.1))
                else:
                    intensity = min(abs(value / min_val), 1.0) if min_val < 0 else 0.0
                    return QColor(255, int(255 * (1 - intensity)), 0, int(255 * 0.1))

            elif metric_name.lower() == 'relative strength':
                # Diverging around 1.0: red < 1 < green
                ref = 1.0
                span = max_val - min_val if max_val != min_val else 1.0
                normalized = (value - min_val) / span
                if value >= ref:
                    return QColor(int(255 * (1 - normalized)), int(255 * normalized), 0, int(255 * 0.1))
                else:
                    return QColor(255, int(255 * normalized), 0, int(255 * 0.1))

            elif metric_name.lower() == 'volatility':
                # Blue → red spectrum, high = blue
                span = max_val - min_val if max_val != min_val else 1.0
                normalized = (value - min_val) / span
                r = int(255 * normalized)
                g = int(255 * (1 - normalized))
                b = 255 if value > 0.15 else int(255 * (1 - normalized))  # emphasize high vol as blue
                return QColor(r, g, b, int(255 * 0.1))

            else:
                # Default red-green spectrum
                span = max_val - min_val if max_val != min_val else 1.0
                normalized = (value - min_val) / span
                return QColor(int(255 * (1 - normalized)), int(255 * normalized), 0, int(255 * 0.1))

        for row_idx, row in enumerate(data_rows):
            table.setItem(row_idx, 0, QTableWidgetItem(row[0]))

            for col_idx, value in enumerate(row[1:], start=1):
                metric_name = metric_labels[col_idx - 1]
                item = QTableWidgetItem(f"{value:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                min_val, max_val = minmax[col_idx - 1]
                item.setBackground(get_color(metric_name, value, min_val, max_val))

                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)
        table.resizeColumnsToContents()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())