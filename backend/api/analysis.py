from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.api.shared import predictor
from backend.services.data_fetcher import DataFetcherService
from backend.services.llm_engine import LLMInsightEngine
from backend.api.market_overview import FRED_KEY_SERIES

router = APIRouter()

# 初始化其他服務
data_fetcher = DataFetcherService()
ai_engine = LLMInsightEngine()


class AnalysisRequest(BaseModel):
    ticker: str
    model: str = "gemini-3.1-flash-lite-preview"

@router.get("/status")
def get_system_status():
    """檢查後端 AI 服務是否就緒，前端頁面載入時輪詢此端點"""
    # 執行真正的穩定性握手 (Handshake)，確保 gRPC 已 warm-up
    ai_ready = ai_engine.check_ready()
    return {
        "ai_ready": ai_ready,
        "message": "AI 引擎就緒，可執行分析" if ai_ready else "AI 引擎暖機中或 API 金鑰失效..."
    }

@router.post("/analyze")
def run_analysis(request: AnalysisRequest):
    ticker = request.ticker
    
    # 1. 取得標的基本面資料 (Data Pipeline)
    stock_data = data_fetcher.get_stock_info(ticker)
    if "error" in stock_data:
        raise HTTPException(status_code=400, detail=f"無法取得 {ticker} 資料: {stock_data['error']}")
        
    industry = stock_data.get("industry", "General")
    sector = stock_data.get("sector", "General")

    # 2. 【獨立新聞管道】直接用 Ticker 抓 Yahoo News，不依賴 AI 關鍵字
    yahoo_news = data_fetcher.fetch_yahoo_news(ticker)
    
    # 3. 嘗試讓 AI 提取中文關鍵字強化 cnyes 搜尋 (失敗也不影響整體流程)
    cnyes_news = []
    try:
        search_keywords = ai_engine.extract_search_keywords(stock_data, request.model)
        cnyes_news = data_fetcher.fetch_market_news(search_keywords)
    except Exception as e:
        print(f"[analyze] AI 關鍵字提取或 cnyes 爬取失敗 (非致命): {e}")
    
    # 合併兩種來源的新聞：Yahoo 為主，cnyes 為輔
    real_news = yahoo_news + cnyes_news
    
    # 4. AI 綜合分析與文本生成 (LLM Task) — 無論新聞多少都嘗試分析
    analysis = ai_engine.generate_analysis_report(stock_data, real_news, request.model)
    
    # 5. 根據產業/股性，動態推薦對應的總經指標 (Smart Macro-Dashboard Task)
    raw_charts = ai_engine.recommend_macro_indicators(industry, request.model)
    
    # 進行去重過濾：若該指標已存在於「📉 宏觀關鍵指標 (FRED_KEY_SERIES)」中，則不在股票分析區重複顯示
    global_macro_ids = {item["id"] for item in FRED_KEY_SERIES}
    recommended_charts = [cid for cid in raw_charts if cid not in global_macro_ids]
    
    # 【新增】取得最近 4 期財報數據並格式化
    import math
    financials_data = None
    try:
        f_data = data_fetcher.get_stock_financials(ticker)
        q_df = f_data.get('quarterly')
        a_df = f_data.get('annual')
        
        if q_df is not None and not q_df.empty:
            financials_data = {
                "dates": q_df.index.strftime('%Y-%m-%d').tolist(),
                "revenue": [None if math.isnan(x) else float(x) for x in q_df['Revenue'].tolist()],
                "earnings": [None if math.isnan(x) else float(x) for x in q_df['NetIncome'].tolist()],
                "eps": [None if math.isnan(x) else float(x) for x in q_df['EPS'].tolist()]
            }
            if a_df is not None and not a_df.empty:
                financials_data.update({
                    "dates_annual": a_df.index.strftime('%Y-%m-%d').tolist(),
                    "revenue_annual": [None if math.isnan(x) else float(x) for x in a_df['Revenue'].tolist()],
                    "earnings_annual": [None if math.isnan(x) else float(x) for x in a_df['NetIncome'].tolist()]
                })
    except Exception as e:
        print(f"[analyze] 財報抓取失敗 (非致命): {e}")

    # 6. 回傳整合結果供前端渲染
    return {
        "status": "success",
        "ticker": ticker,
        "data": {
            "stock_info": stock_data,
            "analysis_report": analysis,
            "news_context": real_news,
            "recommended_charts": recommended_charts,
            "financials": financials_data
        }
    }

@router.get("/macro/{indicator_id}")
def get_macro_chart_data(indicator_id: str, refresh: bool = False):
    """供前端組件呼叫，取得 FRED 真實總經歷史數據的端點"""
    data = data_fetcher.get_macro_indicator(indicator_id, refresh=refresh)
    return {"status": "success", "indicator": indicator_id, "data": data}

@router.get("/kline")
def get_stock_kline_data(ticker: str, interval: str = "1d", period: str = "1y"):
    """供前端獨立呼叫，取得分離載入的 K 線圖與均線資料"""
    data = data_fetcher.get_stock_kline(ticker, interval, period)
    return {"status": "success", "ticker": ticker, "data": data}

@router.post("/predict")
def predict_stock_trend(request: AnalysisRequest):
    """供前端主動觸發，執行 5 種深度學習模型的集成預測 (同步執行以避免阻塞 Event Loop)"""
    ticker = request.ticker.strip().upper()
    print(f"[DEBUG] Starting prediction for ticker: {ticker}")
    try:
        # 1. 取得歷史數據 (用於訓練與預測基準)
        # 我們取 1 年數據，確保有足夠的 look_back (60天)
        df = data_fetcher.get_stock_history_df(ticker, interval="1d", period="1y")
        print(f"[DEBUG] Fetched history for {ticker}: {len(df)} rows")
        
        if df.empty:
             raise HTTPException(status_code=400, detail=f"無法取得 {ticker} 歷史數據進行分析")
        
        # 2. 取得財報數據 (用於強化預測與前端呈現)
        financials_data = data_fetcher.get_stock_financials(ticker)

        # 3. 啟動異步預測任務 (非阻塞)
        status = predictor.start_prediction_task(ticker, df, financials_data)        
        return {
            "status": "processing",
            "ticker": ticker,
            "message": "AI 預算任務已啟動，請定期查詢狀態"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI 預測啟動失敗: {str(e)}")

@router.get("/predict/status/{ticker}")
def get_prediction_status(ticker: str):
    """前端輪詢此端點以獲取預測進度與結果"""
    try:
        u_ticker = ticker.strip().upper()
        task_info = predictor.get_task_status(u_ticker)
        return {
            "status": "success",
            "ticker": u_ticker,
            "task": task_info 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/importance/{ticker}")
def get_feature_importance(ticker: str):
    """取得個別模型的 SHAP 特徵重要性分析"""
    u_ticker = ticker.strip().upper()
    try:
        importance_data = predictor.calculate_shap_importance(u_ticker)
        # 如果返回的是新的結構 (字典包含各模型)，直接返回
        return {"status": "success", "data": importance_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


