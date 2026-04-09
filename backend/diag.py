import time
import sys
import os

def diag():
    print("=== AI Bot Pipeline Diagnostics ===")
    
    # 1. Base Imports
    try:
        start = time.time()
        import pandas as pd
        import numpy as np
        print(f"[OK] Pandas/Numpy loaded in {time.time()-start:.2f}s")
    except Exception as e:
        print(f"[FAIL] Base imports: {e}")
        return

    # 2. Heavy Imports (TensorFlow/Sklearn)
    try:
        print("Loading TensorFlow (this is usually the heavy part)...")
        start = time.time()
        import tensorflow as tf
        print(f"[OK] TensorFlow {tf.__version__} loaded in {time.time()-start:.2f}s")
        
        start = time.time()
        from sklearn.preprocessing import MinMaxScaler
        print(f"[OK] Sklearn loaded in {time.time()-start:.2f}s")
    except Exception as e:
        print(f"[FAIL] Heavy imports: {e}")
        return

    # 3. YFinance Connectivity
    try:
        print("Testing YFinance connectivity...")
        start = time.time()
        import yfinance as yf
        df = yf.Ticker("AAPL").history(period="1mo")
        if not df.empty:
            print(f"[OK] YFinance works. AAPL data: {len(df)} rows. Time: {time.time()-start:.2f}s")
        else:
            print("[FAIL] YFinance returned empty data.")
    except Exception as e:
        print(f"[FAIL] YFinance connectivity: {e}")

    # 4. TensorFlow Logic Test (Small model)
    try:
        print("Testing Model Compilation & Fit...")
        start = time.time()
        model = tf.keras.models.Sequential([
            tf.keras.layers.Dense(4, input_shape=(10, 1)),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        
        # Test fit on dummy data
        X = np.random.rand(10, 10, 1)
        y = np.random.rand(10, 1)
        model.fit(X, y, epochs=1, verbose=0)
        print(f"[OK] Model fit works. Time: {time.time()-start:.2f}s")
    except Exception as e:
        print(f"[FAIL] TensorFlow execution: {e}")

    print("=== Diagnostics Complete ===")

if __name__ == "__main__":
    diag()
