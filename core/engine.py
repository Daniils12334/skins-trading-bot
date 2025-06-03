import subprocess
import time

JS_FILE = "/home/danbar/Desktop/skins-trading-bot/markets/skinport.js"
NODE_CMD = ["node", JS_FILE]

while True:
    print("Запускаю skinport.js...")
    result = subprocess.run(NODE_CMD, capture_output=True, text=True)
    
    print("Результат выполнения:")
    print(result.stdout)

    if result.stderr:
        print("⚠️ Ошибка:", result.stderr)

    print("Жду 10 минут...\n")
    time.sleep(600)  # 600 секунд = 10 минут
