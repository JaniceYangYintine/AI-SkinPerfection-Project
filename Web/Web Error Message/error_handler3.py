# 修改處 1：導入 v3 專用的訊息模組，捨棄 v2 的 LineBotApi
from linebot.v3.messaging import ReplyMessageRequest, TextMessage
import logging

# 錯誤訊息配置表 (保持不變，這是你的核心定義)
ERROR_CONFIG = {
    "AI_TIMEOUT": "AI_TIMEOUT\nAI 模型處理超時系統繁忙中，請稍後再試",
    "YOLO_ERROR": "YOLO_ERROR\nYOLO 模型錯誤分析失敗，請重新拍照",
    "LLM_ERROR": "LLM_ERROR\nLLM 服務錯誤AI 分析服務暫時無法使用",
    "STORAGE_ERROR": "STORAGE_ERROR\n儲存失敗系統錯誤，請稍後再試",
    "UNKNOWN_ERROR": "UNKNOWN_ERROR\n未知錯誤系統錯誤，請稍後再試"
}

# 修改處 2：新增自動判斷 Exception 的函式
def handle_exception_and_reply(line_bot_api, reply_token, exception_obj, app_logger):
    """
    接收 Exception 物件，判斷後自動回覆
    """
    error_str = str(exception_obj).lower()
    error_key = "UNKNOWN_ERROR"

    # 關鍵字判斷邏輯
    if "timeout" in error_str:
        error_key = "AI_TIMEOUT"
    elif any(k in error_str for k in ["yolo", "detect", "image", ".pt", "ultralytics", "boxes"]):
        error_key = "YOLO_ERROR"
    elif any(k in error_str for k in ["llm", "gemini", "openai", "api", "google", "api", "quota"]):
        error_key = "LLM_ERROR"
    elif any(k in error_str for k in ["db", "storage", "insert", "save", "mysql", "google", "upload"]):
        error_key = "STORAGE_ERROR"

    # 紀錄錯誤日誌給工程師看 (修正 app_logger 未定義問題)
    app_logger.error(f"Captured Error [{error_key}]: {exception_obj}")
    
    # 取得對應的友善訊息
    friendly_msg = ERROR_CONFIG.get(error_key, ERROR_CONFIG["UNKNOWN_ERROR"])

    # 呼叫發送函式
    send_error_response(line_bot_api, reply_token, error_key)

# 修改處 3：將發送邏輯改為 v3 語法
def send_error_response(line_bot_api, reply_token, error_key):
    """
    統一發送錯誤訊息給 LINE 使用者 (v3 版本)
    """
    msg_text = ERROR_CONFIG.get(error_key, ERROR_CONFIG["UNKNOWN_ERROR"])
    
    try:
        # v3 使用 ReplyMessageRequest
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=msg_text)]
            )
        )
    except Exception as e:
        logging.error(f"Failed to send LINE reply: {str(e)}")