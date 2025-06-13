import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import os
import time
import threading
import random
from core.engine import MarketEngine
from utils.helpers import load_config

class TradingJournalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Journal")
        self.root.geometry("1300x900")
        self.root.configure(bg="#2c3e50")
        
        # Apply dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background="#2c3e50", foreground="white")
        self.style.configure('TFrame', background="#2c3e50")
        self.style.configure('TLabel', background="#2c3e50", foreground="white")
        self.style.configure('TButton', background="#3498db", foreground="white")
        self.style.configure('Treeview', background="#34495e", fieldbackground="#34495e", foreground="white")
        self.style.configure('Treeview.Heading', background="#2c3e50", foreground="white")
        self.style.map('TButton', background=[('active', '#2980b9')])
        
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
        
        # Create GUI
        self.create_widgets()
        self.load_data()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Main frames
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Top control frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side - Engine control
        engine_frame = ttk.LabelFrame(top_frame, text="Engine Control")
        engine_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(engine_frame, text="Trading Engine Status:").pack(anchor=tk.W, padx=5, pady=2)
        self.engine_status = ttk.Label(engine_frame, text="STOPPED", foreground="red")
        self.engine_status.pack(anchor=tk.W, padx=5, pady=2)
        
        btn_frame = ttk.Frame(engine_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Start Engine", command=self.start_engine, 
                  style='TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Stop Engine", command=self.stop_engine, 
                  style='TButton').pack(side=tk.LEFT, padx=5)
        
        # Log display
        ttk.Label(engine_frame, text="Engine Log:").pack(anchor=tk.W, padx=5, pady=(10, 2))
        self.log_area = scrolledtext.ScrolledText(
            engine_frame, width=40, height=10, bg="#34495e", fg="white", 
            font=("Consolas", 9)
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.log_area.config(state=tk.DISABLED)
        
        # Right side - Trade management
        trade_frame = ttk.LabelFrame(top_frame, text="Trade Management")
        trade_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(trade_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        buttons = [
            ("Add Trade", self.add_record),
            ("Edit", self.edit_record),
            ("Delete", self.delete_record),
            ("Add Sale", self.add_sale),
            ("Save CSV", self.save_csv),
            ("Export Excel", self.export_excel)
        ]
        
        for text, command in buttons:
            ttk.Button(control_frame, text=text, command=command, 
                      width=12, style='TButton').pack(side=tk.LEFT, padx=3, pady=2)
        
        # Search frame
        search_frame = ttk.LabelFrame(trade_frame, text="Search and Filter")
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_records)
        
        ttk.Label(search_frame, text="Status:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_filter_var = tk.StringVar()
        ttk.Combobox(search_frame, textvariable=self.status_filter_var, width=15,
                      values=["All", "Active", "Completed"]).pack(side=tk.LEFT, padx=5)
        self.status_filter_var.set("All")
        self.status_filter_var.trace("w", self.filter_records)
        
        # Trade table
        table_frame = ttk.LabelFrame(main_frame, text="Trade History")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure columns
        col_widths = [40, 120, 80, 80, 150, 150, 80, 150, 80, 80]
        for idx, col in enumerate(self.columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[idx], anchor=tk.CENTER)
        
        # Charts frame
        chart_frame = ttk.LabelFrame(main_frame, text="Analytics Dashboard")
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create matplotlib figure with dark theme
        plt.style.use('dark_background')
        self.fig = plt.Figure(figsize=(12, 5), dpi=100, facecolor="#2c3e50")
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        
        self.fig.subplots_adjust(left=0.07, right=0.97, bottom=0.15, top=0.9, wspace=0.25)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        status_label = ttk.Label(status_bar, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.profit_var = tk.StringVar()
        self.profit_label = ttk.Label(status_bar, textvariable=self.profit_var, anchor=tk.E)
        self.profit_label.pack(side=tk.RIGHT, padx=5)
        
        self.update_status_bar()

    def log_message(self, message):
        """Add a message to the log area with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        
        # Update log display
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, log_entry + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        
    def start_engine(self):
        """Start the trading engine"""
        if not self.engine_running:
            try:
                if self.engine.start():
                    self.engine_running = True
                    self.engine_status.config(text="RUNNING", foreground="green")
                    self.log_message("Engine started successfully")
                else:
                    self.log_message("Engine already running")
            except Exception as e:
                self.log_message(f"Engine start failed: {str(e)}")
        else:
            self.log_message("Engine is already running")
    
    def stop_engine(self):
        """Stop the trading engine"""
        if self.engine_running:
            try:
                if self.engine.stop():
                    self.engine_running = False
                    self.engine_status.config(text="STOPPED", foreground="red")
                    self.log_message("Engine stopped successfully")
                else:
                    self.log_message("Engine stop failed")
            except Exception as e:
                self.log_message(f"Engine stop error: {str(e)}")
        else:
            self.log_message("Engine is not running")
    
    def add_auto_trade(self, product, price, quantity):
        """Add an automatically generated trade"""
        buy_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        analysis_time = buy_time  # Same as buy time for auto trades
        
        data = {
            "ID": self.next_id,
            "Product": product,
            "Buy Price": price,
            "Quantity": quantity,
            "Buy Time": buy_time,
            "Analysis Time": analysis_time,
            "Sell Price": None,
            "Sell Time": None,
            "Profit (%)": None
        }
        
        self.next_id += 1
        self.add_item_to_tree(data)
        self.save_to_df()
        self.log_message(f"Auto-added trade: {product} @ {price} x {quantity}")

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
            messagebox.showerror("Loading Error", f"Failed to load data: {str(e)}")
            self.df = pd.DataFrame(columns=self.columns)

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        for _, row in self.df.iterrows():
            # Handle missing values safely
            price_sell = row["Sell Price"] if "Sell Price" in row and not pd.isna(row["Sell Price"]) else None
            time_sell = row["Sell Time"] if "Sell Time" in row and not pd.isna(row["Sell Time"]) else None
            profit = row["Profit (%)"] if "Profit (%)" in row and not pd.isna(row["Profit (%)"]) else None
            
            status = "Completed" if price_sell is not None else "Active"
            
            values = [
                row["ID"],
                row["Product"],
                f"{row['Buy Price']:.4f}" if "Buy Price" in row else "",
                row["Quantity"] if "Quantity" in row else "",
                row["Buy Time"] if "Buy Time" in row else "",
                row["Analysis Time"] if "Analysis Time" in row else "",
                f"{price_sell:.4f}" if price_sell is not None else "",
                time_sell if time_sell is not None else "",
                f"{profit:.2f}%" if profit is not None else "",
                status
            ]
            self.tree.insert("", tk.END, values=values)

    def update_charts(self):
        self.ax1.clear()
        self.ax2.clear()
        
        if not self.df.empty:
            # Only completed trades
            if "Sell Price" in self.df.columns:
                completed = self.df.dropna(subset=["Sell Price"])
            else:
                completed = pd.DataFrame()
            
            if not completed.empty:
                # Profit by product chart
                completed["Profit (EUR)"] = (completed["Sell Price"] - completed["Buy Price"]) * completed["Quantity"]
                profit_df = completed.groupby("Product")["Profit (EUR)"].sum()
                
                colors = plt.cm.viridis(range(len(profit_df)))
                profit_df.plot(kind="bar", ax=self.ax1, color=colors)
                self.ax1.set_title("Profit by Product", fontsize=12)
                self.ax1.set_ylabel("EUR", fontsize=10)
                self.ax1.tick_params(axis='x', rotation=45)
                self.ax1.grid(True, linestyle='--', alpha=0.7)
                
                # Profit dynamics chart
                if "Sell Time" in completed.columns:
                    completed["Sell Date"] = pd.to_datetime(completed["Sell Time"]).dt.date
                    date_df = completed.groupby("Sell Date")["Profit (EUR)"].sum().cumsum()
                    
                    self.ax2.plot(date_df.index, date_df.values, marker='o', linestyle='-', color='#3498db')
                    self.ax2.fill_between(date_df.index, date_df.values, alpha=0.2, color='#3498db')
                    self.ax2.set_title("Cumulative Profit", fontsize=12)
                    self.ax2.set_ylabel("EUR", fontsize=10)
                    self.ax2.grid(True, linestyle='--', alpha=0.7)
                    self.ax2.tick_params(axis='x', rotation=45)
        
        # Set dark background for charts
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor("#34495e")
        
        self.fig.tight_layout()
        self.canvas.draw()

    def update_status_bar(self):
        total = len(self.df)
        
        # Safely handle active trades count
        if not self.df.empty and "Sell Price" in self.df.columns:
            active = len(self.df[self.df["Sell Price"].isna()])
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
        
        self.status_var.set(f"Total Trades: {total} | Active: {active} | Completed: {completed}")
        self.profit_var.set(f"Total Profit: {total_profit:.2f} EUR")
        
        # Set profit color
        profit_color = "green" if total_profit >= 0 else "red"
        self.profit_label.configure(foreground=profit_color)
        
        self.root.after(5000, self.update_status_bar)  # Update every 5 seconds

    def add_record(self):
        self.edit_window(title="Add Trade", record_type="buy")
    
    def add_sale(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Trade", "Please select an active trade to add a sale")
            return
            
        values = self.tree.item(selected[0], "values")
        if len(values) > 9 and values[9] == "Completed":
            messagebox.showwarning("Error", "Selected trade is already completed")
            return
            
        self.edit_window(title="Add Sale", values=values, record_type="sale")
    
    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        values = self.tree.item(selected[0], "values")
        if len(values) < 10:
            messagebox.showerror("Error", "Invalid trade record")
            return
            
        record_type = "sale" if values[9] == "Completed" else "buy"
        self.edit_window(title="Edit Trade", values=values, record_type=record_type)
    
    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        if messagebox.askyesno("Confirmation", "Delete selected trade?"):
            self.tree.delete(selected[0])
            self.save_to_df()
            self.save_csv(silent=True)
    
    def edit_window(self, title, values=None, record_type="buy"):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.grab_set()
        window.resizable(False, False)
        window.configure(bg="#34495e")
        
        is_sale = record_type == "sale"
        is_edit = values is not None
        
        fields = {}
        row = 0
        
        # Configure style for the window
        window_style = ttk.Style()
        window_style.configure('TLabel', background="#34495e", foreground="white")
        window_style.configure('TFrame', background="#34495e")
        
        if not is_edit:  # New record
            ttk.Label(window, text="ID:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
            ttk.Label(window, text=str(self.next_id)).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            row += 1
        
        # Common fields
        common_fields = ["Product", "Buy Price", "Quantity"]
        for field in common_fields:
            ttk.Label(window, text=field + ":").grid(row=row, column=0, padx=10, pady=5, sticky="e")
            entry = ttk.Entry(window, width=25)
            entry.grid(row=row, column=1, padx=10, pady=5)
            
            if is_edit and field in common_fields:
                idx = self.columns.index(field)
                if len(values) > idx:
                    entry.insert(0, values[idx])
                
            if field == "Buy Price" and not is_edit:
                entry.insert(0, "0.0")
            elif field == "Quantity" and not is_edit:
                entry.insert(0, "1")
            
            fields[field] = entry
            row += 1
        
        # Time fields
        time_fields = ["Buy Time", "Analysis Time"]
        for field in time_fields:
            ttk.Label(window, text=field + ":").grid(row=row, column=0, padx=10, pady=5, sticky="e")
            entry = ttk.Entry(window, width=25)
            entry.grid(row=row, column=1, padx=10, pady=5)
            
            if is_edit and len(values) > self.columns.index(field):
                idx = self.columns.index(field)
                entry.insert(0, values[idx])
            else:
                entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
            fields[field] = entry
            row += 1
        
        # Sale fields
        if is_sale:
            sale_fields = ["Sell Price", "Sell Time"]
            for field in sale_fields:
                ttk.Label(window, text=field + ":").grid(row=row, column=0, padx=10, pady=5, sticky="e")
                entry = ttk.Entry(window, width=25)
                entry.grid(row=row, column=1, padx=10, pady=5)
                
                if is_edit and field == "Sell Price" and len(values) > self.columns.index(field):
                    idx = self.columns.index(field)
                    entry.insert(0, values[idx] if values[idx] else "0.0")
                elif is_edit and field == "Sell Time" and len(values) > self.columns.index(field):
                    idx = self.columns.index(field)
                    entry.insert(0, values[idx] if values[idx] else datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S") if field == "Sell Time" else "0.0")
                
                fields[field] = entry
                row += 1
        
        # Buttons
        btn_frame = ttk.Frame(window)
        btn_frame.grid(row=row, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="Save", 
                  command=lambda: self.save_record(window, fields, is_sale, is_edit, values),
                  style='TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=window.destroy,
                  style='TButton').pack(side=tk.LEFT, padx=10)
    
    def save_record(self, window, fields, is_sale, is_edit, old_values=None):
        try:
            # Validate required fields
            required_fields = ["Product", "Buy Price", "Quantity", "Buy Time", "Analysis Time"]
            for field in required_fields:
                if not fields[field].get().strip():
                    messagebox.showerror("Error", f"{field} is required")
                    return
                    
            if is_sale:
                if not fields["Sell Price"].get().strip():
                    messagebox.showerror("Error", "Sell Price is required")
                    return
            
            # Collect data
            data = {
                "Product": fields["Product"].get(),
                "Buy Price": float(fields["Buy Price"].get()),
                "Quantity": int(fields["Quantity"].get()),
                "Buy Time": fields["Buy Time"].get(),
                "Analysis Time": fields["Analysis Time"].get(),
                "Sell Price": None,
                "Sell Time": None,
                "Profit (%)": None
            }
            
            # Add sale fields if applicable
            if is_sale:
                data["Sell Price"] = float(fields["Sell Price"].get())
                data["Sell Time"] = fields["Sell Time"].get()
                
                # Calculate profit
                if data["Buy Price"] > 0:
                    profit = ((data["Sell Price"] - data["Buy Price"]) / data["Buy Price"]) * 100
                    data["Profit (%)"] = profit
            
            # Update or add record
            if is_edit and old_values and len(old_values) > 0:
                item_id = old_values[0]  # ID from first column
                self.update_item_in_tree(item_id, data)
            else:
                data["ID"] = self.next_id
                self.next_id += 1
                self.add_item_to_tree(data)
            
            window.destroy()
            self.save_to_df()
            self.save_csv(silent=True)  # Auto-save after change
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")

    def add_item_to_tree(self, data):
        status = "Completed" if data.get("Sell Price") is not None else "Active"
        values = [
            data.get("ID", ""),
            data.get("Product", ""),
            f"{data.get('Buy Price', 0):.4f}",
            data.get("Quantity", ""),
            data.get("Buy Time", ""),
            data.get("Analysis Time", ""),
            f"{data.get('Sell Price', 0):.4f}" if data.get("Sell Price") is not None else "",
            data.get("Sell Time", "") if data.get("Sell Time") is not None else "",
            f"{data.get('Profit (%)', 0):.2f}%" if data.get("Profit (%)") is not None else "",
            status
        ]
        self.tree.insert("", tk.END, values=values)

    def update_item_in_tree(self, item_id, new_data):
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            if len(values) > 0 and str(values[0]) == str(item_id):
                status = "Completed" if new_data.get("Sell Price") is not None else "Active"
                new_values = [
                    item_id,
                    new_data.get("Product", ""),
                    f"{new_data.get('Buy Price', 0):.4f}",
                    new_data.get("Quantity", ""),
                    new_data.get("Buy Time", ""),
                    new_data.get("Analysis Time", ""),
                    f"{new_data.get('Sell Price', 0):.4f}" if new_data.get("Sell Price") is not None else "",
                    new_data.get("Sell Time", "") if new_data.get("Sell Time") is not None else "",
                    f"{new_data.get('Profit (%)', 0):.2f}%" if new_data.get("Profit (%)") is not None else "",
                    status
                ]
                self.tree.item(child, values=new_values)
                break

    def save_to_df(self):
        """Update DataFrame from Treeview"""
        records = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            try:
                if len(values) < 10:
                    continue
                    
                record = {
                    "ID": int(values[0]),
                    "Product": values[1],
                    "Buy Price": float(values[2]),
                    "Quantity": int(values[3]),
                    "Buy Time": values[4],
                    "Analysis Time": values[5],
                    "Sell Price": float(values[6]) if values[6] else None,
                    "Sell Time": values[7] if values[7] else None,
                    "Profit (%)": float(values[8].rstrip('%')) if values[8] else None,
                    "Status": values[9]
                }
                records.append(record)
            except (ValueError, IndexError) as e:
                print(f"Data conversion error: {e}")
        
        if records:
            self.df = pd.DataFrame(records)
        else:
            self.df = pd.DataFrame(columns=self.columns)
            
        self.update_charts()
        self.update_status_bar()

    def save_csv(self, silent=False):
        self.save_to_df()
        try:
            self.df.to_csv(self.data_file, index=False)
            if not silent:
                messagebox.showinfo("Saved", f"Data saved to {self.data_file}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {str(e)}")
    
    def export_excel(self):
        self.save_to_df()
        try:
            excel_file = self.data_file.replace(".csv", ".xlsx")
            self.df.to_excel(excel_file, index=False)
            messagebox.showinfo("Export Complete", f"Data exported to {excel_file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

    def search_records(self, event):
        self.filter_records()

    def filter_records(self, *args):
        query = self.search_entry.get().lower()
        status_filter = self.status_filter_var.get()
        
        self.tree.delete(*self.tree.get_children())
        
        for _, row in self.df.iterrows():
            # Apply filters
            status_match = True
            if "Status" in row:
                status_match = (status_filter == "All" or 
                              (status_filter == "Active" and row["Status"] == "Active") or
                              (status_filter == "Completed" and row["Status"] == "Completed"))
            
            text_match = False
            for col in ["ID", "Product", "Buy Time"]:
                if col in row and query in str(row[col]).lower():
                    text_match = True
                    break
            
            if status_match and text_match:
                # Format for display
                price_sell = row["Sell Price"] if "Sell Price" in row and not pd.isna(row["Sell Price"]) else None
                time_sell = row["Sell Time"] if "Sell Time" in row and not pd.isna(row["Sell Time"]) else None
                profit = row["Profit (%)"] if "Profit (%)" in row and not pd.isna(row["Profit (%)"]) else None
                
                status = row.get("Status", "Active")
                
                values = [
                    row["ID"],
                    row["Product"],
                    f"{row.get('Buy Price', 0):.4f}",
                    row["Quantity"],
                    row["Buy Time"],
                    row["Analysis Time"],
                    f"{price_sell:.4f}" if price_sell is not None else "",
                    time_sell if time_sell is not None else "",
                    f"{profit:.2f}%" if profit is not None else "",
                    status
                ]
                self.tree.insert("", tk.END, values=values)
    
    def on_closing(self):
        """Handle application closing"""
        self.stop_engine()
        self.save_csv(silent=True)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingJournalApp(root)
    root.mainloop()