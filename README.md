# Project Structure

## Project Sections

- [📂 Core (Main Logic)](core/README.md)
- [📂 Markets (Work with API)](markets/README.md)
- [📂 Data (Storage Structure)](data/README.md)
- [📂 ML (Model Training)](ml/README.md)


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


```mermaid
sequenceDiagram
    participant Engine as 🚀 Engine (engine.py)
    participant JS_API as 📦 JS API (skinport_items.js + skinport_history.js)
    participant DB as 🗄️ Database (database.py)
    participant Analyzer as 🔍 Deal Analyzer (deal_finder.py)
    participant Visuals as 📊 Visualization Engine (visualizations.py)
    participant CSV as 💾 Market Data (skinport_market_analysis.csv)
    participant HTML as 🌐 Dashboard (deals_dashboard.html)

    Note over Engine, JS_API: Data Collection Phase
    Engine->>JS_API: Execute JavaScript collectors
    JS_API-->>Engine: Return item/history JSON datasets

    Note over Engine, DB: Data Processing Phase
    Engine->>DB: Process & integrate market data
    DB->>CSV: Persist analyzed market trends

    Note over Engine, Analyzer: Deal Discovery Phase
    Engine->>Analyzer: Find profitable opportunities
    Analyzer-->>Engine: Return top-ranked deals

    Note over Engine, Visuals: Visualization Phase
    Engine->>Visuals: Generate interactive dashboard
    Visuals-->>HTML: Render HTML with live charts

    Note over HTML: User Interaction
    HTML->>Visuals: Dynamic data filtering (on user action)
    Visuals-->>HTML: Update visualizations in real-time