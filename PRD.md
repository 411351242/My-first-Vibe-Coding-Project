# 專案需求文件 (PRD) - AI Quant Platform

## 1. 產品概述
AI Quant Platform 是一站式經濟觀測與股票分析平台，旨在透過 AI 輔助分析與自動化資料處理，協助使用者進行投資決策。系統結合總經數據、基本面分析與即時新聞情緒分析。

## 2. 核心功能規格

### 2.1 股票分析引擎
- **基本面資料擷取**：
  - `DataFetcherService`：介接 Yahoo Finance，獲取標的之 `shortName`, `sector`, `industry`, `marketCap` 等基本資訊。
  - 財報處理：自動化整理季度 (Quarterly) 與年度 (Annual) 的 `Revenue`, `NetIncome`, `EPS` 資料，並進行日期對齊與缺失值填補。
- **新聞情緒分析 (LLM 整合)**：
  - `LLMInsightEngine`：使用 Gemini API (via `google-genai`) 進行推理。
  - 關鍵字決定：LLM 根據產業特性自動決定 2 個最佳新聞搜尋關鍵字。
  - 綜合報告：整合新聞標題與內容，輸出 JSON 格式的 SWOT 分析、市場情緒指標 (0-100)、情緒理由及風險提示。
- **宏觀指標關聯 (動態推薦)**：
  - LLM 根據產業類別推薦 4 個最具影響力的 FRED 總經指標 ID（排除通用指標，如 `VIXCLS`, `FEDFUNDS` 等）。
  - `DataFetcherService` 根據推薦 ID 進行 FRED API 串接，包含錯誤重試與 Fallback 機制 (如若查無資料自動切換至 CPI 指標)。

### 2.2 市場數據監測
- **K 線圖數據**：
  - API 支援自定義區間與週期（例如：5m/1h/1d），回傳 ECharts 標準格式：`[Open, Close, Low, High]`。
  - 內建技術指標計算：MA10 與 MA20。
- **總經看板**：
  - 提供 FRED 數據的快取 (`self._macro_cache`) 機制，減少重複 API 呼叫。
  - 資料清理：自動處理 FRED API 缺失值 (".") 與無效數據。

### 2.3 智能預測服務
- **深度學習集成 (Ensemble)**：
  - 核心模型：整合 LSTM、GRU、CNN-LSTM 三種模型進行平均預測，提供未來 5 天價格趨勢。
  - 特徵工程：結合價格數據與財務報表（EPS/PE Ratio），並透過 `MinMaxScaler` 進行歸一化。
- **模型訓練流程**：
  - 執行緒管理：採用 `threading` 的 `Daemon Threads` 與全域鎖 (`threading.Lock`)，解決併發訓練導致的內存溢出問題。
  - 記憶體保護：訓練過程中強制執行 `tf.keras.backend.clear_session()` 與 `gc.collect()`。
- **可解釋性 (Explainability)**：
  - 採用 Permutation-based 特徵重要性分析，量化各模型對預測結果的貢獻度。
- **狀態追蹤機制**：
  - 定義 `_task_status`, `_task_progress`, `_task_results` 字典維護任務生命週期（processing, success, error）。

## 3. 技術架構
- **後端 (FastAPI)**：標準化 RESTful API，內含 CORS 設定與模組化路由結構 (`api/analysis.py`, `api/market_overview.py`)。
- **外部整合與安全**：
  - `.env` 檔案管理：`GEMINI_API_KEY`, `FRED_API_KEY` 等敏感資訊統一控管。
  - `LLMInsightEngine`：具備首次存取的「懶加載」(Lazy Initialization) 與握手機制，驗證 API 金鑰與連線池可用性。
- **資料處理層**：
  - 使用 Pandas `merge_asof` 將技術面數據與財報數據進行日期對齊 (Backward-fill)。
  - `_sanitize_data` 工具函數：將 NumPy/Pandas 資料結構中的 NaN/Inf 轉換為合法的 JSON `None` 值，確保 API 回應穩定性。

## 4. 非功能性需求
- **擴充性**：後端服務分層設計 (`Core`, `Services`, `API`)，新增模型僅需實作新工廠函數並添加到 `model_factories` 清單。
- **效能**：針對 AI 推理的非阻塞架構，API 收到請求後立即返回 status，實際運算透過背景 thread 完成。
- **容錯性**：關鍵資料請求具備多層級 Failover (例：FRED API 失敗時切換至 Consumer Price Index)。

## 5. API 清單
- `GET /api/status`：系統檢查。
- `POST /api/analyze`：分析報告 (輸入 ticker，返回 SWOT 與宏觀推薦)。
- `GET /api/macro/{indicator_id}`：獲取 FRED 指標詳細數值。
- `GET /api/kline`：K 線資料 API (query params: `ticker`, `interval`, `period`)。
- `POST /api/predict`：啟動預測 (輸入 ticker)，返回狀態碼。
- `GET /api/predict/status/{ticker}`：獲取最新預測結果、SHAP 重要性、財報數據。
