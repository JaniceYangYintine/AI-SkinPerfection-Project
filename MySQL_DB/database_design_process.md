
### 靜態資料表（4 個）

| #   | 資料表名稱                 | 主要欄位                                                                                                                                                                                                                                                      | 資料來源          |
| --- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 1   | `ingredients`         | ingredient_id, ingredient_name_zh, ingredient_name_en, spot_primary, spot_support, wrinkle_primary, wrinkle_support, pore_primary, pore_support, acne_primary, acne_support, comedone_primary, comedone_support, dark_circle_primary, dark_circle_support | 手動整理          |
| 2   | `products`            | product_id, brand, price_tier, category, name, price, description, ingredients, concerns, <br>skintypes, sensitivity, anti-aging, moisturizing, product_url, image_url, crawled_at                                                                        | 爬蟲 + 手動標註     |
| 3   | `product_ingredients` | relation_id, ingredient_id, ingredient_name_zh, product_id, category, name, created_at                                                                                                                                                                    | 爬蟲 + 文字提取     |
| 4   | `actions`             | action_id, action_name, description, target_issues, gif_url, category                                                                                                                                                                                     | 手動整理 + GIF 製作 |
### 動態資料表 - 儲存使用者記錄

| #   | 資料表名稱                         | 主要欄位                                                                                                                                                                                        | 何時寫入     |
| --- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 5   | `users`                       | user_id, line_user_id, created_at, last_session_at                                                                                                                                          | 使用者首次加入  |
| 6   | `sessions`                    | session_id, user_id, photoload_at, updated_at, original_photo_url, analyzed_photo_url, <br>status                                                                                           | 每次分析開始   |
| 7   | `questionnaire_answers_tags`  | answer_id, session_id  <br>answer1_tag, answer2_tag, answer3_tag, answer4_tag, answer5_tag, answer6_tag, answer7_tag, answer8_tag, answer9_tag, questionnaire_version                       | 填問卷時     |
| 8   | `session_llm_analysis`        | session_id, a_score,  a_complexion_issues, a_complexion_text, a_massage_action,  c_lifestyle_advice                                                                                         | AI 分析完成後 |
| 9   | `session_skin_scores`         | session_id, acne_score, comedone_score, wrinkle_score, spot_score, pore_score, dark_circle_score, top_1_issues, top_2_issues, llm_1_text, llm_2_text                                        |          |
| 10  | `session_recommendations` 待處理 | recommendation_id, session_id, <br>issue_1_recommendation, issue_2_recommendation, product_1, product_2, product_3, product_4, product_5, product_6                                         | 推薦系統執行後  |
| 11  | `ga_events`                   | event_id, session_id  <br>overview_duration, section_a_duration, section_b_duration, section_c_duration, section_d_duration, clicked_products, products_click_count, exit_method, exit_time | 使用者互動時   |

```
使用者加入LINE Bot

1. 使用者點擊 LINE Bot 連結
2. 後端接收 LINE User ID
3. 查詢 users 表
4. 判斷：
	- 如果不存在 → 新增使用者
	- 如果存在 → 繼續下一步
	  
✅users（查詢 + 可能新增）
```

```
檢查 30 天內是否分析過

5. 讀取使用者的最後分析時間
6. 判斷：
	- 如果 last_session_at 是 NULL → 首次使用，顯示問卷
	- 如果 last_session_at < 30 天前 → 顯示問卷
	- 如果 last_session_at ≥ 30 天內 → 顯示問卷+跳過問卷按鈕

✅users（查詢 last_session_at）
```

```
拍照

7. 使用者拍照
8. 前端上傳照片（Base64）
9. 後端接收照片
	- 上傳到 Google Cloud Storage (GCS)
	- 取得 original_photo_url
10. 建立新的 session 紀錄
    → 紀錄 original_photo_url
	→ 取得 session_id

✅sessions（新增）
```

```
填問卷（如需要）

11. 顯示問卷（9 題，題目在 config/questionnaires.json）
12. 使用者填寫答案
13. 儲存問卷答案（9 筆記錄）

✅ questionnaire_answers_tags（新增 9 筆）
```

