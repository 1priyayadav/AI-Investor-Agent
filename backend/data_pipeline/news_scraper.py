import uuid
from backend.utils.logger import logger
from backend.services.vector_service import vector_service
from backend.data_pipeline.et_markets_feed import et_markets_feed


class NewsScraper:
    def ingest_news(self, ticker: str):
        logger.info(f"Ingesting ET Markets + synthetic news for {ticker}")
        news_items = [
            {
                "title": f"India market focus: {ticker}",
                "content": f"Retail participation and FII/DII positioning around {ticker} remain key watch items.",
            }
        ]

        sym = ticker.replace(".NS", "").upper()
        for h in et_markets_feed.fetch_recent_headlines(25):
            blob = f"{h.get('title','')} {h.get('summary','')}"
            if sym in blob.upper() or sym[:4] in blob.upper():
                news_items.append(
                    {
                        "title": h.get("title", ""),
                        "content": h.get("summary", ""),
                        "source": "ET_Markets",
                        "link": h.get("link", ""),
                    }
                )

        for item in news_items:
            doc_id = str(uuid.uuid4())
            text = f"{item.get('title','')}. {item.get('content','')}"
            vector_service.store_document(
                doc_id,
                text,
                metadata={
                    "ticker": ticker,
                    "type": "news",
                    "title": item.get("title", ""),
                    "source": item.get("source", "synthetic"),
                },
            )

        return news_items


news_scraper = NewsScraper()
