import requests
import json
import os
from datetime import datetime

def save_skinport_items():
    """Скачивание и сохранение данных с Skinport API"""
    url = "https://api.skinport.com/v1/items"
    
    try:
        # Простейший GET-запрос
        print(f"Загрузка данных с {url}...")
        response = requests.get(url)
        
        # Проверка успешности запроса
        if response.status_code == 200:
            # Прямое сохранение сырых данных
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            directory = "/data/skin-data"
            os.makedirs(directory, exist_ok=True)
            filename = os.path.join(directory, f"skinport_items_{timestamp}.json")
            
            # Сохраняем как есть
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"Данные успешно сохранены в {filename}")
            print(f"Размер файла: {len(response.content) / 1024:.2f} KB")
            return True
        else:
            print(f"Ошибка HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    if save_skinport_items():
        print("Готово! Данные сохранены.")
    else:
        print("Не удалось получить данные.")