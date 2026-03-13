import logging
from linebot.v3.messaging import ReplyMessageRequest, TextMessage

# 1. 錯誤訊息定義 (與之前定義的一致)
ERROR_CONFIG = {
    "AI_TIMEOUT": "AI_TIMEOUT\nAI 模型處理超時系統繁忙中，請稍後再試",
    "YOLO_ERROR": "YOLO_ERROR\nYOLO 模型錯誤分析失敗，請重新拍照",
    "LLM_ERROR": "LLM_ERROR\nLLM 服務錯誤AI 分析服務暫時無法使用",
    "STORAGE_ERROR": "STORAGE_ERROR\n儲存失敗系統錯誤，請稍後再試",
    "UNKNOWN_ERROR": "UNKNOWN_ERROR\n未知錯誤系統錯誤，請稍後再試"
}

def handle_exception_and_reply(line_bot_api, reply_token, exception_obj):
    """
    自動判斷 Exception 類型並回覆對應訊息
    """
    error_key = "UNKNOWN_ERROR" # 預設值
    
    # 2. 自動判斷邏輯 (依照不同的 Exception 類型轉換為 Error Key)
    error_str = str(exception_obj)
    
    if "timeout" in error_str.lower():
        error_key = "AI_TIMEOUT"
    elif "yolo" in error_str.lower() or "detect" in error_str.lower():
        error_key = "YOLO_ERROR"
    elif "llm" in error_str.lower() or "openai" in error_str.lower() or "gemini" in error_str.lower():
        error_key = "LLM_ERROR"
    elif "db" in error_str.lower() or "storage" in error_str.lower() or "insert" in error_str.lower():
        error_key = "STORAGE_ERROR"

    # 3. 呼叫發送函式
    send_error_response(line_bot_api, reply_token, error_key)
    return error_key

def send_error_response(line_bot_api, reply_token, error_key):
    """
    純發送訊息的底層函式
    """
    msg_text = ERROR_CONFIG.get(error_key, ERROR_CONFIG["UNKNOWN_ERROR"])
    
    try:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=msg_text)]
            )
        )
    except Exception as e:
        logging.error(f"Failed to send LINE reply: {e}")