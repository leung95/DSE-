#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用打包脚本：根据当前平台自动调用 PyInstaller 打包。

- Windows : 生成單檔 .exe
- macOS   : 生成 .app Bundle
- Linux   : 生成單檔可執行檔

用法:
    python build.py
"""
import sys
import subprocess
import platform


def main():
    system = platform.system()
    # 基礎指令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--windowed",
        "--clean",
        "--name", "作文小工具",
        "main.py"
    ]

    if system == "Windows":
        # Windows 用單檔 exe 方便分發
        cmd.insert(4, "--onefile")
        print("[INFO] 偵測到 Windows，開始打包單檔 .exe …")
    elif system == "Darwin":
        print("[INFO] 偵測到 macOS，開始打包 .app Bundle …")
        # macOS 加上 --osx-bundle-identifier 避免簽名警告（可選）
        cmd.extend(["--osx-bundle-identifier", "com.example.essaytool"])
    else:
        cmd.insert(4, "--onefile")
        print(f"[INFO] 偵測到 {system}，開始打包單檔可執行檔 …")

    print("[CMD] ", " ".join(cmd))
    subprocess.run(cmd, check=True)

    print("\n[SUCCESS] 打包完成！請查看 dist/ 目錄。")
    if system == "Windows":
        print("          輸出檔案: dist\\作文小工具.exe")
    elif system == "Darwin":
        print("          輸出檔案: dist/作文小工具.app")
    else:
        print("          輸出檔案: dist/作文小工具")


if __name__ == "__main__":
    main()
