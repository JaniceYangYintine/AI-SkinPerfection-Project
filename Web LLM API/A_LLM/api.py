import os
from dotenv import load_dotenv     
import google.generativeai as genai
import sys
from flask import Flask, request, jsonify
import json
from datetime import datetime
import uuid
import random

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
# 4.5. 載入面部動作資料
# ==========================================

# 載入 face.json
FACE_DATA_FILE = "face.json"
try:
    with open(FACE_DATA_FILE, 'r', encoding='utf-8') as f:
        FACE_ACTIONS = json.load(f)
    print(f"[INFO] 已載入 {len(FACE_ACTIONS)} 個面部動作資料")
except FileNotFoundError:
    print(f"[ERROR] 找不到 {FACE_DATA_FILE} 檔案")
    FACE_ACTIONS = []
except json.JSONDecodeError as e:
    print(f"[ERROR] {FACE_DATA_FILE} 格式錯誤: {e}")
    FACE_ACTIONS = []

# ==========================================
# 4.6. 日誌記錄功能
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
    氣色分析專家版本
    """
    # 將用戶資料格式化為易讀的文字
    user_info = f"""
用戶基本資料：
- 年齡：{user_data.get('age', '未提供')}
- 膚質：{user_data.get('skin_type', '未提供')}
- 敏感度：{user_data.get('sensitivity', '未提供')}
- 保養習慣：{user_data.get('skincare_routine', '未提供')}
- 睡眠狀況：{user_data.get('sleep', '未提供')}
- 壓力程度：{user_data.get('stress', '未提供')}
- 運動頻率：{user_data.get('exercise', '未提供')}
- 油炸食物：{user_data.get('fried_food', '未提供')}
- 蔬菜攝取：{user_data.get('veggies', '未提供')}
"""
    
    prompt = f"""# Role: 溫暖貼心的肌膚氣色分析專家

# Task: 根據提供的用戶問卷資料，針對 10 項指標進行深度觀察與暖心建議。

# Constraints:
1. 語氣：像好朋友般親切、溫馨且具鼓勵性，避免冰冷的指令感。
2. 總分限制：氣色總分必須設定在 70 / 100 以上。
3. 整體評價：限制於 80 字內。
4. 內容結構：
   - 先給出總分
   - 寫出整體評價（格式：先稱讚優點，再指出 2 個最嚴重的指標問題）
   - 針對那 2 個最嚴重的問題，從「10項清單」中對應出改善建議
5. 禁令：禁止冗長解釋與開場白，直接進入分析。

# 10 項指標清單 (僅限從中挑選)：
1. 面部明暗分布
2. 面部紅潤度
3. 神經肌肉張力
4. 眼神聚焦感
5. 組織水分感
6. 面部輪廓線
7. 眉心緊縮度
8. 鼻翼呼吸感
9. 頸部線條
10. 眼神透亮度

# 用戶資料：
{user_info}

