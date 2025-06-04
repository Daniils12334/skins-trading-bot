# core/deal_finder.py
import csv
import urllib.parse
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

def find_best_deals(input_csv, output_csv, discount_threshold=-15, min_volume=5, min_price=0.0, max_price=10.0):
    """Анализирует рынок и находит лучшие предложения на основе минимальных цен"""
    best_deals = []
    
    if not os.path.exists(input_csv):
        logger.error(f"Файл {input_csv} не найден!")
        return 0
    
    processed_items = 0
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for item in reader:
            processed_items += 1
            if not item.get('current_min_price'):
                continue
                
            try:
                current_price = float(item['current_min_price'])
                suggested_price = float(item.get('suggested_price', 0))
                
                # Пропускаем предметы вне диапазона цен
                if current_price < min_price or current_price > max_price:
                    continue
                
                # Пропускаем если suggested_price отсутствует или невалиден
                if suggested_price <= 0:
                    continue
                    
                # Рассчитываем скидку относительно suggested_price
                discount_percent = (current_price - suggested_price) / suggested_price * 100
                
                # Проверяем объем торгов
                volume_24h = float(item.get('volume_24h', 0)) or 0
                volume_7d = float(item.get('volume_7d', 0) or 0)
                
                # Условия для "горячего" предложения:
                # 1. Текущая цена ниже suggested_price (с учетом порога)
                # 2. Достаточный объем торгов
                # 3. Исключаем случаи, когда текущая цена равна 0 или отрицательная
                if (current_price > 0 and
                    discount_percent <= discount_threshold and 
                    (volume_24h >= min_volume or volume_7d >= min_volume)):
                    
                    item_name = item['market_hash_name']
                    encoded_name = urllib.parse.quote_plus(item_name)
                    item_url = f"https://skinport.com/market?item={encoded_name}"
                    
                    best_deals.append({
                        'item': item_name,
                        'current_price': current_price,
                        'reference_min_price': suggested_price,  # Используем suggested_price здесь
                        'discount_percent': discount_percent,
                        'url': item_url,
                        'currency': item.get('currency', 'EUR'),
                        'found_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'volume_24h': volume_24h,
                        'volume_7d': volume_7d
                    })
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Ошибка обработки {item.get('market_hash_name', 'unknown')}: {e}")
                continue
    
    # Сортируем по размеру скидки (самые большие скидки вверху)
    best_deals.sort(key=lambda x: x['discount_percent'])
    
    # Сохраняем в CSV
    if best_deals:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        fieldnames = [
            'item', 
            'current_price', 
            'reference_min_price', 
            'discount_percent', 
            'currency', 
            'url', 
            'found_at',
            'volume_24h',
            'volume_7d'
        ]
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(best_deals)
            
        logger.info(f"Найдено {len(best_deals)} выгодных предложений из {processed_items} предметов")
        return len(best_deals)
        
    logger.info("Выгодных предложений не найдено")
    return 0