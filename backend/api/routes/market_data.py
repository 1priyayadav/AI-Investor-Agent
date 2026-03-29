from fastapi import APIRouter, Depends, Query

from backend.api.deps import TokenData, get_optional_user
from backend.data_pipeline.yahoo_finance import YahooFinanceAPI

router = APIRouter()


@router.get("/ohlcv")
async def get_ohlcv(
    symbol: str = Query(..., description="yfinance symbol e.g. RELIANCE.NS"),
    period: str = Query("3mo"),
    current_user: TokenData = Depends(get_optional_user),
):
    yf = YahooFinanceAPI()
    df = yf.get_ohlcv_history(symbol, period=period, interval="1d")
    if df is None:
        return {"symbol": symbol, "series": []}
    records = []
    for idx, row in df.tail(120).iterrows():
        records.append(
            {
                "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            }
        )
    return {"symbol": symbol, "series": records}
