import subprocess
import time
import os
import glob
import csv
import json
from datetime import datetime
import yaml
from data.database import SkinportDatabase
from core.deal_finder import find_best_deals
from core.visualizations import generate_deals_dashboard
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Получаем абсолютный путь к корню проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Загрузка конфигурации
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.yaml')
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# Конфигурация путей
JS_DIR = os.path.join(PROJECT_ROOT, "markets")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MARKET_DATA_CSV = os.path.join(DATA_DIR, "market_data.csv")  # Абсолютный путь
ITEMS_DIR = os.path.join(DATA_DIR, "skinport-items")
HISTORY_DIR = os.path.join(DATA_DIR, "skinport-history")
BEST_DEALS_CSV = os.path.join(DATA_DIR, "best_deals.csv")    # Абсолютный путь
DASHBOARD_DIR = os.path.join(DATA_DIR, "dashboard")          # Директория для дашборда

# Параметры из конфига с приоритетом для deal_finder
deal_finder_config = config.get('deal_finder', {})
trading_config = config.get('trading', {})

min_price = trading_config.get('min_item_price', 0.0)
max_price = trading_config.get('max_item_price', 10.0)
min_volume = deal_finder_config.get('min_volume', trading_config.get('min_volume', 5))
discount_threshold = deal_finder_config.get('discount_threshold', -5.0)

