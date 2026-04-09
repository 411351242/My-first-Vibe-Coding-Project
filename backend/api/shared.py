from backend.services.predictor_service import PredictorService

# 建立全局單例，確保在整個應用生命週期內狀態不丟失
predictor = PredictorService()
