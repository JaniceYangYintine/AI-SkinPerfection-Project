@echo off
chcp 65001 >nul
echo ========================================
echo   啟動健康建議系統
echo ========================================
echo.

REM 檢查並清理 Port 5000
echo [檢查] 正在檢查 Port 5000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo [警告] Port 5000 被佔用,正在清理 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

REM 檢查並清理 Port 8080
echo [檢查] 正在檢查 Port 8080...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo [警告] Port 8080 被佔用,正在清理 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo [完成] Port 檢查完成
echo.

echo [1/2] 啟動後端 API (Port 5000)...
start "後端 API" cmd /k "chcp 65001 >nul && python api.py"
timeout /t 3 /nobreak >nul

echo [2/2] 啟動前端伺服器 (Port 8080)...
start "前端伺服器" cmd /k "chcp 65001 >nul && python frontend_server.py"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   系統啟動完成！
echo ========================================
echo.
echo 後端 API:     http://localhost:5000
echo 前端頁面:     http://localhost:8080
echo.
echo 請在瀏覽器開啟: http://localhost:8080
echo.
echo 提示: 如果仍然出現 Port 佔用錯誤,
echo       請執行 cleanup_ports.bat 進行完整清理
echo.
echo 按任意鍵關閉此視窗...
pause >nul
