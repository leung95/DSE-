"""
主窗口：整合文本编辑器、填空框架、任务管理、历史记录
"""

import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QDockWidget, QLabel, QPushButton, QMessageBox,
    QFileDialog, QScrollArea, QSpinBox,
    QFontComboBox, QComboBox, QAction
)
from PyQt6.QtGui import QFont, QKeySequence
from PyQt6.QtCore import Qt

from text_editor import TextEditor
from frame_widgets import FrameCanvas
from task_history import TaskManager, HistoryManager, TaskPanel, HistoryPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("作文小工具")
        self.resize(1500, 950)

        # 核心管理器
        self.task_manager = TaskManager(self)
        self.history_manager = HistoryManager(self)

        # UI 组件
        self.text_editor = TextEditor()
        self.frame_canvas = FrameCanvas()
        self.task_panel = TaskPanel(self.task_manager, self.history_manager)
        self.history_panel = HistoryPanel(self.history_manager)

        self._init_ui()
        self._init_toolbar()
        self._init_menubar()
        self._init_statusbar()
        self._connect_signals()

        # 初始任务
        default_tid = self.task_manager.create_task("示例任务")
        self._load_task_to_ui(default_tid)
        self.history_manager.add_log("启动应用", "已创建默认任务")

    def _init_ui(self):
        # 中央分割器
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：编辑器 + 字数条
        left_wrap = QWidget()
        left_layout = QVBoxLayout(left_wrap)
        left_layout.setContentsMargins(6, 6, 6, 6)

        # 顶部小工具栏（字体选择）
        fmt_bar = QHBoxLayout()
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont())
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        fmt_bar.addWidget(QLabel("字体:"))
        fmt_bar.addWidget(self.font_combo)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(14)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        fmt_bar.addWidget(QLabel("字号:"))
        fmt_bar.addWidget(self.size_spin)
        fmt_bar.addStretch()

        left_layout.addLayout(fmt_bar)
        left_layout.addWidget(self.text_editor, stretch=1)

        self.word_label = QLabel("字数: 0 / 2500")
        self.word_label.setStyleSheet("padding: 4px; font-weight: bold;")
        left_layout.addWidget(self.word_label)

        splitter.addWidget(left_wrap)

        # 右侧：框架画布（放在滚动区）
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_wrap = QWidget()
        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(4, 4, 4, 4)

        # 右侧顶部按钮
        right_btn_bar = QHBoxLayout()
        self.btn_add_frame = QPushButton("＋ 添加框架")
        self.btn_add_frame.setToolTip("在右侧添加一个填空框架")
        self.btn_add_frame.clicked.connect(self._add_new_frame)
        right_btn_bar.addWidget(self.btn_add_frame)

        self.btn_clear_frames = QPushButton("清空框架")
        self.btn_clear_frames.setToolTip("移除右侧所有框架")
        self.btn_clear_frames.clicked.connect(self.frame_canvas.clear_all)
        right_btn_bar.addWidget(self.btn_clear_frames)
        right_btn_bar.addStretch()
        right_layout.addLayout(right_btn_bar)

        right_layout.addWidget(self.frame_canvas, stretch=1)
        right_scroll.setWidget(right_wrap)
        splitter.addWidget(right_scroll)

        splitter.setSizes([900, 500])
        main_layout.addWidget(splitter)

        # Dock：任务列表（左侧停靠）
        self.dock_tasks = QDockWidget("任务列表", self)
        self.dock_tasks.setWidget(self.task_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_tasks)

        # Dock：历史记录（右侧停靠）
        self.dock_history = QDockWidget("历史记录", self)
        self.dock_history.setWidget(self.history_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_history)

    def _init_toolbar(self):
        toolbar = QToolBar("常用工具", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 撤销 / 重做
        act_undo = QAction("↩ 撤销", self)
        act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_undo.triggered.connect(self.text_editor.undo)
        toolbar.addAction(act_undo)

        act_redo = QAction("↪ 重做", self)
        act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        act_redo.triggered.connect(self.text_editor.redo)
        toolbar.addAction(act_redo)

        toolbar.addSeparator()

        # 颜色 / 字号 / 覆盖
        act_color = QAction("A 字体颜色", self)
        act_color.triggered.connect(self.text_editor.apply_foreground_color)
        toolbar.addAction(act_color)

        act_size = QAction("T 字号设定", self)
        act_size.triggered.connect(self.text_editor.apply_font_size)
        toolbar.addAction(act_size)

        act_overlay = QAction("▣ 颜色覆盖", self)
        act_overlay.triggered.connect(self.text_editor.apply_background_overlay)
        toolbar.addAction(act_overlay)

        act_note = QAction("📝 添加备注", self)
        act_note.triggered.connect(self.text_editor.add_note)
        toolbar.addAction(act_note)

        toolbar.addSeparator()

        # 快速标记下拉
        self.mark_combo = QComboBox()
        self.mark_combo.addItem("★ 快速标记...")
        self.mark_combo.addItems(["重点", "待修改", "好词好句", "批注蓝"])
        self.mark_combo.currentIndexChanged.connect(self._on_quick_mark)
        toolbar.addWidget(self.mark_combo)

        toolbar.addSeparator()

        act_clear = QAction("清除格式", self)
        act_clear.triggered.connect(self.text_editor.clear_formatting)
        toolbar.addAction(act_clear)

    def _init_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件 (&F)")
        act_save = QAction("保存当前任务 (&S)", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._save_current_task_to_file)
        file_menu.addAction(act_save)

        act_export = QAction("导出所有任务 (&E)", self)
        act_export.triggered.connect(self._export_all_tasks)
        file_menu.addAction(act_export)

        act_import = QAction("导入任务 (&I)", self)
        act_import.triggered.connect(self._import_tasks)
        file_menu.addAction(act_import)

        file_menu.addSeparator()

        act_exit = QAction("退出 (&Q)", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        edit_menu = menubar.addMenu("编辑 (&E)")
        act_undo = QAction("撤销 (&Z)", self)
        act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_undo.triggered.connect(self.text_editor.undo)
        edit_menu.addAction(act_undo)

        act_redo = QAction("重做 (&Y)", self)
        act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        act_redo.triggered.connect(self.text_editor.redo)
        edit_menu.addAction(act_redo)

        view_menu = menubar.addMenu("视图 (&V)")
        act_toggle_tasks = QAction("显示/隐藏任务列表", self)
        act_toggle_tasks.triggered.connect(
            lambda: self.dock_tasks.setVisible(not self.dock_tasks.isVisible())
        )
        view_menu.addAction(act_toggle_tasks)

        act_toggle_history = QAction("显示/隐藏历史记录", self)
        act_toggle_history.triggered.connect(
            lambda: self.dock_history.setVisible(not self.dock_history.isVisible())
        )
        view_menu.addAction(act_toggle_history)

    def _init_statusbar(self):
        self.statusBar().showMessage("就绪。支持 Ctrl+Z 无限撤销、Ctrl+Y 重做。")

    def _connect_signals(self):
        self.text_editor.word_count_changed.connect(self._update_word_label)
        self.text_editor.text_modified.connect(self._on_editor_modified)
        self.frame_canvas.frame_changed.connect(self._on_frame_modified)

        self.task_panel.switch_task.connect(self._on_switch_task_request)

    def _update_word_label(self, count: int):
        self.word_label.setText(f"字数: {count} / 2500")
        if count > 2500:
            self.word_label.setStyleSheet("color: red; font-weight: bold; padding: 4px;")
        else:
            self.word_label.setStyleSheet("color: black; padding: 4px;")

    def _on_editor_modified(self):
        self._auto_save_current_state()

    def _on_frame_modified(self):
        self._auto_save_current_state()

    def _on_quick_mark(self, index: int):
        if index <= 0:
            return
        mark_name = self.mark_combo.itemText(index)
        self.text_editor.apply_mark(mark_name)
        self.mark_combo.setCurrentIndex(0)

    def _on_font_changed(self, font: QFont):
        cursor = self.text_editor.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        cursor.mergeCharFormat(fmt)

    def _on_size_changed(self, size: int):
        cursor = self.text_editor.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        cursor.mergeCharFormat(fmt)

    def _add_new_frame(self):
        frame = self.frame_canvas.add_frame()
        self.history_manager.add_log("添加框架", frame.frame_name)
        self._auto_save_current_state()

    def _auto_save_current_state(self):
        """在任务对象中保存当前编辑状态（非磁盘）"""
        self.task_manager.save_current_state(
            self.text_editor.toHtml(),
            self.frame_canvas.get_frames_data(),
            self.text_editor.get_notes_data()
        )

    def _on_switch_task_request(self, tid: str):
        if tid == self.task_manager.current_task_id:
            return
        self._auto_save_current_state()
        self._load_task_to_ui(tid)
        task = self.task_manager.get_task(tid)
        title = task.title if task else tid
        self.history_manager.add_log("切换任务", title)

    def _load_task_to_ui(self, tid: str):
        task = self.task_manager.load_task(tid)
        if not task:
            return
        self.text_editor.blockSignals(True)
        self.text_editor.setHtml(task.text_html)
        self.text_editor.set_notes_data(task.notes_data)
        self.text_editor.blockSignals(False)
        self.frame_canvas.set_frames_data(task.frames_data)
        self.task_manager.set_current_task(tid)
        self._update_word_label(len(self.text_editor.toPlainText()))

    # ---------- 文件操作 ----------

    def _save_current_task_to_file(self):
        self._auto_save_current_state()
        task = self.task_manager.get_task(self.task_manager.current_task_id)
        if not task:
            QMessageBox.warning(self, "保存失败", "当前没有任务可保存")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存任务", f"{task.title}.json", "JSON (*.json)"
        )
        if not path:
            return
        data = {
            "title": task.title,
            "created_at": task.created_at,
            "text_html": task.text_html,
            "frames": task.frames_data,
            "notes": task.notes_data,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.history_manager.add_log("保存任务到文件", task.title)
            self.statusBar().showMessage(f"已保存: {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "保存错误", str(e))

    def _export_all_tasks(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出所有任务", "all_tasks.json", "JSON (*.json)"
        )
        if not path:
            return
        all_data = []
        for t in self.task_manager.get_all_tasks():
            all_data.append({
                "title": t.title,
                "created_at": t.created_at,
                "text_html": t.text_html,
                "frames": t.frames_data,
                "notes": t.notes_data,
            })
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            self.history_manager.add_log("导出所有任务", f"共 {len(all_data)} 个")
            self.statusBar().showMessage(f"已导出: {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "导出错误", str(e))

    def _import_tasks(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入任务", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "导入错误", str(e))
            return

        imported = 0
        if isinstance(data, list):
            for item in data:
                self._import_single_task(item)
                imported += 1
        elif isinstance(data, dict):
            self._import_single_task(data)
            imported += 1
        else:
            QMessageBox.warning(self, "格式错误", "文件内容格式无法识别")
            return

        self.history_manager.add_log("导入任务", f"共 {imported} 个")
        self.task_panel._refresh_list()
        current = self.task_manager.current_task_id
        if current:
            self._load_task_to_ui(current)
        QMessageBox.information(self, "导入完成", f"成功导入 {imported} 个任务")

    def _import_single_task(self, item: dict):
        title = item.get("title", "导入任务")
        tid = self.task_manager.create_task(title)
        task = self.task_manager.get_task(tid)
        if task:
            task.text_html = item.get("text_html", "")
            task.frames_data = item.get("frames", [])
            task.notes_data = item.get("notes", {})
        # 最后导入的设为当前任务，但不触发切换信号，由外部统一刷新 UI
        self.task_manager.set_current_id_silent(tid)

    def closeEvent(self, event):
        # 退出前保存当前状态到任务对象（如果需要持久化到本地文件可在此扩展）
        self._auto_save_current_state()
        # 保存自动恢复文件
        self._save_session()
        event.accept()

    def _save_session(self):
        """保存会话到本地 AppData，下次可恢复（简易实现）"""
        try:
            session = []
            for t in self.task_manager.get_all_tasks():
                session.append({
                    "title": t.title,
                    "created_at": t.created_at,
                    "text_html": t.text_html,
                    "frames": t.frames_data,
                    "notes": t.notes_data,
                })
            save_dir = Path.home() / ".essay_tool"
            save_dir.mkdir(exist_ok=True)
            path = save_dir / "session.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_session(self):
        """启动时尝试恢复上次会话"""
        try:
            path = Path.home() / ".essay_tool" / "session.json"
            if not path.exists():
                return
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list) or not data:
                return
            # 清空默认任务，加载存档
            first = True
            for item in data:
                if first:
                    # 替换默认任务
                    default_tid = self.task_manager.current_task_id
                    task = self.task_manager.get_task(default_tid)
                    if task and default_tid:
                        task.title = item.get("title", "恢复任务")
                        task.text_html = item.get("text_html", "")
                        task.frames_data = item.get("frames", [])
                        task.notes_data = item.get("notes", {})
                        first = False
                        continue
                self._import_single_task(item)
            if not first:
                self._load_task_to_ui(self.task_manager.current_task_id)
                self.history_manager.add_log("恢复会话", f"加载 {len(data)} 个任务")
        except Exception:
            pass
