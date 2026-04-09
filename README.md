# 專案名稱：一站式產業分析平台 (AI Quant Platform)

這是一套設計給台股投資人的 **AI 輔助分析 Web 平台**。平台整合了多種總經數據、基本面資料及新聞情緒，並以大型語言模型（LLM）為核心提供選股與產業的視覺化分析報告與圖表。

## 🚀 核心功能
1. **單一標的查詢與產業比較**：提供個股或特定產業的比較與資金流向分析。
2. **AI 綜合分析報告**：RAG 架構生成，產出產業優劣勢、市場情緒總結、潛在風險提示。
3. **智慧總經視覺化追蹤**：AI 動態挑選與標的高度相關的總經指標並繪製圖表。

## 🛠 本地快速啟動

在開始之前，請確保您的電腦已安裝 **Python 3.10+** 與 **Node.js**。

### 1. 取得專案
```bash
git clone <你的 GitHub 倉庫連結>
cd AIBot
```

### 2. 設定環境變數
請在專案根目錄建立一個名為 `.env` 的檔案，並填入您的 API 金鑰：

```env
# Gemini API Key (必要 - 系統鎖定使用 gemini-3.1-flash-lite-preview)
GEMINI_API_KEY=your_gemini_api_key_here

# FRED API Key (選填，若無則會使用模擬數據)
FRED_API_KEY=your_fred_api_key_here
```

### 3. 安裝依賴並啟動

**後端 (FastAPI):**
```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

**前端 (Vue.js):**
```bash
cd frontend
npm install
npm run dev
```

現在，打開瀏覽器存取 `http://localhost:5173` 即可開始使用！

---

## ⚙️ 系統配置說明
本專案透過 `backend/core/config.py` 進行統一管理，模型版本已鎖定為 `gemini-3.1-flash-lite-preview`，確保分析品質的一致性。

## 🛡 授權與貢獻
* 本專案採用 **MIT License**。
* 歡迎提交 Issues 回報錯誤或 Pull Requests 改進功能。

---
*註：若啟動時遇到 API Key 錯誤，請檢查根目錄的 `.env` 檔案格式是否正確。*
