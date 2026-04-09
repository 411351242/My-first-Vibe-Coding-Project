from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Quant Platform - 一站式產業分析平台",
    description="結合總經數據、基本面與新聞情緒的 AI 輔助投資分析 API",
    version="0.1.0"
)

# 解決跨域問題 (CORS)，方便後續與 React/Vue 前端界接
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """確認 API 是否正常運作的測試端點"""
    return {"message": "Welcome to AI Quant Platform API"}

from backend.api.analysis import router as analysis_router
app.include_router(analysis_router, prefix="/api")

from backend.api.market_overview import router as market_router
app.include_router(market_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # 強制監聽 127.0.0.1 以確保與 Vite Proxy 一致，避免 Windows 上的連線問題
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

