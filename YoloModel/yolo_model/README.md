圖片測試指令(開啟app.py後在新的終端機執行)
curl -X POST http://localhost:8000/predict -F "file=@face_test.jpg"



直接用yolo辨識(要在python環境裡面)
yolo detect predict model=best.pt source=face_test.jpg

(整個資料夾)
yolo detect predict model=best.pt source=images/


到時候再資料夾裡放model(要打名字)

執行pip
pip install -r requirements.txt
