"""
簡易 HTTP 伺服器 - 用於提供前端頁面
解決 CORS 跨域問題
"""
import http.server
import socketserver
import os
import sys

# 設定 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 設定端口
PORT = 8081

# 切換到當前目錄
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 建立伺服器
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"\n🌐 前端伺服器已啟動！")
    print(f"📍 請在瀏覽器開啟: http://localhost:{PORT}")
    print(f"📄 主頁面: http://localhost:{PORT}/index.html")
    print(f"\n⚠️  請確保後端 API 也在運行 (python api.py)")
    print(f"按 Ctrl+C 停止伺服器\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 伺服器已停止")
