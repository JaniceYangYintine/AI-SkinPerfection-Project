import os
from flask import Flask, request, abort
from dotenv import load_dotenv

load_dotenv()

from linebot.v3 import (
    WebhookHandler
)
# ... 其餘 import 保持不變
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from error_handler3 import send_error_response
from error_handler3 import handle_exception_and_reply

#llm error
import google.generativeai as genai
from google.api_core import exceptions

#storage error
import pymysql
from google.cloud import storage

app = Flask(__name__)

# 從環境變數讀取 LINE Bot 設定
line_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')

configuration = Configuration(access_token=line_access_token)
handler = WebhookHandler(line_channel_secret)

# 從環境變數讀取 Gemini API Key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # 修正 A: 定義 user_text，從 event 中提取使用者傳來的文字
        user_text = event.message.text

        try:
            # 使用 request_options 設定 25 秒超時
            response = model.generate_content(
                user_text, 
                request_options={"timeout": 25} 
            )

            llm_text = response.text  # 取得文字結果  

            # --- [第二步：GCP Cloud Storage 儲存] ---
            gcs_client = storage.Client()
            bucket_name = os.getenv('GCS_BUCKET_NAME')
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob('logs/reply.txt')
            blob.upload_from_string(llm_text) # 將結果存入 GCS


            # --- [第三步：GCP Cloud SQL (MySQL) 儲存紀錄] ---
            connection = pymysql.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            with connection.cursor() as cursor:
                sql = "INSERT INTO chat_logs (content) VALUES (%s)"
                cursor.execute(sql, (llm_text,))
            connection.commit()
            connection.close()

            
            # 正常回覆
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=llm_text)]
                )
            )

        except Exception as e:
            handle_exception_and_reply(line_bot_api, event.reply_token, e, app.logger)

            
if __name__ == "__main__":
    app.run()