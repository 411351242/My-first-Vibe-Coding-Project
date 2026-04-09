import sys
import os
import pandas as pd
import numpy as np
import threading
import time
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.predictor_service import PredictorService
from backend.services.data_fetcher import DataFetcherService

def simulate_request():
    print("=== FINAL DEBUG START ===")
    fetcher = DataFetcherService()
    predictor = PredictorService()
    
    ticker = "2330.TW"
    print(f"Target: {ticker}")
    
    try:
        print("[1] Fetching data...")
        df = fetcher.get_stock_history_df(ticker)
        f_df = fetcher.get_stock_financials(ticker)
        
        print(f"[2] Data ready. History: {len(df)} rows. Financials: {len(f_df)} rows.")
        
        print("[3] Running prediction (with Lock)...")
        start_time = time.time()
        
        # Simulate simultaneous requests to test the lock
        def run_task(tid):
            print(f"Thread-{tid}: Starting...")
            try:
                res = predictor.predict_future(df, f_df)
                print(f"Thread-{tid}: SUCCESS. Result keys: {res.keys()}")
                # Test JSON serialization
                json.dumps(res)
                print(f"Thread-{tid}: JSON Serialization SUCCESS.")
            except Exception as e:
                print(f"Thread-{tid}: FAILED: {str(e)}")
                import traceback
                traceback.print_exc()

        t1 = threading.Thread(target=run_task, args=(1,))
        t2 = threading.Thread(target=run_task, args=(2,))
        
        t1.start()
        time.sleep(1) 
        t2.start() # This should be blocked by the lock
        
        t1.join()
        t2.join()
        
        print(f"=== FINAL DEBUG COMPLETE in {time.time()-start_time:.2f}s ===")
        
    except Exception as e:
        print(f"GLOBAL ERROR: {e}")

if __name__ == "__main__":
    simulate_request()
