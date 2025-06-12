import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.helpers import load_config
from utils.logger import setup_logger

def calculate_lis_skins_prices(items):
    """Calculate median prices for Lis-Skins items grouped by name"""
    df = pd.DataFrame(items['items'])
    df['name'] = df['name'].str.strip()  # Clean whitespace
    
    # Group by item name and calculate metrics
    grouped = df.groupby('name')['price'].agg(
        ls_min_price='min',
        ls_median_price='median',
        ls_quantity='count'
    ).reset_index()
    
    return grouped

def prepare_skinport_data(items):
    """Prepare Skinport data for merging"""
    df = pd.DataFrame(items)
    df['market_hash_name'] = df['market_hash_name'].str.strip()  # Clean whitespace
    
    # Select and rename columns
    sp_df = df[['market_hash_name', 'min_price', 'suggested_price', 'quantity']].rename(columns={
        'market_hash_name': 'name',
        'min_price': 'sp_min_price',
        'suggested_price': 'sp_suggested_price',
        'quantity': 'sp_quantity'
    })
    
    return sp_df

def merge_markets(ls_items, sp_items):
    """
    Merge data from both markets and save as parquet
    
    Args:
        ls_items: Lis-Skins API response
        sp_items: Skinport API response
        
    Returns:
        pd.DataFrame: Merged dataframe with market comparison
    """
    logger = setup_logger("market_merger")
    config = load_config()
    
    try:
        # Process Lis-Skins data
        ls_processed = calculate_lis_skins_prices(ls_items)
        
        # Process Skinport data
        sp_processed = prepare_skinport_data(sp_items)
        
        # Merge datasets
        merged = pd.merge(
            ls_processed,
            sp_processed,
            on='name',
            how='outer'
        )
        
        # Calculate price differences
        merged['price_diff'] = merged['sp_min_price'] - merged['ls_min_price']
        merged['price_ratio'] = merged['sp_min_price'] / merged['ls_min_price']
        
        # Save to parquet
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = Path(config['data']['combined']) / f"merged_markets_{timestamp}.parquet"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        merged.to_parquet(save_path)
        logger.info(f"Saved merged market data to {save_path}")
        
        return merged
        
    except Exception as e:
        logger.error(f"Failed to merge markets: {str(e)}")
        raise