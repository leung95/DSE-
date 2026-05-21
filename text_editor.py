"""
富文本编辑器组件
支持：字数统计(2500字限制提示)、颜色、字体大小、标记、备注、
半透明背景覆盖、无限撤回/重做、自由拖放文本
"""

import uuid
from PyQt6.QtWidgets import (
    QTextEdit, QColorDialog, QInputDialog, QMessageBox, QMenu,
    QToolTip
)
from PyQt6.QtGui import (
    QTextCharFormat, QColor, QFont, QAction, QMouseEvent,
    QKeyEvent, QContextMenuEvent
)
from PyQt6.QtCore import Qt, pyqtSignal


class TextEditor(QTextEdit):
    word_count_changed = pyqtSignal(int)
    text_modified = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        # 启用无限撤销/重做（0 表示不限深度）
        self.setUndoRedoEnabled(True)
        self.document().setUndoDepth(0)

        # 拖拽移动文本默认已开启，显式保证
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

        self.notes = {}          # note_id -> note_text
        self.mark_styles = {}    # mark_name -> QTextCharFormat
        self._init_preset_marks()

        self.textChanged.connect(self._on_text_changed)
        self.setPlaceholderText("在此输入作文内容（2500字以内）...")
        self._warned = False

    def _init_preset_marks(self):
        """预设标记样式"""
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 255, 0, 120))
        self.mark_styles["重点"] = fmt

        fmt = QTextCharFormat()
        fmt.setUnderlineColor(QColor(255, 0, 0))
        fmt.setFontUnderline(True)
        self.mark_styles["待修改"] = fmt

        fmt = QTextCharFormat()
        fmt.setBackground(QColor(0, 255, 0, 80))
        self.mark_styles["好词好句"] = fmt

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(0, 0, 255))
        self.mark_styles["批注蓝"] = fmt

    def _on_text_changed(self):
        text = self.toPlainText()
        count = len(text)
        self.word_count_changed.emit(count)
        self.text_modified.emit()
        if count > 2500 and not self._warned:
            self._warned = True
            QMessageBox.warning(
                self, "字数提示",
                f"当前字数已达 {count}，已超过 2500 字建议上限。请适当精简。"
            )
        elif count <= 2500:
            self._warned = False

    # ---------- 格式应用 ----------

    def apply_foreground_color(self, color: QColor = None):
        if color is None:
            color = QColorDialog.getColor(
                QColor("#000000"), self, "选择字体颜色"
            )
        if color.isValid():
            cursor = self.textCursor()
            if not cursor.hasSelection():
                return
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            self.text_modified.emit()

    def apply_font_size(self, size: int = None):
        if size is None:
            val, ok = QInputDialog.getInt(
                self, "字体大小", "请输入字号 (pt):", 12, 6, 72, 1
            )
            if not ok:
                return
            size = val
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        cursor.mergeCharFormat(fmt)
        self.text_modified.emit()

    def apply_background_overlay(self, color: QColor = None):
        """半透明颜色覆盖（支持调节透明度）"""
        if color is None:
            color = QColorDialog.getColor(
                QColor(255, 255, 0, 100), self,
                "选择覆盖颜色（支持透明度调节）",
                QColorDialog.ColorDialogOption.ShowAlphaChannel
            )
        if color.isValid():
            cursor = self.textCursor()
            if not cursor.hasSelection():
                return
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            cursor.mergeCharFormat(fmt)
            self.text_modified.emit()

    def add_note(self, note_text: str = None):
        """为选中文本添加备注（使用 anchor 绑定，可随文本移动）"""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(self, "提示", "请先选中要添加备注的文本")
            return
        if note_text is None:
            note_text, ok = QInputDialog.getMultiLineText(
                self, "添加备注", "请输入备注内容:"
            )
            if not ok or not note_text.strip():
                return

        note_id = f"note_{uuid.uuid4().hex[:8]}"
        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref(f"note:{note_id}")
        # 视觉提示：浅蓝背景 + 下划线
        fmt.setBackground(QColor(173, 216, 230, 100))
        fmt.setUnderlineColor(QColor(0, 100, 200))
        fmt.setFontUnderline(True)
        cursor.mergeCharFormat(fmt)

        self.notes[note_id] = note_text.strip()
        self.text_modified.emit()

    def apply_mark(self, mark_name: str):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        fmt = self.mark_styles.get(mark_name)
        if fmt:
            cursor.mergeCharFormat(fmt)
            self.text_modified.emit()

    def clear_formatting(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        cursor.setCharFormat(fmt)
        self.text_modified.emit()

    # ---------- 交互增强 ----------

    def mouseMoveEvent(self, event: QMouseEvent):
        # 悬停显示备注
        cursor = self.cursorForPosition(event.pos())
        fmt = cursor.charFormat()
        href = fmt.anchorHref()
        if href and href.startswith("note:"):
            note_id = href.split(":", 1)[1]
            note_text = self.notes.get(note_id, "")
            if note_text:
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"📌 备注:\n{note_text}",
                    self
                )
                return
        QToolTip.hideText()
        super().mouseMoveEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)

        undo_action = QAction("撤销 (Ctrl+Z)", self)
        undo_action.triggered.connect(self.undo)
        undo_action.setEnabled(self.isUndoAvailable())
        menu.addAction(undo_action)

        redo_action = QAction("重做 (Ctrl+Y)", self)
        redo_action.triggered.connect(self.redo)
        redo_action.setEnabled(self.isRedoAvailable())
        menu.addAction(redo_action)

        menu.addSeparator()

        cut_action = QAction("剪切", self)
        cut_action.triggered.connect(self.cut)
        menu.addAction(cut_action)

        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)

        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.paste)
        menu.addAction(paste_action)

        menu.addSeparator()

        color_action = QAction("字体颜色...", self)
        color_action.triggered.connect(self.apply_foreground_color)
        menu.addAction(color_action)

        size_action = QAction("字体大小...", self)
        size_action.triggered.connect(self.apply_font_size)
        menu.addAction(size_action)

        overlay_action = QAction("颜色覆盖 (透明度可调)...", self)
        overlay_action.triggered.connect(self.apply_background_overlay)
        menu.addAction(overlay_action)

        note_action = QAction("添加备注...", self)
        note_action.triggered.connect(self.add_note)
        menu.addAction(note_action)

        mark_menu = menu.addMenu("快速标记")
        for name in self.mark_styles.keys():
            a = QAction(name, self)
            a.triggered.connect(lambda checked, n=name: self.apply_mark(n))
            mark_menu.addAction(a)

        clear_action = QAction("清除格式", self)
        clear_action.triggered.connect(self.clear_formatting)
        menu.addAction(clear_action)

        menu.exec(event.globalPos())

    def keyPressEvent(self, event: QKeyEvent):
        # 快捷键支持（与 Qt 原生快捷键并存）
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                self.undo()
                return
            elif event.key() == Qt.Key.Key_Y:
                self.redo()
                return
        super().keyPressEvent(event)

    # ---------- 序列化辅助 ----------

    def get_notes_data(self):
        """导出备注映射，用于保存"""
        return dict(self.notes)

    def set_notes_data(self, data: dict):
        """导入备注映射"""
        self.notes = dict(data) if data else {}

    def clear_notes(self):
        self.notes.clear()
