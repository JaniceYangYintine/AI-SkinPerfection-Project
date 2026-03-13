@echo off
chcp 65001 >nul
echo ========================================
echo   啟動雙 LLM 健康建議系統
echo ========================================
echo.

REM 檢查並清理 Port 5000 (C_LLM)
echo [檢查] 正在檢查 Port 5000 (C_LLM)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo [警告] Port 5000 被佔用,正在清理 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

REM 檢查並清理 Port 5001 (A_LLM)
echo [檢查] 正在檢查 Port 5001 (A_LLM)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001" ^| findstr "LISTENING"') do (
    echo [警告] Port 5001 被佔用,正在清理 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

REM 檢查並清理 Port 9000 (統一前端)
echo [檢查] 正在檢查 Port 9000 (統一前端)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9000" ^| findstr "LISTENING"') do (
    echo [警告] Port 9000 被佔用,正在清理 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo [完成] Port 檢查完成
echo.

echo [1/3] 啟動 A_LLM 後端 (Port 5001)...
start "A_LLM 後端" cmd /k "chcp 65001 >nul && cd A_LLM && python api.py"
timeout /t 2 /nobreak >nul

echo [2/3] 啟動 C_LLM 後端 (Port 5000)...
start "C_LLM 後端" cmd /k "chcp 65001 >nul && cd C_LLM && python api.py"
timeout /t 2 /nobreak >nul

echo [3/3] 啟動統一前端伺服器 (Port 9000)...
start "統一前端" cmd /k "chcp 65001 >nul && python frontend_server.py"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   系統啟動完成！
echo ========================================
echo.
echo A_LLM 後端:   http://localhost:5001
echo C_LLM 後端:   http://localhost:5000
echo 統一前端:     http://localhost:9000
echo.
echo 請在瀏覽器開啟: http://localhost:9000
echo.
echo 提示: 如果仍然出現 Port 佔用錯誤,
echo       請執行 cleanup_ports.bat 進行完整清理
echo.
echo 按任意鍵關閉此視窗...
pause >nul
