from markets.skinport.sp_get_items import SkinportAPI
from markets.lis_skins.ls_get_items import LisSkinsAPI
from markets.merge_markets import merge_markets

from core.analyzer import analyze_market_opportunities, generate_html_report

from utils.logger import setup_logger

def run_full_analysis():
    """
    Complete workflow: get data, analyze, generate report
    """
    logger = setup_logger("market_analysis")
    
    try:
        # Step 1: Get market data
        logger.info("Fetching market data...")
        ls_items = LisSkinsAPI.get_items()
        sp_items = SkinportAPI.get_items(currency="EUR")
        
        if not ls_items or not sp_items:
            raise ValueError("Failed to fetch market data")
        
        # Step 2: Merge and analyze
        logger.info("Analyzing opportunities...")
        merged = merge_markets(ls_items, sp_items)
        opportunities = analyze_market_opportunities(merged)
        
        if opportunities.empty:
            logger.warning("No profitable opportunities found")
            return None
        
        # Step 3: Generate report
        logger.info("Generating report...")
        report_path = generate_html_report(opportunities)
        logger.info(f"Report generated at {report_path}")
        
        return report_path
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    report = run_full_analysis()
    if report:
        print(f"Analysis complete. Report saved to: {report}")