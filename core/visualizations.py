import os
import csv
import json
import glob
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

def generate_deals_dashboard(best_deals_csv, history_dir, items_dir, output_dir):
    """Генерирует HTML-дашборд с агрегированными историческими данными"""
    # Создаем директорию для вывода
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Загружаем лучшие предложения
    deals = []
    with open(best_deals_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            deals.append(row)
    
    if not deals:
        print("Нет предложений для визуализации")
        return 0
    
    # Собираем все исторические данные
    history_files = glob.glob(os.path.join(history_dir, "*.json"))
    if not history_files:
        print("Исторические данные не найдены")
        return 0
    
    # Собираем данные о текущих предметах
    items_files = glob.glob(os.path.join(items_dir, "*.json"))
    if not items_files:
        print("Данные о предметах не найдены")
        return 0
    
    # Загружаем последние файлы
    latest_history = max(history_files, key=os.path.getctime)
    latest_items = max(items_files, key=os.path.getctime)
    
    with open(latest_history, 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    with open(latest_items, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    # Создаем дашборд
    dashboard_data = []
    
    for deal in deals:
        item_name = deal['item']
        
        # Ищем историю для этого предмета
        item_history = next((item for item in history_data if item['market_hash_name'] == item_name), None)
        if not item_history:
            continue
        
        # Ищем текущие данные о предмете
        current_item = next((item for item in items_data if item['market_hash_name'] == item_name), None)
        if not current_item:
            continue
        
        # Создаем график
        chart_filename = f"chart_{item_name.replace(' ', '_')[:50]}.html"
        chart_path = output_dir / chart_filename
        create_aggregated_chart(deal, item_history, chart_path)
        
        # Собираем статистику
        periods = {
            '24h': item_history.get('last_24_hours', {}),
            '7d': item_history.get('last_7_days', {}),
            '30d': item_history.get('last_30_days', {}),
            '90d': item_history.get('last_90_days', {}),
        }
        
        # Собираем минимальные цены для отображения
        min_prices = {period: data.get('min') for period, data in periods.items() if data}
        
        dashboard_data.append({
            'item': item_name,
            'current_price': float(deal['current_price']),
            'reference_min_price': float(deal['reference_min_price']),
            'discount_percent': float(deal['discount_percent']),
            'url': deal['url'],
            'chart': chart_filename,
            'min_price_24h': min_prices.get('24h', 'N/A'),
            'min_price_7d': min_prices.get('7d', 'N/A'),
            'min_price_30d': min_prices.get('30d', 'N/A'),
            'min_price_90d': min_prices.get('90d', 'N/A'),
            'volume_24h': periods['24h'].get('volume', 0),
            'volume_7d': periods['7d'].get('volume', 0),
            'currency': deal['currency'],
            'item_page': current_item.get('item_page', '#'),
            'market_page': current_item.get('market_page', '#')
        })
    
    # Сортируем по размеру скидки
    dashboard_data.sort(key=lambda x: x['discount_percent'])
    
    # Генерируем HTML дашборд
    generate_html_dashboard(dashboard_data, output_dir / "best_deals_dashboard.html")
    
    return len(dashboard_data)

def create_aggregated_chart(deal, item_history, output_path):
    pass


def generate_html_dashboard(dashboard_data, output_path):
    """Генерирует HTML страницу с дашбордом, поиском и фильтрами"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Лучшие предложения на Skinport</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background-color: #f8f9fa; 
                opacity: 0;
                transition: opacity 0.5s ease-in;
            }}
            body.loaded {{ 
                opacity: 1; 
            }}
            .card {{ 
                transition: transform 0.2s; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                opacity: 0;
                transform: translateY(20px);
                animation: fadeInUp 0.5s forwards;
            }}
            .card:hover {{ 
                transform: translateY(-5px) scale(1.02); 
                box-shadow: 0 12px 20px rgba(0,0,0,0.15); 
            }}
            .discount-badge {{ font-size: 1.1rem; }}
            .item-name {{ font-weight: 600; }}
            .stat-badge {{ font-size: 0.9rem; margin-right: 5px; }}
            .profit-positive {{ color: #28a745; font-weight: bold; }}
            .profit-negative {{ color: #dc3545; font-weight: bold; }}
            .price-card {{ border-left: 4px solid #0d6efd; }}
            .profit-card {{ border-left: 4px solid #198754; }}
            .filter-section {{ 
                background: white; 
                padding: 15px; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                margin-bottom: 20px; 
                opacity: 0;
                transform: translateY(-20px);
                animation: fadeInDown 0.5s 0.3s forwards;
            }}
            .no-items {{ 
                display: none; 
                text-align: center; 
                padding: 30px; 
                opacity: 0;
                animation: fadeIn 0.5s forwards;
            }}
            .btn-reset {{ width: 100%; }}
            #dealsContainer {{
                opacity: 0;
                transition: opacity 0.5s;
            }}
            #dealsContainer.visible {{
                opacity: 1;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
            @keyframes fadeInUp {{
                from {{ 
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{ 
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            @keyframes fadeInDown {{
                from {{ 
                    opacity: 0;
                    transform: translateY(-20px);
                }}
                to {{ 
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            .loading-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.9);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                transition: opacity 0.5s;
            }}
            .spinner {{
                width: 3rem;
                height: 3rem;
            }}
        </style>
    </head>
    <body>
        <div class="loading-overlay" id="loadingOverlay">
            <div class="spinner-border text-primary spinner" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
        </div>
        
        <div class="container py-4">
            <div class="text-center mb-4">
                <h1 class="display-4"><i class="fa-solid fa-coins text-primary"></i> Лучшие предложения на Skinport</h1>
                <p class="lead">Актуальные скидки на предметы CS2 с расчётом прибыли после комиссии</p>
                <p class="text-muted">Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <!-- Панель фильтров и поиска -->
            <div class="filter-section">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <div class="input-group">
                            <span class="input-group-text"><i class="fa-solid fa-search"></i></span>
                            <input type="text" id="searchInput" class="form-control" placeholder="Поиск по названию предмета...">
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <select id="profitFilter" class="form-select">
                            <option value="all">Вся прибыль</option>
                            <option value="positive">Только прибыльные</option>
                            <option value="negative">Только убыточные</option>
                        </select>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <select id="volumeFilter" class="form-select">
                            <option value="all">Любой объем</option>
                            <option value="high">Высокий объем (>20)</option>
                            <option value="medium">Средний объем (5-20)</option>
                            <option value="low">Низкий объем (<5)</option>
                        </select>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <div class="input-group">
                            <span class="input-group-text">Мин. прибыль</span>
                            <input type="number" id="minProfit" class="form-control" placeholder="0.00" step="0.01" value="0.10">
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="input-group">
                            <span class="input-group-text">Макс. цена</span>
                            <input type="number" id="maxPrice" class="form-control" placeholder="10.00" step="0.01" value="10.00">
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="input-group">
                            <span class="input-group-text">Мин. скидка</span>
                            <input type="number" id="minDiscount" class="form-control" placeholder="20" step="1" value="10">
                            <span class="input-group-text">%</span>
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="d-flex gap-2">
                            <button id="applyFilters" class="btn btn-primary btn-reset">
                                <i class="fa-solid fa-filter"></i> Применить
                            </button>
                            <button id="resetFilters" class="btn btn-outline-danger btn-reset">
                                <i class="fa-solid fa-rotate-left"></i> Сбросить
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="noItemsMessage" class="no-items alert alert-warning">
                <h4><i class="fa-solid fa-exclamation-circle"></i> Предметы не найдены</h4>
                <p>Попробуйте изменить параметры фильтров</p>
            </div>
            
            <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4" id="dealsContainer">
    """
    
    for i, item in enumerate(dashboard_data):
        # Рассчитываем финансовые показатели
        commission_rate = 0.12
        current_price = float(item['current_price'])
        reference_price = float(item['reference_min_price'])
        revenue_after_commission = reference_price * (1 - commission_rate)
        profit = revenue_after_commission - current_price
        
        if current_price > 0:
            profitability = (profit / current_price) * 100
        else:
            profitability = 0
        
        # Форматируем цены
        current_price_fmt = f"{current_price:.2f}"
        reference_price_fmt = f"{reference_price:.2f}"
        revenue_fmt = f"{revenue_after_commission:.2f}"
        profit_fmt = f"{profit:.2f}"
        profitability_fmt = f"{profitability:.1f}%"
        
        # Определяем класс для стилизации прибыли
        profit_class = "profit-positive" if profit > 0 else "profit-negative"
        profit_icon = "fa-arrow-up" if profit > 0 else "fa-arrow-down"
        
        # Цвет скидки
        discount_color = "danger" if item['discount_percent'] < -15 else "warning"
        
        # Статистика объемов
        volume_html = f"""
        <div class="d-flex flex-wrap mb-2">
            <span class="badge bg-info stat-badge">Объем 24ч: {item['volume_24h']}</span>
            <span class="badge bg-info stat-badge">Объем 7д: {item['volume_7d']}</span>
        </div>
        """
        
        # Добавляем задержку для анимации
        animation_delay = i * 0.05
        html_content += f"""
                <div class="col deal-card" data-name="{item['item'].lower()}" 
                    data-profit="{profit}" data-price="{current_price}" 
                    data-discount="{abs(float(item['discount_percent']))}" 
                    data-volume24h="{item['volume_24h']}"
                    style="animation-delay: {animation_delay}s;">
                    <div class="card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div>
                                    <h5 class="card-title item-name">{item['item']}</h5>
                                    {volume_html}
                                </div>
                                <span class="badge bg-{discount_color} discount-badge">
                                    <i class="fa-solid fa-tag"></i> {item['discount_percent']:.1f}%
                                </span>
                            </div>
                            
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <div class="card price-card h-100">
                                        <div class="card-header bg-primary text-white">
                                            <i class="fa-solid fa-money-bill-wave"></i> Цены
                                        </div>
                                        <div class="card-body">
                                            <div class="d-flex justify-content-between mb-2">
                                                <span>Покупка:</span>
                                                <strong>{current_price_fmt} {item['currency']}</strong>
                                            </div>
                                            
                                            <div class="d-flex justify-content-between mb-2">
                                                <span>Продажа (план):</span>
                                                <strong>{reference_price_fmt} {item['currency']}</strong>
                                            </div>
                                            
                                            <div class="d-flex justify-content-between">
                                                <span>Выручка после комиссии 12%:</span>
                                                <strong>{revenue_fmt} {item['currency']}</strong>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <div class="card profit-card h-100">
                                        <div class="card-header bg-success text-white">
                                            <i class="fa-solid fa-chart-line"></i> Прибыль
                                        </div>
                                        <div class="card-body">
                                            <div class="d-flex justify-content-between mb-2">
                                                <span>Ожидаемая:</span>
                                                <strong class="{profit_class}">
                                                    <i class="fa-solid {profit_icon}"></i> {profit_fmt} {item['currency']}
                                                </strong>
                                            </div>
                                            
                                            <div class="d-flex justify-content-between mb-2">
                                                <span>Рентабельность:</span>
                                                <strong class="{profit_class}">{profitability_fmt}</strong>
                                            </div>
                                            
                                            <div class="d-flex justify-content-between">
                                                <span>Скидка от плана:</span>
                                                <strong class="text-{discount_color}">
                                                    {item['discount_percent']:.1f}%
                                                </strong>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="d-grid gap-2 mt-3">
                                <a href="{item['url']}" class="btn btn-primary" target="_blank">
                                    <i class="fa-solid fa-cart-shopping"></i> Купить на Skinport
                                </a>
                                
                                <div class="d-grid gap-2">
                                    <a href="{item['item_page']}" class="btn btn-outline-secondary" target="_blank">
                                        <i class="fa-solid fa-info-circle"></i> Страница предмета
                                    </a>
                                    <a href="{item['market_page']}" class="btn btn-outline-secondary" target="_blank">
                                        <i class="fa-solid fa-store"></i> Весь рынок
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const body = document.body;
                const loadingOverlay = document.getElementById('loadingOverlay');
                const dealsContainer = document.getElementById('dealsContainer');
                const searchInput = document.getElementById('searchInput');
                const profitFilter = document.getElementById('profitFilter');
                const volumeFilter = document.getElementById('volumeFilter');
                const minProfitInput = document.getElementById('minProfit');
                const maxPriceInput = document.getElementById('maxPrice');
                const minDiscountInput = document.getElementById('minDiscount');
                const applyFiltersBtn = document.getElementById('applyFilters');
                const resetFiltersBtn = document.getElementById('resetFilters');
                const noItemsMessage = document.getElementById('noItemsMessage');
                
                // Значения по умолчанию
                const DEFAULT_FILTERS = {
                    search: '',
                    profitType: 'positive',
                    volumeLevel: 'all',
                    minProfit: '0.10',
                    maxPrice: '10.00',
                    minDiscount: '10'
                };
                
                // Загружаем сохраненные фильтры из localStorage
                function loadFilters() {
                    const savedFilters = JSON.parse(localStorage.getItem('dealFilters')) || {};
                    
                    // Применяем сохраненные значения или значения по умолчанию
                    searchInput.value = savedFilters.search || DEFAULT_FILTERS.search;
                    profitFilter.value = savedFilters.profitType || DEFAULT_FILTERS.profitType;
                    volumeFilter.value = savedFilters.volumeLevel || DEFAULT_FILTERS.volumeLevel;
                    minProfitInput.value = savedFilters.minProfit || DEFAULT_FILTERS.minProfit;
                    maxPriceInput.value = savedFilters.maxPrice || DEFAULT_FILTERS.maxPrice;
                    minDiscountInput.value = savedFilters.minDiscount || DEFAULT_FILTERS.minDiscount;
                }
                
                // Сохраняем фильтры в localStorage
                function saveFilters() {
                    const filters = {
                        search: searchInput.value,
                        profitType: profitFilter.value,
                        volumeLevel: volumeFilter.value,
                        minProfit: minProfitInput.value,
                        maxPrice: maxPriceInput.value,
                        minDiscount: minDiscountInput.value
                    };
                    localStorage.setItem('dealFilters', JSON.stringify(filters));
                }
                
                // Сброс фильтров к значениям по умолчанию
                function resetFilters() {
                    searchInput.value = DEFAULT_FILTERS.search;
                    profitFilter.value = DEFAULT_FILTERS.profitType;
                    volumeFilter.value = DEFAULT_FILTERS.volumeLevel;
                    minProfitInput.value = DEFAULT_FILTERS.minProfit;
                    maxPriceInput.value = DEFAULT_FILTERS.maxPrice;
                    minDiscountInput.value = DEFAULT_FILTERS.minDiscount;
                    
                    saveFilters();
                    filterDeals();
                }
                
                // Функция фильтрации и сортировки сделок
                function filterDeals() {
                    const searchTerm = searchInput.value.toLowerCase();
                    const profitType = profitFilter.value;
                    const volumeLevel = volumeFilter.value;
                    const minProfit = parseFloat(minProfitInput.value) || -Infinity;
                    const maxPrice = parseFloat(maxPriceInput.value) || Infinity;
                    const minDiscount = parseFloat(minDiscountInput.value) || 0;
                    
                    let visibleCards = [];
                    
                    // Собираем все карточки сделок
                    document.querySelectorAll('.deal-card').forEach(card => {
                        const name = card.dataset.name;
                        const profit = parseFloat(card.dataset.profit);
                        const price = parseFloat(card.dataset.price);
                        const discount = parseFloat(card.dataset.discount);
                        const volume24h = parseFloat(card.dataset.volume24h);
                        
                        // Проверяем соответствие фильтрам
                        const matchesSearch = name.includes(searchTerm);
                        const matchesProfitType = 
                            (profitType === 'all') || 
                            (profitType === 'positive' && profit > 0) || 
                            (profitType === 'negative' && profit <= 0);
                        const matchesMinProfit = profit >= minProfit;
                        const matchesMaxPrice = price <= maxPrice;
                        const matchesMinDiscount = discount >= minDiscount;
                        
                        // Проверка объема
                        let matchesVolume = true;
                        if (volumeLevel === 'high') matchesVolume = volume24h > 20;
                        else if (volumeLevel === 'medium') matchesVolume = volume24h >= 5 && volume24h <= 20;
                        else if (volumeLevel === 'low') matchesVolume = volume24h < 5;
                        
                        // Показываем/скрываем карточку
                        if (matchesSearch && matchesProfitType && matchesMinProfit && 
                            matchesMaxPrice && matchesMinDiscount && matchesVolume) {
                            card.style.display = 'block';
                            visibleCards.push(card);
                        } else {
                            card.style.display = 'none';
                        }
                    });
                    
                    // Сортируем по прибыли (от большей к меньшей)
                    visibleCards.sort((a, b) => {
                        const profitA = parseFloat(a.dataset.profit);
                        const profitB = parseFloat(b.dataset.profit);
                        return profitB - profitA;
                    });
                    
                    // Переупорядочиваем карточки в контейнере
                    const container = document.getElementById('dealsContainer');
                    container.innerHTML = '';
                    visibleCards.forEach(card => {
                        container.appendChild(card);
                    });
                    
                    // Показываем сообщение, если нет видимых элементов
                    noItemsMessage.style.display = visibleCards.length > 0 ? 'none' : 'block';
                    
                    // Сохраняем фильтры
                    saveFilters();
                    
                    // Показываем контейнер после фильтрации
                    dealsContainer.classList.add('visible');
                }
                
                // События для элементов управления
                searchInput.addEventListener('input', filterDeals);
                profitFilter.addEventListener('change', filterDeals);
                volumeFilter.addEventListener('change', filterDeals);
                minProfitInput.addEventListener('input', filterDeals);
                maxPriceInput.addEventListener('input', filterDeals);
                minDiscountInput.addEventListener('input', filterDeals);
                applyFiltersBtn.addEventListener('click', filterDeals);
                resetFiltersBtn.addEventListener('click', resetFilters);
                
                // Инициализируем фильтры
                loadFilters();
                
                // Задержка для демонстрации загрузки
                setTimeout(() => {
                    filterDeals();
                    
                    // Скрываем индикатор загрузки и показываем контент
                    loadingOverlay.style.opacity = '0';
                    body.classList.add('loaded');
                    
                    setTimeout(() => {
                        loadingOverlay.style.display = 'none';
                    }, 500);
                }, 500);
            });
        </script>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def format_price(price):
    """Форматирует цену для отображения"""
    if price is None:
        return "N/A"
    try:
        return f"{float(price):.2f}"
    except:
        return "N/A"