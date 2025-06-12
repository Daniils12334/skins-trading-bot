import pandas as pd
from datetime import datetime
from pathlib import Path
import jinja2
from utils.helpers import load_config
from utils.logger import setup_logger

def analyze_market_opportunities(merged_df):
    """
    Analyze market opportunities based on the strategy config
    Returns filtered DataFrame with profitable items
    
    Now accounts for Skinport commission rate when calculating profits
    """
    config = load_config()
    strategy = config['strategy']
    risk = config['risk']
    commission_rate = config['skinport']['commission_rate']  # Get commission rate from config
    
    logger = setup_logger("market_analyzer")
    
    try:
        # Calculate NET sell price after commission
        merged_df['sp_net_price'] = merged_df['sp_suggested_price'] * (1 - commission_rate)
        
        # Calculate potential profit metrics (now using net price)
        merged_df['potential_profit'] = merged_df['sp_net_price'] - merged_df['ls_min_price']
        merged_df['profit_pct'] = ((merged_df['sp_net_price'] - merged_df['ls_min_price']) / 
                                 merged_df['ls_min_price']) * 100
        
        # Apply filters based on config
        filtered = merged_df[
            (merged_df['profit_pct'] >= strategy['min_profit_pct']) &
            (merged_df['profit_pct'] <= strategy['max_profit_pct']) &
            (merged_df['ls_quantity'] >= strategy['min_quantity']) &
            (merged_df['ls_min_price'] <= risk['max_investment_per_item'])
        ].copy()
        
        # Add commission-adjusted columns for reporting
        filtered['commission'] = filtered['sp_suggested_price'] * commission_rate
        filtered['gross_profit'] = filtered['sp_suggested_price'] - filtered['ls_min_price']
        filtered['net_profit'] = filtered['potential_profit']
        
        # Calculate investment metrics
        filtered['investment'] = filtered['ls_min_price']
        filtered = filtered.sort_values('profit_pct', ascending=False)
        
        # Apply risk limits
        filtered = filtered.head(risk['max_items_per_day'])
        total_investment = filtered['investment'].sum()
        
        if total_investment > risk['max_total_investment']:
            # Scale down to stay within budget
            filtered = filtered.assign(
                investment=lambda x: x['investment'] * risk['max_total_investment'] / total_investment
            )
        
        logger.info(
            f"Found {len(filtered)} profitable opportunities "
            f"(after {commission_rate*100:.1f}% commission)"
        )
        return filtered
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

def generate_html_report(opportunities_df, output_path=None):
    """
    Generate an HTML report from the opportunities DataFrame
    """
    config = load_config()
    
    if output_path is None:
        output_path = Path(config['html_reports']['path']) / f"market_opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    
    # Prepare data for display
    report_df = opportunities_df[[
        'name', 'ls_min_price', 'sp_suggested_price', 
        'potential_profit', 'profit_pct', 'ls_quantity',
        'investment'
    ]].copy()
    
    report_df.columns = [
        'Item Name', 'Buy Price (LS)', 'Sell Price (SP)', 
        'Potential Profit', 'Profit %', 'Available Qty',
        'Recommended Investment'
    ]
    
    # Format numbers
    for col in ['Buy Price (LS)', 'Sell Price (SP)', 'Potential Profit', 'Recommended Investment']:
        report_df[col] = report_df[col].apply(lambda x: f"€{x:.2f}")
    
    report_df['Profit %'] = report_df['Profit %'].apply(lambda x: f"{x:.1f}%")
    
    # Create HTML template
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Market Opportunities Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .positive { color: green; }
            .negative { color: red; }
        </style>
    </head>
    <body>
        <h1>Market Opportunities Report</h1>
        <p>Generated on {{ timestamp }}</p>
        
        <h2>Strategy Parameters</h2>
        <ul>
            <li>Minimum Profit: {{ strategy.min_profit_pct }}%</li>
            <li>Maximum Profit: {{ strategy.max_profit_pct }}%</li>
            <li>Minimum Quantity: {{ strategy.min_quantity }}</li>
        </ul>
        
        <h2>Risk Management</h2>
        <ul>
            <li>Max Investment Per Item: €{{ risk.max_investment_per_item }}</li>
            <li>Max Total Investment: €{{ risk.max_total_investment }}</li>
            <li>Max Items Per Day: {{ risk.max_items_per_day }}</li>
        </ul>
        
        <h2>Recommended Opportunities ({{ count }})</h2>
        {{ table_html }}
        
        <h3>Summary</h3>
        <ul>
            <li>Total Potential Profit: €{{ total_profit | round(2) }}</li>
            <li>Total Investment: €{{ total_investment | round(2) }}</li>
            <li>ROI: {{ roi | round(1) }}%</li>
        </ul>
    </body>
    </html>
    """
    
    # Calculate summary metrics
    total_profit = opportunities_df['potential_profit'].sum()
    total_investment = opportunities_df['investment'].sum()
    roi = (total_profit / total_investment) * 100 if total_investment > 0 else 0
    
    # Render HTML
    html = jinja2.Template(template).render(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        strategy=config['strategy'],
        risk=config['risk'],
        table_html=report_df.to_html(index=False, classes='opportunity-table'),
        count=len(opportunities_df),
        total_profit=total_profit,
        total_investment=total_investment,
        roi=roi
    )
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path

