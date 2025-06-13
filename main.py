import sys
import os
import random
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QTabWidget, QGroupBox,
    QScrollArea, QStatusBar, QHeaderView, QCalendarWidget, QTimeEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QDoubleValidator, QIntValidator

from core.engine import MarketEngine

class TradingJournalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Journal")
        self.setGeometry(100, 100, 1400, 900)
        
        # Parameters
        self.columns = [
            "ID", "Product", "Buy Price", "Quantity", "Buy Time",
            "Analysis Time", "Sell Price", "Sell Time", "Profit (%)", "Status"
        ]
        self.data_file = "trading_journal.csv"
        self.df = pd.DataFrame(columns=self.columns)
        self.next_id = 1
        
        # Engine control
        self.engine = MarketEngine()
        self.engine_running = False
        self.log_messages = []
        
        # Create UI
        self.create_ui()
        
        # Load data
        self.load_data()
        
        # Status bar updates
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(5000)
        
    def create_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Splitter for top and bottom sections
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Top section (controls and table)
        top_section = QWidget()
        top_layout = QVBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        
        # Engine controls
        engine_group = QGroupBox("Trading Engine")
        engine_layout = QVBoxLayout()
        
        self.engine_status = QLabel("STOPPED")
        self.engine_status.setStyleSheet("color: red; font-weight: bold;")
        
        self.log_area = QLabel()
        self.log_area.setWordWrap(True)
        self.log_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll = QScrollArea()
        scroll.setWidget(self.log_area)
        scroll.setWidgetResizable(True)
        
        btn_start = QPushButton("Start Engine")
        btn_start.setIcon(QIcon.fromTheme("media-playback-start"))
        btn_start.setStyleSheet("background-color: #6a4c93; color: white;")
        btn_start.clicked.connect(self.start_engine)
        
        btn_stop = QPushButton("Stop Engine")
        btn_stop.setIcon(QIcon.fromTheme("media-playback-stop"))
        btn_stop.setStyleSheet("background-color: #ff5555; color: white;")
        btn_stop.clicked.connect(self.stop_engine)
        
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(btn_start)
        controls_layout.addWidget(btn_stop)
        
        engine_layout.addWidget(QLabel("Status:"))
        engine_layout.addWidget(self.engine_status)
        engine_layout.addLayout(controls_layout)
        engine_layout.addWidget(QLabel("Engine Log:"))
        engine_layout.addWidget(scroll)
        
        engine_group.setLayout(engine_layout)
        
        # Trade management controls
        trade_group = QGroupBox("Trade Management")
        trade_layout = QVBoxLayout()
        
        # Buttons
        btn_add = QPushButton("Add Trade")
        btn_add.setIcon(QIcon.fromTheme("list-add"))
        btn_add.setStyleSheet("background-color: #6a4c93; color: white;")
        btn_add.clicked.connect(self.add_record)
        
        btn_edit = QPushButton("Edit")
        btn_edit.setIcon(QIcon.fromTheme("document-edit"))
        btn_edit.setStyleSheet("background-color: #4a6fa5; color: white;")
        btn_edit.clicked.connect(self.edit_record)
        
        btn_delete = QPushButton("Delete")
        btn_delete.setIcon(QIcon.fromTheme("edit-delete"))
        btn_delete.setStyleSheet("background-color: #ff5555; color: white;")
        btn_delete.clicked.connect(self.delete_record)
        
        btn_sale = QPushButton("Add Sale")
        btn_sale.setIcon(QIcon.fromTheme("tag"))
        btn_sale.setStyleSheet("background-color: #50a05a; color: white;")
        btn_sale.clicked.connect(self.add_sale)
        
        btn_save = QPushButton("Save CSV")
        btn_save.setIcon(QIcon.fromTheme("document-save"))
        btn_save.setStyleSheet("background-color: #4a6fa5; color: white;")
        btn_save.clicked.connect(self.save_csv)
        
        btn_export = QPushButton("Export Excel")
        btn_export.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
        btn_export.setStyleSheet("background-color: #50a05a; color: white;")
        btn_export.clicked.connect(self.export_excel)
        
        # Button grid
        button_grid = QHBoxLayout()
        button_grid.addWidget(btn_add)
        button_grid.addWidget(btn_edit)
        button_grid.addWidget(btn_delete)
        button_grid.addWidget(btn_sale)
        button_grid.addWidget(btn_save)
        button_grid.addWidget(btn_export)
        
        # Search and filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search trades...")
        self.search_field.textChanged.connect(self.search_records)
        search_layout.addWidget(self.search_field)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "Completed"])
        self.status_filter.currentIndexChanged.connect(self.filter_records)
        filter_layout.addWidget(self.status_filter)
        
        trade_layout.addLayout(button_grid)
        trade_layout.addLayout(search_layout)
        trade_layout.addLayout(filter_layout)
        trade_group.setLayout(trade_layout)
        
        # Top row layout (engine controls + trade controls)
        top_row = QHBoxLayout()
        top_row.addWidget(engine_group, 1)
        top_row.addWidget(trade_group, 1)
        top_layout.addLayout(top_row)
        
        # Trade table
        table_group = QGroupBox("Trade History")
        table_layout = QVBoxLayout()
        
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(len(self.columns))
        self.trade_table.setHorizontalHeaderLabels(self.columns)
        self.trade_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.trade_table.setSelectionMode(QTableWidget.SingleSelection)
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trade_table.verticalHeader().setVisible(False)
        
        table_layout.addWidget(self.trade_table)
        table_group.setLayout(table_layout)
        top_layout.addWidget(table_group)
        
        top_section.setLayout(top_layout)
        splitter.addWidget(top_section)
        
        # Bottom section (analytics)
        bottom_section = QWidget()
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        # Analytics tabs
        analytics_tabs = QTabWidget()
        
        # Charts tab
        charts_tab = QWidget()
        charts_layout = QHBoxLayout(charts_tab)
        
        # Create matplotlib figures
        self.figure1 = plt.Figure(facecolor='#f0f0f0')
        self.canvas1 = FigureCanvas(self.figure1)
        
        self.figure2 = plt.Figure(facecolor='#f0f0f0')
        self.canvas2 = FigureCanvas(self.figure2)
        
        charts_layout.addWidget(self.canvas1)
        charts_layout.addWidget(self.canvas2)
        analytics_tabs.addTab(charts_tab, "Charts")
        
        bottom_layout.addWidget(analytics_tabs)
        bottom_section.setLayout(bottom_layout)
        splitter.addWidget(bottom_section)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel()
        self.profit_label = QLabel()
        self.profit_label.setStyleSheet("color: #50a05a; font-weight: bold;")
        
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addWidget(self.profit_label)
        
        # Set light theme colors
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #333333;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                gridline-color: #dddddd;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #cccccc;
            }
            QLineEdit, QComboBox {
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        
    def log_message(self, message):
        """Add a message to the log area with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_messages.append(log_entry)
        
        # Update log display (keep last 20 messages)
        self.log_area.setText("".join(self.log_messages[-20:]))
        
    def start_engine(self):
        """Start the trading engine"""
        if not self.engine_running:
            self.engine.start()
            self.engine_running = True
            self.engine_status.setText("RUNNING")
            self.engine_status.setStyleSheet("color: green; font-weight: bold;")
            self.log_message("Engine started successfully")
            
            # Start simulated engine activity
            self.engine_timer = QTimer(self)
            self.engine_timer.timeout.connect(self.engine_activity)
            self.engine_timer.start(2000)
        else:
            self.log_message("Engine is already running")
    
    def stop_engine(self):
        """Stop the trading engine"""
        if self.engine_running:
            self.engine.stop()
            self.engine_running = False
            self.engine_status.setText("STOPPED")
            self.engine_status.setStyleSheet("color: red; font-weight: bold;")
            self.log_message("Engine stopped successfully")
            
            if hasattr(self, 'engine_timer'):
                self.engine_timer.stop()
        else:
            self.log_message("Engine is not running")
    
    def engine_activity(self):
        pass
    
    def add_auto_trade(self, product, price, quantity):
        pass
    
    def update_table(self):
        self.trade_table.setRowCount(0)
        
        for _, row in self.df.iterrows():
            row_pos = self.trade_table.rowCount()
            self.trade_table.insertRow(row_pos)
            
            for col_idx, col_name in enumerate(self.columns):
                if col_name in row:
                    value = row[col_name]
                    if pd.isna(value):
                        item = QTableWidgetItem("")
                    elif isinstance(value, float):
                        if col_name in ["Buy Price", "Sell Price"]:
                            item = QTableWidgetItem(f"{value:.4f}")
                        elif col_name == "Profit (%)":
                            item = QTableWidgetItem(f"{value:.2f}%")
                        else:
                            item = QTableWidgetItem(str(value))
                    else:
                        item = QTableWidgetItem(str(value))
                else:
                    item = QTableWidgetItem("")
                
                # Color status column
                if col_name == "Status":
                    if item.text() == "Completed":
                        item.setForeground(QColor(0, 128, 0))  # Green
                    else:
                        item.setForeground(QColor(200, 120, 0))  # Orange
                
                self.trade_table.setItem(row_pos, col_idx, item)
    
    def update_charts(self):
        # Clear previous figures
        self.figure1.clear()
        self.figure2.clear()
        
        if not self.df.empty:
            # Only completed trades
            if "Sell Price" in self.df.columns:
                completed = self.df.dropna(subset=["Sell Price"])
            else:
                completed = pd.DataFrame()
            
            if not completed.empty:
                # Set light theme colors for matplotlib
                plt.style.use('default')
                
                # Create figure 1 - Profit by product
                ax1 = self.figure1.add_subplot(111)
                
                completed["Profit (EUR)"] = (completed["Sell Price"] - completed["Buy Price"]) * completed["Quantity"]
                profit_df = completed.groupby("Product")["Profit (EUR)"].sum()
                
                colors = plt.cm.viridis(range(len(profit_df)))
                profit_df.plot(kind="bar", ax=ax1, color=colors)
                ax1.set_title("Profit by Product", fontsize=14)
                ax1.set_ylabel("EUR", fontsize=12)
                ax1.tick_params(axis='x', rotation=45)
                ax1.grid(True, linestyle='--', alpha=0.3, color='gray')
                
                # Create figure 2 - Cumulative profit
                ax2 = self.figure2.add_subplot(111)
                
                if "Sell Time" in completed.columns:
                    # Convert to datetime and ensure proper format
                    try:
                        completed["Sell Date"] = pd.to_datetime(completed["Sell Time"]).dt.date
                        date_df = completed.groupby("Sell Date")["Profit (EUR)"].sum().cumsum()
                        
                        # Ensure dates are properly sorted
                        date_df = date_df.sort_index()
                        
                        # Convert dates to matplotlib-compatible format
                        dates = date_df.index
                        values = date_df.values
                        
                        ax2.plot(dates, values, marker='o', linestyle='-', color='#6a4c93')
                        ax2.fill_between(dates, values, alpha=0.2, color='#6a4c93')
                        ax2.set_title("Cumulative Profit", fontsize=14)
                        ax2.set_ylabel("EUR", fontsize=12)
                        ax2.grid(True, linestyle='--', alpha=0.3, color='gray')
                        
                        # Format x-axis dates
                        ax2.tick_params(axis='x', rotation=45)
                        ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
                    except Exception as e:
                        print(f"Error plotting cumulative profit: {e}")
                
                self.figure1.tight_layout()
                self.figure2.tight_layout()
                self.canvas1.draw()
                self.canvas2.draw()
    
    def update_status_bar(self):
        total = len(self.df)
        
        # Safely handle active trades count
        if not self.df.empty and "Status" in self.df.columns:
            active = len(self.df[self.df["Status"] == "Active"])
            completed = total - active
        else:
            active = 0
            completed = 0
        
        # Calculate total profit
        total_profit = 0
        if not self.df.empty and "Sell Price" in self.df.columns and "Buy Price" in self.df.columns:
            completed_deals = self.df.dropna(subset=["Sell Price"])
            if not completed_deals.empty:
                completed_deals["Profit (EUR)"] = (completed_deals["Sell Price"] - completed_deals["Buy Price"]) * completed_deals["Quantity"]
                total_profit = completed_deals["Profit (EUR)"].sum()
        
        self.status_label.setText(f"Total Trades: {total} | Active: {active} | Completed: {completed}")
        
        # Set profit color
        profit_color = "#50a05a" if total_profit >= 0 else "#ff5555"
        self.profit_label.setText(f"Total Profit: {total_profit:.2f} EUR")
        self.profit_label.setStyleSheet(f"color: {profit_color}; font-weight: bold;")
    
    def add_record(self):
        self.edit_window(title="Add Trade", record_type="buy")
    
    def add_sale(self):
        selected = self.trade_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Select Trade", "Please select an active trade to add a sale")
            return
            
        row_idx = self.trade_table.row(selected[0])
        status = self.df.iloc[row_idx]["Status"] if "Status" in self.df.columns else "Active"
        
        if status == "Completed":
            QMessageBox.warning(self, "Error", "Selected trade is already completed")
            return
            
        self.edit_window(title="Add Sale", row_idx=row_idx, record_type="sale")
    
    def edit_record(self):
        selected = self.trade_table.selectedItems()
        if not selected:
            return
            
        row_idx = self.trade_table.row(selected[0])
        status = self.df.iloc[row_idx]["Status"] if "Status" in self.df.columns else "Active"
        record_type = "sale" if status == "Completed" else "buy"
        self.edit_window(title="Edit Trade", row_idx=row_idx, record_type=record_type)
    
    def delete_record(self):
        selected = self.trade_table.selectedItems()
        if not selected:
            return
            
        row_idx = self.trade_table.row(selected[0])
        if self.confirm_action("Confirmation", "Delete selected trade?"):
            self.df = self.df.drop(row_idx).reset_index(drop=True)
            self.save_to_df()
            self.update_table()
            self.update_charts()
            self.update_status_bar()
    
    def edit_window(self, title, row_idx=None, record_type="buy"):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        
        fields = {}
        is_sale = record_type == "sale"
        is_edit = row_idx is not None

        # ID field (readonly for edits)
        if is_edit:
            id_label = QLabel(str(self.df.iloc[row_idx]["ID"]))
        else:
            id_label = QLabel(str(self.next_id))
        id_label.setStyleSheet("font-weight: bold;")
        form.addRow("ID:", id_label)

        # Product field with autocomplete
        product_field = QComboBox()
        product_field.setEditable(True)
        if not self.df.empty and "Product" in self.df.columns:
            product_field.addItems(sorted(self.df["Product"].unique()))
        fields["Product"] = product_field
        form.addRow("Product:", product_field)

        # Numeric fields
        buy_price_edit = QLineEdit()
        buy_price_edit.setValidator(QDoubleValidator(0, 999999, 4))
        buy_price_edit.setText("0.0")
        fields["Buy Price"] = buy_price_edit
        form.addRow("Buy Price:", buy_price_edit)

        quantity_edit = QLineEdit()
        quantity_edit.setValidator(QIntValidator(1, 999999))
        quantity_edit.setText("1")
        fields["Quantity"] = quantity_edit
        form.addRow("Quantity:", quantity_edit)

        if is_sale:
            sell_price_edit = QLineEdit()
            sell_price_edit.setValidator(QDoubleValidator(0, 999999, 4))
            sell_price_edit.setText("0.0")
            fields["Sell Price"] = sell_price_edit
            form.addRow("Sell Price:", sell_price_edit)

        # Date fields with calendar widget
        for field in ["Buy Time", "Analysis Time"] + (["Sell Time"] if is_sale else []):
            date_edit = QLineEdit()
            date_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
            calendar_btn = QPushButton("...")
            calendar_btn.setFixedWidth(30)
            
            def create_calendar_callback(edit_field):
                def show_calendar():
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Select Date")
                    calendar = QCalendarWidget()
                    time_edit = QTimeEdit()
                    time_edit.setDisplayFormat("HH:mm:ss")
                    
                    btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                    btn_box.accepted.connect(dialog.accept)
                    btn_box.rejected.connect(dialog.reject)
                    
                    layout = QVBoxLayout()
                    layout.addWidget(calendar)
                    layout.addWidget(time_edit)
                    layout.addWidget(btn_box)
                    dialog.setLayout(layout)
                    
                    if dialog.exec_() == QDialog.Accepted:
                        date = calendar.selectedDate().toString("yyyy-MM-dd")
                        time = time_edit.time().toString("HH:mm:ss")
                        edit_field.setText(f"{date} {time}")
                
                return show_calendar
            
            calendar_btn.clicked.connect(create_calendar_callback(date_edit))
            
            hbox = QHBoxLayout()
            hbox.addWidget(date_edit)
            hbox.addWidget(calendar_btn)
            
            fields[field] = date_edit
            form.addRow(f"{field}:", hbox)

            # Set current datetime if not editing
            if not is_edit:
                date_edit.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Set initial values for edits
        if is_edit:
            row = self.df.iloc[row_idx]
            for field in fields:
                if field in row and not pd.isna(row[field]):
                    if isinstance(fields[field], QComboBox):
                        fields[field].setCurrentText(str(row[field]))
                    elif isinstance(row[field], float) and "Price" in field:
                        fields[field].setText(f"{row[field]:.4f}")
                    else:
                        fields[field].setText(str(row[field]))

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        # Layout
        layout.addLayout(form)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            try:
                # Validate required fields
                required_fields = ["Product", "Buy Price", "Quantity", "Buy Time", "Analysis Time"]
                for field in required_fields:
                    if field == "Product":
                        if not fields[field].currentText().strip():
                            QMessageBox.warning(self, "Error", f"{field} is required")
                            return
                    elif not fields[field].text().strip():
                        QMessageBox.warning(self, "Error", f"{field} is required")
                        return

                # Validate date formats
                date_fields = ["Buy Time", "Analysis Time"] + (["Sell Time"] if is_sale else [])
                for field in date_fields:
                    try:
                        datetime.strptime(fields[field].text(), "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        QMessageBox.warning(self, "Error", 
                                        f"Invalid {field} format. Use YYYY-MM-DD HH:MM:SS")
                        return

                # Prepare data dictionary
                data = {
                    "Product": fields["Product"].currentText(),  # Use currentText() for QComboBox
                    "Buy Price": float(fields["Buy Price"].text()),
                    "Quantity": int(fields["Quantity"].text()),
                    "Buy Time": fields["Buy Time"].text(),
                    "Analysis Time": fields["Analysis Time"].text(),
                    "Sell Price": None,
                    "Sell Time": None,
                    "Profit (%)": None,
                    "Status": "Active"
                }

                if is_sale:
                    data.update({
                        "Sell Price": float(fields["Sell Price"].text()),
                        "Sell Time": fields["Sell Time"].text(),
                        "Status": "Completed"
                    })
                    if data["Buy Price"] > 0:
                        data["Profit (%)"] = ((data["Sell Price"] - data["Buy Price"]) / data["Buy Price"]) * 100

                # Update or add record
                if is_edit:
                    data["ID"] = self.df.iloc[row_idx]["ID"]
                    self.df.iloc[row_idx] = data
                else:
                    data["ID"] = self.next_id
                    self.next_id += 1
                    self.df = pd.concat([self.df, pd.DataFrame([data])], ignore_index=True)

                self.save_to_df()
                self.update_table()
                self.update_charts()
                self.update_status_bar()
                
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Invalid input: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def add_item_to_table(self, data):
        self.df = pd.concat([self.df, pd.DataFrame([data])], ignore_index=True)
        self.update_table()
    
    def save_to_df(self):
        """Data is already in self.df"""
        self.update_charts()
        self.update_status_bar()
    
    def save_csv(self):
        try:
            self.df.to_csv(self.data_file, index=False)
            QMessageBox.information(self, "Saved", f"Data saved to {self.data_file}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save data: {str(e)}")
    
    def export_excel(self):
        try:
            excel_file = self.data_file.replace(".csv", ".xlsx")
            self.df.to_excel(excel_file, index=False)
            QMessageBox.information(self, "Export Complete", f"Data exported to {excel_file}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def search_records(self):
        search_text = self.search_field.text().lower()
        
        if not search_text:
            self.update_table()
            return
        
        # Filter dataframe
        filtered = self.df[
            self.df["Product"].str.lower().str.contains(search_text) |
            self.df["ID"].astype(str).str.contains(search_text)
        ]
        
        # Update table with filtered results
        self.trade_table.setRowCount(0)
        
        for _, row in filtered.iterrows():
            row_pos = self.trade_table.rowCount()
            self.trade_table.insertRow(row_pos)
            
            for col_idx, col_name in enumerate(self.columns):
                if col_name in row:
                    value = row[col_name]
                    if pd.isna(value):
                        item = QTableWidgetItem("")
                    elif isinstance(value, float):
                        if col_name in ["Buy Price", "Sell Price"]:
                            item = QTableWidgetItem(f"{value:.4f}")
                        elif col_name == "Profit (%)":
                            item = QTableWidgetItem(f"{value:.2f}%")
                        else:
                            item = QTableWidgetItem(str(value))
                    else:
                        item = QTableWidgetItem(str(value))
                else:
                    item = QTableWidgetItem("")
                
                self.trade_table.setItem(row_pos, col_idx, item)

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                self.df = pd.read_csv(
                    self.data_file, 
                    parse_dates=["Buy Time", "Analysis Time", "Sell Time"],
                    dtype={"ID": int, "Buy Price": float, "Quantity": int, 
                           "Sell Price": float, "Profit (%)": float}
                )
                if not self.df.empty:
                    self.next_id = self.df["ID"].max() + 1
                self.update_table()
                self.update_charts()
            else:
                self.df = pd.DataFrame(columns=self.columns)
        except Exception as e:
            print(f"Loading error: {str(e)}")
            self.df = pd.DataFrame(columns=self.columns)
              
    def filter_records(self):
        status_filter = self.status_filter.currentText()
        
        if status_filter == "All":
            self.update_table()
            return
        
        # Filter dataframe
        if status_filter == "Active":
            filtered = self.df[self.df["Status"] == "Active"]
        else:  # Completed
            filtered = self.df[self.df["Status"] == "Completed"]
        
        # Update table with filtered results
        self.trade_table.setRowCount(0)
        
        for _, row in filtered.iterrows():
            row_pos = self.trade_table.rowCount()
            self.trade_table.insertRow(row_pos)
            
            for col_idx, col_name in enumerate(self.columns):
                if col_name in row:
                    value = row[col_name]
                    if pd.isna(value):
                        item = QTableWidgetItem("")
                    elif isinstance(value, float):
                        if col_name in ["Buy Price", "Sell Price"]:
                            item = QTableWidgetItem(f"{value:.4f}")
                        elif col_name == "Profit (%)":
                            item = QTableWidgetItem(f"{value:.2f}%")
                        else:
                            item = QTableWidgetItem(str(value))
                    else:
                        item = QTableWidgetItem(str(value))
                else:
                    item = QTableWidgetItem("")
                
                self.trade_table.setItem(row_pos, col_idx, item)
    
    def confirm_action(self, title, message):
        reply = QMessageBox.question(
            self, title, message, 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return reply == QMessageBox.Yes


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingJournalApp()
    window.show()
    sys.exit(app.exec_())