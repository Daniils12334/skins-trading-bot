import os
import csv
import json
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def generate_deals_dashboard(best_deals_csv, items_dir, output_dir):
    """Генерирует HTML-дашборд с лучшими предложениями и графиками"""
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
        return
    
    # Собираем данные для дашборда
    dashboard_data = []
    
    for deal in deals:
        # Ищем JSON файл с детальной информацией о предмете
        item_data = find_item_data(deal['item'], items_dir)
        if not item_data:
            continue
        # Генерируем имя и путь для графика
        chart_filename = f"{deal['item'].replace('/', '_').replace(' ', '_')}_chart.html"
        chart_path = output_dir / chart_filename
        create_price_chart(deal, item_data, chart_path)
        # Формируем данные для дашборда
        dashboard_data.append({
            'item': deal['item'],
            'current_price': float(deal['current_price']),
            'reference_min_price': float(deal['reference_min_price']),
            'discount_percent': float(deal['discount_percent']),
            'url': deal['url'],
            'chart': chart_filename,
            'volume_24h': safe_int(deal.get('volume_24h', 0)),
            'volume_7d': safe_int(deal.get('volume_7d', 0)),
            'item_data': item_data
        })
    
    # Сортируем по размеру скидки
    dashboard_data.sort(key=lambda x: x['discount_percent'])
    
    # Генерируем HTML дашборд
    generate_html_dashboard(dashboard_data, output_dir / "best_deals_dashboard.html")
    
    return len(dashboard_data)

def find_item_data(item_name, items_dir):
    """Находит JSON файл с данными о предмете"""
    items_dir = Path(items_dir)
    for json_file in items_dir.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if item.get('market_hash_name') == item_name:
                    return item
    return None

def create_price_chart(deal, item_data, output_path):
    """Создает интерактивный график ценовой истории"""
    # Подготовка данных для графика
    periods = ['24h', '7d', '30d', '90d']
    min_prices = []
    avg_prices = []
    median_prices = []
    
    for period in periods:
        min_key = f"min_{period}"
        avg_key = f"avg_{period}"
        median_key = f"median_{period}"

        min_prices.append(float(item_data[min_key]) if item_data.get(min_key) is not None else None)
        avg_prices.append(float(item_data[avg_key]) if item_data.get(avg_key) is not None else None)
        median_prices.append(float(item_data[median_key]) if item_data.get(median_key) is not None else None)
    
    # Создаем график
    fig = go.Figure()
    
    # Добавляем данные
    fig.add_trace(go.Scatter(
        x=periods, 
        y=min_prices,
        mode='lines+markers',
        name='Минимальная цена',
        line=dict(color='blue', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=periods, 
        y=avg_prices,
        mode='lines+markers',
        name='Средняя цена',
        line=dict(color='green', width=2, dash='dot')
    ))
    
    fig.add_trace(go.Scatter(
        x=periods, 
        y=median_prices,
        mode='lines+markers',
        name='Медианная цена',
        line=dict(color='orange', width=2, dash='dash')
    ))
    
    # Добавляем текущую цену
    current_price = float(deal['current_price'])
    fig.add_hline(
        y=current_price, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Текущая цена: {current_price} {deal['currency']}",
        annotation_position="bottom right"
    )
    
    # Добавляем референсную цену
    reference_price = float(deal['reference_min_price'])
    fig.add_hline(
        y=reference_price, 
        line_dash="dash", 
        line_color="purple",
        annotation_text=f"Референсная цена: {reference_price} {deal['currency']}",
        annotation_position="top right"
    )
    
    # Настраиваем оформление
    fig.update_layout(
        title=f"{deal['item']} - Ценовая история",
        xaxis_title="Период",
        yaxis_title=f"Цена ({deal['currency']})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white"
    )
    
    # Сохраняем график
    fig.write_html(output_path)

def generate_html_dashboard(dashboard_data, output_path):
    """Генерирует HTML страницу с дашбордом"""
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
            .chart-container {{ height: 300px; }}
            .volume-badge {{ font-size: 0.85rem; }}
            .item-name {{ font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="container py-4">
            <div class="text-center mb-4">
                <h1 class="display-4"><i class="fa-solid fa-chart-line text-primary"></i> Лучшие предложения на Skinport</h1>
                <p class="lead">Актуальные скидки на предметы CS2</p>
                <p class="text-muted">Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="row row-cols-1 g-4">
    """
    
    for item in dashboard_data:
        # Форматируем цены
        current_price = f"{item['current_price']:.2f}"
        reference_price = f"{item['reference_min_price']:.2f}"
        
        # Цвет скидки
        discount_color = "danger" if item['discount_percent'] < -10 else "warning"
        
        # Бейджи объемов
        volume_badges = [
            f'<span class="badge bg-secondary volume-badge me-1">24ч: {item["volume_24h"]}</span>',
            f'<span class="badge bg-secondary volume-badge">7д: {item["volume_7d"]}</span>'
        ]
        
        # Ссылки
        item_page = item['item_data'].get('item_page', '#')
        market_page = item['item_data'].get('market_page', '#')
        
        html_content += f"""
                <div class="col">
                    <div class="card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div>
                                    <h5 class="card-title item-name">{item['item']}</h5>
                                    <div class="mb-2">{''.join(volume_badges)}</div>
                                </div>
                                <span class="badge bg-{discount_color} discount-badge">
                                    <i class="fa-solid fa-arrow-trend-down"></i> {item['discount_percent']:.1f}%
                                </span>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-8">
                                    <div class="chart-container" id="chart-{item['item'][:10]}">
                                        <iframe src="{item['chart']}" style="width:100%; height:100%; border:none;"></iframe>
                                    </div>
                                </div>
                                
                                <div class="col-md-4">
                                    <div class="d-grid gap-3">
                                        <div class="d-flex justify-content-between">
                                            <span>Текущая цена:</span>
                                            <strong>{current_price} {item['item_data'].get('currency', 'EUR')}</strong>
                                        </div>
                                        
                                        <div class="d-flex justify-content-between">
                                            <span>Референсная цена:</span>
                                            <strong>{reference_price} {item['item_data'].get('currency', 'EUR')}</strong>
                                        </div>
                                        
                                        <div class="d-flex justify-content-between">
                                            <span>Экономия:</span>
                                            <strong class="text-{discount_color}">
                                                {item['reference_min_price'] - item['current_price']:.2f} {item['item_data'].get('currency', 'EUR')}
                                            </strong>
                                        </div>
                                        
                                        <hr>
                                        
                                        <a href="{item['url']}" class="btn btn-primary" target="_blank">
                                            <i class="fa-solid fa-cart-shopping"></i> Купить на Skinport
                                        </a>
                                        
                                        <div class="d-grid gap-2">
                                            <a href="{item_page}" class="btn btn-outline-secondary" target="_blank">
                                                <i class="fa-solid fa-info-circle"></i> Страница предмета
                                            </a>
                                            <a href="{market_page}" class="btn btn-outline-secondary" target="_blank">
                                                <i class="fa-solid fa-store"></i> Весь рынок
                                            </a>
                                        </div>
                                    </div>
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

if __name__ == "__main__":
    # Пример использования
    print("Запуск генерации дашборда...")
    result = generate_deals_dashboard(
        best_deals_csv="data/best_deals.csv",
        items_dir="data/skinport-items",
        output_dir="data/dashboard"
    )
    print(f"Готово! Сгенерировано {result if result is not None else 0} предложений.")