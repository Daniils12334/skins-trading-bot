```text
skins_trading_bot/
│
├── main.py                      # Точка входа (запускает бота)
├── config.yaml                  # Конфигурации (ключи, тайминги, лимиты, фильтры)
├── requirements.txt             # Зависимости проекта
│
├── 📁 core/                     # Бизнес-логика
│   ├── engine.py                # Основной цикл: сканирование, анализ, торговля
│   ├── strategy.py              # Торговые стратегии (например, отклонение от медианы)
│   ├── scheduler.py             # Планирование задач (например, парс каждые 30 мин)
│
├── 📁 markets/                  # Адаптеры к разным площадкам
│   ├── __init__.py
│   ├── skinport.py              # Обёртка API Skinport
│   ├── lis_skins.py             # Обёртка API LisSkins
│   └── steam.py                 # Получение цен с маркетплейса Steam
│
├── 📁 data/                     # Работа с данными
│   ├── price_tracker.py         # История цен, медианы и отклонения
│   ├── database.py              # База данных предметов и сделок (SQLite/PostgreSQL)
│   └── history/                 # CSV/JSON-логи с историей цен
│
├── 📁 ml/                       # ML/анализ моделей
│   ├── feature_engineering.py   # Преобразование данных в признаки
│   ├── model.py                 # Модели прогнозов и аномалий
│   └── trainer.py               # Обучение моделей
│
├── 📁 utils/                    # Утилиты
│   ├── logger.py                # Логирование
│   └── helpers.py               # Разные вспомогательные функции
│
└── 📁 tests/                    # Юнит-тесты
    ├── test_engine.py
    └── test_strategies.py

```