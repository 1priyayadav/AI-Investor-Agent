from backend.data_pipeline.yahoo_finance import YahooFinanceAPI
from backend.data_pipeline.alpha_vantage import AlphaVantageAPI
from backend.data_pipeline.news_scraper import NewsScraper
from backend.data_pipeline.filing_parser import FilingParser
from backend.data_pipeline.et_markets_feed import et_markets_feed
from backend.services.cache_service import cache_service
from backend.services.vector_service import vector_service, stable_id
from backend.utils.logger import logger

class IngestionManager:
    def __init__(self):
        self.yf = YahooFinanceAPI()
        self.av = AlphaVantageAPI()
        self.news = NewsScraper()
        self.filings = FilingParser()

    def gather_all_data(self, ticker: str) -> dict:
        # 1. Check Redis cache first to avoid rate limiting
        cache_key = f"market_data_{ticker}"
        cached_data = cache_service.get_data(cache_key)
        if cached_data:
            logger.info(f"Retrieving {ticker} data from Redis Cache.")
            return cached_data

        logger.info(f"Fetching fresh data for {ticker} from external APIs.")
        
        # 2. Fetch fresh data
        price_data = self.yf.get_stock_price(ticker)
        earnings = self.av.get_earnings(ticker)
        insider = self.av.get_insider_trading(ticker)
        
        # 3. Ingest unstructured data to Vector DB seamlessly
        news_data = self.news.ingest_news(ticker)
        filing_data = self.filings.parse_corporate_filings(ticker)

        et_headlines = et_markets_feed.fetch_recent_headlines(15)
        et_hits = 0
        for h in et_headlines:
            blob = f"{h.get('title', '')} {h.get('summary', '')}"
            if ticker.replace(".NS", "").upper() in blob.upper():
                et_hits += 1
                vector_service.store_document(
                    stable_id("et_ingest", blob[:400]),
                    blob[:4000],
                    metadata={"ticker": ticker, "type": "et_markets", "source": "ET_RSS"},
                )

        # 4. Aggregate combined structured response
        combined_data = {
            "ticker": ticker,
            "price": price_data,
            "earnings": earnings,
            "insider_trading": insider,
            "recent_news_count": len(news_data),
            "recent_filings_count": len(filing_data),
            "et_markets_headline_hits": et_hits,
        }

        # 5. Cache for 10 minutes (600 seconds)
        cache_service.set_data(cache_key, combined_data, ttl_seconds=600)
        
        return combined_data

ingestion_manager = IngestionManager()
