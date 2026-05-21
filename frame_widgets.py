"""
填空框架组件
支持：自由增减方形框架、拖动/输入调整大小、线条颜色编辑、
命名标示编辑、接收左侧拖拽文本
"""

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QColorDialog, QInputDialog, QScrollArea
)
from PyQt6.QtGui import QColor, QPainter, QMouseEvent, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, pyqtSignal, QSize


class FrameItem(QFrame):
    """单个填空框架"""
    text_dropped = pyqtSignal(str, str, str)  # frame_id, frame_name, text
    delete_requested = pyqtSignal(str)        # frame_id
    size_changed = pyqtSignal(str, int, int)  # frame_id, w, h

    def __init__(self, frame_id: str, name: str = "填空框",
                 width: int = 200, height: int = 150,
                 line_color: str = "#333333", parent=None):
        super().__init__(parent)
        self.frame_id = frame_id
        self.frame_name = name
        self.line_color = QColor(line_color)
        self._content_text = ""

        self._resizing = False
        self._resize_start_pos = None
        self._resize_start_size = None

        self.setAcceptDrops(True)
        self.setMinimumSize(60, 60)
        self.setFixedSize(width, height)
        self._init_ui()
        self._update_border()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        # 标题栏
        header = QHBoxLayout()
        header.setSpacing(2)

        self.name_edit = QLineEdit(self.frame_name)
        self.name_edit.setMaxLength(30)
        self.name_edit.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        self.name_edit.editingFinished.connect(self._on_name_changed)
        header.addWidget(self.name_edit, stretch=1)

        self.btn_color = QPushButton("颜色")
        self.btn_color.setFixedSize(36, 22)
        self.btn_color.setStyleSheet("font-size: 10px;")
        self.btn_color.setToolTip("编辑边框颜色")
        self.btn_color.clicked.connect(self._change_color)
        header.addWidget(self.btn_color)

        self.btn_size = QPushButton("尺寸")
        self.btn_size.setFixedSize(36, 22)
        self.btn_size.setStyleSheet("font-size: 10px;")
        self.btn_size.setToolTip("输入精确宽高")
        self.btn_size.clicked.connect(self._edit_size_dialog)
        header.addWidget(self.btn_size)

        self.btn_del = QPushButton("×")
        self.btn_del.setFixedSize(22, 22)
        self.btn_del.setStyleSheet("font-size: 12px; color: red;")
        self.btn_del.setToolTip("删除此框架")
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.frame_id))
        header.addWidget(self.btn_del)

        main_layout.addLayout(header)

        # 内容区（接收投放）
        self.content_label = QLabel("拖拽文本到此处")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.content_label.setStyleSheet(
            "background-color: #fafafa; border: 1px dashed #cccccc; padding: 6px;"
        )
        main_layout.addWidget(self.content_label, stretch=1)

        # 尺寸提示
        self.size_label = QLabel(f"{self.width()} × {self.height()}")
        self.size_label.setStyleSheet("color: #888; font-size: 10px;")
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.size_label)

    def _update_border(self):
        c = self.line_color.name()
        self.setStyleSheet(
            f"FrameItem {{"
            f"  border: 2px solid {c};"
            f"  border-radius: 4px;"
            f"  background: #ffffff;"
            f"}}"
        )

    def _on_name_changed(self):
        self.frame_name = self.name_edit.text().strip() or "填空框"

    def _change_color(self):
        color = QColorDialog.getColor(self.line_color, self, "选择边框颜色")
        if color.isValid():
            self.line_color = color
            self._update_border()

    def _edit_size_dialog(self):
        w, ok1 = QInputDialog.getInt(self, "设定宽度", "宽度 (px):", self.width(), 40, 1200, 10)
        if not ok1:
            return
        h, ok2 = QInputDialog.getInt(self, "设定高度", "高度 (px):", self.height(), 40, 800, 10)
        if ok2:
            self.setFixedSize(w, h)
            self.size_label.setText(f"{w} × {h}")
            self.size_changed.emit(self.frame_id, w, h)

    # ---------- 鼠标拖动调整大小 ----------

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if (event.pos().x() > self.width() - 15 and
                event.pos().y() > self.height() - 15):
                self._resizing = True
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_size = QSize(self.width(), self.height())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resizing:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_w = max(60, self._resize_start_size.width() + delta.x())
            new_h = max(60, self._resize_start_size.height() + delta.y())
            self.setFixedSize(new_w, new_h)
            self.size_label.setText(f"{new_w} × {new_h}")
            self.size_changed.emit(self.frame_id, new_w, new_h)
            event.accept()
            return

        # 鼠标在右下角时改变光标
        if (event.pos().x() > self.width() - 15 and
            event.pos().y() > self.height() - 15):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._resizing:
            self._resizing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        # 绘制右下角 resize handle
        with QPainter(self) as painter:
            painter.setPen(self.line_color)
            painter.setBrush(self.line_color)
            painter.drawRect(self.width() - 10, self.height() - 10, 8, 8)

    # ---------- 拖放接收 ----------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() or event.mimeData().hasHtml():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        text = event.mimeData().text()
        if not text:
            text = event.mimeData().html()
        self._content_text = text
        self.content_label.setText(text)
        self.content_label.setStyleSheet(
            "background-color: #eef7ff; border: 1px solid #aaccee; padding: 6px;"
        )
        self.text_dropped.emit(self.frame_id, self.frame_name, text)
        event.acceptProposedAction()

    # ---------- 序列化 ----------

    def to_dict(self):
        return {
            "id": self.frame_id,
            "name": self.frame_name,
            "width": self.width(),
            "height": self.height(),
            "line_color": self.line_color.name(),
            "content": self._content_text,
        }

    def from_dict(self, data: dict):
        self.frame_id = data.get("id", self.frame_id)
        self.frame_name = data.get("name", "填空框")
        self.name_edit.setText(self.frame_name)
        w = data.get("width", 200)
        h = data.get("height", 150)
        self.setFixedSize(w, h)
        self.size_label.setText(f"{w} × {h}")
        self.line_color = QColor(data.get("line_color", "#333333"))
        self._update_border()
        self._content_text = data.get("content", "")
        self.content_label.setText(self._content_text if self._content_text else "拖拽文本到此处")
        if self._content_text:
            self.content_label.setStyleSheet(
                "background-color: #eef7ff; border: 1px solid #aaccee; padding: 6px;"
            )
        else:
            self.content_label.setStyleSheet(
                "background-color: #fafafa; border: 1px dashed #cccccc; padding: 6px;"
            )