```
AI 分析 - A 區（氣色）

14. 從 sessions 表讀取 original_photo_url
15. 呼叫 LLM 分析氣色
	→ 偵測氣色問題：["臉色蒼白", "眼睛疲勞"]
	→ 生成詳細分析文字
	→ 給分數：7 分
16. 查詢對應的按摩動作
17. 儲存 A 區結果
    → a_score
	→ a_complexion_issues
	→ a_complexion_text
	→ a_massage_action

✅ sessions（讀取 original_photo_url）
✅ massage_actions（查詢）
✅ session_llm_analysis（新增，寫入 A 區欄位）
```

```
AI 分析 - B 區（膚況）

18. 讀取原始照片
19. YOLO 分析膚況
	→ 6 種分數（痘痘 8 分、黑眼圈 7 分、粉刺 5 分...）
	→ 挑出最嚴重的兩個：["acne", "dark_circle"]
	→ 產生遮罩圖（有框線、標記）
	→ LLM 生成文字說明
20. 上傳遮罩圖到 GCS
	→ 取得 analyzed_photo_url
21. 更新 sessions 表
22. 新增 session_skin_scores 表
	→ acne_score, comedone_score, wrinkle_score, spot_score, pore_score, dark_circle_score
	→ top_two_issues
	→ llm_text

✅ sessions（讀取 original_photo_url，更新 analyzed_photo_url）
✅ session_skin_scores（新增 B 區欄位）
```

```
AI 分析 - C 區（生活建議）

23. 讀取問卷答案
24. 組合成 Prompt + LLM 生成飲食建議
	→ 生成建議文字
25. 更新 session_llm_analysis 表
	→ c_lifestyle_advice

✅ questionnaire_answers_tags（讀取）
✅ session_llm_analysis（更新 C 區欄位）
```

```
推薦系統 - D 區（成分 + 產品）

步驟 1：推薦成分
26. 讀取最嚴重的兩個膚況問題
	→ 結果：["acne", "dark_circle"]
27. 查詢推薦成分
	→ 針對痘痘：["水楊酸", "茶樹精油"]
	→ 針對黑眼圈：["咖啡因", "維他命K"]
28. 組合成推薦文字
	→ issue_1_recommendation = "針對您的痘痘問題，推薦成分：水楊酸、茶樹精油"
	→ issue_2_recommendation = "針對您的黑眼圈問題，推薦成分：咖啡因、維他命K"

步驟 2：推薦產品
29. 【第1層】成分匹配（必須）
	查詢含有推薦成分的產品
	→ 假設結果：50 個產品
30. 【第2層】讀取問卷答案
	→ sensitivity = "medium"
	→ skin_condition = "oily"
	→ age_band = "20_30"
31. 【第3層】敏感肌篩選（必須）
	如果 sensitivity IN ('high', 'medium'):
	只保留有標記 sensitivity 的產品
	→ 假設結果：30 個產品
32. 【第4層】膚質篩選（必須）
	WHERE skintypes LIKE '%oily%'
	→ 假設結果：18 個產品
33. 【第5層】抗老篩選
	如果 age_band IN ('30_40', '40p') OR 'wrinkle' IN top_two_issues:
	優先推薦有「抗老」標籤的產品
	→ 假設結果：18 個產品（年齡 20_30，不篩選）
34. 【第6層】分開架/專櫃，各取 3 個
	開架產品：
	SELECT * FROM ... WHERE price_tier = 'drugstore' LIMIT 3
	→ 假設結果：3 個
	專櫃產品：
	SELECT * FROM ... WHERE price_tier = 'counter' LIMIT 3
	→ 假設結果：3 個
	如果某個價格帶不足 3 個：
	→ 從另一個價格帶補足
35. 【第7層】如果產品還是太多（超過 6 個可選）
	在各價格帶內，優先選有「保濕」標籤的產品
	開架產品（如果 > 3 個）：
	SELECT * FROM ...
	WHERE price_tier = 'drugstore'
	ORDER BY (CASE WHEN 加分條件 LIKE '%保濕%' THEN 1 ELSE 0 END) DESC
	LIMIT 3
	專櫃產品（如果 > 3 個）：
	SELECT * FROM ...
	WHERE price_tier = 'counter'
	ORDER BY (CASE WHEN 加分條件 LIKE '%保濕%' THEN 1 ELSE 0 END) DESC
	LIMIT 3
36. 儲存推薦到 session_recommendations
	→ product_1, product_2, product_3（開架）
	→ product_4, product_5, product_6（專櫃）

✅ analysis_results（讀取 top_two_issues）
✅ ingredients（查詢推薦成分）
✅ product_ingredients（查詢產品-成分關聯）
✅ products（查詢產品）
✅ questionnaire_answers_tags（讀取 sensitivity, skin_condition, age_band）
✅ session_recommendations（新增）
```

