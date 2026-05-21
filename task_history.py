"""
任务管理与历史记录模块
支持：增加/删除任务、任务切换、任务历史日志
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QInputDialog, QMessageBox, QLabel, QTextEdit, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject


class EssayTask:
    """单个任务的数据实体"""
    def __init__(self, title: str):
        self.id = str(uuid.uuid4())
        self.title = title
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text_html = ""
        self.frames_data: List[dict] = []
        self.notes_data: dict = {}


class TaskManager(QObject):
    task_switched = pyqtSignal(str)   # task_id
    task_list_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: Dict[str, EssayTask] = {}
        self._current_id: Optional[str] = None

    def create_task(self, title: str) -> str:
        if not title.strip():
            title = "未命名任务"
        task = EssayTask(title.strip())
        self._tasks[task.id] = task
        self._current_id = task.id
        self.task_list_changed.emit()
        return task.id

    def delete_task(self, task_id: str) -> bool:
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        if self._current_id == task_id:
            self._current_id = next(iter(self._tasks), None)
        self.task_list_changed.emit()
        return True

    def rename_task(self, task_id: str, new_title: str) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.title = new_title.strip() or task.title
        self.task_list_changed.emit()
        return True

    def get_task(self, task_id: str) -> Optional[EssayTask]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[EssayTask]:
        return list(self._tasks.values())

    @property
    def current_task_id(self) -> Optional[str]:
        return self._current_id

    def set_current_task(self, task_id: str):
        if task_id in self._tasks:
            self._current_id = task_id
            self.task_switched.emit(task_id)

    def set_current_id_silent(self, task_id: str):
        """仅更新当前 id，不发射 task_switched 信号（用于批量导入时）"""
        if task_id in self._tasks:
            self._current_id = task_id

    def save_current_state(self, html: str, frames: List[dict], notes: dict):
        if self._current_id:
            t = self._tasks[self._current_id]
            t.text_html = html
            t.frames_data = list(frames)
            t.notes_data = dict(notes)

    def load_task(self, task_id: str) -> Optional[EssayTask]:
        return self._tasks.get(task_id)


class HistoryManager(QObject):
    log_added = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logs: List[str] = []

    def add_log(self, action: str, detail: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        msg = f"[{ts}] {action}"
        if detail:
            msg += f" — {detail}"
        self._logs.append(msg)
        self.log_added.emit(msg)

    def get_logs(self) -> List[str]:
        return list(self._logs)

    def clear(self):
        self._logs.clear()
        self.log_added.emit("(历史记录已清空)")


class TaskPanel(QWidget):
    """任务列表面板 UI"""
    switch_task = pyqtSignal(str)

    def __init__(self, manager: TaskManager, history: HistoryManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.history = history
        self._init_ui()
        self._connect()
        self._refresh_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        header.addWidget(QLabel("任务列表"))
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("＋ 新增")
        self.btn_add.setToolTip("新增任务项目")
        self.btn_add.clicked.connect(self._add_task)
        btn_layout.addWidget(self.btn_add)

        self.btn_rename = QPushButton("重命名")
        self.btn_rename.setToolTip("重命名选中的任务")
        self.btn_rename.clicked.connect(self._rename_task)
        btn_layout.addWidget(self.btn_rename)

        self.btn_del = QPushButton("－ 删除")
        self.btn_del.setToolTip("删除选中的任务")
        self.btn_del.clicked.connect(self._delete_task)
        btn_layout.addWidget(self.btn_del)

        layout.addLayout(btn_layout)

    def _connect(self):
        self.manager.task_list_changed.connect(self._refresh_list)
        self.manager.task_switched.connect(self._on_task_switched)

    def _refresh_list(self):
        self.list_widget.blockSignals(True)
        current_id = self.manager.current_task_id
        self.list_widget.clear()
        for task in self.manager.get_all_tasks():
            item = QListWidgetItem(f"{task.title} ({task.created_at.split()[0]})")
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self.list_widget.addItem(item)
            if task.id == current_id:
                item.setSelected(True)
        self.list_widget.blockSignals(False)

    def _on_item_clicked(self, item: QListWidgetItem):
        tid = item.data(Qt.ItemDataRole.UserRole)
        if tid:
            self.switch_task.emit(tid)

    def _on_task_switched(self, tid: str):
        self._refresh_list()

    def _add_task(self):
        title, ok = QInputDialog.getText(self, "新增任务", "请输入任务名称:")
        if ok:
            tid = self.manager.create_task(title)
            self.history.add_log("创建任务", title)
            self.switch_task.emit(tid)

    def _rename_task(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        task = self.manager.get_task(tid)
        if not task:
            return
        new_title, ok = QInputDialog.getText(self, "重命名任务", "新名称:", text=task.title)
        if ok and new_title.strip():
            self.manager.rename_task(tid, new_title)
            self.history.add_log("重命名任务", f"{task.title} -> {new_title.strip()}")
            self._refresh_list()

    def _delete_task(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        task = self.manager.get_task(tid)
        if not task:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除任务『{task.title}』吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.manager.delete_task(tid):
                self.history.add_log("删除任务", task.title)
                self._refresh_list()
                current = self.manager.current_task_id
                if current:
                    self.switch_task.emit(current)


class HistoryPanel(QWidget):
    """历史记录面板 UI"""
    def __init__(self, manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._init_ui()
        self.manager.log_added.connect(self._append_log)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        header.addWidget(QLabel("操作历史"))
        layout.addLayout(header)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.btn_clear = QPushButton("清空历史")
        self.btn_clear.clicked.connect(self._clear)
        layout.addWidget(self.btn_clear)

    def _append_log(self, msg: str):
        self.text_area.append(msg)

    def _clear(self):
        self.text_area.clear()
        self.manager.clear()
