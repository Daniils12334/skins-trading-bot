# skinport
```json
  {
    "market_hash_name": "10 Year Birthday Sticker Capsule",
    "currency": "EUR",
    "suggested_price": 0.88,
    "item_page": "https://skinport.com/item/10-year-birthday-sticker-capsule",
    "market_page": "https://skinport.com/market?item=10%20Year%20Birthday%20Sticker%20Capsule&cat=Container",
    "min_price": 0.83,
    "max_price": 4.05,
    "mean_price": 1.55,
    "median_price": 1.13,
    "quantity": 211,
    "created_at": 1661324437,
    "updated_at": 1749739389
  },
```
# lis_skins
```json
  "status": "success",
  "items":
    {
      "id": 136809667,
      "name": "AK-47 | Phantom Disruptor (Field-Tested)",
      "price": 4.26,
      "unlock_at": null,
      "item_class_id": "3770669115",
      "created_at": "2025-03-10T08:06:49.000000Z",
      "item_asset_id": "42485617603",
      "game_id": 1,
      "item_float": "0.216031059622765",
      "name_tag": null,
      "item_paint_index": 941,
      "item_paint_seed": 870,
      "stickers": []
    },
    {
      "id": 136831087,
      "name": "USP-S | Ticket to Hell (Factory New)",
      "price": 1.76,
      "unlock_at": null,
      "item_class_id": "4726068446",
      "created_at": "2025-03-10T10:33:01.000000Z",
      "item_asset_id": "42487812981",
      "game_id": 1,
      "item_float": "0.057116512209177",
      "name_tag": null,
      "item_paint_index": 1136,
      "item_paint_seed": 938,
      "stickers": [
        {
          "name": "Heroic | 2020 RMR",
          "image": "https://steamcdn-a.akamaihd.net/apps/730/icons/econ/stickers/rmr2020/hero.7a21b96378cb45f8df47422feb05f8d2d7a041d3.png",
          "wear": 0,
          "slot": 0
        },
        {
          "name": "IHC Esports (Gold) | Antwerp 2022",
          "image": "https://steamcdn-a.akamaihd.net/apps/730/icons/econ/stickers/antwerp2022/ihc_gold.cc4b23500decf00efcae4123ab4548284de87e7f.png",
          "wear": 0,
          "slot": 1
        },
        {
          "name": "9z Team (Glitter) | Antwerp 2022",
          "image": "https://steamcdn-a.akamaihd.net/apps/730/icons/econ/stickers/antwerp2022/nine_glitter.ca335176f7d1c55fca22e418bac72432aa088e04.png",
          "wear": 0,
          "slot": 2
        },
        {
          "name": "Team Liquid (Glitter) | Antwerp 2022",
          "image": "https://steamcdn-a.akamaihd.net/apps/730/icons/econ/stickers/antwerp2022/liq_glitter.cb3f993a59dff59759f4e942e03f5e3736d2c76e.png",
          "wear": 0,
          "slot": 3
        }
      ]
    },
```
```text
Data columns (total 9 columns):
 #   Column              Non-Null Count  Dtype  
---  ------              --------------  -----  
 0   name                25629 non-null  object 
 1   ls_min_price        18599 non-null  float64
 2   ls_median_price     18599 non-null  float64
 3   ls_quantity         18599 non-null  float64
 4   sp_min_price        21156 non-null  float64
 5   sp_suggested_price  25131 non-null  float64
 6   sp_quantity         25156 non-null  float64
 7   price_diff          16204 non-null  float64
 8   price_ratio         16204 non-null  float64
```