class FrameCanvas(QWidget):
    """框架画布：管理多个填空框架"""
    frame_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setSpacing(10)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._frames = {}
        self._counter = 0

    def add_frame(self, name: str = None, width: int = 200, height: int = 150,
                  line_color: str = "#333333", content: str = "") -> FrameItem:
        self._counter += 1
        fid = f"frame_{self._counter}"
        frame = FrameItem(fid, name or f"框架{self._counter}", width, height, line_color)
        frame.delete_requested.connect(self.remove_frame)
        frame.text_dropped.connect(self._on_text_dropped)
        self._layout.addWidget(frame)
        self._frames[fid] = frame
        if content:
            frame._content_text = content
            frame.content_label.setText(content)
            frame.content_label.setStyleSheet(
                "background-color: #eef7ff; border: 1px solid #aaccee; padding: 6px;"
            )
        self.frame_changed.emit()
        return frame

    def remove_frame(self, fid: str):
        frame = self._frames.pop(fid, None)
        if frame:
            self._layout.removeWidget(frame)
            frame.deleteLater()
            self.frame_changed.emit()

    def clear_all(self):
        for frame in list(self._frames.values()):
            self._layout.removeWidget(frame)
            frame.deleteLater()
        self._frames.clear()
        self._counter = 0
        self.frame_changed.emit()

    def _on_text_dropped(self, fid: str, name: str, text: str):
        # 内部信号转发，外部可通过 frame_changed 感知
        self.frame_changed.emit()

    def get_frames_data(self) -> list:
        return [f.to_dict() for f in self._frames.values()]

    def set_frames_data(self, data: list):
        self.clear_all()
        for item in data:
            self._counter += 1
            fid = item.get("id", f"frame_{self._counter}")
            frame = FrameItem(fid, item.get("name", "填空框"),
                              item.get("width", 200), item.get("height", 150),
                              item.get("line_color", "#333333"))
            frame.delete_requested.connect(self.remove_frame)
            frame.text_dropped.connect(self._on_text_dropped)
            self._layout.addWidget(frame)
            self._frames[fid] = frame
            frame.from_dict(item)
        self.frame_changed.emit()

    def frame_count(self) -> int:
        return len(self._frames)
