# 作文小工具

一款基於 Python + PyQt6 的跨平台作文輔助桌面應用，支援 Windows、macOS 與 Linux。

## 功能概覽

### 左側 —— 富文本編輯器
- **2500 字以內** 的文本輸入與字數即時統計（超標標紅提示）
- **自由移動字段**：選中任意文字後，可直接在編輯器內拖曳移動位置
- **字體與顏色**：選中文字後，可透過工具列或右鍵選單修改字體、字號、字體顏色
- **標記（Highlight）**：內建「重點 / 待修改 / 好詞好句 / 批注藍」等快速標記，也可自訂顏色覆蓋
- **備註**：為選中文字添加備註（Anchor 綁定），滑鼠懸停即可查看備註氣泡
- **顏色覆蓋（可調透明度）**：選中文字後使用「顏色覆蓋」，在彈出的 QColorDialog 中調節透明度（Alpha 通道），並在其上繼續編輯文字
- **無限撤銷 / 重做**：`Ctrl+Z` 撤銷、`Ctrl+Y` 重做，撤銷堆疊無深度限制

### 右側 —— 填空框架（方形框架）
- **自由增減框架**：點擊「＋ 添加框架」新增，點擊「×」刪除單個框架，也可「清空框架」
- **自由設定尺寸**：
  - **拖曳調整**：滑鼠按住框架右下角黑色小方塊拖曳，即時改變長寬
  - **精確輸入**：點擊「尺寸」按鈕，輸入像素級寬高
- **邊框顏色**：點擊「顏色」按鈕修改每個框架的線條顏色
- **命名標示**：雙擊或直接修改頂部輸入框，自由命名每個框架
- **文本投放**：在左側編輯器中選中文字，拖曳到右側任意框架內完成填空

### 任務與歷史
- **任務管理**：左側面板可新增、重新命名、刪除任務項目；每個任務獨立儲存文本、框架與備註
- **歷史記錄**：右側「歷史記錄」面板自動記錄建立、刪除、切換、儲存等操作日誌
- **會話恢復**：退出時自動儲存所有任務狀態，下次啟動自動恢復（儲存在使用者目錄下的 `.essay_tool/session.json`）

### 檔案操作
- **儲存 / 匯出**：支援將當前任務或全部任務匯出為 JSON，方便備份或跨裝置遷移
- **匯入**：可將之前匯出的 JSON 任務檔案重新匯入

---

## 安裝與執行

### 1. 安裝依賴

確保已安裝 Python 3.9+，然後執行：

```bash
pip install -r requirements.txt
```

> 唯一依賴為 `PyQt6`，它會自動處理 Windows / macOS / Linux 的跨平台相容性。

### 2. 啟動程式

```bash
python main.py
```

---

## 一鍵打包成執行檔（.exe / .app）

由於 PyInstaller 無法跨平台編譯（在 Windows 上才能打包 .exe，在 macOS 上才能打包 .app），這裡提供 **三種方式** 讓你取得原生執行檔：

### 方式一：本地打包腳本（最簡單）

#### Windows —— 產生 `作文小工具.exe`
1. 確定已安裝 Python 3.9+。
2. 雙擊執行專案內的 **`build_windows.bat`**。
3. 等待完成後，在 `dist\作文小工具.exe` 取得單檔執行檔。

#### macOS —— 產生 `作文小工具.app`
1. 開啟「終端機」，進入專案資料夾。
2. 執行：
   ```bash
   bash build_mac.sh
   ```
3. 等待完成後，在 `dist/作文小工具.app` 取得應用程式 Bundle。
4. 首次開啟若出現「無法驗證開發者」警告，請前往「系統設定 → 隱私權與安全性」允許執行。

#### 跨平台通用腳本
```bash
python build.py
```
腳本會自動偵測作業系統並呼叫對應的 PyInstaller 參數。

### 方式二：GitHub Actions 雲端自動打包（推薦，免費）

如果你已將本專案推送到 **GitHub 儲存庫**，無需本機安裝任何環境即可取得 .exe 與 .app：

1. 將程式碼推送到 GitHub（已包含 `.github/workflows/build.yml`）。
2. 進入儲存庫頁面 → **Actions** → **Build Cross-Platform Executables**。
3. 點選右上角的 **Run workflow** 手動觸發。
4. 等待約 5～10 分鐘後，在該次 workflow 的 **Artifacts** 區塊即可下載：
   - `essay-tool-windows` → 內含 `作文小工具.exe`
   - `essay-tool-macos` → 內含 `作文小工具.app`
   - `essay-tool-linux` → 內含 Linux 執行檔（如有需要）

### 方式三：手動執行 PyInstaller

如果你已熟悉命令列，也可直接手動打包：

```bash
pip install pyinstaller

# Windows（單檔 exe）
python -m PyInstaller --onefile --windowed --name "作文小工具" main.py

# macOS（.app Bundle）
python -m PyInstaller --windowed --name "作文小工具" --osx-bundle-identifier "com.example.essaytool" main.py
```

---

## 快速上手

1. **左邊寫作**：直接打字，字數會即時顯示在下方。
2. **選中改格式**：反白文字 → 右鍵選「字體顏色 / 字號 / 顏色覆蓋 / 添加備註」。
3. **拖曳填空**：左側選中要填入的詞句，**按住滑鼠拖曳**到右側框架內放開。
4. **調整框架**：把滑鼠移到框架右下角黑色小方塊，按住拉動即可改變長寬。
5. **切換任務**：左側「任務列表」可新增多篇作文，各自獨立儲存文字與框架。

---

## 專案結構

```
.
├── main.py                    # 程式入口
├── main_window.py             # 主視窗整合
├── text_editor.py             # 富文本編輯器
├── frame_widgets.py           # 填空框架
├── task_history.py            # 任務管理與歷史記錄
├── build.py                   # 通用打包腳本（自動偵測 OS）
├── build_windows.bat          # Windows 一鍵打包
├── build_mac.sh               # macOS 一鍵打包
├── .github/workflows/build.yml # GitHub Actions 自動打包
├── requirements.txt           # 依賴列表
└── README.md                  # 本說明
```

---

## 注意事項

- 字數統計按 **字元數** 計算（一個漢字 = 1 字），適用於中文作文場景。
- 顏色覆蓋的透明度在調色板彈窗中透過 **Alpha（A）通道** 滑桿調節。
- 框架的尺寸最小值為 60×60 像素，防止過度縮小。
- 會話恢復檔案儲存在使用者主目錄下的 `.essay_tool/session.json`，如需徹底清空可手動刪除該目錄。
- 備註與格式會隨文字一起拖曳移動，實現「自由移動字段」的體驗。