# Output Format (JSON Only)
請直接輸出 JSON，不要包含任何 Markdown 標記、程式碼區塊符號（```）或額外文字：
{{
    "score": 82,
    "overall_review": "妳的皮膚基礎非常好，膚色均勻且散發自然光澤，給人一種知性穩定的美感。目前較明顯的狀況是眼神聚焦感略顯疲憊，以及面部明暗分布受限於光源，顯得鼻翼與眼周稍有陰影，適度放鬆會更亮眼。",
    "top_issues": ["眼神聚焦感", "面部明暗分布"]
}}

注意：
- score 必須是 70-100 之間的數字
- overall_review 必須在 80 字以內
- top_issues 必須是陣列，包含 2 個從 10 項指標清單中選出的問題
- 請確保輸出的是純 JSON 格式，不要有任何額外的文字或標記
"""
    
    return prompt

def get_action_by_issue(issue_name):
    """
    根據問題名稱從 face.json 中找出對應的改善建議
    
    Args:
        issue_name: 問題名稱（例如："眼神聚焦感"）
    
    Returns:
        對應的動作資料，如果找不到則返回 None
    """
    for action in FACE_ACTIONS:
        if action['target_issue'] == issue_name:
            return action
    return None

def format_action_advice(action):
    """
    格式化單個動作建議
    
    Args:
        action: 動作資料字典
    
    Returns:
        格式化的建議文字
    """
    if not action:
        return "目前沒有對應的改善建議。"
    
    result = f"""🎯 目標問題：{action['target_issue']}

💡 建議動作：
{action['action']}

✨ 預期效果：
{action['effect']}
"""
    return result

def analyze_with_gemini(user_data):
    """
    使用 Gemini AI 分析用戶資料
    
    Args:
        user_data: 用戶問卷資料
    
    Returns:
        AI 分析結果的字典，包含 score, overall_review, top_issues
    """
    print("[INFO] 正在呼叫 Gemini AI 進行氣色分析...\n")
    
    try:
        # 生成 prompt
        prompt = generate_health_prompt(user_data)
        
        # 呼叫 Gemini API
        response = model.generate_content(prompt)
        
        # 取得回應文字
        response_text = response.text.strip()
        print(f"[DEBUG] AI 原始回應:\n{response_text}\n")
        
        # 清理可能的 Markdown 程式碼區塊標記
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # 移除 ```json
        elif response_text.startswith("```"):
            response_text = response_text[3:]  # 移除 ```
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # 移除結尾的 ```
        
        response_text = response_text.strip()
        
        # 解析 JSON
        ai_result = json.loads(response_text)
        
        # 驗證必要欄位
        required_fields = ['score', 'overall_review', 'top_issues']
        for field in required_fields:
            if field not in ai_result:
                raise ValueError(f"AI 回應缺少必要欄位: {field}")
        
        # 驗證 score 範圍
        if not (70 <= ai_result['score'] <= 100):
            print(f"[WARNING] AI 給出的分數 {ai_result['score']} 不在 70-100 範圍內，已調整為 75")
            ai_result['score'] = 75
        
        # 驗證 top_issues 是陣列且有 2 個元素
        if not isinstance(ai_result['top_issues'], list) or len(ai_result['top_issues']) != 2:
            print(f"[WARNING] top_issues 格式不正確，使用預設值")
            ai_result['top_issues'] = ["眼神聚焦感", "面部明暗分布"]
        
        print(f"[SUCCESS] AI 分析完成 - 分數: {ai_result['score']}, 問題: {ai_result['top_issues']}\n")
        
        return ai_result
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析失敗: {e}")
        print(f"[ERROR] 原始回應: {response_text}")
        raise Exception(f"AI 回應格式錯誤，無法解析 JSON: {e}")
    except Exception as e:
        print(f"[ERROR] Gemini AI 呼叫失敗: {e}")
        raise

def get_face_advice(user_input_data):
    """
    獲取完整的氣色分析建議
    
    Returns:
        (prompt, formatted_result) 元組
        - prompt: 發送給 AI 的完整 prompt
        - formatted_result: 格式化後的完整分析結果
    """
    print("[INFO] 正在生成氣色分析報告...\n")
    
    try:
        # 使用 Gemini AI 進行分析
        ai_result = analyze_with_gemini(user_input_data)
        
        # 根據 AI 識別的問題找出對應的改善建議
        issue1 = ai_result['top_issues'][0]
        issue2 = ai_result['top_issues'][1]
        
        action1 = get_action_by_issue(issue1)
        action2 = get_action_by_issue(issue2)
        
        # 格式化完整結果
        formatted_result = f"""氣色總分：{ai_result['score']} / 100

整體評價
{ai_result['overall_review']}

【改善建議】

{format_action_advice(action1)}
---
{format_action_advice(action2)}"""
        
        # 生成 prompt 用於日誌記錄
        prompt = generate_health_prompt(user_input_data)
        
        return prompt, formatted_result
        
    except Exception as e:
        error_msg = f"生成建議失敗: {e}"
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)

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
        
        # 取得氣色分析建議 (返回 prompt 和 formatted_result)
        prompt, result = get_face_advice(user_data)
        
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
                error_message=error_msg, model_name='gemini-2.5-flash', 
                prompt=prompt if prompt else None)
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
    print("[INFO] API 端點: http://localhost:5001/api/health-advice")
    print("[INFO] 測試端點: http://localhost:5001/api/test\n")
    app.run(debug=True, host='0.0.0.0', port=5001)