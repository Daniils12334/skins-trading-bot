import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import os

class TradeJournalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Торговый журнал")
        self.root.geometry("1200x800")
        
        # Параметры
        self.columns = [
            "ID", "Товар", "Цена покупки", "Количество", "Время покупки",
            "Время анализа", "Цена продажи", "Время продажи", "Прибыль (%)", "Статус"
        ]
        self.data_file = "trade_journal.csv"
        self.df = pd.DataFrame(columns=self.columns)
        self.next_id = 1
        
        # Создание GUI
        self.create_widgets()
        self.load_data()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Основные фреймы
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Фрейм управления
        control_frame = ttk.LabelFrame(main_frame, text="Управление записями")
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Добавить сделку", command=self.add_record, width=20).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(control_frame, text="Редактировать", command=self.edit_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Удалить", command=self.delete_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Добавить продажу", command=self.add_sale).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Сохранить CSV", command=self.save_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Экспорт в Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)
        
        # Фрейм поиска
        search_frame = ttk.LabelFrame(main_frame, text="Поиск и фильтрация")
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_records)
        
        ttk.Label(search_frame, text="Статус:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_filter_var = tk.StringVar()
        ttk.Combobox(search_frame, textvariable=self.status_filter_var, width=15,
                      values=["Все", "Активна", "Завершена"]).pack(side=tk.LEFT, padx=5)
        self.status_filter_var.set("Все")
        self.status_filter_var.trace("w", self.filter_records)
        
        # Таблица с данными
        table_frame = ttk.LabelFrame(main_frame, text="История сделок")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Настройка колонок
        col_widths = [40, 120, 80, 80, 120, 120, 80, 120, 80, 80]
        for idx, col in enumerate(self.columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[idx], anchor=tk.CENTER)
        
        # Графики
        graph_frame = ttk.LabelFrame(main_frame, text="Аналитика")
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax1 = ax1
        self.ax2 = ax2
        
        # Статус бар
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar()
        
    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                self.df = pd.read_csv(
                    self.data_file, 
                    parse_dates=["Время покупки", "Время анализа", "Время продажи"],
                    dtype={"ID": int, "Цена покупки": float, "Количество": int, "Цена продажи": float, "Прибыль (%)": float}
                )
                if not self.df.empty:
                    self.next_id = self.df["ID"].max() + 1
                self.update_table()
                self.update_charts()
            else:
                self.df = pd.DataFrame(columns=self.columns)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить данные: {str(e)}")
            self.df = pd.DataFrame(columns=self.columns)

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        for _, row in self.df.iterrows():
            # Проверка на NaN значения
            price_sell = row["Цена продажи"] if not pd.isna(row["Цена продажи"]) else None
            time_sell = row["Время продажи"] if not pd.isna(row["Время продажи"]) else None
            profit = row["Прибыль (%)"] if not pd.isna(row["Прибыль (%)"]) else None
            
            status = "Завершена" if price_sell is not None else "Активна"
            
            values = [
                row["ID"],
                row["Товар"],
                f"{row['Цена покупки']:.2f}",
                row["Количество"],
                row["Время покупки"],
                row["Время анализа"],
                f"{price_sell:.2f}" if price_sell is not None else "",
                time_sell if time_sell is not None else "",
                f"{profit:.2f}%" if profit is not None else "",
                status
            ]
            self.tree.insert("", tk.END, values=values)

    def update_charts(self):
        self.ax1.clear()
        self.ax2.clear()
        
        if not self.df.empty:
            # Только завершенные сделки
            completed = self.df.dropna(subset=["Цена продажи"])
            
            if not completed.empty:
                # График прибыли по товарам
                completed["Прибыль (руб)"] = (completed["Цена продажи"] - completed["Цена покупки"]) * completed["Количество"]
                profit_df = completed.groupby("Товар")["Прибыль (руб)"].sum()
                profit_df.plot(kind="bar", ax=self.ax1, title="Прибыль по товарам", color='green')
                self.ax1.set_ylabel("Рубли")
                self.ax1.tick_params(axis='x', rotation=45)
                
                # График динамики сделок
                completed["Дата продажи"] = pd.to_datetime(completed["Время продажи"]).dt.date
                date_df = completed.groupby("Дата продажи")["Прибыль (руб)"].sum()
                date_df.plot(ax=self.ax2, marker="o", linestyle="-", title="Динамика прибыли", color='blue')
                self.ax2.set_ylabel("Прибыль")
                self.ax2.grid(True)
                self.ax2.tick_params(axis='x', rotation=45)
        
        self.canvas.draw()

    def update_status_bar(self):
        total = len(self.df)
        active = len(self.df[self.df["Цена продажи"].isna()])
        completed = total - active
        
        # Рассчет общей прибыли
        completed_deals = self.df.dropna(subset=["Цена продажи"])
        total_profit = 0
        if not completed_deals.empty:
            completed_deals["Прибыль (руб)"] = (completed_deals["Цена продажи"] - completed_deals["Цена покупки"]) * completed_deals["Количество"]
            total_profit = completed_deals["Прибыль (руб)"].sum()
        
        self.status_var.set(f"Всего сделок: {total} | Активных: {active} | Завершенных: {completed} | Общая прибыль: {total_profit:.2f} руб")

    def add_record(self):
        self.edit_window(title="Добавить сделку", record_type="buy")
    
    def add_sale(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор сделки", "Выберите активную сделку для добавления продажи")
            return
            
        values = self.tree.item(selected[0], "values")
        if values[9] == "Завершена":
            messagebox.showwarning("Ошибка", "Выбранная сделка уже завершена")
            return
            
        self.edit_window(title="Добавить продажу", values=values, record_type="sale")
    
    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        record_type = "sale" if values[9] == "Завершена" else "buy"
        self.edit_window(title="Редактировать сделку", values=values, record_type=record_type)
    
    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранную сделку?"):
            self.tree.delete(selected[0])
            self.save_to_df()
            self.save_csv(silent=True)
    
    def edit_window(self, title, values=None, record_type="buy"):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.grab_set()
        window.resizable(False, False)
        
        is_sale = record_type == "sale"
        is_edit = values is not None
        
        fields = {}
        row = 0
        
        if not is_edit:  # Новая запись
            ttk.Label(window, text="ID:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(window, text=str(self.next_id)).grid(row=row, column=1, padx=5, pady=5, sticky="w")
            row += 1
        
        # Общие поля
        common_fields = ["Товар", "Цена покупки", "Количество"]
        for field in common_fields:
            ttk.Label(window, text=field + ":").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(window, width=25)
            entry.grid(row=row, column=1, padx=5, pady=5)
            
            if is_edit and field in ["Товар", "Цена покупки", "Количество"]:
                idx = self.columns.index(field)
                entry.insert(0, values[idx])
                
            if field == "Цена покупки" and not is_edit:
                entry.insert(0, "0.0")
            elif field == "Количество" and not is_edit:
                entry.insert(0, "1")
            
            fields[field] = entry
            row += 1
        
        # Поля времени покупки/анализа
        time_fields = ["Время покупки", "Время анализа"]
        for field in time_fields:
            ttk.Label(window, text=field + ":").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(window, width=25)
            entry.grid(row=row, column=1, padx=5, pady=5)
            
            if is_edit:
                idx = self.columns.index(field)
                entry.insert(0, values[idx])
            else:
                entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
            fields[field] = entry
            row += 1
        
        # Поля для продажи
        if is_sale:
            sale_fields = ["Цена продажи", "Время продажи"]
            for field in sale_fields:
                ttk.Label(window, text=field + ":").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                entry = ttk.Entry(window, width=25)
                entry.grid(row=row, column=1, padx=5, pady=5)
                
                if is_edit and field == "Цена продажи":
                    idx = self.columns.index(field)
                    entry.insert(0, values[idx] if values[idx] else "0.0")
                elif is_edit and field == "Время продажи":
                    idx = self.columns.index(field)
                    entry.insert(0, values[idx] if values[idx] else datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S") if field == "Время продажи" else "0.0")
                
                fields[field] = entry
                row += 1
        
        # Кнопки
        btn_frame = ttk.Frame(window)
        btn_frame.grid(row=row, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", 
                  command=lambda: self.save_record(window, fields, is_sale, is_edit, values)).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=window.destroy).pack(side=tk.LEFT, padx=10)
    
    def save_record(self, window, fields, is_sale, is_edit, old_values=None):
        try:
            # Сбор данных
            data = {
                "Товар": fields["Товар"].get(),
                "Цена покупки": float(fields["Цена покупки"].get()),
                "Количество": int(fields["Количество"].get()),
                "Время покупки": fields["Время покупки"].get(),
                "Время анализа": fields["Время анализа"].get(),
                "Цена продажи": None,
                "Время продажи": None,
                "Прибыль (%)": None
            }
            
            # Для продажи добавляем дополнительные поля
            if is_sale:
                data["Цена продажи"] = float(fields["Цена продажи"].get())
                data["Время продажи"] = fields["Время продажи"].get()
                
                # Расчет прибыли
                if data["Цена покупки"] > 0:
                    profit = ((data["Цена продажи"] - data["Цена покупки"]) / data["Цена покупки"]) * 100
                    data["Прибыль (%)"] = profit
            
            # Обновление или добавление записи
            if is_edit:
                item_id = old_values[0]  # ID из первой колонки
                self.update_item_in_tree(item_id, data)
            else:
                data["ID"] = self.next_id
                self.next_id += 1
                self.add_item_to_tree(data)
            
            window.destroy()
            self.save_to_df()
            self.save_csv(silent=True)  # Автосохранение после изменения
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода числовых значений")

    def add_item_to_tree(self, data):
        status = "Завершена" if data["Цена продажи"] is not None else "Активна"
        values = [
            data["ID"],
            data["Товар"],
            f"{data['Цена покупки']:.2f}",
            data["Количество"],
            data["Время покупки"],
            data["Время анализа"],
            f"{data['Цена продажи']:.2f}" if data["Цена продажи"] is not None else "",
            data["Время продажи"] if data["Время продажи"] is not None else "",
            f"{data['Прибыль (%)']:.2f}%" if data["Прибыль (%)"] is not None else "",
            status
        ]
        self.tree.insert("", tk.END, values=values)

    def update_item_in_tree(self, item_id, new_data):
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            if str(values[0]) == str(item_id):
                status = "Завершена" if new_data["Цена продажи"] is not None else "Активна"
                new_values = [
                    item_id,
                    new_data["Товар"],
                    f"{new_data['Цена покупки']:.2f}",
                    new_data["Количество"],
                    new_data["Время покупки"],
                    new_data["Время анализа"],
                    f"{new_data['Цена продажи']:.2f}" if new_data["Цена продажи"] is not None else "",
                    new_data["Время продажи"] if new_data["Время продажи"] is not None else "",
                    f"{new_data['Прибыль (%)']:.2f}%" if new_data["Прибыль (%)"] is not None else "",
                    status
                ]
                self.tree.item(child, values=new_values)
                break

    def save_to_df(self):
        """Обновляет DataFrame из Treeview"""
        records = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            try:
                record = {
                    "ID": int(values[0]),
                    "Товар": values[1],
                    "Цена покупки": float(values[2]),
                    "Количество": int(values[3]),
                    "Время покупки": values[4],
                    "Время анализа": values[5],
                    "Цена продажи": float(values[6]) if values[6] else None,
                    "Время продажи": values[7] if values[7] else None,
                    "Прибыль (%)": float(values[8].rstrip('%')) if values[8] else None,
                    "Статус": values[9]
                }
                records.append(record)
            except ValueError as e:
                print(f"Ошибка преобразования данных: {e}")
        
        self.df = pd.DataFrame(records)
        self.update_charts()
        self.update_status_bar()

    def save_csv(self, silent=False):
        self.save_to_df()
        try:
            self.df.to_csv(self.data_file, index=False)
            if not silent:
                messagebox.showinfo("Сохранено", f"Данные сохранены в {self.data_file}")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить данные: {str(e)}")
    
    def export_excel(self):
        self.save_to_df()
        try:
            excel_file = self.data_file.replace(".csv", ".xlsx")
            self.df.to_excel(excel_file, index=False)
            messagebox.showinfo("Экспорт завершен", f"Данные экспортированы в {excel_file}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", f"Не удалось экспортировать данные: {str(e)}")

    def search_records(self, event):
        self.filter_records()

    def filter_records(self, *args):
        query = self.search_entry.get().lower()
        status_filter = self.status_filter_var.get()
        
        self.tree.delete(*self.tree.get_children())
        
        for _, row in self.df.iterrows():
            # Проверка соответствия фильтрам
            status_match = (status_filter == "Все" or 
                          (status_filter == "Активна" and pd.isna(row["Цена продажи"])) or
                          (status_filter == "Завершена" and not pd.isna(row["Цена продажи"])))
            
            text_match = (query in str(row["ID"]).lower() or 
                         query in str(row["Товар"]).lower() or 
                         query in str(row["Время покупки"]).lower())
            
            if status_match and text_match:
                # Форматирование для отображения
                price_sell = row["Цена продажи"] if not pd.isna(row["Цена продажи"]) else None
                time_sell = row["Время продажи"] if not pd.isna(row["Время продажи"]) else None
                profit = row["Прибыль (%)"] if not pd.isna(row["Прибыль (%)"]) else None
                
                status = "Завершена" if price_sell is not None else "Активна"
                
                values = [
                    row["ID"],
                    row["Товар"],
                    f"{row['Цена покупки']:.2f}",
                    row["Количество"],
                    row["Время покупки"],
                    row["Время анализа"],
                    f"{price_sell:.2f}" if price_sell is not None else "",
                    time_sell if time_sell is not None else "",
                    f"{profit:.2f}%" if profit is not None else "",
                    status
                ]
                self.tree.insert("", tk.END, values=values)
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        self.save_csv(silent=True)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TradeJournalApp(root)
    root.mainloop()