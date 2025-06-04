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
    # """Создает график минимальных цен за периоды"""
    # try:
    #     # Периоды и их метки
    #     periods = ['24h', '7d', '30d', '90d']
    #     period_labels = ['24 часа', '7 дней', '30 дней', '90 дней']
        
    #     # Собираем минимальные цены для каждого периода
    #     min_prices = []
        
    #     for period in periods:
    #         period_key = f'last_{period}'
    #         period_data = item_history.get(period_key, {})
    #         min_price = period_data.get('min')
    #         min_prices.append(min_price)

    #     # Создаем график
    #     fig = go.Figure()
        
    #     # Минимальные цены - толстая синяя линия с точками и значениями
    #     fig.add_trace(go.Scatter(
    #         x=period_labels, 
    #         y=min_prices,
    #         mode='lines+markers+text',
    #         name='Минимальная цена',
    #         line=dict(color='blue', width=4),
    #         marker=dict(size=12, color='blue'),
    #         text=[f"{p:.2f}" if p is not None else "N/A" for p in min_prices],
    #         textposition="top center",
    #         textfont=dict(size=12, color='blue')
    #     ))
        
    #     # Добавляем заголовок
    #     title_text = f"{deal['item']} - Минимальные цены"
        
    #     # Настраиваем оформление
    #     fig.update_layout(
    #         title=dict(text=title_text, font=dict(size=16)),
    #         xaxis_title="Период",
    #         yaxis_title=f"Минимальная цена ({deal['currency']})",
    #         legend=dict(
    #             orientation="h",
    #             yanchor="bottom",
    #             y=1.02,
    #             xanchor="center",
    #             x=0.5
    #         ),
    #         hovermode="x unified",
    #         template="plotly_white",
    #         showlegend=True,
    #         margin=dict(l=50, r=50, t=80, b=50),
    #         height=500
    #     )
        
    #     # Настраиваем оси
    #     fig.update_yaxes(
    #         title_font=dict(color='blue', size=14),
    #         tickfont=dict(color='blue', size=12),
    #         showgrid=True,
    #         gridwidth=1,
    #         gridcolor='LightGrey'
    #     )
        
    #     fig.update_xaxes(
    #         title_font=dict(size=14), 
    #         tickfont=dict(size=12),
    #         showgrid=True,
    #         gridwidth=1,
    #         gridcolor='LightGrey'
    #     )
        
    #     # Сохраняем график
    #     fig.write_html(output_path)
        
    # except Exception as e:
    #     print(f"Ошибка создания графика для {deal['item']}: {str(e)}")
    #     import traceback
    #     print(traceback.format_exc())
        
    #     # Создаем простой график с сообщением об ошибке
    #     fig = go.Figure()
    #     fig.update_layout(
    #         title=f"{deal['item']} - Ошибка данных",
    #         xaxis=dict(visible=False),
    #         yaxis=dict(visible=False),
    #         annotations=[dict(
    #             text=f"Ошибка: {str(e)}",
    #             xref="paper",
    #             yref="paper",
    #             x=0.5,
    #             y=0.5,
    #             showarrow=False,
    #             font=dict(size=16)
    #         )]
    #     )
    #     fig.write_html(output_path)


# core/visualizations.py (обновлённая функция generate_html_dashboard)

def generate_html_dashboard(dashboard_data, output_path):
    """Генерирует HTML страницу с дашбордом и расчётом прибыли без графиков"""
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
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; }}
            .card {{ transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }}
            .discount-badge {{ font-size: 1.1rem; }}
            .item-name {{ font-weight: 600; }}
            .stat-badge {{ font-size: 0.9rem; margin-right: 5px; }}
            .profit-positive {{ color: #28a745; font-weight: bold; }}
            .profit-negative {{ color: #dc3545; font-weight: bold; }}
            .price-card {{ border-left: 4px solid #0d6efd; }}
            .profit-card {{ border-left: 4px solid #198754; }}
        </style>
    </head>
    <body>
        <div class="container py-4">
            <div class="text-center mb-4">
                <h1 class="display-4"><i class="fa-solid fa-coins text-primary"></i> Лучшие предложения на Skinport</h1>
                <p class="lead">Актуальные скидки на предметы CS2 с расчётом прибыли после комиссии</p>
                <p class="text-muted">Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
    """
    
    for item in dashboard_data:
        # Рассчитываем финансовые показатели
        commission_rate = 0.12
        current_price = float(item['current_price'])
        reference_price = float(item['reference_min_price'])
        
        # Выручка после вычета комиссии 12%
        revenue_after_commission = reference_price * (1 - commission_rate)
        
        # Прибыль (выручка минус затраты на покупку)
        profit = revenue_after_commission - current_price
        
        # Рентабельность (%)
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
        
        html_content += f"""
                <div class="col">
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
                                <!-- Карточка цен -->
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
                                
                                <!-- Карточка прибыли -->
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