def create_directories():
    """Создает необходимые директории"""
    os.makedirs(ITEMS_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    os.makedirs(DASHBOARD_DIR, exist_ok=True)  # Создаем директорию для дашборда
    logger.info(f"📁 Директории созданы:\n- {ITEMS_DIR}\n- {HISTORY_DIR}\n- {DASHBOARD_DIR}")

def get_latest_file(directory):
    """Возвращает последний созданный файл в указанной директории"""
    files = glob.glob(os.path.join(directory, "*.json"))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def run_skinport_js(script_name, timeout=180):
    """Запускает JS-скрипт с таймаутом"""
    js_path = os.path.join(JS_DIR, script_name)
    
    if not os.path.exists(js_path):
        raise FileNotFoundError(f"JS файл не найден: {js_path}")
    
    try:
        logger.info(f"Запуск JS-скрипта: {script_name}")
        result = subprocess.run(
            ["node", js_path],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        logger.error(f"JS скрипт {script_name} превысил время выполнения ({timeout} сек)")
        return subprocess.CompletedProcess(
            args=["node", js_path],
            returncode=-1,
            stdout="",
            stderr=f"Timeout after {timeout} seconds"
        )

def update_database():
    """Обновляет базу данных с использованием последних файлов"""
    try:
        latest_items = get_latest_file(ITEMS_DIR)
        latest_history = get_latest_file(HISTORY_DIR)
        
        if not latest_items:
            logger.warning("Файлы предметов не найдены")
        if not latest_history:
            logger.warning("Файлы истории не найдены")
        if not latest_items or not latest_history:
            return
        
        logger.info(f"🔄 Обновляю базу данных:")
        logger.info(f"- Items: {os.path.basename(latest_items)}")
        logger.info(f"- History: {os.path.basename(latest_history)}")
        
        db = SkinportDatabase(latest_items, latest_history, MARKET_DATA_CSV)
        db.update_database()
        
        logger.info(f"✅ База данных успешно обновлена")
    except Exception as e:
        logger.error(f"⛔ Ошибка при обновлении базы: {str(e)}")

def run_deal_finder():
    """Ищет лучшие предложения и сохраняет в CSV"""
    if not config.get('deal_finder', {}).get('enabled', True):
        logger.info("🔍 Поиск предложений отключен в конфигурации")
        return 0
        
    logger.info("🔍 Поиск лучших предложений...")
    try:
        deals_count = find_best_deals(
            input_csv=MARKET_DATA_CSV,  # Используем абсолютный путь
            output_csv=BEST_DEALS_CSV,   # Используем абсолютный путь
            discount_threshold=discount_threshold,
            min_volume=min_volume,
            min_price=min_price,
            max_price=max_price
        )
        logger.info(f"✅ Найдено выгодных предложений: {deals_count}")
        return deals_count
    except Exception as e:
        logger.error(f"⛔ Ошибка при поиске предложений: {str(e)}")
        return 0

def check_deals_file():
    """Проверяет и выводит информацию о файле с предложениями"""
    if not os.path.exists(BEST_DEALS_CSV):
        logger.warning(f"Файл предложений не найден: {BEST_DEALS_CSV}")
        return 0
    
    try:
        with open(BEST_DEALS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            deals = list(reader)
            logger.info(f"Файл {BEST_DEALS_CSV} содержит {len(deals)} предложений")
            
            if deals:
                logger.info("Примеры предложений:")
                for i, deal in enumerate(deals[:3]):  # Показать первые 3
                    logger.info(f"{i+1}. {deal['item']} - Цена: {deal['current_price']} {deal.get('currency', 'EUR')}")
            
            return len(deals)
    except Exception as e:
        logger.error(f"Ошибка чтения файла предложений: {str(e)}")
        return 0

def check_history_data():
    """Проверяет и выводит информацию о исторических данных (адаптировано под новую структуру)"""
    history_files = glob.glob(os.path.join(HISTORY_DIR, "*.json"))
    if not history_files:
        logger.warning("Исторические данные не найдены")
        return 0
    
    latest_history = max(history_files, key=os.path.getctime)
    logger.info(f"Последний файл истории: {os.path.basename(latest_history)}")
    
    try:
        with open(latest_history, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
            logger.info(f"Файл истории содержит {len(history_data)} предметов")
            
            if history_data:
                # Проверяем структуру данных
                sample_item = history_data[0]
                logger.info(f"Пример элемента истории:")
                logger.info(f" - Имя: {sample_item.get('market_hash_name')}")
                
                # Проверяем наличие данных за периоды
                for period in ['last_24_hours', 'last_7_days', 'last_30_days', 'last_90_days']:
                    period_data = sample_item.get(period, {})
                    min_price = period_data.get('min', 'N/A')
                    volume = period_data.get('volume', 'N/A')
                    logger.info(f" - {period}: мин={min_price}, объем={volume}")
            
            return len(history_data)
    except Exception as e:
        logger.error(f"Ошибка чтения файла истории: {str(e)}")
        return 0

def generate_dashboard():
    """Генерирует дашборд с визуализацией данных"""
    if not config.get('visualization', {}).get('enabled', True):
        logger.info("Визуализация отключена в конфигурации")
        return 0
    
    logger.info("\n📊 Генерация визуализации...")
    try:
        deals_count = generate_deals_dashboard(
            best_deals_csv=BEST_DEALS_CSV,
            history_dir=HISTORY_DIR,
            items_dir=ITEMS_DIR,
            output_dir=DASHBOARD_DIR
        )
        dashboard_path = os.path.join(DASHBOARD_DIR, "best_deals_dashboard.html")
        logger.info(f"✅ Дашборд создан: {dashboard_path} (предложений: {deals_count})")
            
        if deals_count == 0:
            logger.warning("⚠️ На дашборде нет предложений. Возможные причины:")
            logger.warning("1. Несоответствие имен предметов между best_deals.csv и историческими данными")
            logger.warning("2. Отсутствие данных о продажах для найденных предметов")
            logger.warning("3. Ошибки в формате исторических данных")
        
        return deals_count
    except Exception as e:
        logger.error(f"⛔ Ошибка при генерации дашборда: {str(e)}")
        return 0

def run_engine():
    """Основной цикл работы бота"""
    try:
        logger.info("\n" + "="*50)
        logger.info(f"🚀 Запуск системы мониторинга Skinport")
        logger.info(f"⚙️ Конфигурация: {CONFIG_PATH}")
        logger.info(f"📂 Корневая директория: {PROJECT_ROOT}")
        logger.info(f"💾 База данных: {MARKET_DATA_CSV}")
        logger.info(f"💎 Лучшие предложения: {BEST_DEALS_CSV}")
        logger.info(f"📊 Директория дашборда: {DASHBOARD_DIR}")
        logger.info("="*50 + "\n")
        
        # Проверка JS файлов
        items_js = os.path.join(JS_DIR, "skinport_items.js")
        history_js = os.path.join(JS_DIR, "skinport_history.js")
        
        if not os.path.exists(items_js):
            raise FileNotFoundError(f"Файл не найден: {items_js}")
        if not os.path.exists(history_js):
            raise FileNotFoundError(f"Файл не найден: {history_js}")
        
        create_directories()
        items_counter = 0
        last_history_update = 0
        
        while True:
            current_time = time.time()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"\n{timestamp} Начало цикла")
            
            # Обновление предметов
            logger.info("\n🔄 Обновление текущих предметов...")
            items_result = run_skinport_js("skinport_items.js")
            items_counter += 1
            
            logger.info(f"Результат ({items_counter}):")
            if items_result.stdout:
                logger.info(items_result.stdout.strip())
            if items_result.stderr:
                logger.error(f"⚠️ Ошибка: {items_result.stderr.strip()}")
            
            # Обновление истории раз в 24 часа
            if current_time - last_history_update > 86400:  # 24 часа
                logger.info("\n🕒 Обновление истории продаж...")
                history_result = run_skinport_js("skinport_history.js")
                
                logger.info("Результат:")
                if history_result.stdout:
                    logger.info(history_result.stdout.strip())
                if history_result.stderr:
                    logger.error(f"⚠️ Ошибка: {history_result.stderr.strip()}")
                
                last_history_update = current_time
                next_update_time = datetime.fromtimestamp(last_history_update + 86400).strftime('%Y-%m-%d %H:%M')
                logger.info(f"⏱️ Следующее обновление истории: {next_update_time}")
            else:
                next_update_time = datetime.fromtimestamp(last_history_update + 86400).strftime('%Y-%m-%d %H:%M')
                logger.info(f"⏳ История будет обновлена: {next_update_time}")
            
            # Обновление базы данных
            logger.info("\n📊 Обновление базы данных...")
            update_database()
            
            # Поиск лучших предложений
            logger.info("\n🔍 Поиск лучших предложений...")
            deals_count = run_deal_finder()
            
            # Диагностика данных перед генерацией дашборда
            logger.info("\n🔍 Проверка данных для дашборда...")
            actual_deals_count = check_deals_file()
            history_items_count = check_history_data()
            
            # Генерация визуализации
            generate_dashboard()
            
            # Ожидание следующего цикла
            wait_time = config.get('update_interval', 500)
            logger.info(f"\n⏳ Следующее обновление через {wait_time} секунд...")
            time.sleep(wait_time)
            
    except Exception as e:
        logger.error(f"\n❌❌❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        logger.error("="*50)
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run_engine()