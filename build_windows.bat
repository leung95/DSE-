@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo   作文小工具 - Windows 打包腳本
echo ==========================================
echo.

REM 檢查 Python
echo [1/3] 檢查 Python 環境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未偵測到 Python，請先安裝 Python 3.9+！
    pause
    exit /b 1
)

REM 安裝依賴與 PyInstaller
echo [2/3] 安裝 PyInstaller 與依賴...
python -m pip install -r requirements.txt pyinstaller

REM 打包單檔 EXE
echo [3/3] 開始打包 .exe（單檔模式）...
python -m PyInstaller --onefile --windowed --clean --name "作文小工具" main.py

echo.
echo ==========================================
echo   打包完成！
echo ==========================================
echo 輸出位置: dist\作文小工具.exe
echo.
pause
endlocal
