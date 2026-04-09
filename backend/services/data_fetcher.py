"""
Data Fetcher 模組 (負責與外部 API 串接並整合資料)
包含以下來源處理機制：
1. yfinance: 獲取國際市場指數與台股個股價格及基本面資料。
2. FRED API: 抓取美國聯準會提供的關鍵總體經濟數據 (如利率、消費者信心指數等)。
3. Taiwan Open API (政府/證交所): 取台股每日交易數據、三大法人籌碼動向、上市櫃公司月營收。
4. 鉅亨網 (或爬蟲機制): 即時產業新聞萃取，為市場情緒分析與 RAG 系統建立基礎。
"""

import yfinance as yf
import pandas as pd
import requests

class DataFetcherService:
    def __init__(self):
        # 初始化設定，例如 FRED API key
        self._macro_cache = {}
        pass

    def get_stock_info(self, ticker: str) -> dict:
        """獲取指定個股/公司的基本面資訊與最新價格。支援台股 (例如 2330.TW)。"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 若為無效代號，info 可能為空或是只有一些基本內容
            if not info or "regularMarketPrice" not in info and "currentPrice" not in info:
                # 也許 yfinance 沒有此標的，或是網路錯誤
                pass

            return {
                "symbol": info.get("symbol", ticker),
                "shortName": info.get("shortName", "Unknown"),
                "sector": info.get("sector", "General"),
                "industry": info.get("industry", "General"),
                "previousClose": info.get("previousClose", 0.0),
                "marketCap": info.get("marketCap", 0),
                "businessSummary": info.get("longBusinessSummary", "")
            }
        except Exception as e:
            return {"symbol": ticker, "error": str(e)}

    def get_macro_indicator(self, indicator_id: str, is_fallback=False, refresh=False) -> dict:
        """從 FRED 抓取特定總經指標 (附帶快取與 Fallback 機制)"""
        if refresh and indicator_id in self._macro_cache:
            del self._macro_cache[indicator_id]
            
        if indicator_id in self._macro_cache:
            return self._macro_cache[indicator_id]
            
        from backend.core.config import settings
        from datetime import datetime
        
        # FRED API URL 模板 (Series 本身 metadata 包含英文全名)
        api_key = settings.FRED_API_KEY
        if not api_key or api_key == "your_fred_api_key_here":
            # 返回模擬資料防止前端錯誤
            return {"title": indicator_id, "dates": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4", "2024-Q1"], "values": [0, 1, 2, 3, 2]}
            
        try:
            # 必須發送兩隻 Request 才能拿到完整資料: 1 抓名字, 2 抓時序數值。為求效能我們從 Series API 挖出 title
            info_url = f"https://api.stlouisfed.org/fred/series?series_id={indicator_id}&api_key={api_key}&file_type=json"
            info_res = requests.get(info_url)
            real_title = indicator_id
            if info_res.status_code == 200:
                series_data = info_res.json().get("seriess", [])
                if series_data:
                    real_title = series_data[0].get("title", indicator_id)
            
            # 抓時序數值 (放寬提取至 1990 年起)
            start_date = "1990-01-01"
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={indicator_id}&api_key={api_key}&file_type=json&observation_start={start_date}"
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
            
            dates = []
            values = []
            for obs in data.get("observations", []):
                if obs["value"] != ".":  # FRED 有時會回傳 "." 作為缺失值
                    dates.append(obs["date"])
                    values.append(float(obs["value"]))
            
            if len(dates) == 0:
                raise ValueError("FRED API 回傳空資料")
                
            result = {"title": real_title, "dates": dates, "values": values}
            self._macro_cache[indicator_id] = result
            return result
            
        except Exception as e:
            if not is_fallback:
                # 替補機制：若 AI 給了奇怪的 ID 被 FRED 拒絕或無資料，自動換成 Consumer Price Index
                fallback_id = "CPIAUCSL" if indicator_id != "CPIAUCSL" else "GDP"
                print(f"[FRED Fallback] 指標 {indicator_id} 載入失敗 ({e}), 改用 {fallback_id}")
                return self.get_macro_indicator(fallback_id, is_fallback=True)
            return {"error": str(e), "dates": [], "values": []}

    def get_stock_kline(self, ticker: str, interval: str, period: str) -> dict:
        """從 Yahoo Finance 抓取 K 線資料與均線"""
        try:
            stock = yf.Ticker(ticker)
            # period: 5d, 1mo, 1y. interval: 5m, 1h, 1d
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                return {"times": [], "values": [], "ma1": [], "ma2": []}
                
            # 計算簡單移動平均線 (MA10, MA20)
            ma1_window = 10
            ma2_window = 20
            
            df['MA1'] = df['Close'].rolling(window=ma1_window).mean()
            df['MA2'] = df['Close'].rolling(window=ma2_window).mean()
            
            # 清理時間格式，支援 5m, 1h 的精細時間顯示
            if interval in ["5m", "1h"]:
                times = df.index.strftime('%Y-%m-%d %H:%M').tolist()
            else:
                times = df.index.strftime('%Y-%m-%d').tolist()
            
            # 回傳 ECharts 所需的 OHLC 格式: [開, 關, 低, 高] 以及均線數值、成交量
            values = []
            volumes = []
            for i in range(len(df)):
                # ECharts K線格式: [open, close, lowest, highest]
                values.append([
                    round(df['Open'].iloc[i], 2),
                    round(df['Close'].iloc[i], 2),
                    round(df['Low'].iloc[i], 2),
                    round(df['High'].iloc[i], 2)
                ])
                # 成交量
                volumes.append(int(df['Volume'].iloc[i]))
                
            # 處理 NaN
            ma1_list = [round(x, 2) if not pd.isna(x) else None for x in df['MA1']]
            ma2_list = [round(x, 2) if not pd.isna(x) else None for x in df['MA2']]
            
            return {
                "times": times,
                "values": values,
                "volumes": volumes,
                "ma1": ma1_list,
                "ma2": ma2_list,
                "ma1_name": f"MA{ma1_window}",
                "ma2_name": f"MA{ma2_window}"
            }
        except Exception as e:
            return {"error": str(e), "times": [], "values": []}

    def get_stock_history_df(self, ticker: str, interval: str = "1d", period: str = "1y") -> pd.DataFrame:
        """專供後端 PredictorService 使用，獲取原始的 Pandas DataFrame"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            return df
        except Exception as e:
            print(f"Error fetching raw history: {e}")
            return pd.DataFrame()

    def get_stock_financials(self, ticker: str) -> dict:
        """獲取最近的季度與年度財報數據 (營收、淨利、EPS)"""
        try:
            stock = yf.Ticker(ticker)
            
            def _extract_data(df):
                if df is None or df.empty: return None
                df = df.T
                df.index = pd.to_datetime(df.index, errors='coerce')
                df = df[df.index.notna()].sort_index()
                
                keys_map = {
                    'Revenue': ['Total Revenue', 'Operating Revenue', 'Revenue'],
                    'NetIncome': ['Net Income', 'Net Income Common Stockholders'],
                    'EPS': ['Basic EPS', 'Diluted EPS']
                }
                res = pd.DataFrame(index=df.index)
                for new_name, possible_keys in keys_map.items():
                    res[new_name] = 0.0
                    for k in possible_keys:
                        if k in df.columns:
                            res[new_name] = df[k]
                            break
                return res

            q_df = _extract_data(stock.quarterly_income_stmt if hasattr(stock, 'quarterly_income_stmt') else stock.quarterly_financials)
            a_df = _extract_data(stock.income_stmt if hasattr(stock, 'income_stmt') else stock.financials)
            
            return {"quarterly": q_df, "annual": a_df}
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return {"quarterly": pd.DataFrame(), "annual": pd.DataFrame()}
    def fetch_market_news(self, keywords: list[str]) -> list[dict]:
        """使用鉅亨網 API 爬取最新產業新聞，並清理髒資料"""
        from datetime import datetime
        from bs4 import BeautifulSoup
        import re
        
        # 蒐集新聞的最終容器
        all_news = []
        
        # 遍歷 AI 推薦的關鍵字
        for kw in keywords:
            try:
                # 預設抓取最近 10 條
                url = f"https://news.cnyes.com/api/v3/news/category/headline?limit=10&page=1"
                # 實務上鉅亨網通常是用關鍵字搜尋 API，這裡為求簡便使用全量新聞 API 並做關鍵字過濾
                # 或是 mock 一些資料如果 API 不通
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json().get("items", {}).get("data", [])
                    for item in data:
                        title = item.get("title", "")
                        # 簡單文字過濾
                        if kw.lower() in title.lower():
                            all_news.append({
                                "keyword": kw,
                                "title": title,
                                "url": f"https://news.cnyes.com/news/id/{item.get('newsId')}",
                                "date": datetime.fromtimestamp(item.get("publishAt")).strftime("%Y-%m-%d")
                            })
            except Exception as e:
                print(f"Error fetching CNYES news for {kw}: {e}")
                
        return all_news

    def fetch_yahoo_news(self, ticker: str) -> list[dict]:
        """抓取 Yahoo Finance 的新聞 (英文為主)"""
        from datetime import datetime
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if not isinstance(news, list):
                return []
            
            formatted_news = []
            for n in news[:9]: # 取前 9 則
                # yfinance >= 0.2.37 改為嵌套結構 {'content': {...}}
                content = n.get("content") if isinstance(n, dict) else None
                if not content: 
                    content = n if isinstance(n, dict) else {}
                    
                title = content.get("title", "")
                
                # 安全解析 URL (避免 clickThroughUrl 為 None 導致 .get 報錯)
                click_urls = content.get("clickThroughUrl") or {}
                url = click_urls.get("url") or content.get("link", "")
                
                pub_date = content.get("pubDate", "")
                if pub_date:
                    date_str = pub_date[:10]
                else:
                    ppt = content.get("providerPublishTime")
                    date_str = datetime.fromtimestamp(ppt).strftime("%Y-%m-%d") if ppt else ""
                    
                formatted_news.append({
                    "keyword": "Yahoo",
                    "title": title,
                    "url": url,
                    "date": date_str
                })
            return formatted_news
        except Exception as e:
            print(f"Error fetching Yahoo news: {e}")
            return []
