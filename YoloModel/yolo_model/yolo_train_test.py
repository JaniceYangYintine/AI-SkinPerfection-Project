from ultralytics import YOLO

# 1. 初始化模型
model = YOLO('yolo11n.pt') 

# 2. 開始訓練(以下train可以用AI給範例)
model.train(
    data='data.yaml',   # 指向你的 yaml 檔案路徑
    # 在data.yaml改(有範例)
    epochs=100,              # 訓練 100 輪
    imgsz=640,               # 如果顯存夠 (12G以上)，建議調到 1024 偵測毛孔更準
    batch=16,                # 批次大小
    patience=20,             # 早停機制
    optimizer='AdamW',         # 醫療影像偵測有時 SGD 比 AdamW 更穩定
    lr0=0.01,                # 初始學習率
    augment=True,            # 開啟數據增強（旋轉、縮放、亮度變換）
    # 針對小目標（粉刺、毛孔）優化損失權重
    box=7.5,                 # 提高座標框的損失權重，讓 ROI 更精準
    cls=0.5,                 # 分類損失
    dfl=1.5                  # 分佈聚焦損失
)