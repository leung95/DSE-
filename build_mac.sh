#!/bin/bash
# ==========================================
#  作文小工具 - macOS 打包腳本
#  輸出: dist/作文小工具.app
# ==========================================

set -e

echo "=========================================="
echo "  作文小工具 - macOS 打包腳本"
echo "=========================================="
echo ""

# 檢查 Python
echo "[1/3] 檢查 Python 環境..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] 未偵測到 python3，請先安裝 Python 3.9+！"
    exit 1
fi
python3 --version

# 安裝依賴與 PyInstaller
echo ""
echo "[2/3] 安裝 PyInstaller 與依賴..."
pip3 install -r requirements.txt pyinstaller

# 打包 .app Bundle
echo ""
echo "[3/3] 開始打包 .app Bundle..."
python3 -m PyInstaller \
    --windowed \
    --clean \
    --name "作文小工具" \
    --osx-bundle-identifier "com.example.essaytool" \
    main.py

echo ""
echo "=========================================="
echo "  打包完成！"
echo "=========================================="
echo "輸出位置: dist/作文小工具.app"
echo ""
echo "提示: 若無法開啟，請前往『系統偏好設定 → 安全性與隱私』允許執行。"
