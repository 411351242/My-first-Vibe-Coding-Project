import asyncio
import pandas as pd
import numpy as np
import logging
import sys
import os

# 將專案路徑加入以引用 services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.predictor_service import PredictorService
from services.data_fetcher import DataFetcherService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_manual_prediction():
    ticker = "2330.TW"
    print(f"=== Starting Standalone Prediction Test for {ticker} ===")
    
    fetcher = DataFetcherService()
    predictor = PredictorService()
    
    try:
        print("[1/3] Fetching data...")
        history_df = fetcher.get_stock_history_df(ticker, interval="1d", period="1y")
        financials_df = fetcher.get_stock_financials(ticker)
        
        if history_df.empty:
            print("Error: History data is empty")
            return
            
        print(f"[2/3] Data fetched. History: {len(history_df)} rows. Financials: {len(financials_df)} rows.")
        
        print("[3/3] Running prediction service (this may take time)...")
        # 直接調用同步方法 (之前已改為同步)
        result = predictor.predict_future(history_df, financials_df)
        
        print("\n=== Result ===")
        print(f"Signal: {result.get('signal')}")
        print(f"Strategy: {result.get('strategy')}")
        print(f"Forecast: {result.get('forecast')[:5]}...")
        print("Success!")
        
    except Exception as e:
        print(f"\n!!! Prediction FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_manual_prediction()
