import threading
import time
import webbrowser
import os
import traceback
import pandas as pd
from datetime import datetime
from markets.skinport.sp_get_items import SkinportAPI
from markets.lis_skins.ls_get_items import LisSkinsAPI
from markets.merge_markets import merge_markets
from core.analyzer import analyze_market_opportunities, generate_html_report
from utils.logger import setup_logger
from utils.helpers import load_config

class MarketEngine:
    def __init__(self):
        self.logger = setup_logger("market_engine")
        self.config = load_config()
        self.cycle_interval = self.config.get("cycle_interval", 300)  # Default 5 minutes
        self.stop_event = threading.Event()
        self.logger.info("MarketEngine initialized")

    def _fetch_market_data(self, api_func, market_name, results, errors):
        """Thread target for market data fetching with detailed logging"""
        try:
            self.logger.info(f"Starting {market_name} data fetch...")
            # Handle currency parameter specifically for Skinport
            if market_name == "Skinport":
                result = api_func(currency="EUR")
            else:
                result = api_func()
                
            if result is None:
                errors[market_name] = f"{market_name} returned None"
                self.logger.error(f"{market_name} returned no data")
            elif isinstance(result, pd.DataFrame) and result.empty:
                errors[market_name] = f"{market_name} returned empty DataFrame"
                self.logger.error(f"{market_name} returned empty data")
            else:
                results[market_name] = result
                item_count = len(result) if hasattr(result, '__len__') else "N/A"
                self.logger.info(f"{market_name} fetch successful ({item_count} items)")
        except Exception as e:
            errors[market_name] = str(e)
            self.logger.error(f"{market_name} fetch failed: {str(e)}")
            self.logger.debug(traceback.format_exc())

    def run_cycle(self):
        """Run single analysis cycle with threading and detailed diagnostics"""
        self.logger.info("Starting new analysis cycle")
        results = {"Skinport": None, "LisSkins": None}
        errors = {}
        
        # Create and start threads
        threads = [
            threading.Thread(
                target=self._fetch_market_data,
                args=(SkinportAPI.get_items, "Skinport", results, errors),
                name="SkinportFetcher"
            ),
            threading.Thread(
                target=self._fetch_market_data,
                args=(LisSkinsAPI.get_items, "LisSkins", results, errors),
                name="LisSkinsFetcher"
            )
        ]
        
        for t in threads:
            t.daemon = True
            t.start()
        
        # Wait for both threads to complete with timeout
        timeout = self.config.get("fetch_timeout", 120)
        for t in threads:
            t.join(timeout)
            if t.is_alive():
                errors[t.name] = f"Thread timed out after {timeout}s"
                self.logger.error(f"{t.name} timed out")
        
        # Validate results
        if errors:
            self.logger.error(f"Market fetch completed with errors: {errors}")
            return None
            
        if not all(results.values()):
            self.logger.error("One or more markets returned no data")
            return None
        
        # Process and analyze data
        try:
            self.logger.info("Merging market data...")
            merged = merge_markets(results["LisSkins"], results["Skinport"])
            self.logger.info(f"Merged data shape: {merged.shape}")
            
            self.logger.info("Analyzing opportunities...")
            opportunities = analyze_market_opportunities(merged)
            
            if opportunities.empty:
                self.logger.warning("No profitable opportunities found")
                return None
                
            self.logger.info(f"Found {len(opportunities)} opportunities")
            
            # Generate report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            report_path = f"data/html_report/market_opportunities.html"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            self.logger.info(f"Generating report at {report_path}")
            generate_html_report(opportunities) 
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None

    def start(self):
        """Main engine loop with enhanced diagnostics"""
        self.logger.info(f"Starting market engine. Cycle interval: {self.cycle_interval}s")
        
        while not self.stop_event.is_set():
            cycle_start = time.time()
            self.logger.info("-" * 60)
            self.logger.info(f"Starting cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            try:
                report_path = self.run_cycle()
                if report_path:
                    abs_path = os.path.abspath(report_path)
                    # Print clickable link
                    print(f"\n[REPORT] file://{abs_path}")
                    self.logger.info(f"Report generated: file://{abs_path}")
                    
                    if self.config.get("auto_open", True):
                        webbrowser.open(f"file://{abs_path}")
            except Exception as e:
                self.logger.critical(f"Engine cycle crashed: {str(e)}")
                self.logger.debug(traceback.format_exc())
            
            # Calculate sleep time
            elapsed = time.time() - cycle_start
            sleep_time = max(0, self.cycle_interval - elapsed)
            
            if sleep_time > 0:
                self.logger.info(f"Cycle completed in {elapsed:.1f}s. Next cycle in {sleep_time:.1f}s")
                self.stop_event.wait(sleep_time)
    
    def stop(self):
        """Gracefully stop the engine"""
        self.logger.info("Stopping market engine")
        self.stop_event.set()

if __name__ == "__main__":
    engine = MarketEngine()
    
    try:
        engine.start()
    except KeyboardInterrupt:
        engine.logger.info("Keyboard interrupt received")
        engine.stop()
    except Exception as e:
        engine.logger.critical(f"Engine fatal error: {str(e)}")
        engine.logger.debug(traceback.format_exc())
        engine.stop()