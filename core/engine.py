import subprocess
import time
import os
import glob
from datetime import datetime
import yaml  # Убедитесь что установлен pyyaml (pip install pyyaml)
from data.database import SkinportDatabase
from core.deal_finder import find_best_deals
import logger
from core.visualizations import generate_deals_dashboard
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
ITEMS_DIR = os.path.join(DATA_DIR, "skinport-items")
HISTORY_DIR = os.path.join(DATA_DIR, "skinport-history")
OUTPUT_CSV = os.path.join(DATA_DIR, "skinport_market_analysis.csv")
BEST_DEALS_CSV = os.path.join(DATA_DIR, "best_deals.csv")

def create_directories():
    """Создает необходимые директории, если они отсутствуют"""
    os.makedirs(ITEMS_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    print(f"📁 Директории созданы:\n- {ITEMS_DIR}\n- {HISTORY_DIR}")

def get_latest_file(directory):
    """Возвращает последний созданный файл в указанной директории"""
    files = glob.glob(os.path.join(directory, "*.json"))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def run_skinport_js(script_name, timeout=120):
    """Запускает JS-скрипт с таймаутом"""
    js_path = os.path.join(JS_DIR, script_name)
    
    if not os.path.exists(js_path):
        raise FileNotFoundError(f"JS файл не найден: {js_path}")
    
    try:
        result = subprocess.run(
            ["node", js_path],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout  # Таймаут выполнения
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
        
        if not latest_items or not latest_history:
            return
        
        print(f"🔄 Обновляю базу данных:")
        print(f"- Items: {os.path.basename(latest_items)}")
        print(f"- History: {os.path.basename(latest_history)}")
        
        db = SkinportDatabase(latest_items, latest_history, OUTPUT_CSV)
        db.update_database()
        
        print(f"✅ База данных успешно обновлена")
    except Exception as e:
        print(f"⛔ Ошибка при обновлении базы: {str(e)}")

def run_deal_finder():
    """Ищет лучшие предложения и сохраняет в CSV"""
    if not config.get('deal_finder', {}).get('enabled', True):
        return 0
        
    print("🔍 Поиск лучших предложений...")
    try:
        deals_count = find_best_deals(
            input_csv=OUTPUT_CSV,
            output_csv=BEST_DEALS_CSV,
            discount_threshold=config['deal_finder'].get('discount_threshold', -12),
            min_volume=config['deal_finder'].get('min_volume', 3)
        )
        print(f"✅ Найдено выгодных предложений: {deals_count}")
        return deals_count
    except Exception as e:
        print(f"⛔ Ошибка при поиске предложений: {str(e)}")
        return 0

def run_engine():
    """Основной цикл выполнения"""
    try:
        print("\n" + "="*50)
        print(f"🚀 Запуск системы мониторинга Skinport")
        print(f"⚙️ Конфигурация: {CONFIG_PATH}")
        print(f"📂 Корневая директория: {PROJECT_ROOT}")
        print(f"💾 База данных: {OUTPUT_CSV}")
        print(f"💎 Лучшие предложения: {BEST_DEALS_CSV}")
        print("="*50 + "\n")
        
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
            print(f"\n{timestamp} Начало цикла")
            
            # Обновление предметов
            print("\n🔄 Обновление текущих предметов...")
            items_result = run_skinport_js("skinport_items.js")
            items_counter += 1
            
            print(f"Результат ({items_counter}):")
            if items_result.stdout:
                print(items_result.stdout.strip())
            if items_result.stderr:
                print(f"⚠️ Ошибка: {items_result.stderr.strip()}")
            
            # Обновление истории раз в 24 часа
            if current_time - last_history_update > 86400:  # 24 часа
                print("\n🕒 Обновление истории продаж...")
                history_result = run_skinport_js("skinport_history.js")
                
                print("Результат:")
                if history_result.stdout:
                    print(history_result.stdout.strip())
                if history_result.stderr:
                    print(f"⚠️ Ошибка: {history_result.stderr.strip()}")
                
                last_history_update = current_time
                print(f"⏱️ Следующее обновление истории: {datetime.fromtimestamp(last_history_update + 86400).strftime('%Y-%m-%d %H:%M')}")
            else:
                next_update = datetime.fromtimestamp(last_history_update + 86400).strftime('%Y-%m-%d %H:%M')
                print(f"⏳ История будет обновлена: {next_update}")
            
            # Обновление базы данных
            print("\n📊 Обновление базы данных...")
            update_database()
            
            # Поиск лучших предложений
            run_deal_finder()

            if config.get('visualization', {}).get('enabled', True):
                print("\n📊 Генерация визуализации...")
                dashboard_dir = os.path.join(DATA_DIR, "dashboard")
                deals_count = generate_deals_dashboard(
                    best_deals_csv=BEST_DEALS_CSV,
                    items_dir=ITEMS_DIR,
                    output_dir=dashboard_dir
                )
                dashboard_path = os.path.join(dashboard_dir, "best_deals_dashboard.html")
                print(f"✅ Дашборд создан: {dashboard_path} (предложений: {deals_count})")
            
            # Ожидание следующего цикла
            wait_time = config.get('update_interval', 120)
            print(f"\n⏳ Следующее обновление через {wait_time} секунд...")
            time.sleep(wait_time)
            
    except Exception as e:
        print(f"\n❌❌❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        print("="*50)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_engine()