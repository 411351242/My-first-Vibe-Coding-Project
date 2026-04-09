"""
市場總覽 API — 全球指數、大宗商品、外匯、宏觀關鍵指標
使用 yfinance (已有依賴) + FRED API (已有 Key)
"""
import os
import time
import requests
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

# ─── 全球主要指數 ────────────────────────────────────────────────────
INDICES = [
    {"symbol": "^GSPC",  "name": "S&P 500",     "region": "US"},
    {"symbol": "^IXIC",  "name": "Nasdaq",       "region": "US"},
    {"symbol": "^DJI",   "name": "Dow Jones",    "region": "US"},
    {"symbol": "^RUT",   "name": "Russell 2000", "region": "US"},
    {"symbol": "^FTSE",  "name": "FTSE 100",     "region": "UK"},
    {"symbol": "^GDAXI", "name": "DAX",          "region": "DE"},
    {"symbol": "^FCHI",  "name": "CAC 40",       "region": "FR"},
    {"symbol": "^N225",  "name": "Nikkei 225",   "region": "JP"},
    {"symbol": "^HSI",   "name": "Hang Seng",    "region": "HK"},
    {"symbol": "^TWII",  "name": "TWSE",         "region": "TW"},
    {"symbol": "000300.SS","name":"CSI 300",      "region": "CN"},
    {"symbol": "^KS11",  "name": "KOSPI",        "region": "KR"},
    {"symbol": "^BSESN", "name": "Sensex",       "region": "IN"},
    {"symbol": "^AXJO",  "name": "ASX 200",      "region": "AU"},
]

# ─── 大宗商品 ────────────────────────────────────────────────────────
COMMODITIES = [
    {"symbol": "GC=F",  "name": "Gold",          "unit": "USD/oz"},
    {"symbol": "SI=F",  "name": "Silver",         "unit": "USD/oz"},
    {"symbol": "CL=F",  "name": "WTI Crude",      "unit": "USD/bbl"},
    {"symbol": "BZ=F",  "name": "Brent Crude",    "unit": "USD/bbl"},
    {"symbol": "NG=F",  "name": "Natural Gas",    "unit": "USD/MMBtu"},
    {"symbol": "HG=F",  "name": "Copper",         "unit": "USD/lb"},
    {"symbol": "ZW=F",  "name": "Wheat",          "unit": "USD/bu"},
    {"symbol": "ZC=F",  "name": "Corn",           "unit": "USD/bu"},
]

# ─── 外匯貨幣對 ──────────────────────────────────────────────────────
FX_PAIRS = [
    {"symbol": "EURUSD=X", "name": "EUR/USD", "flag": "🇪🇺🇺🇸"},
    {"symbol": "USDJPY=X", "name": "USD/JPY", "flag": "🇺🇸🇯🇵"},
    {"symbol": "GBPUSD=X", "name": "GBP/USD", "flag": "🇬🇧🇺🇸"},
    {"symbol": "USDTWD=X", "name": "USD/TWD", "flag": "🇺🇸🇹🇼"},
    {"symbol": "USDCNH=X", "name": "USD/CNH", "flag": "🇺🇸🇨🇳"},
    {"symbol": "USDKRW=X", "name": "USD/KRW", "flag": "🇺🇸🇰🇷"},
    {"symbol": "AUDUSD=X", "name": "AUD/USD", "flag": "🇦🇺🇺🇸"},
    {"symbol": "USDCHF=X", "name": "USD/CHF", "flag": "🇺🇸🇨🇭"},
]

# ─── FRED 關鍵宏觀指標 ───────────────────────────────────────────────
FRED_KEY_SERIES = [
    {"id": "VIXCLS",   "name": "VIX 恐慌指數",        "unit": ""},
    {"id": "RECPROUSM156N", "name": "美國衰退機率",    "unit": "%"},
    {"id": "T10Y2Y",   "name": "10Y-2Y 殖利率利差",   "unit": "%"},
    {"id": "FEDFUNDS", "name": "聯邦基金利率",         "unit": "%"},
    {"id": "CPIAUCSL", "name": "美國 CPI YoY",         "unit": "%"},
    {"id": "UNRATE",   "name": "美國失業率",           "unit": "%"},
    {"id": "DGS10",    "name": "10年期公債殖利率",   "unit": "%"},
    {"id": "UMCSENT",  "name": "密大消費者信心",       "unit": "pts"},
    {"id": "HOUST",    "name": "新屋開工率",           "unit": "k"},
    {"id": "M2SL",     "name": "M2 貨幣供給",          "unit": "B"},
]


