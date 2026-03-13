@echo off
chcp 65001 >nul
echo ========================================
echo   清理佔用的 Port
echo ========================================
echo.

echo [檢查] 正在檢查 Port 5000, 5001, 9000 的佔用狀況...
echo.

REM 檢查 Port 5000 (C_LLM)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo [發現] Port 5000 被 PID %%a 佔用
    echo [清理] 正在終止 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! == 0 (
        echo [成功] 已終止 PID %%a
    ) else (
        echo [失敗] 無法終止 PID %%a
    )
)

REM 檢查 Port 5001 (A_LLM)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001" ^| findstr "LISTENING"') do (
    echo [發現] Port 5001 被 PID %%a 佔用
    echo [清理] 正在終止 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! == 0 (
        echo [成功] 已終止 PID %%a
    ) else (
        echo [失敗] 無法終止 PID %%a
    )
)

REM 檢查 Port 9000 (統一前端)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9000" ^| findstr "LISTENING"') do (
    echo [發現] Port 9000 被 PID %%a 佔用
    echo [清理] 正在終止 PID %%a...
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! == 0 (
        echo [成功] 已終止 PID %%a
    ) else (
        echo [失敗] 無法終止 PID %%a
    )
)

echo.
echo ========================================
echo   清理完成！
echo ========================================
echo.
echo 現在可以執行 start.bat 啟動系統
echo.
pause
