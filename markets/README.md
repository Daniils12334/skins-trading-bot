# 🏪 Market Documentations

This section contains documentation and structure for all market integrations used in this bot.

---

## 📘 Overview

- **Skinport** – [API Docs](https://docs.skinport.com/)
- **Lis-Skins** – [API Docs](https://lis-skins-ru.stoplight.io/docs/lis-skins-ru-public-user-api/285cz7ux1xocn-api-overview)
- **SkinBaron** – [API Docs](https://skinbaron.de/misc/apidoc/)

---

## 🟣 Skinport
### 💸 Fees

-    Sales Commission: 12% taken from every sale

-    Buyer Pays: No extra fees for buyers (prices are final)

### 🔗 Endpoint Example:
`GET https://api.skinport.com/v1/items`
The `/v1/items` endpoint provides a comprehensive list of items available on the marketplace, along with their associated metadata. This includes details such as item names, pricing, availability, and other relevant attributes.
### 🧾 Response JSON (sample):
```json
  {
    "market_hash_name": "★ Hand Wraps | Giraffe (Minimal Wear)",
    "currency": "EUR",
    "suggested_price": 183.45,
    "item_page": "https://skinport.com/item/hand-wraps-giraffe-minimal-wear",
    "market_page": "https://skinport.com/market?item=Giraffe&cat=Gloves&type=Hand%20Wraps",
    "min_price": 147.73,
    "max_price": 227.27,
    "mean_price": 173.06,
    "median_price": 169.8,
    "quantity": 6,
    "created_at": 1609473027,
    "updated_at": 1748943856
  }
```
### 🔗 Endpoint Example:
`GET https://api.skinport.com/v1/sales/history`
The `/v1/sales/history` endpoint provides aggregated data for specific in-game items that have been sold on Skinport. The response includes key statistics (min, max, avg, median prices, and sales volume) for different time periods (24 hours, 7 days, 30 days, and 90 days).
### 🧾 Response JSON (sample):
```json
  {
    "market_hash_name": "★ Hand Wraps | Giraffe (Minimal Wear)",
    "version": null,
    "currency": "EUR",
    "item_page": "https://skinport.com/item/hand-wraps-giraffe-minimal-wear",
    "market_page": "https://skinport.com/market?item=Giraffe&cat=Gloves&type=Hand%20Wraps",
    "last_24_hours": {
      "min": null,
      "max": null,
      "avg": null,
      "median": null,
      "volume": 0
    },
    "last_7_days": {
      "min": 147.73,
      "max": 147.73,
      "avg": 147.73,
      "median": 147.73,
      "volume": 1
    },
    "last_30_days": {
      "min": 107.77,
      "max": 154.89,
      "avg": 137.01,
      "median": 137,
      "volume": 9
    },
    "last_90_days": {
      "min": 107.77,
      "max": 187.15,
      "avg": 140.79,
      "median": 136.52,
      "volume": 24
    }
  }
```

## 🔵 Lis-Skins

## 🔴 SkinBaron

# markdown
## 📊 Market Fee Comparison
```
| Market     | Seller Fee | Buyer Fee | Notes                  |
|------------|------------|-----------|-------------------------|
| Skinport   | 12%        | 0%        | No buyer commission     |
| Lis-Skins  | 10%        | 0%        | Prices in RUB           |
| SkinBaron  | ~15%       | ?         | Private API, EUR-based  |
```