```
完成分析

37. 更新 session 狀態
	→ status = 'completed'
	⭐加入錯誤代碼⭐
38. 更新使用者最後分析時間(僅成功時間)
	→ last_session_at = NOW()
39. 回傳結果到 LINE（使用 BUBBLE）
	- A 區：氣色分析 + 按摩 GIF
	- B 區：膚況分數 + 遮罩圖
	- C 區：生活建議
	- D 區：成分推薦 + 產品推薦

✅ sessions（更新 status）
✅ users（更新 last_session_at）
```
 **錯誤代碼定義**

| 錯誤代碼             | 說明        | 使用者訊息         |
| ---------------- | --------- | ------------- |
| AI_TIMEOUT       | AI 模型處理超時 | 系統繁忙中，請稍後再試   |
| YOLO_ERROR       | YOLO 模型錯誤 | 分析失敗，請重新拍照    |
| LLM_ERROR        | LLM 服務錯誤  | AI 分析服務暫時無法使用 |
| PHOTO_INVALID    | 照片無效      | 照片品質不佳，請重新拍照  |
| PHOTO_TOO_DARK   | 照片過暗      | 請在光線充足的地方重新拍照 |
| NO_FACE_DETECTED | 未偵測到臉部    | 請確保臉部清晰可見     |
| STORAGE_ERROR    | 儲存失敗      | 系統錯誤，請稍後再試    |
| UNKNOWN_ERROR    | 未知錯誤      | 系統錯誤，請稍後再試    |

```
使用者互動（GA4 追蹤）
40. 使用者瀏覽各區域
	- 總覽頁停留 5 秒
	- A 區停留 8 秒
	- B 區停留 10 秒
	- C 區停留 6 秒
	- D 區停留 15 秒
	- 點擊產品：2 個
	- 點擊「返回 LINE」
41. 記錄 GA4 事件到 ga_events
	→ overview_duration, section_a_duration, section_b_duration, section_c_duration, section_d_duration
	→ clicked_products, products_click_count
	→ exit_method, exit_time
	
✅ ga_events（新增）
```


設計資料庫時，我比較過三種做法：
- 字串：最簡單，但結構性差，後續查詢、治理成本高
- JSON：彈性高，結構保留，適合資料仍在變動
- 結構化：最可控、最利於查詢與治理，但前期設計成本高

沒有拆成更多張表，是因為欄位尚不穩定，為了保留彈性並加快調整，先用 JSON 存放。  
選 JSON 而不是字串，是因為它仍有結構可用，MySQL 也支援 JSON 函式與虛擬欄位索引，未來更容易轉成結構化。

後續我會導入 Slow Query Log，觀察實際慢查詢，以此決定何時調整 schema 或補索引。

---
 `ga_events` 資料更新機制

即時更新（Real-time）
- **做法**：使用者每次互動（點擊產品、切換區塊）都立即寫入資料庫
- **優點**：資料即時、不會遺失
- **缺點**：資料庫寫入次數多、效能負擔較大

批次更新（Batch）
- **做法**：在使用者離開報告頁面時，一次性寫入所有互動資料
- **優點**：減少資料庫寫入次數、效能較好
- **缺點**：如果使用者異常離開（關閉瀏覽器），資料可能遺失

✅混合模式
- **做法**：前端先暫存互動資料，每 30 秒或離開時批次寫入
- **優點**：平衡效能和資料完整性