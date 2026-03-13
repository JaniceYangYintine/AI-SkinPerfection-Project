from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
import cv2
import numpy as np
import os
import uuid
from fastapi.responses import FileResponse # 用於測試時直接查看圖片

app = FastAPI()

# 載入你的模型
model = YOLO("best.pt")

# 建立一個存放結果圖片的暫存資料夾
RESULT_DIR = "test_images"
os.makedirs(RESULT_DIR, exist_ok=True)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # 1. 讀取上傳的圖片內容
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 將門檻調低到 0.1，讓更多疑似物體被標註出來
    results = model(img, conf=0.4)
    # print(f"偵測到的物體數量: {len(results[0].boxes)}") # 在終端機看有沒有抓到東西
    # # 3. 取得繪製後的圖片 (帶有框線與標籤)
    # results[0].plot() 會回傳一個畫好框的 BGR 圖片 (numpy array)
    annotated_frame = results[0].plot()

    # 4. 存檔到本地 (為了讓 n8n 讀取並上傳到 GCS)
    # 使用 uuid 確保檔名不重複
    file_name = f"{uuid.uuid4()}.jpg"
    # 取得這台電腦的絕對路徑
    abs_result_dir = os.path.abspath(RESULT_DIR) 
    file_path = os.path.join(abs_result_dir, file_name)
    cv2.imwrite(file_path, annotated_frame)

    # 5. 整理偵測數據 (保留你原本需要的 JSON 資訊)
    r = results[0]
    names = model.names
    detections = []
    for box in r.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        detections.append({
            "label": names[cls],
            "confidence": conf
        })

    # 6. 回傳結果
    # 我們回傳 file_path，這樣 n8n 才知道要去哪裡抓這張畫好的圖
    return {
        "count": len(detections),
        "detections": detections,
        "image_path": file_path, # 讓 n8n 知道檔案在哪
        "file_name": file_name
    }

# 可選：新增一個路徑讓瀏覽器可以直接看圖 (測試用)
@app.get("/get-image/{file_name}")
async def get_image(file_name: str):
    path = os.path.join(RESULT_DIR, file_name)
    return FileResponse(path)


if __name__ == "__main__":
    import uvicorn
    # 遠端執行時 host 設為 0.0.0.0 以便外部連線
    uvicorn.run(app, host="localhost", port=8000)