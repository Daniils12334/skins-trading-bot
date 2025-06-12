import requests
import json
from datetime import datetime
from pathlib import Path
import time
from utils.helpers import load_config
from utils.logger import setup_logger

class LisSkinsAPI:
    _last_request_time = 0
    _rate_limit_delay = 30  # Conservative rate limiting

    @classmethod
    def get_items(cls, save_file=True, filename_prefix="lis_skins"):
        """
        Fetch market data from Lis-Skins API with proper rate limiting
        
        Args:
            save_file (bool): Save response to file
            filename_prefix (str): Prefix for saved files
            
        Returns:
            dict: API response data or None if error
        """
        logger = setup_logger("lis_skins_api")
        config = load_config()
        
        # Rate limiting
        elapsed = time.time() - cls._last_request_time
        if elapsed < cls._rate_limit_delay:
            wait_time = cls._rate_limit_delay - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
        
        try:
            # Prepare request
            api_url = "https://lis-skins.com/market_export_json/api_csgo_full.json"
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; LisSkinsAPI/1.0)"
            }
            
            # Make request
            cls._last_request_time = time.time()
            logger.info("Downloading data from Lis-Skins...")
            response = requests.get(api_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Process response
            data = response.json()
            
            if data.get("status") != "success":
                raise ValueError(f"API returned error status: {data.get('status')}")
            
            # Add timestamp metadata
            update_timestamp = data["last_update"]
            update_date = datetime.utcfromtimestamp(update_timestamp).strftime("%Y-%m-%d")
            data["update_date"] = update_date
            logger.info(f"Data successfully received (update: {update_date})")
            
            # Save to file if requested
            if save_file:
                save_folder = Path(config['data']['raw']['lis_skins'])
                save_folder.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{filename_prefix}_{timestamp}.json"
                full_path = save_folder / filename
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Raw data saved to {full_path}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {str(e)}")
        except ValueError as e:
            logger.error(f"Data validation error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        
        return None