def _fetch_yf_quotes(symbols: list[str]) -> dict:
    """批次用 yfinance 抓取即時報價"""
    try:
        import yfinance as yf
        tickers = yf.Tickers(" ".join(symbols))
        result = {}
        for sym in symbols:
            try:
                info = tickers.tickers[sym].fast_info
                price = getattr(info, "last_price", None)
                prev = getattr(info, "previous_close", None)
                change_pct = ((price - prev) / prev * 100) if price and prev else None
                result[sym] = {
                    "price": round(price, 4) if price else None,
                    "change_pct": round(change_pct, 2) if change_pct is not None else None,
                }
            except Exception:
                result[sym] = {"price": None, "change_pct": None}
        return result
    except Exception as e:
        return {s: {"price": None, "change_pct": None} for s in symbols}


def _fetch_fred_latest(series_ids: list[str]) -> dict:
    """從 FRED 取最新值與約一年歷史趨勢"""
    import datetime
    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        return {}
    results = {}
    one_yr_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

    for sid in series_ids:
        try:
            url = (
                f"https://api.stlouisfed.org/fred/series/observations"
                f"?series_id={sid}&api_key={api_key}&file_type=json"
                f"&sort_order=desc&observation_start={one_yr_ago}"
            )
            r = requests.get(url, timeout=8)
            data = r.json().get("observations", [])
            if len(data) >= 1:
                latest_val = data[0].get("value", ".")
                prev_val = data[1].get("value", ".") if len(data) >= 2 else "."
                val = float(latest_val) if latest_val != "." else None
                prev = float(prev_val) if prev_val != "." else None
                
                history = []
                for pt in reversed(data):
                    v = pt.get("value", ".")
                    if v != ".":
                        history.append([pt.get("date"), float(v)])

                results[sid] = {
                    "value": round(val, 3) if val is not None else None,
                    "change": round(val - prev, 3) if val is not None and prev is not None else None,
                    "date": data[0].get("date", ""),
                    "history": history
                }
        except Exception:
            results[sid] = {"value": None, "change": None, "date": "", "history": []}
    return results


@router.get("/market-overview")
def get_market_overview():
    """
    全球市場總覽：指數、商品、外匯、宏觀指標
    """
    import time
    start = time.time()

    # 一次抓取所有 yfinance symbols
    all_yf_symbols = (
        [idx["symbol"] for idx in INDICES]
        + [c["symbol"] for c in COMMODITIES]
        + [fx["symbol"] for fx in FX_PAIRS]
    )
    quotes = _fetch_yf_quotes(all_yf_symbols)

    # 整理指數
    indices_data = []
    for idx in INDICES:
        q = quotes.get(idx["symbol"], {})
        indices_data.append({
            "symbol": idx["symbol"],
            "name": idx["name"],
            "region": idx["region"],
            "price": q.get("price"),
            "change_pct": q.get("change_pct"),
        })

    # 整理大宗商品
    commodities_data = []
    for c in COMMODITIES:
        q = quotes.get(c["symbol"], {})
        commodities_data.append({
            "symbol": c["symbol"],
            "name": c["name"],
            "unit": c["unit"],
            "price": q.get("price"),
            "change_pct": q.get("change_pct"),
        })

    # 整理外匯
    fx_data = []
    for fx in FX_PAIRS:
        q = quotes.get(fx["symbol"], {})
        fx_data.append({
            "symbol": fx["symbol"],
            "name": fx["name"],
            "flag": fx["flag"],
            "price": q.get("price"),
            "change_pct": q.get("change_pct"),
        })

    # FRED 宏觀指標
    fred_ids = [s["id"] for s in FRED_KEY_SERIES]
    fred_raw = _fetch_fred_latest(fred_ids)
    macro_data = []
    for s in FRED_KEY_SERIES:
        r = fred_raw.get(s["id"], {})
        macro_data.append({
            "id": s["id"],
            "name": s["name"],
            "unit": s["unit"],
            "value": r.get("value"),
            "change": r.get("change"),
            "date": r.get("date", ""),
            "history": r.get("history", []),
        })

    return {
        "data": {
            "indices": indices_data,
            "commodities": commodities_data,
            "fx": fx_data,
            "macro": macro_data,
        },
        "elapsed_ms": round((time.time() - start) * 1000),
    }
