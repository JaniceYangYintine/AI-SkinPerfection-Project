import os
from dotenv import load_dotenv     
import google.generativeai as genai
import sys
from flask import Flask, request, jsonify
import json
from datetime import datetime
import uuid

# 嘗試導入 flask_cors，如果失敗則手動設定 CORS
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("⚠️ flask_cors 未安裝，將使用手動 CORS 設定")

# 設定輸出編碼為 UTF-8 以支援 Emoji
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 1. 前置作業：開保險箱 (Load Environment)
# ==========================================

# 步驟 A: 執行開啟動作 (這行最重要！沒這行讀不到 .env)
load_dotenv('key.env')

# 步驟 B: 從環境變數抓取 Key
API_KEY = os.getenv("GEMINI_API_KEY")

# ==========================================
# 2. 檢查環節 (Debug Check)
# ==========================================

if not API_KEY:
    print("❌ 錯誤：找不到鑰匙！請檢查 .env 檔案或是變數名稱是否打錯。")
    sys.exit()
else:
    print("✅ 系統顯示：鑰匙讀取成功！(安全模式)")

# ==========================================
# 3. 設定區域 (Configuration)
# ==========================================
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"[WARNING] 初始化錯誤: {e}")

# ==========================================
# 4. Flask API 設定
# ==========================================

app = Flask(__name__)

# 設定 CORS
if CORS_AVAILABLE:
    CORS(app)  # 允許跨域請求
    print("[OK] 使用 flask_cors")
else:
    # 手動設定 CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    print("[OK] 使用手動 CORS 設定")

# ==========================================
# 4.5. 日誌記錄功能
# ==========================================

# 確保 logs 目錄存在
LOGS_DIR = "logs"
LOGS_FILE = os.path.join(LOGS_DIR, "history.json")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
    print(f"[INFO] 已創建日誌目錄: {LOGS_DIR}")

def save_log(user_data, ai_response, status="success", error_message=None, model_name=None, prompt=None):
    """
    保存日誌到 JSON 文件
    
    Args:
        user_data: 使用者問卷數據
        ai_response: AI 回應內容
        status: 執行狀態 (success/error)
        error_message: 錯誤訊息 (如果有)
        model_name: 使用的 AI 模型名稱
        prompt: 發送給 AI 的完整 prompt
    """
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_name": model_name,
        "user_input": user_data,
        "prompt": prompt,
        "ai_response": ai_response,
        "status": status
    }
    
    if error_message:
        log_entry["error"] = error_message
    
    # 讀取現有日誌
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    else:
        logs = []
    
    # 添加新記錄
    logs.append(log_entry)
    
    # 寫入文件 - 使用自定義格式讓長文本更易讀
    try:
        # 將 prompt 和 ai_response 轉換為行陣列以便分行顯示
        formatted_logs = []
        for log in logs:
            formatted_log = log.copy()
            # 將長文本按行分割
            if 'prompt' in formatted_log and formatted_log['prompt']:
                formatted_log['prompt'] = formatted_log['prompt'].split('\n')
            if 'ai_response' in formatted_log and formatted_log['ai_response']:
                formatted_log['ai_response'] = formatted_log['ai_response'].split('\n')
            formatted_logs.append(formatted_log)
        
        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(formatted_logs, f, ensure_ascii=False, indent=2)
        print(f"[LOG] 已保存日誌: {log_entry['id']}")
    except Exception as e:
        print(f"[ERROR] 日誌保存失敗: {e}")


# 5. 核心邏輯層 (Logic Layer)
# ==========================================

