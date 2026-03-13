from linebot import LineBotApi
from linebot.models import TextSendMessage
import logging

# 錯誤訊息配置表
ERROR_CONFIG = {
    "AI_TIMEOUT": "AI_TIMEOUT\nAI 模型處理超時系統繁忙中，請稍後再試",
    "YOLO_ERROR": "YOLO_ERROR\nYOLO 模型錯誤分析失敗，請重新拍照",
    "LLM_ERROR": "LLM_ERROR\nLLM 服務錯誤AI 分析服務暫時無法使用",
    "STORAGE_ERROR": "STORAGE_ERROR\n儲存失敗系統錯誤，請稍後再試",
    "UNKNOWN_ERROR": "UNKNOWN_ERROR\n未知錯誤系統錯誤，請稍後再試"
}

def send_error_response(line_bot_api, reply_token, error_key):
    """
    統一發送錯誤訊息給 LINE 使用者
    """
    # 取得對應的訊息，若找不到則預設為 UNKNOWN_ERROR
    msg = ERROR_CONFIG.get(error_key, ERROR_CONFIG["UNKNOWN_ERROR"])
    
    # 執行回覆
    try:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
    except Exception as e:
        logging.error(f"Failed to send error message: {str(e)}")

# --- 使用範例 ---
# if error_occurs:
#     send_error_response(line_bot_api, event.reply_token, "LLM_ERROR")