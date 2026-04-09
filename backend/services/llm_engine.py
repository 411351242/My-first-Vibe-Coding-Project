"""
LLM Insight Engine 模組 (負責分析報告與總經儀表板邏輯)
核心邏輯 (RAG 任務分工):
1. 資訊匯總與推理：自動搜集標的財務數據與新聞，利用 LLM 閱讀、摘要與邏輯推理。
2. 文字報告生成：產生「產業優劣勢」、「市場情緒總結」、「潛在風險與觀察重點」。
3. 總經圖表指標推薦：動態挑選與標的或產業「高度相關」的總經指標 ID 陣列供前端繪製。
"""

import json
from google import genai
from backend.core.config import settings

class LLMInsightEngine:
    def __init__(self):
        # 取得設定的 API 金鑰
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.DEFAULT_LLM_MODEL
        # 使用延遲初始化 (Lazy Init)，避免冷啟動時與 Gemini 建立連線失敗
        self._client = None
        self._ready_cached = False

    @property
    def client(self):
        """首次存取時才建立 Gemini client，避免冷啟動失效"""
        if self._client is None and self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                self._client = genai.Client(api_key=self.api_key)
                print("[LLM] Gemini client 物件建立成功 (待握手)")
            except Exception as e:
                print(f"[LLM] Gemini client 實例化失敗: {e}")
        return self._client

    def check_ready(self) -> bool:
        """真正的穩定性握手：不只是檢查物件，而是執行一次 metadata 讀取測試。"""
        if self._ready_cached:
            return True
        
        c = self.client
        if c:
            try:
                # 執行最輕量的 metadata 讀取，驗證 API KEY 與網路連線池
                # list_models 是分頁讀取，效能極高
                models = c.models.list(config={'page_size': 1})
                # 遍歷第一個元素以觸發真實連線
                for _ in models: break
                
                self._ready_cached = True
                print("[LLM] Gemini Handshake 成功，連線池已熱機")
                return True
            except Exception as e:
                print(f"[LLM] Gemini Handshake 失敗 (這通常是 API Key 沒過或暖機中): {e}")
                return False
        return False

    def extract_search_keywords(self, stock_info: dict, model_name: str) -> list[str]:
        """讓 LLM 根據公司名稱與產業決定 2 個最佳的搜尋關鍵字"""
        if not self.client:
            return [stock_info.get('symbol'), stock_info.get('industry', '半導體')]
            
        prompt = f"""
        使用者正在研究股票 {stock_info.get('symbol')} ({stock_info.get('shortName')})，其產業為 {stock_info.get('industry', '')}。
        請判斷該股票最具代表性的 2 個中文新聞搜尋關鍵字（可以是公司中文全名、簡稱或核心產業名稱）。
        請直接輸出純 JSON 陣列，內部字串為關鍵字，例如：["台積電", "半導體"]
        """
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            return data[:2] if isinstance(data, list) and data else [stock_info.get('symbol')]
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "quota" in msg or "limit" in msg or "exhausted" in msg:
                print(f"Gemini API 達上限: {e}")
            else:
                print(f"Gemini API 關鍵字提取失敗: {e}")
            return [stock_info.get('symbol')]

    def generate_analysis_report(self, stock_info: dict, structured_news: list[dict], model_name: str) -> dict:
        """
        利用 LLM 閱讀新聞與基本面數據，生成綜合分析報告。
        """
        sector = stock_info.get('sector', '未知')
        
        fallback_res = {
            "swot_analysis": f"優勢：本系統已經準備好為 {sector} 產業進行推理。\n劣勢：您尚未填寫有效的 GEMINI_API_KEY，這是一段模擬測試文字。請前往 .env 填寫金鑰。",
            "market_sentiment": "中立",
            "sentiment_score": 50,
            "sentiment_reasons": ["尚未啟用 AI 模型"],
            "risk_warnings": "尚未啟用 AI 模型。請確認後端已正確啟動並讀取您的 API 金鑰。"
        }
        
        if not self.client:
            return fallback_res

        # 將結構化新聞轉為 Prompt 文字
        news_text = ""
        for n in structured_news:
            news_text += f"標題：{n.get('title')}\n內容：{n.get('summary')}\n\n"

        # 組合 RAG Prompt
        prompt_text = f"""
        你是一位資深台股與美股量化投資分析師。
        請根據以下標的資訊與近期新聞，產出一份 JSON 格式的投資摘要報告。

        【標的資訊】
        - 代號/名稱: {stock_info.get('symbol')} ({stock_info.get('shortName')})
        - 產業類別: {sector} / {stock_info.get('industry')}
        - 業務摘要: {stock_info.get('businessSummary', '')[:500]}

        【近期新聞脈絡】
        {news_text}

        請輸出符合以下 JSON 結構的報告（絕不輸出多餘的文字或 Markdown，僅限可解析的 JSON）：
        {{
            "swot_analysis": "一段約50字，總結該公司或產業的短期優劣勢與機會威脅。",
            "market_sentiment": "必須是這三個詞之一: 偏多, 偏空, 中立。請依據新聞內容做綜合判讀。",
            "sentiment_score": "從 0 到 100 的整數，表示看多情緒的強烈程度 (0=極度看空, 100=極度看多)",
            "sentiment_reasons": ["以極度精簡的列點方式", "說明為何給出該看多/空分數", "最多列出 3 點"],
            "risk_warnings": "一段約30字，提示買進前應注意的宏觀或公司層面風險。"
        }}
        """

        try:
            # 呼叫 Gemini, 要求強制吐出 JSON
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2, # 降低隨機性，保證報告穩健
                )
            )
            data = json.loads(response.text)
            return {
                "swot_analysis": data.get("swot_analysis", "無法解析的分析"),
                "market_sentiment": data.get("market_sentiment", "中立"),
                "sentiment_score": data.get("sentiment_score", 50),
                "sentiment_reasons": data.get("sentiment_reasons", ["無特別情緒指標"]),
                "risk_warnings": data.get("risk_warnings", "無風險提示")
            }
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "quota" in msg or "limit" in msg or "exhausted" in msg:
                return {
                    "swot_analysis": "優勢：無\n劣勢：您今日的分析已達上限，請更換模型或明天再試。",
                    "market_sentiment": "中立",
                    "sentiment_score": 50,
                    "sentiment_reasons": ["您今日的分析已達上限，請更換模型或明天再試。"],
                    "risk_warnings": "您今日的分析已達上限，請更換模型或明天再試。"
                }
            print(f"Gemini API 失敗: {e}")
            return fallback_res

    def recommend_macro_indicators(self, industry_or_sector: str, model_name: str) -> list[str]:
        """
        動態拋棄傳統固定儀表板，由 AI 分析並返回高度相關之總經指標(ID)陣列。
        """
        if not self.client:
            # Fallback Mock logic
            if "Technology" in industry_or_sector or "電子" in industry_or_sector:
                return ["DGS10", "UMCSENT"] 
            elif "Real Estate" in industry_or_sector or "營建" in industry_or_sector:
                return ["FEDFUNDS", "HOUST"] 
            return ["FEDFUNDS", "CPIAUCSL"]

        prompt_text = f"""
        你熟悉美國聯準會 FRED Database，現在使用者正在查詢 "{industry_or_sector}" 相關產業的公司。
        請推薦 4 個最能影響該產業資金流動或基本面的 FRED 總經數據指標 ID。
        
        【重要規範】
        請避開以下全局通用的宏觀指標（因為儀表板已顯示）：
        VIXCLS, RECPROUSM156N, T10Y2Y, FEDFUNDS, CPIAUCSL, UNRATE, DGS10, UMCSENT, HOUST, M2SL

        請依據產業特性挑選更精確的指標，例如：
        - 零售/電商：RETAILMS (零售銷售額), PCE (個人消費支出)
        - 半導體/電子：PCU334413334413 (半導體產出物價指數)
        - 能源：IPG211111N (原油與天然氣開採生產指數)
        - 航運：BDIY (波羅的海乾散貨運價指數 - 若支援)
        - 一般製造業：IPMAN (工業生產指數)
        
        請直接輸出純 JSON 陣列，內部字串為指標 ID，不要包含其他解釋文字：
        例如：["RETAILMS", "IPMAN", "PCE", "INDPRO"]
        """
        
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            data = json.loads(response.text)
            if isinstance(data, list) and len(data) > 0:
                return data[:4] # 修改為最多回傳 4 個
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "quota" in msg or "limit" in msg or "exhausted" in msg:
                print(f"Gemini 達上限，使用預設 ID: {e}")
            else:
                print(f"Gemini API 宏觀推薦失敗: {e}")
            
        # 使用不會與左側儀表板(VIXCLS, CPIAUCSL, FEDFUNDS等)衝突的經典總經指標
        return ["RETAILMS", "INDPRO", "PCE", "PAYEMS"]
