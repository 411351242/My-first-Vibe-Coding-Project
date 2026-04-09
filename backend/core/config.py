import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# 定義專案根目錄
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # --- 專案基礎配置 ---
    APP_NAME: str = "AIBot-Investment-Platform"
    DEBUG: bool = False
    
    # --- 模型配置 (鎖定為指定的模型版本) ---
    DEFAULT_LLM_MODEL: str = "gemini-3.1-flash-lite-preview"
    
    # --- API Keys ---
    GEMINI_API_KEY: Optional[str] = None
    FRED_API_KEY: Optional[str] = None
    
    # --- 資料庫配置 ---
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/app_data.db"

    # 讀取 .env 設定
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_keys(self):
        """檢查必要的 API Key 是否存在"""
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "\n[!] 錯誤：專案已配置使用 Gemini 模型，但找不到 GEMINI_API_KEY。\n"
                "請在 .env 檔案中設定：GEMINI_API_KEY=your_gemini_key"
            )

# 初始化設定實例
settings = Settings()

# 在模組載入時執行初步校驗
try:
    settings.validate_keys()
except ValueError as e:
    print(e)