def generate_health_prompt(user_data):
    """
    將問卷資料轉換成 AI 看得懂的指令 (Prompt Engineering)
    """
    prompt = f"""
你是一位專業的營養與肌膚健康顧問。請根據以下使用者問卷資料，生成 3 組精準的「食材組合建議」。

【使用者問卷資料】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
年齡：{user_data.get('age', '未知')}
膚質狀態：{user_data.get('skin_type', '未知')}
敏感度：{user_data.get('sensitivity', '未知')}
保養步驟：{user_data.get('skincare_routine', '未知')}
睡眠時間：{user_data.get('sleep', '未知')}
壓力指數：{user_data.get('stress', '未知')}
運動頻率（每週）：{user_data.get('exercise', '未知')}
油炸食物攝取（每週）：{user_data.get('fried_food', '未知')}
蔬果攝取：{user_data.get('veggies', '未知')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【輸出格式要求】
請嚴格按照以下格式輸出，不要添加任何額外的標題、前言或結語：

組合名稱
推薦食材： 食材1、食材2、食材3、食材4。
功效說明文字（一句話，說明這組食材的主要功效和作用機制）。

組合名稱
推薦食材： 食材1、食材2、食材3、食材4。
功效說明文字（一句話，說明這組食材的主要功效和作用機制）。

組合名稱
推薦食材： 食材1、食材2、食材3、食材4。
功效說明文字（一句話，說明這組食材的主要功效和作用機制）。

【範例參考】
敏感屏障修護組
推薦食材： 鮭魚、亞麻仁油、核桃、酪梨。
這組食材富含 Omega-3 脂肪酸，能從內而外修補肌膚屏障並降低敏感發炎反應。

皮脂平衡代謝組
推薦食材： 糙米、無糖豆漿、雞肉、菠菜。
透過維生素 B 群調節油脂分泌並穩定代謝，改善 T 字部出油與粉刺困擾。

熬夜亮膚抗氧組
推薦食材： 奇異果、藍莓、大番茄、綠茶。
高濃度的維生素 C 與植化素能清除熬夜產生的自由基，拯救蠟黃並提升肌膚防禦力。

【重要提醒】
1. 組合名稱要精準反映使用者的肌膚問題和生活狀態
2. 每組推薦 4 種具體食材（不要用「等」字）
3. 功效說明要科學、具體、一句話完成
4. 不要添加任何 emoji 或表情符號
5. 嚴格按照格式，不要有多餘的標題或分隔線
6. 根據使用者的膚質、睡眠、壓力、飲食習慣來客製化建議

現在請開始生成：
"""
    return prompt

def get_ai_analysis(user_input_data):
    """
    發送請求給 LLM
    返回: (prompt, response) 元組
    """
    print("[INFO] 正在讀取數據並生成... (AI 運算中)\n")
    
    final_prompt = generate_health_prompt(user_input_data)
    
    try:
        response = model.generate_content(final_prompt)
        # 確保輸出格式適合前端使用,保留原始換行
        return final_prompt, response.text
    except Exception as e:
        error_msg = f"[ERROR] 連線失敗: {e}"
        return final_prompt, error_msg

# ==========================================
# 6. API 路由 (API Routes)
# ==========================================

@app.route('/api/health-advice', methods=['POST'])
def health_advice():
    """
    接收前端問卷資料,返回 AI 建議
    """
    user_data = None
    prompt = None
    try:
        # 從前端接收 JSON 資料
        user_data = request.json
        
        # 驗證必要欄位
        required_fields = ['age', 'skin_type', 'sensitivity', 'skincare_routine', 
                          'sleep', 'stress', 'exercise', 'fried_food', 'veggies']
        
        for field in required_fields:
            if field not in user_data:
                error_msg = f'缺少必要欄位: {field}'
                # 記錄錯誤日誌
                save_log(user_data, None, status="error", error_message=error_msg, 
                        model_name='gemini-2.5-flash', prompt=None)
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
        
        # 取得 AI 分析結果 (返回 prompt 和 response)
        prompt, result = get_ai_analysis(user_data)
        
        # 記錄成功日誌
        save_log(user_data, result, status="success", 
                model_name='gemini-2.5-flash', prompt=prompt)
        
        # 返回結果
        return jsonify({
            'success': True,
            'advice': result
        })
        
    except Exception as e:
        error_msg = str(e)
        # 記錄錯誤日誌
        save_log(user_data if user_data else {}, None, status="error", 
                error_message=error_msg, model_name='gemini-2.5-flash', prompt=prompt)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/test', methods=['GET'])
def test():
    """
    測試 API 是否正常運作
    """
    return jsonify({
        'success': True,
        'message': 'API 運作正常 ✅'
    })

# ==========================================
# 7. 啟動伺服器
# ==========================================

if __name__ == "__main__":
    print("\n[START] Flask API 伺服器啟動中...")
    print("[INFO] API 端點: http://localhost:5000/api/health-advice")
    print("[INFO] 測試端點: http://localhost:5000/api/test\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
