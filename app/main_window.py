from __future__ import annotations

import webbrowser
from pathlib import Path

from PyQt6.QtCore import Qt, QDateTime, QTimer, QStringListModel
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCompleter,
    QComboBox,
    QGridLayout,
    QDateTimeEdit,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from .callsign_db import CallsignDatabase
from .qso_core import QSOData, QSOEngine
from .satellite_manager import SatelliteManager


class MainWindow(QMainWindow):
    """PyQt6 front end for the simplified satellite log workflow."""

    WINDOW_WIDTH = 760
    WINDOW_HEIGHT = 722
    SIDE_MARGIN = 13
    CONTENT_WIDTH = WINDOW_WIDTH - SIDE_MARGIN * 2

    def __init__(self, root: Path, icon_path: Path | None = None):
        super().__init__()
        self.root = root
        self.satellites = SatelliteManager(root / "data" / "satellites.json")
        self.callsigns = CallsignDatabase(root)
        self.engine = QSOEngine(self.satellites)
        self.qso_list: list[QSOData] = []

        self.setWindowTitle("卫星QSO记录软件,Modified from x-qsl-tool(BG5BTK,BH6BEZ)")
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setWindowIcon(QIcon(str(icon_path or (root / "resources" / "app.ico"))))

        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #EBF3FF; }
            QLabel, QDateTimeEdit, QLineEdit, QTableWidget, QRadioButton {
                font-family: 'Microsoft YaHei';
                font-size: 12pt;
                color: #222222;
            }
            QLineEdit, QDateTimeEdit, QTableWidget {
                background: #FFFFFF;
                border: 1px solid #50A0FF;
                border-radius: 4px;
            }
            QLineEdit:focus, QDateTimeEdit:focus, QTableWidget:focus {
                border: 1px solid #50A0FF;
            }
            QDateTimeEdit, QLineEdit { min-height: 32px; }
            QTableWidget {
                gridline-color: #D7D7D7;
                selection-background-color: #DDEBFF;
                alternate-background-color: #FFFFFF;
            }
            QTableWidget::item { padding: 2px 5px; }
            QHeaderView::section {
                background: #EBF3FF;
                border: 0;
                border-bottom: 1px solid #D7D7D7;
                padding: 3px;
                font-weight: normal;
            }
            QRadioButton {
                spacing: 6px;
            }
            QRadioButton:disabled {
                color: #9B9B9B;
            }
            QPushButton {
                border-radius: 4px;
                padding: 4px 10px;
                background: #EBF3FF;
                color: #50A0FF;
                border: 1px solid #50A0FF;
            }
            QPushButton:hover { background: #50A0FF; color: #FFFFFF; }
            QPushButton:pressed { background: #407FCF; color: #FFFFFF; }
            QPushButton#btn_openSourcePage {
                background: #F4F2FB; color: #663AB7; border: 1px solid #663AB7;
            }
            QPushButton#btn_openSourcePage:hover { background: #663AB7; color: #FFFFFF; }
            QPushButton#btn_openSourcePage:pressed { background: #522E93; color: #FFFFFF; }
            QPushButton#clear_btn {
                background: #FBEEEE; color: #E65050; border: 1px solid #E65050;
            }
            QPushButton#clear_btn:hover { background: #E65050; color: #FFFFFF; }
            QPushButton#clear_btn:pressed { background: #CA5759; color: #FFFFFF; }
            QPushButton#export_btn {
                background: #EFF8E8; color: #6EBE28; border: 1px solid #6EBE28;
            }
            QPushButton#export_btn:hover { background: #6EBE28; color: #FFFFFF; }
            QPushButton#export_btn:pressed { background: #64A823; color: #FFFFFF; }
            QPushButton#delete_row {
                background: #FBEEEE; color: #E65050; border: 1px solid #E65050;
                padding: 1px 5px;
            }
            QPushButton#delete_row:hover { background: #E65050; color: #FFFFFF; }
            QPushButton#delete_row:pressed { background: #CA5759; color: #FFFFFF; }
            """
        )

        self.lab_inputInfo = QLabel("卫星日志：选择卫星和时间", self)
        self.lab_inputInfo.setGeometry(self.SIDE_MARGIN, 14, 330, 35)

        self.time_mode_set = QRadioButton("设定", self)
        self.time_mode_set.setGeometry(352, 17, 60, 30)
        self.time_mode_realtime = QRadioButton("实时", self)
        self.time_mode_realtime.setGeometry(413, 17, 60, 30)
        self.time_mode_set.setChecked(True)
        self.time_mode_set.setToolTip("设定：手动选择日志时间")
        self.time_mode_realtime.setToolTip("实时：顶部时间自动跟随当前 UTC 时间")
        self.time_mode_group = QButtonGroup(self)
        self.time_mode_group.setExclusive(True)
        self.time_mode_group.addButton(self.time_mode_set)
        self.time_mode_group.addButton(self.time_mode_realtime)
        self.time_mode_set.toggled.connect(self._on_time_mode_changed)

        self.btn_openSourcePage = QPushButton("项目开源", self)
        self.btn_openSourcePage.setObjectName("btn_openSourcePage")
        self.btn_openSourcePage.setGeometry(self.WINDOW_WIDTH - 111, 14, 98, 35)
        self.btn_openSourcePage.clicked.connect(
            lambda: self.open_url("https://github.com/BH2VSQ/XQSL_PyQt")
        )

        self.satellite_combo = QComboBox(self)
        self.satellite_combo.setGeometry(self.SIDE_MARGIN, 59, 250, 35)
        self.satellite_combo.addItems([sat.name for sat in self.satellites.satellites])

        self.datetime_edit = QDateTimeEdit(self)
        self.datetime_edit.setGeometry(273, 59, 310, 35)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTimeUtc())

        self.clear_btn = QPushButton("清空", self)
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setGeometry(self.WINDOW_WIDTH - 111, 59, 98, 71)
        self.clear_btn.clicked.connect(self.clear_all)

        self.callsign_edit = QLineEdit(self)
        self.callsign_edit.setGeometry(self.SIDE_MARGIN, 101, 250, 35)
        self.callsign_edit.setPlaceholderText("输入呼号，支持模糊搜索")
        self.callsign_edit.returnPressed.connect(self.add_log_row)

        # 模式选择区域固定预留至少两行，后续新增模式自动换行。
        self.mode_buttons_container = QWidget(self)
        self.mode_buttons_container.setGeometry(273, 98, 335, 72)
        self.mode_buttons_container.setVisible(False)
        self.mode_buttons_layout = QGridLayout(self.mode_buttons_container)
        self.mode_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.mode_buttons_layout.setHorizontalSpacing(0)
        self.mode_buttons_layout.setVerticalSpacing(2)
        for column in range(4):
            self.mode_buttons_layout.setColumnStretch(column, 1)
        self.mode_buttons: list[QRadioButton] = []
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)

        self.call_table = QTableWidget(self)
        self.call_table.setGeometry(
            self.SIDE_MARGIN,
            180,
            self.CONTENT_WIDTH,
            496,
        )
        self.call_table.setColumnCount(5)
        self.call_table.setHorizontalHeaderLabels(["呼号", "卫星名称", "时间", "模式", "删除"])
        self.call_table.verticalHeader().setVisible(False)
        self.call_table.verticalHeader().setDefaultSectionSize(32)
        self.call_table.setEditTriggers(
            self.call_table.EditTrigger.DoubleClicked
            | self.call_table.EditTrigger.SelectedClicked
        )
        self.call_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.call_table.setAlternatingRowColors(False)
        self.call_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.call_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.call_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.call_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.call_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.call_table.setColumnWidth(3, 95)
        self.call_table.setColumnWidth(4, 72)
        self.call_table.setRowCount(0)

        self.export_btn = QPushButton("导出ADIF", self)
        self.export_btn.setObjectName("export_btn")
        self.export_btn.setGeometry(self.SIDE_MARGIN, 684, self.CONTENT_WIDTH, 31)
        self.export_btn.clicked.connect(self.export_adif)

        self.satellite_combo.currentIndexChanged.connect(self._update_mode_choices)
        self._init_call_completer()
        self._update_mode_choices()

        self.utc_timer = QTimer(self)
        self.utc_timer.setInterval(1000)
        self.utc_timer.timeout.connect(self._update_realtime_clock)
        self.utc_timer.start()

    def _init_call_completer(self) -> None:
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.callsign_edit.setCompleter(self.completer)
        self.callsign_edit.textChanged.connect(self.refresh_call_suggestions)
        self.refresh_call_suggestions("")

    def refresh_call_suggestions(self, query: str) -> None:
        self.completer_model.setStringList(self.callsigns.search(query, 80))

    def _current_satellite(self):
        return self.satellites.get(self.satellite_combo.currentText().strip())

    def _clear_mode_buttons(self) -> None:
        while self.mode_buttons_layout.count():
            item = self.mode_buttons_layout.takeAt(0)
            button = item.widget()
            if button is not None:
                self.mode_group.removeButton(button)
                button.deleteLater()
        self.mode_buttons.clear()

    def _update_mode_choices(self) -> None:
        sat = self._current_satellite()
        self._clear_mode_buttons()

        if sat is None or len(sat.modes) <= 1:
            self.mode_buttons_container.setVisible(False)
            return

        mode_count = len(sat.modes)
        # 每行最多 4 个模式，并至少预留一整行空白。
        row_count = max(2, (mode_count + 3) // 4)
        button_height = 30
        vertical_gap = 2
        container_height = row_count * button_height + (row_count - 1) * vertical_gap
        self.mode_buttons_container.setFixedHeight(container_height)

        for index, mode in enumerate(sat.modes):
            row = index // 4
            column = index % 4
            button = QRadioButton(mode, self.mode_buttons_container)
            button.setMinimumHeight(button_height)
            button.setMaximumHeight(button_height)
            button.setToolTip(f"选择 {mode} 模式")
            if index == 0:
                button.setChecked(True)
            self.mode_buttons_layout.addWidget(button, row, column)
            self.mode_group.addButton(button)
            self.mode_buttons.append(button)

        self.mode_buttons_container.setVisible(True)

    def _selected_mode(self) -> str:
        sat = self._current_satellite()
        if sat is None:
            return ""
        checked = self.mode_group.checkedButton()
        if checked is not None and self.mode_buttons_container.isVisible():
            return checked.text().strip().upper()
        return sat.modes[0].strip().upper() if sat.modes else "FM"

    def _on_time_mode_changed(self, checked: bool) -> None:
        if not checked:
            return
        realtime = self.time_mode_realtime.isChecked()
        self.datetime_edit.setReadOnly(realtime)
        if realtime:
            self._update_realtime_clock()

    def _update_realtime_clock(self) -> None:
        if self.time_mode_realtime.isChecked():
            self.datetime_edit.setDateTime(QDateTime.currentDateTimeUtc())

    def _selected_datetime(self):
        return self.datetime_edit.dateTime().toPyDateTime().replace(tzinfo=None, microsecond=0)

    def add_log_row(self) -> None:
        call = self.callsign_edit.text().strip().upper()
        if not call:
            QMessageBox.warning(self, "提示", "请输入呼号。")
            return

        sat = self._current_satellite()
        if sat is None:
            QMessageBox.warning(self, "提示", "卫星配置不存在。")
            return

        if self.time_mode_realtime.isChecked():
            self._update_realtime_clock()
        log_time = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        selected_mode = self._selected_mode()

        row = self.call_table.rowCount()
        self.call_table.insertRow(row)

        call_item = QTableWidgetItem(call)
        call_item.setData(Qt.ItemDataRole.UserRole, selected_mode)
        self.call_table.setItem(row, 0, call_item)

        satellite_item = QTableWidgetItem(sat.name)
        self.call_table.setItem(row, 1, satellite_item)

        time_item = QTableWidgetItem(log_time)
        time_item.setData(Qt.ItemDataRole.UserRole, log_time)
        self.call_table.setItem(row, 2, time_item)

        mode_item = QTableWidgetItem(selected_mode)
        mode_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_item.setFlags(mode_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.call_table.setItem(row, 3, mode_item)

        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("delete_row")
        delete_btn.clicked.connect(lambda _checked=False, r=row: self.delete_log_row(r))
        self.call_table.setCellWidget(row, 4, delete_btn)

        self.callsigns.record(call)
        self.callsign_edit.clear()
        self.call_table.scrollToBottom()
        self._renumber_delete_buttons()

    def _renumber_delete_buttons(self) -> None:
        for row in range(self.call_table.rowCount()):
            button = self.call_table.cellWidget(row, 4)
            if button is None:
                continue
            try:
                button.clicked.disconnect()
            except TypeError:
                pass
            button.clicked.connect(lambda _checked=False, r=row: self.delete_log_row(r))

    def delete_log_row(self, row: int) -> None:
        if 0 <= row < self.call_table.rowCount():
            self.call_table.removeRow(row)
            self._renumber_delete_buttons()

    def _collect_qso_list(self) -> list[QSOData] | None:
        if self.call_table.rowCount() == 0:
            QMessageBox.warning(self, "提示", "请先加入至少一个呼号。")
            return None

        result: list[QSOData] = []
        errors: list[str] = []
        for row in range(self.call_table.rowCount()):
            call_item = self.call_table.item(row, 0)
            satellite_item = self.call_table.item(row, 1)
            time_item = self.call_table.item(row, 2)
            call = call_item.text().strip() if call_item else ""
            satellite_name = satellite_item.text().strip() if satellite_item else ""
            row_time = time_item.text().strip() if time_item else ""
            if not row_time and time_item is not None:
                saved_time = time_item.data(Qt.ItemDataRole.UserRole)
                row_time = str(saved_time or "").strip()
            mode_item = self.call_table.item(row, 3)
            row_mode = mode_item.text().strip().upper() if mode_item else ""
            if not row_mode and call_item is not None:
                row_mode = str(call_item.data(Qt.ItemDataRole.UserRole) or "").strip().upper()

            if not call:
                errors.append(f"第 {row + 1} 行：呼号为空")
                continue
            if not satellite_name:
                errors.append(f"第 {row + 1} 行：卫星名称为空")
                continue

            snapshot_dt = self._selected_datetime()
            try:
                result.append(
                    self.engine.generate_satellite_qso(
                        satellite_name=satellite_name,
                        row_callsign=call,
                        row_time=row_time,
                        default_dt=snapshot_dt,
                        mode_override=row_mode,
                    )
                )
            except ValueError as exc:
                errors.append(f"第 {row + 1} 行：{exc}")

        if errors:
            QMessageBox.warning(self, "解析错误", "\n".join(errors))

        return result or None

    def export_adif(self) -> None:
        result = self._collect_qso_list()
        if not result:
            return

        self.qso_list = result
        adif = self.engine.generate_adif_file(self.qso_list)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存 ADIF",
            "QSO_Log.adi",
            "ADIF Files (*.adi);;All Files (*.*)",
        )
        if not path:
            return

        try:
            Path(path).write_text(adif, encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", f"无法保存 ADIF 文件：\n{exc}")
            return

        self.lab_inputInfo.setText("ADIF 导出完成，可继续添加呼号")
        QMessageBox.information(self, "完成", f"ADIF 已保存：\n{path}")

    def clear_all(self) -> None:
        self.call_table.setRowCount(0)
        self.callsign_edit.clear()
        self.qso_list = []
        self.lab_inputInfo.setText("卫星日志：选择卫星和时间")

    @staticmethod
    def open_url(url: str) -> None:
        webbrowser.open(url)

    def show_usage(self) -> None:
        QMessageBox.information(
            self,
            "使用说明",
            "1. 选择卫星。\n"
            "2. 使用‘设定’或‘实时’单选框控制顶部日志时间；实时模式跟随当前UTC时间。\n"
            "3. 对支持多模式的卫星使用顶部模式单选框选择模式。\n"
            "4. 在呼号框按回车直接加入日志。\n"
            "5. 加入日志时会把当前卫星、时间和模式固定保存到该行。\n"
            "6. 表格显示呼号、卫星名称、时间和模式，模式为只读文本。\n"
            "7. 点击底部‘导出ADIF’完成解析并导出。",
        )

    def about_author(self) -> None:
        QMessageBox.information(
            self,
            "关于作者",
            "X-QSL Amateur Radio ADIF Tool\nPython + PyQt6 迁移版",
        )
