import requests
import datetime
import json
import os
import time
from utils.helpers import load_config
from utils.logger import setup_logger

class SkinportAPI:
    _last_request_time = 0
    _rate_limit_delay = 38  # 5 minutes = 300 seconds / 8 requests = ~37.5s between requests

    @classmethod
    def get_items(cls, save_file=True, filename_prefix="sp_items", currency="EUR", tradable=False, app_id=730):
        """
        Get items from Skinport API with proper rate limiting and Brotli support
        
        Args:
            save_file (bool): Save response to file
            filename_prefix (str): Prefix for saved files
            currency (str): Currency code (default USD)
            tradable (bool): Only show tradable items
            app_id (int): Game app ID (default 730 for CS2)
            
        Returns:
            dict: API response data or None if error
        """
        logger = setup_logger("skinport_api")
        config = load_config()
        
        # Rate limiting
        elapsed = time.time() - cls._last_request_time
        if elapsed < cls._rate_limit_delay:
            wait_time = cls._rate_limit_delay - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
        
        try:
            # Prepare request
            api_url = "https://api.skinport.com/v1/items"
            params = {
                'app_id': app_id,
                'currency': currency,
                'tradable': str(tradable).lower()
            }
            
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "br",  # Brotli required
                "User-Agent": "Mozilla/5.0 (compatible; SkinportAPI/1.0)"
            }
            
            # Make request
            cls._last_request_time = time.time()
            response = requests.get(api_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            # Process response
            data = response.json()
            
            # Save to file if requested
            if save_file:
                save_folder = config['data']['raw']['skinport_items']
                os.makedirs(save_folder, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{filename_prefix}_{currency}_{'tradable' if tradable else 'all'}_{timestamp}.json"
                full_path = os.path.join(save_folder, filename)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Data saved to {full_path}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        
        return None