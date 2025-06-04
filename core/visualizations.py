import os
import csv
import json
import glob
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

def generate_deals_dashboard(best_deals_csv, history_dir, output_dir):
    """Генерирует HTML-дашборд с реальными историческими данными"""
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
    
    # Загружаем последний файл истории
    latest_history = max(history_files, key=os.path.getctime)
    with open(latest_history, 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    # Создаем дашборд
    dashboard_data = []
    
    for deal in deals:
        item_name = deal['item']
        
        # Ищем историю для этого предмета
        item_history = next((item for item in history_data if item['market_hash_name'] == item_name), None)
        if not item_history or not item_history.get('sales'):
            continue
        
        # Анализируем историю продаж
        sales = item_history['sales']
        
        # Создаем график
        chart_filename = f"chart_{item_name.replace(' ', '_')[:50]}.html"
        chart_path = output_dir / chart_filename
        create_price_chart(deal, sales, chart_path)
        
        # Рассчитываем статистику
        prices = [sale['price'] for sale in sales]
        volumes = [sale['volume'] for sale in sales]
        
        dashboard_data.append({
            'item': item_name,
            'current_price': float(deal['current_price']),
            'reference_min_price': float(deal['reference_min_price']),
            'discount_percent': float(deal['discount_percent']),
            'url': deal['url'],
            'chart': chart_filename,
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'total_volume': sum(volumes),
            'sales_count': len(sales),
            'last_sale': max(sale['time'] for sale in sales) if sales else "N/A"
        })
    
    # Сортируем по размеру скидки
    dashboard_data.sort(key=lambda x: x['discount_percent'])
    
    # Генерируем HTML дашборд
    generate_html_dashboard(dashboard_data, output_dir / "best_deals_dashboard.html")
    
    return len(dashboard_data)

def create_price_chart(deal, sales, output_path):
    """Создает интерактивный график на основе реальных продаж"""
    if not sales:
        return
    
    # Сортируем продажи по времени
    sales.sort(key=lambda x: x['time'])
    
    # Подготовка данных
    times = [sale['time'] for sale in sales]
    prices = [sale['price'] for sale in sales]
    volumes = [sale['volume'] for sale in sales]
    
    # Рассчитываем скользящее среднее
    window_size = min(7, len(prices))
    moving_avg = []
    for i in range(len(prices)):
        start = max(0, i - window_size + 1)
        moving_avg.append(sum(prices[start:i+1]) / (i - start + 1))
    
    # Создаем график
    fig = go.Figure()
    
    # Цены продаж
    fig.add_trace(go.Scatter(
        x=times, 
        y=prices,
        mode='markers',
        name='Цена продажи',
        marker=dict(
            size=8,
            color=volumes,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Объем')
        )
    ))
    
    # Скользящее среднее
    fig.add_trace(go.Scatter(
        x=times, 
        y=moving_avg,
        mode='lines',
        name='Скользящее среднее',
        line=dict(color='red', width=3)
    ))
    
    # Текущая цена
    current_price = float(deal['current_price'])
    fig.add_hline(
        y=current_price, 
        line_dash="dash", 
        line_color="blue",
        annotation_text=f"Текущая цена: {current_price} {deal['currency']}",
        annotation_position="bottom right"
    )
    
    # Референсная цена
    reference_price = float(deal['reference_min_price'])
    fig.add_hline(
        y=reference_price, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Референсная цена: {reference_price} {deal['currency']}",
        annotation_position="top right"
    )
    
    # Настраиваем оформление
    fig.update_layout(
        title=f"{deal['item']} - История продаж",
        xaxis_title="Дата продажи",
        yaxis_title=f"Цена ({deal['currency']})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white",
        showlegend=True
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
            .chart-container {{ height: 400px; }}
            .volume-badge {{ font-size: 0.85rem; }}
            .item-name {{ font-weight: 600; }}
            .stat-badge {{ font-size: 0.9rem; margin-right: 5px; }}
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
        discount_color = "danger" if item['discount_percent'] < -15 else "warning"
        
        # Статистика
        stats_html = f"""
        <div class="d-flex flex-wrap mb-2">
            <span class="badge bg-info stat-badge">Мин: {item['min_price']:.2f}</span>
            <span class="badge bg-info stat-badge">Макс: {item['max_price']:.2f}</span>
            <span class="badge bg-info stat-badge">Средн: {item['avg_price']:.2f}</span>
            <span class="badge bg-info stat-badge">Продажи: {item['sales_count']}</span>
            <span class="badge bg-info stat-badge">Объем: {item['total_volume']}</span>
        </div>
        """
        
        html_content += f"""
                <div class="col">
                    <div class="card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div>
                                    <h5 class="card-title item-name">{item['item']}</h5>
                                    {stats_html}
                                </div>
                                <span class="badge bg-{discount_color} discount-badge">
                                    <i class="fa-solid fa-arrow-trend-down"></i> {item['discount_percent']:.1f}%
                                </span>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-8">
                                    <div class="chart-container">
                                        <iframe src="{item['chart']}" style="width:100%; height:100%; border:none;"></iframe>
                                    </div>
                                </div>
                                
                                <div class="col-md-4">
                                    <div class="d-grid gap-3">
                                        <div class="d-flex justify-content-between">
                                            <span>Текущая цена:</span>
                                            <strong>{current_price} EUR</strong>
                                        </div>
                                        
                                        <div class="d-flex justify-content-between">
                                            <span>Референсная цена:</span>
                                            <strong>{reference_price} EUR</strong>
                                        </div>
                                        
                                        <div class="d-flex justify-content-between">
                                            <span>Экономия:</span>
                                            <strong class="text-{discount_color}">
                                                {item['reference_min_price'] - item['current_price']:.2f} EUR
                                            </strong>
                                        </div>
                                        
                                        <hr>
                                        
                                        <a href="{item['url']}" class="btn btn-primary" target="_blank">
                                            <i class="fa-solid fa-cart-shopping"></i> Купить на Skinport
                                        </a>
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
