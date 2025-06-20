# Skins Trading Bot - Enhanced README
## Overview

### This trading bot analyzes and trades CS:GO skins across multiple marketplaces, featuring both a powerful backend engine and a user-friendly PyQt-based UI with advanced visualization capabilities.

https:///home/danbar/Desktop/skins-trading-bot/stock/app_showcase1.png
Main dashboard with market overview

https:///home/danbar/Desktop/skins-trading-bot/stock/app_showcase.png
Detailed trade analysis and statistics
# Key Features
## Core Functionality

    Multi-market data collection from Skinport, LIS Skins, and more (additional markets in development)

    Real-time arbitrage opportunity detection

    Historical price tracking and analysis

## Advanced UI Features

-    **Interactive dashboards with PyQt charts showing:**

    -   Profit trends over time

    -   Market price comparisons

    -   Portfolio performance

-    **Trade management interface:**

    -   Manual trade entry and editing

    -   Status tracking (Active/Completed)

    -   Profit/loss calculations

-    **Data visualization:**

    -   Interactive price history graphs

    -   Market spread heatmaps

    -   Performance metrics

# Trading Journal & Analysis

The bot maintains a comprehensive trading journal (`trading_journal.csv`) with detailed records of all transactions.

## Transaction History

| ID | Product                        | Buy Price | Quantity | Buy Time            | Sell Price | Sell Time           | Profit (%) | Status    |
|----|---------------------------------|-----------|----------|---------------------|------------|---------------------|------------|-----------|
| 2  | Disco MAC (Charm)               | 0.86      | 1        | 2025-06-04 20:51:27 | 1.05       | 2025-06-14          | 22.09%     | Completed |
| 3  | P250 Franklin (FN)              | 1.53      | 1        | 2025-06-04 20:52:50 | 1.63       | 2025-06-13          | 6.54%      | Completed |
| 14 | Five-SeveN Mokey Business (FT)  | 2.30      | 1        | 2025-06-05 00:47:19 | 2.79       | 2025-06-11          | 21.30%     | Completed |

## Recent Performance Highlights

### Top Performers:
- **Mac-10 Echoing Sands**: 50% profit (0.08 → 0.12)
- **MAC-10 Derailment (FT)**: 27.14% profit (2.69 → 3.42)
- **Disco MAC (Charm)**: 22.09% profit (0.86 → 1.05)

### Active Positions:
- StatTrak™ MP9 Ruby Poison Dart (FN) - Bought at 5.81
- StatTrak™ Desert Eagle Oxide Blaze (FN) - Bought at 1.95
- FAMAS Bad Trip (FT) - Bought at 1.94

## Roadmap & Upcoming Features

### Market Expansion:
- Integration with Buff163, CSGOFloat, and SkinBaron
- Steam Community Market support

### UI Enhancements:
- Mobile-responsive web dashboard
- Advanced filtering for trade opportunities
- Custom alert system

### Advanced Features:
- Automated trade execution
- Machine learning price prediction
- Portfolio risk analysis
# Getting Started
## Installation
```bash
git clone https://github.com/yourrepo/skins-trading-bot.git
cd skins-trading-bot
pip install -r requirements.txt
```
## Running the Application
```bash
python main.py
```

# Price Formation Analysis and HTML Visualization

# This section explains how item prices are determined across different markets and how we visualize this data in our HTML reports.
---
## Skinport Market Pricing
```json

{
  "market_hash_name": "10 Year Birthday Sticker Capsule",
  "suggested_price": 0.88,
  "min_price": 0.83,
  "max_price": 4.05,
  "mean_price": 1.55,
  "median_price": 1.13,
  "quantity": 211
}
```
-    **Suggested Price:** Algorithmically determined reference price

-    **Min/Max Price:** Current listing extremes

-    **Mean/Median:** Market price distribution indicators

-    **Quantity:** Available items affecting liquidity
---
## LIS Skins Pricing
```json

{
  "name": "USP-S | Ticket to Hell (Factory New)",
  "price": 1.76,
  "item_float": "0.057116512209177",
  "stickers": [...]
}
```
-    **Base Price:** Condition-dependent (Factory New, Field-Tested etc.)

-    **Float Value:** Additional wear-based pricing (lower = better)

-    **Stickers:** Can significantly increase value (especially rare/tournament stickers)

# Price Comparison Metrics

- Our analysis generates several key metrics:
```text

Data columns:
1. name                 - Item name
2. ls_min_price         - LIS Skins lowest price
3. ls_median_price      - LIS Skins median price  
4. ls_quantity          - LIS Skins available stock
5. sp_min_price         - Skinport lowest price
6. sp_suggested_price   - Skinport algorithm price
7. sp_quantity          - Skinport available stock
8. price_diff           - Absolute price difference (sp_min - ls_min)
9. price_ratio          - Relative price ratio (sp_min/ls_min)
```

# HTML Visualization

Here's a HTML report structure showing our price analysis:
```html
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
        <p>Generated on 2025-06-20 03:03:04</p>
        
        <h2>Strategy Parameters</h2>
        <ul>
            <li>Minimum Profit: 20%</li>
            <li>Maximum Profit: 400%</li>
            <li>Minimum Quantity: 20</li>
        </ul>
        
        <h2>Risk Management</h2>
        <ul>
            <li>Max Investment Per Item: €50</li>
            <li>Max Total Investment: €510</li>
            <li>Max Items Per Day: 200</li>
        </ul>
        
        <h2>Recommended Opportunities (172)</h2>
        <table border="1" class="dataframe opportunity-table">
  <thead>
    <tr style="text-align: right;">
      <th>Item Name</th>
      <th>Buy Price (LS)</th>
      <th>Sell Price (SP)</th>
      <th>Potential Profit</th>
      <th>Profit %</th>
      <th>Available Qty</th>
      <th>Recommended Investment</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>G3SG1 | Orange Crash (Field-Tested)</td>
      <td>€0.12</td>
      <td>€0.22</td>
      <td>€0.07</td>
      <td>61.3%</td>
      <td>24.0</td>
      <td>€0.12</td>
    </tr>
    <tr>
      <td>Austin 2025 Contenders Autograph Capsule</td>
      <td>€0.73</td>
      <td>€1.24</td>
      <td>€0.36</td>
      <td>49.5%</td>
      <td>310.0</td>
      <td>€0.73</td>
    </tr>
  </tbody>
</table>
        
        <h3>Summary</h3>
        <ul>
            <li>Total Potential Profit: €22.08</li>
            <li>Total Investment: €81.94</li>
            <li>ROI: 26.9%</li>
        </ul>
    </body>
    </html>
```
## Key Visualization Features

-    **Side-by-Side Market Comparison**

-        Clear presentation of prices from both markets

-        Highlighting of key differentiators (float value, stickers)

    **Arbitrage Opportunity Calculator**

-        Instant visibility of profit potential

-        Color-coded based on opportunity size

    **Historical Price Charts**

-        Interactive time-series graphs

-        Support for multiple price metrics (min, max, median)

    **Condition Indicators**

-        Visual representation of wear quality

-        Sticker impact visualization

    **Mobile-Responsive Design**

-        Adapts to different screen sizes

-        Touch-friendly interactive elements

## The HTML reports are generated automatically after each market scan, providing traders with up-to-date visual analysis of market conditions and trading opportunities.

# First-Time Setup

  -  Configure API keys in config.yaml

  -  Set your preferred markets and thresholds

  -  Customize UI preferences in config.yaml under ui_settings

## Support

For issues or feature requests, please open an issue on our GitHub repository.

Note: This bot is for educational purposes only. Trading virtual items carries risks, and past performance is not indicative of future results.

