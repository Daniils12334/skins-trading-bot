import json
import csv
import os
from datetime import datetime

class SkinportDatabase:
    def __init__(self, items_path, history_path, output_csv):
        self.items_path = items_path
        self.history_path = history_path
        self.output_csv = output_csv
        self.items_data = {}
        self.history_data = {}
        
    def load_items_data(self):
        """Загружает и обрабатывает данные из файла items"""
        try:
            with open(self.items_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
            
            for item in items:
                name = item.get('market_hash_name')
                if name:
                    self.items_data[name] = {
                        'current_min_price': item.get('min_price'),
                        'currency': item.get('currency', 'EUR')
                    }
            print(f"Loaded {len(self.items_data)} items")
        except Exception as e:
            print(f"Error loading items: {str(e)}")

    def load_history_data(self):
        """Загружает и обрабатывает данные из файла истории продаж"""
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            for entry in history:
                name = entry.get('market_hash_name')
                if name:
                    self.history_data[name] = {
                        'currency': entry.get('currency', 'EUR'),
                        'last_24h': entry.get('last_24_hours', {}),
                        'last_7d': entry.get('last_7_days', {}),
                        'last_30d': entry.get('last_30_days', {}),
                        'last_90d': entry.get('last_90_days', {})
                    }
            print(f"Loaded {len(self.history_data)} history entries")
        except Exception as e:
            print(f"Error loading history: {str(e)}")

    def merge_data(self):
        """Объединяет данные из обоих источников"""
        merged = []
        
        # Обрабатываем элементы, присутствующие в обоих источниках
        for name in set(self.items_data.keys()) | set(self.history_data.keys()):
            item = self.items_data.get(name, {})
            history = self.history_data.get(name, {})
            
            # Определяем валюту (приоритет у актуальных items)
            currency = item.get('currency') or history.get('currency') or 'EUR'
            
            merged.append({
                'market_hash_name': name,
                'currency': currency,
                'current_min_price': item.get('current_min_price'),
                **self._extract_period_data(history.get('last_24h', {}), '24h'),
                **self._extract_period_data(history.get('last_7d', {}), '7d'),
                **self._extract_period_data(history.get('last_30d', {}), '30d'),
                **self._extract_period_data(history.get('last_90d', {}), '90d')
            })
        
        print(f"Merged {len(merged)} records")
        return merged

    def _extract_period_data(self, period, suffix):
        """Извлекает данные для периода и добавляет суффикс к ключам"""
        return {
            f'min_{suffix}': period.get('min'),
            f'max_{suffix}': period.get('max'),
            f'avg_{suffix}': period.get('avg'),
            f'median_{suffix}': period.get('median'),
            f'volume_{suffix}': period.get('volume', 0)
        }

    def export_to_csv(self, data):
        """Экспортирует объединенные данные в CSV"""
        if not data:
            print("No data to export")
            return
        
        fieldnames = ['market_hash_name', 'currency', 'current_min_price']
        periods = ['24h', '7d', '30d', '90d']
        metrics = ['min', 'max', 'avg', 'median', 'volume']
        
        # Генерация динамических заголовков
        for period in periods:
            for metric in metrics:
                fieldnames.append(f"{metric}_{period}")
        
        try:
            with open(self.output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"Exported {len(data)} records to {self.output_csv}")
        except Exception as e:
            print(f"Export error: {str(e)}")

    def update_database(self):
        """Основной метод для обновления базы данных"""
        print("\n" + "="*50)
        print(f"Starting database update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.load_items_data()
        self.load_history_data()
        merged_data = self.merge_data()
        self.export_to_csv(merged_data)
        
        print("Database update completed")
        print("="*50 + "\n")

# Пример использования
if __name__ == "__main__":
    # Пути к файлам (замените на актуальные)
    ITEMS_FILE = "/home/danbar/Desktop/skins-trading-bot/data/skinport-items/skinport_items_2025-06-03T09-44-35-965Z.json"
    HISTORY_FILE = "/home/danbar/Desktop/skins-trading-bot/data/skinport-history/all_sales_history_2025-06-03T16-37-36-710Z.json"
    OUTPUT_CSV = "/home/danbar/Desktop/skins-trading-bot/data/skinport_database.csv"
    
    db = SkinportDatabase(ITEMS_FILE, HISTORY_FILE, OUTPUT_CSV)
    db.update_database()