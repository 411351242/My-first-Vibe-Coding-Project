# ✦ AI QUANT PLATFORM (一站式產業分析平台)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203-4FC08D?style=flat-square&logo=vuedotjs)](https://vuejs.org/)
[![Gemini](https://img.shields.io/badge/AI-Gemini%201.5-blue?style=flat-square&logo=google-gemini)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

這是一套設計給現代投資人的 **AI 輔助決策平台**。平台整合了全球指數、總經數據、即時新聞與基本面資料，並以 Google Gemini LLM 為核心，產出高度專業的選股建議與產業洞察報告。

---

## ✨ 核心亮點 (Core Features)

*   **⚡ 極速平行抓取引擎**：優化數據載入邏輯，利用多線程 (Thread Pool) 平行抓取 Yahoo Finance 與 FRED 數據，載入效能提升 10 倍。
*   **🌐 全球市場熱力矩陣**：利用 ECharts Treemap 動態展示美、歐、亞及大洋洲市場規模與漲跌即時分布。
*   **🤖 AI 深度研究報告**：
    *   **SWOT 分析**：優劣勢與機會威脅自動摘要。
    *   **情緒偵測**：AI 自動研讀最新新聞，給予 0-100 的市場情緒評分。
    *   **風險提示**：列出標的潛在的產業或財務風險。
*   **📉 智慧總經指標追蹤**：AI 會根據查詢標的之產業特性，自動推薦並繪製相關度最高的總經指標 (如：CPI, Fed Rates, 10Y Bond Yields)。

---

## 🛠 技術棧 (Tech Stack)

*   **Frontend**: Vue 3 (Composition API), Vite, Axios, ECharts (Vue-ECharts)
*   **Backend**: FastAPI (Python), Uvicorn, TenserFlow Core
*   **Data Sources**: yfinance, FRED API (St. Louis Fed)
*   **AI Engine**: Google Gemini API (gemini-1.5-flash)

---

## 🚀 本地快速啟動 (Quick Start)

專案配備了自動化啟動腳本，您不需要手動開啟多個視窗。

### 1. 環境準備
*   **Python 3.10+**
*   **Node.js 18+**

### 2. 環境變數設定
在專案根目錄建立 `.env` 檔案：
```env
# 必要：Google Gemini API 金鑰
GEMINI_API_KEY=your_key_here

# 必要：FRED API 金鑰 (用於獲取總經數據)
FRED_API_KEY=your_key_here
```

### 3. 一鍵啟動 (Windows 專用)
直接執行根目錄的腳本：
```powershell
python start.py
```
*此腳本會自動檢查環境、安裝缺失依賴、並同時啟動後端伺服器 (Port 8000) 與前端開發環境 (Port 3000)。*

---

## 📂 專案結構 (Directory Structure)

```text
AIBot/
├── backend/            # FastAPI 後端服務
│   ├── api/            # API 路由 (市場概覽、分析、診斷)
│   ├── core/           # 核心配置與環境變數載入
│   ├── services/       # AI 引擎、數據抓取、預測模型
│   └── main.py         # 應用程式入口
├── frontend/           # Vue 3 前端專案
│   ├── src/
│   │   ├── components/ # UI 元件 (儀表板、圖表、預測卡片)
│   │   └── App.vue     # 主頁面邏輯
│   └── vite.config.js  # Vite 配置 (包含 API Proxy)
├── start.py            # 多線程自動啟動與監控腳本
└── .env                # API Key 設定
```

---

## 🔧 疑難排解 (Troubleshooting)

| 問題 | 解決方法 |
| :--- | :--- |
| **ECONNREFUSED 127.0.0.1:8000** | 後端尚未啟動完成。請稍候約 10-20 秒，等待 AI 引擎熱機成功。 |
| **市場資料載入失敗** | 檢查 `FRED_API_KEY` 是否有效。專案已具備並行抓取重試機制，通常重整頁面即可。 |
| **TensorFlow 警告訊息** | 這是 Windows 下的常見警告，不影響程式分析功能。 |

---
