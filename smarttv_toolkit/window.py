from __future__ import annotations

from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QScrollArea,
    QProgressBar, QListWidget, QListWidgetItem, QPlainTextEdit, QMessageBox,
    QCheckBox, QButtonGroup, QSizePolicy, QSpacerItem
)

APP_STYLE = """
* { font-family: 'Segoe UI'; }
QMainWindow, QWidget#central { background: #060d18; color: #e8f1ff; }
QFrame#sidebar { background: #07111f; border-right: 1px solid #172a41; }
QLabel { color: #e8f1ff; }
QLabel.muted { color: #8ea5c2; }
QFrame.panel { background: #0a1524; border: 1px solid #1a3049; border-radius: 13px; }
QFrame.tile { border-radius: 15px; border: 1px solid #23405e; }
QPushButton { background: #122238; color: #dceaff; border: 1px solid #253d59; border-radius: 9px; padding: 9px 12px; text-align: left; }
QPushButton:hover { background: #1b3452; border-color: #2b91f0; }
QPushButton:checked { background: #103e71; border-color: #1c9cff; color: white; }
QPushButton.primary { background: #087dcc; border: 1px solid #1999ed; color: white; font-weight: 600; }
QPushButton.primary:hover { background: #1597e8; }
QPushButton.purple { background: #5d35be; border: 1px solid #a16aff; color: white; font-weight: 600; }
QPushButton.green { background: #04654f; border: 1px solid #12c99a; color: white; font-weight: 600; }
QPushButton.gold { background: #775514; border: 1px solid #ffc247; color: white; font-weight: 600; }
QPushButton.danger { color: #ffb8c0; background: #291825; border-color: #87384a; }
QLineEdit, QPlainTextEdit, QListWidget { background: #07111e; color: #e8f1ff; border: 1px solid #203750; border-radius: 8px; padding: 8px; selection-background-color: #145da0; }
QProgressBar { background: #142b42; border: 0; border-radius: 5px; height: 9px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #138cf0; border-radius: 5px; }
QCheckBox { color: #bdd0e8; spacing: 8px; }
QScrollArea { border: 0; }
QScrollBar:vertical { background: #091422; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #27425f; border-radius: 4px; min-height: 22px; }
"""

PAGES = [
    ("⌂", "Главная"),
    ("▣", "Подключение"),
    ("⌕", "Анализ системы"),
    ("➤", "Оптимизация"),
    ("▤", "Удаление приложений"),
    ("▦", "Управление приложениями"),
    ("⚙", "Настройки системы"),
    ("◉", "Темы и оформление"),
    ("⌁", "Инструменты"),
    ("▤", "Резервные копии"),
    ("▧", "Логи и отчёты"),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SmartTV Toolkit")
        self.resize(1536, 1024)
        self.setMinimumSize(1120, 760)
        self.setStyleSheet(APP_STYLE)
        self.logs: list[str] = []
        self.connected = False
        self.nav_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self._show_page("Главная")

    def _label(self, text: str, size: int = 10, bold: bool = False, color: str | None = None) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setPointSize(size)
        font.setBold(bold)
        label.setFont(font)
        if color:
            label.setStyleSheet(f"color: {color};")
        return label

    def _panel(self, title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setProperty("class", "panel")
        frame.setStyleSheet("QFrame { background:#0a1524; border:1px solid #1a3049; border-radius:13px; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(13, 12, 13, 12)
        layout.setSpacing(9)
        if title:
            row = QHBoxLayout()
            row.addWidget(self._label(title, 12, True))
            row.addStretch(1)
            layout.addLayout(row)
        return frame, layout

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 22, 14, 16)
        side.setSpacing(5)

        brand = QHBoxLayout()
        icon = self._label("▣", 30, True, "#1da6ff")
        icon.setFixedWidth(42)
        brand.addWidget(icon)
        brand_text = QVBoxLayout()
        brand_text.addWidget(self._label("SmartTV Toolkit", 18, True))
        brand_text.addWidget(self._label("Make your TV yours", 9, False, "#20a9ff"))
        brand_text.addWidget(self._label("v1.0.0 • Preview", 8, False, "#7188a8"))
        brand.addLayout(brand_text)
        side.addLayout(brand)
        side.addSpacing(25)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for glyph, name in PAGES:
            button = QPushButton(f"{glyph}   {name}")
            button.setCheckable(True)
            button.setMinimumHeight(43)
            button.clicked.connect(lambda checked=False, page=name: self._show_page(page))
            self.nav_group.addButton(button)
            self.nav_buttons[name] = button
            side.addWidget(button)
        side.addStretch(1)

        lang = QPushButton("◎   Русский / Language    ⌄")
        lang.setMinimumHeight(40)
        side.addWidget(lang)
        theme = QHBoxLayout()
        theme.addWidget(self._label("◐   Тёмная тема", 9))
        theme.addStretch(1)
        theme_tag = self._label("ON", 9, True, "#21c3ff")
        theme.addWidget(theme_tag)
        side.addLayout(theme)

        content = QWidget()
        body = QVBoxLayout(content)
        body.setContentsMargins(22, 18, 20, 14)
        body.setSpacing(12)
        self.page_title = self._label("Главная", 23, True)
        body.addWidget(self.page_title)
        self.page_stack = QStackedWidget()
        body.addWidget(self.page_stack, 1)

        root.addWidget(sidebar)
        root.addWidget(content, 1)

        self.pages: dict[str, QWidget] = {}
        self.pages["Главная"] = self._home_page()
        self.pages["Подключение"] = self._connection_page()
        self.pages["Анализ системы"] = self._analysis_page()
        self.pages["Оптимизация"] = self._optimization_page()
        self.pages["Удаление приложений"] = self._apps_page()
        self.pages["Управление приложениями"] = self._apps_page()
        self.pages["Настройки системы"] = self._settings_page()
        self.pages["Темы и оформление"] = self._placeholder_page("Темы и оформление", "Темы будут доступны после подключения и определения возможностей устройства.")
        self.pages["Инструменты"] = self._tools_page()
        self.pages["Резервные копии"] = self._backups_page()
        self.pages["Логи и отчёты"] = self._logs_page()
        for page in PAGES:
            self.page_stack.addWidget(self.pages[page[1]])

    def _scroll(self, child: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(child)
        return area

    def _home_page(self) -> QWidget:
        outer = QWidget()
        root = QVBoxLayout(outer)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        hero = QFrame()
        hero.setStyleSheet("QFrame { border:1px solid #1a3049; border-radius:16px; background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0b1a2c,stop:0.55 #101b35,stop:1 #17152e); }")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(23, 20, 23, 20)
        hero_left = QVBoxLayout()
        hero_left.addWidget(self._label("Добро пожаловать!", 24, True))
        hero_left.addWidget(self._label("Сделайте ваш Android TV быстрее, чище и удобнее.", 12, False, "#a9c0de"))
        pills = QHBoxLayout()
        for label, tone in [("⚡ Быстрее", "#11d69a"), ("▤ Чище", "#b88aff"), ("◈ Стабильнее", "#28c4ff"), ("♥ Удобнее", "#ff86bd")]:
            chip = self._label(f"  {label}  ", 10, True, tone)
            chip.setStyleSheet(f"color:{tone};background:#0c2336;border:1px solid {tone};border-radius:9px;padding:8px;")
            pills.addWidget(chip)
        pills.addStretch(1)
        hero_left.addSpacing(6)
        hero_left.addLayout(pills)
        hero_layout.addLayout(hero_left, 3)
        hero_layout.addStretch(1)
        hero_art = self._label("◈\nSMART\nTV", 18, True, "#45b9ff")
        hero_art.setAlignment(Qt.AlignCenter)
        hero_art.setStyleSheet("background:#0b1425;border:1px solid #2a5882;border-radius:14px;padding:14px;color:#54beff;")
        hero_art.setMinimumWidth(140)
        hero_layout.addWidget(hero_art, 1)
        root.addWidget(hero)

        # Dashboard body: data overview and utility rail.
        grid = QGridLayout()
        grid.setSpacing(10)
        root.addLayout(grid, 1)
        left = QWidget()
        left_col = QVBoxLayout(left)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(10)
        right = QWidget()
        right_col = QVBoxLayout(right)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(10)

        tiles = QGridLayout()
        tiles.setSpacing(9)
        tiles_data = [
            ("🧹", "Быстрая очистка", "Безопасная проверка временных файлов", "#0879b9", "Очистить"),
            ("🚀", "Turbo Mode", "Обратимые настройки интерфейса", "#6235b9", "Запустить"),
            ("⚙", "Оптимизация", "Анимации и параметры Android", "#047b61", "Настроить"),
            ("⌕", "Анализ системы", "Устройство, память и приложения", "#775514", "Анализировать"),
        ]
        for i, (glyph, title, desc, color, action) in enumerate(tiles_data):
            tile = QFrame()
            tile.setMinimumHeight(162)
            tile.setStyleSheet(f"QFrame {{ background:#0a1b2e; border:1px solid {color}; border-radius:14px; }}")
            tv = QVBoxLayout(tile)
            tv.setContentsMargins(13, 12, 13, 12)
            tv.setSpacing(7)
            tv.addWidget(self._label(glyph, 22, True, color))
            tv.addWidget(self._label(title, 12, True))
            lbl = self._label(desc, 9, False, "#9db2cb")
            lbl.setWordWrap(True)
            tv.addWidget(lbl)
            tv.addStretch(1)
            btn = QPushButton(action + "    ›")
            btn.setProperty("class", "primary")
            btn.setStyleSheet(f"background:{color};color:white;border:1px solid {color};border-radius:8px;padding:8px;font-weight:600;")
            if i == 0:
                btn.clicked.connect(lambda: self._show_page("Оптимизация"))
            elif i == 1:
                btn.clicked.connect(lambda: self._show_page("Оптимизация"))
            elif i == 2:
                btn.clicked.connect(lambda: self._show_page("Настройки системы"))
            else:
                btn.clicked.connect(lambda: self._show_page("Анализ системы"))
            tv.addWidget(btn)
            tiles.addWidget(tile, i // 2, i % 2)
        left_col.addLayout(tiles)

        device_panel, device_layout = self._panel("▣   Информация об устройстве")
        refresh_btn = QPushButton("↻  Обновить")
        refresh_btn.clicked.connect(self._refresh_device_info)
        refresh_row = device_layout.itemAt(0).layout()
        refresh_row.addWidget(refresh_btn)
        info_grid = QGridLayout()
        self.device_values: dict[str, QLabel] = {}
        for col, (key, label) in enumerate([("brand", "Бренд"), ("model", "Модель"), ("device", "Устройство"), ("android", "Android"), ("sdk", "SDK")]):
            stat = QFrame()
            stat.setStyleSheet("QFrame { background:#0d1b2b;border:1px solid #1a3049;border-radius:9px; }")
            sv = QVBoxLayout(stat)
            sv.setContentsMargins(10, 8, 10, 8)
            sv.addWidget(self._label(label, 8, False, "#8ea5c2"))
            value = self._label("Неизвестно", 10, True)
            self.device_values[key] = value
            sv.addWidget(value)
            info_grid.addWidget(stat, 0, col)
        device_layout.addLayout(info_grid)
        left_col.addWidget(device_panel)

        perf_panel, perf_layout = self._panel("▤   Память и производительность")
        perf_grid = QGridLayout()
        for i, (title, caption, percent, color) in enumerate([
            ("Внутренняя память", "Ожидает подключения", 0, "#168bff"),
            ("ОЗУ (RAM)", "Ожидает подключения", 0, "#a855f7"),
            ("Загрузка CPU", "Ожидает подключения", 0, "#15d99a"),
            ("Температура", "Не поддерживается всеми ТВ", 0, "#fb6d99"),
        ]):
            card = QFrame()
            card.setStyleSheet("QFrame { background:#0d1b2b;border:1px solid #1a3049;border-radius:10px; }")
            cv = QVBoxLayout(card)
            cv.setContentsMargins(10, 9, 10, 9)
            cv.addWidget(self._label(title, 9, True))
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(percent)
            cv.addWidget(bar)
            cap = self._label(caption, 8, False, "#8ea5c2")
            cap.setWordWrap(True)
            cv.addWidget(cap)
            perf_grid.addWidget(card, 0, i)
        perf_layout.addLayout(perf_grid)
        left_col.addWidget(perf_panel)

        recommend_panel, recommend_layout = self._panel("★   Рекомендуемые действия")
        recommendations = [
            ("▦", "Проверить приложения", "Ничего не удаляется автоматически."),
            ("◈", "Оптимизировать анимации", "Настройки можно вернуть обратно."),
            ("▤", "Создать резервную копию", "Сохранить состояние перед изменениями."),
            ("⌕", "Проверить устройство", "Определить Android и модель через ADB."),
        ]
        for glyph, title, desc in recommendations:
            row = QHBoxLayout()
            symbol = self._label(glyph, 16, True, "#20baff")
            symbol.setFixedWidth(24)
            row.addWidget(symbol)
            center = QVBoxLayout()
            center.addWidget(self._label(title, 9, True))
            center.addWidget(self._label(desc, 8, False, "#8ea5c2"))
            row.addLayout(center, 1)
            button = QPushButton("Показать")
            button.clicked.connect(lambda checked=False, t=title: self._recommendation_action(t))
            row.addWidget(button)
            recommend_layout.addLayout(row)
        left_col.addWidget(recommend_panel)

        connection_panel, connection_layout = self._panel("●   Устройство")
        self.connection_status = self._label("Устройство не подключено", 9, True, "#f6bd4b")
        connection_layout.addWidget(self.connection_status)
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("IP-адрес ТВ, например 192.168.1.50")
        connection_layout.addWidget(self.ip_edit)
        connect = QPushButton("Подключиться")
        connect.setProperty("class", "primary")
        connect.clicked.connect(self._connect_device)
        connection_layout.addWidget(connect)
        disconnect = QPushButton("Отключиться")
        disconnect.setProperty("class", "danger")
        disconnect.clicked.connect(self._disconnect_device)
        connection_layout.addWidget(disconnect)
        right_col.addWidget(connection_panel)

        actions_panel, actions_layout = self._panel("⌘   Быстрые действия")
        for label, glyph in [
            ("Создать резервную копию", "▤"),
            ("Открыть ADB Shell", ">_"),
            ("Перезагрузить устройство", "⏻"),
            ("Сделать скриншот", "▣"),
            ("Проверить подключение", "↻"),
        ]:
            btn = QPushButton(f"{glyph}   {label}    ›")
            btn.clicked.connect(lambda checked=False, text=label: self._quick_action(text))
            actions_layout.addWidget(btn)
        right_col.addWidget(actions_panel)

        links_panel, links_layout = self._panel("↗   Полезное")
        for label in ["Руководство", "GitHub", "Проверить обновления"]:
            btn = QPushButton(f"◇   {label}    ›")
            btn.clicked.connect(lambda checked=False, text=label: self._quick_action(text))
            links_layout.addWidget(btn)
        right_col.addWidget(links_panel)
        right_col.addStretch(1)

        grid.addWidget(left, 0, 0, 1, 3)
        grid.addWidget(right, 0, 3, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 0)
        return self._scroll(outer)

    def _connection_page(self) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        p, pv = self._panel("Подключение Android TV")
        pv.addWidget(self._label("Введи IP телевизора. На ТВ должны быть включены параметры разработчика и ADB по сети.", 10, False, "#8ea5c2"))
        self.connection_ip = QLineEdit()
        self.connection_ip.setPlaceholderText("192.168.1.50")
        pv.addWidget(self.connection_ip)
        row = QHBoxLayout()
        connect = QPushButton("Подключиться по Wi-Fi")
        connect.setProperty("class", "primary")
        connect.clicked.connect(lambda: self._connect_device(self.connection_ip.text().strip()))
        row.addWidget(connect)
        disconnect = QPushButton("Отключиться")
        disconnect.clicked.connect(self._disconnect_device)
        row.addWidget(disconnect)
        pv.addLayout(row)
        pv.addWidget(self._label("Подключение по USB можно будет добавить, когда будут определены и проверены команды Platform Tools.", 9, False, "#8ea5c2"))
        layout.addWidget(p)
        layout.addStretch(1)
        return outer

    def _analysis_page(self) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, pv = self._panel("Сканирование системы")
        pv.addWidget(self._label("Собираем только диагностическую информацию. Ничего не отключается и не удаляется.", 10, False, "#8ea5c2"))
        self.analysis_output = QPlainTextEdit()
        self.analysis_output.setReadOnly(True)
        self.analysis_output.setPlaceholderText("Подключи телевизор и нажми «Начать анализ»...")
        pv.addWidget(self.analysis_output, 1)
        buttons = QHBoxLayout()
        scan = QPushButton("Начать анализ")
        scan.setProperty("class", "primary")
        scan.clicked.connect(self._run_analysis)
        buttons.addWidget(scan)
        export = QPushButton("Экспортировать отчёт")
        export.clicked.connect(self._export_report)
        buttons.addWidget(export)
        pv.addLayout(buttons)
        layout.addWidget(panel, 1)
        return outer

    def _optimization_page(self) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        notice = QFrame()
        notice.setStyleSheet("QFrame { background:#211b13;border:1px solid #725728;border-radius:12px; }")
        nv = QVBoxLayout(notice)
        nv.addWidget(self._label("⚠  Сначала диагностика, потом оптимизация", 13, True, "#ffd27d"))
        nv.addWidget(self._label("Изменения обратимы, но поддержка команд зависит от прошивки. Не отключаем системные пакеты автоматически.", 9, False, "#c8b48b"))
        layout.addWidget(notice)
        panel, pv = self._panel("Turbo Mode")
        pv.addWidget(self._label("Выбери профиль. До применения программа покажет перечень конкретных изменений.", 10, False, "#8ea5c2"))
        self.safe_profile = QCheckBox("Safe: отключить анимации интерфейса (обратимо)")
        self.safe_profile.setChecked(True)
        pv.addWidget(self.safe_profile)
        self.cache_profile = QCheckBox("Очистить кеш Android (системная команда, если поддерживается)")
        pv.addWidget(self.cache_profile)
        self.compile_profile = QCheckBox("Оптимизировать установленные приложения штатным компилятором Android")
        pv.addWidget(self.compile_profile)
        self.preview_output = QPlainTextEdit()
        self.preview_output.setReadOnly(True)
        self.preview_output.setMaximumHeight(110)
        self.preview_output.setPlainText("Изменения появятся после подключения устройства и предпросмотра.")
        pv.addWidget(self.preview_output)
        preview = QPushButton("Показать план изменений")
        preview.clicked.connect(self._preview_optimization)
        pv.addWidget(preview)
        run = QPushButton("Применить выбранное")
        run.setProperty("class", "primary")
        run.clicked.connect(self._apply_optimization)
        pv.addWidget(run)
        restore = QPushButton("Вернуть анимации")
        restore.clicked.connect(self._restore_animations)
        pv.addWidget(restore)
        layout.addWidget(panel)
        layout.addStretch(1)
        return outer

    def _apps_page(self) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, pv = self._panel("Установленные приложения")
        pv.addWidget(self._label("На первом этапе отображаем список приложений. Массовое удаление не выполняется.", 9, False, "#8ea5c2"))
        self.apps_list = QListWidget()
        pv.addWidget(self.apps_list, 1)
        row = QHBoxLayout()
        refresh = QPushButton("Сканировать приложения")
        refresh.setProperty("class", "primary")
        refresh.clicked.connect(self._scan_apps)
        row.addWidget(refresh)
        details = QPushButton("Показать пакет")
        details.clicked.connect(self._show_selected_app)
        row.addWidget(details)
        pv.addLayout(row)
        layout.addWidget(panel, 1)
        return outer

    def _settings_page(self) -> QWidget:
        return self._placeholder_page("Настройки системы", "Позже сюда добавим проверяемые настройки системы, локальные копии текущих значений и откат. Слепое изменение свойств Android запрещено.")

    def _tools_page(self) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, pv = self._panel("Инструменты устройства")
        pv.addWidget(self._label("ADB Shell работает только после успешного подключения. Выполняй команды, которые понимаешь.", 9, False, "#8ea5c2"))
        self.shell_command = QLineEdit()
        self.shell_command.setPlaceholderText("Команда adb shell, например getprop ro.build.version.release")
        pv.addWidget(self.shell_command)
        run = QPushButton("Выполнить диагностическую команду")
        run.clicked.connect(self._run_shell)
        pv.addWidget(run)
        self.shell_output = QPlainTextEdit()
        self.shell_output.setReadOnly(True)
        pv.addWidget(self.shell_output, 1)
        layout.addWidget(panel, 1)
        return outer

    def _backups_page(self) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, pv = self._panel("Резервные копии и восстановление")
        pv.addWidget(self._label("До внедрения низкоуровневых изменений будем сохранять поддерживаемые настройки на ПК. Это не копия прошивки.", 9, False, "#8ea5c2"))
        create = QPushButton("Создать локальную резервную копию отчёта")
        create.clicked.connect(self._export_report)
        pv.addWidget(create)
        self.backup_list = QListWidget()
        self.backup_list.addItem("Резервные копии устройства пока не созданы")
        pv.addWidget(self.backup_list, 1)
        layout.addWidget(panel, 1)
        return outer

    def _logs_page(self) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, pv = self._panel("Журнал действий")
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        pv.addWidget(self.log_output, 1)
        clear = QPushButton("Очистить журнал на экране")
        clear.clicked.connect(self.log_output.clear)
        pv.addWidget(clear)
        layout.addWidget(panel, 1)
        return outer

    def _placeholder_page(self, title: str, desc: str) -> QWidget:
        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, pv = self._panel(title)
        pv.addWidget(self._label(desc, 10, False, "#8ea5c2"))
        pv.addStretch(1)
        layout.addWidget(panel, 1)
        layout.addStretch(2)
        return outer

    def _show_page(self, name: str) -> None:
        if name not in self.pages:
            return
        self.page_title.setText(name)
        self.page_stack.setCurrentWidget(self.pages[name])
        if name in self.nav_buttons:
            self.nav_buttons[name].setChecked(True)
        self._log(f"Открыт раздел: {name}")

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        self.logs.append(line)
        if hasattr(self, "log_output"):
            self.log_output.appendPlainText(line)

    def _client(self):
        from smarttv_toolkit.adb import AdbClient, AdbError
        ip = getattr(self, "ip_edit", None)
        host = ip.text().strip() if ip else ""
        if not host:
            host = self.connection_ip.text().strip() if hasattr(self, "connection_ip") else ""
        if not host:
            QMessageBox.warning(self, "Нет IP-адреса", "Введи IP-адрес телевизора.")
            return None
        try:
            return AdbClient(host)
        except Exception as exc:
            QMessageBox.critical(self, "ADB", str(exc))
            return None

    def _connect_device(self, host: str | None = None) -> None:
        if host is None:
            host = self.ip_edit.text().strip()
        if not host:
            QMessageBox.warning(self, "Подключение", "Укажи IP-адрес Android TV.")
            return
        from smarttv_toolkit.adb import AdbClient, AdbError
        client = AdbClient(host)
        try:
            client.connect()
            info = client.info()
            self.connected = True
            self.connection_status.setText(f"Подключено: {host}:5555")
            self.connection_status.setStyleSheet("color:#18d59b;font-weight:600")
            for key, value in [
                ("brand", info.manufacturer), ("model", info.model),
                ("device", self._get_prop(client, "ro.product.device")),
                ("android", info.android), ("sdk", self._get_prop(client, "ro.build.version.sdk")),
            ]:
                self.device_values[key].setText(value or "Неизвестно")
            self._log(f"Подключено устройство: {info.manufacturer} {info.model} / Android {info.android}")
            if hasattr(self, "analysis_output"):
                self.analysis_output.setPlainText(f"Устройство: {info.manufacturer} {info.model}\nAndroid: {info.android}\nIP: {host}")
        except Exception as exc:
            self.connected = False
            QMessageBox.critical(self, "Ошибка подключения", str(exc))
            self._log(f"Ошибка подключения: {exc}")

    def _disconnect_device(self) -> None:
        host = self.ip_edit.text().strip()
        if host:
            try:
                from smarttv_toolkit.adb import AdbClient
                AdbClient(host).disconnect()
            except Exception:
                pass
        self.connected = False
        self.connection_status.setText("Устройство не подключено")
        self.connection_status.setStyleSheet("color:#f6bd4b")
        self._log("Устройство отключено")

    def _get_prop(self, client, key: str) -> str:
        try:
            return client.shell(f"getprop {key}")
        except Exception:
            return "не поддерживается"

    def _refresh_device_info(self) -> None:
        host = self.ip_edit.text().strip()
        if not host:
            QMessageBox.information(self, "Обновление", "Сначала подключи телевизор.")
            return
        self._connect_device(host)

    def _run_analysis(self) -> None:
        client = self._client()
        if client is None:
            return
        try:
            text = client.shell("getprop")
            packages = client.shell("pm list packages")
            mem = client.shell("cat /proc/meminfo")
            report = (
                "SMARTTV TOOLKIT • SYSTEM REPORT\n"
                f"Generated: {datetime.now().isoformat(timespec='seconds')}\n\n"
                f"PROPERTIES\n{text[:12000]}\n\n"
                f"INSTALLED PACKAGES\n{packages[:12000]}\n\n"
                f"MEMORY\n{mem[:4000]}\n"
            )
            self.analysis_output.setPlainText(report)
            self._log("Создан диагностический отчёт")
        except Exception as exc:
            QMessageBox.critical(self, "Анализ", str(exc))

    def _preview_optimization(self) -> None:
        steps = []
        if self.safe_profile.isChecked():
            steps.append("• Запомнить текущие масштабы анимации")
            steps.append("• Установить 0 для оконных/переходных анимаций")
        if self.cache_profile.isChecked():
            steps.append("• Запросить у Android обрезку кеша до 512 MiB")
        if self.compile_profile.isChecked():
            steps.append("• Запустить штатную компиляцию приложений в speed-profile")
        self.preview_output.setPlainText("\n".join(steps) if steps else "Ничего не выбрано.")
        self._log("Подготовлен план оптимизации")

    def _apply_optimization(self) -> None:
        client = self._client()
        if client is None:
            return
        plan = self.preview_output.toPlainText().strip()
        if not plan or plan.startswith("Изменения появятся") or plan == "Ничего не выбрано.":
            QMessageBox.information(self, "Turbo Mode", "Сначала нажми «Показать план изменений».")
            return
        if QMessageBox.question(self, "Подтверждение", "Применить показанные настройки к подключённому Android TV?") != QMessageBox.Yes:
            return
        try:
            from smarttv_toolkit.optimizer import TvOptimizer
            optimizer = TvOptimizer(client)
            messages = []
            original_scales = optimizer.read_animation_scales()
            if self.safe_profile.isChecked():
                result = optimizer.apply_fast_ui()
                messages.extend(result.changed)
                messages.extend(f"Пропущено: {x}" for x in result.skipped)
                self.animation_restore_values = original_scales
            if self.cache_profile.isChecked():
                messages.append(optimizer.trim_caches() or "Кеш очищен (системная команда завершена)")
            if self.compile_profile.isChecked():
                messages.append(optimizer.compile_apps() or "Команда оптимизации приложений завершена")
            output = "\n".join(messages) or "Изменений не было."
            QMessageBox.information(self, "Turbo Mode завершён", output[:3000])
            self._log("Применена оптимизация")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка оптимизации", str(exc))
            self._log(f"Ошибка оптимизации: {exc}")

    def _restore_animations(self) -> None:
        client = self._client()
        if client is None:
            return
        saved = getattr(self, "animation_restore_values", None)
        try:
            from smarttv_toolkit.optimizer import TvOptimizer
            optimizer = TvOptimizer(client)
            result = optimizer.restore_ui(saved)
            QMessageBox.information(self, "Восстановление", "\n".join(result.changed + result.skipped))
            self._log("Восстановлены настройки анимации")
        except Exception as exc:
            QMessageBox.critical(self, "Восстановление", str(exc))

    def _scan_apps(self) -> None:
        client = self._client()
        if client is None:
            return
        try:
            output = client.shell("pm list packages")
            self.apps_list.clear()
            for line in output.splitlines():
                package = line.strip().removeprefix("package:")
                if package:
                    self.apps_list.addItem(package)
            self._log(f"Список пакетов получен: {self.apps_list.count()}")
        except Exception as exc:
            QMessageBox.critical(self, "Приложения", str(exc))

    def _show_selected_app(self) -> None:
        item = self.apps_list.currentItem()
        if not item:
            QMessageBox.information(self, "Приложения", "Сначала выбери приложение.")
            return
        QMessageBox.information(self, "Пакет приложения", item.text())

    def _run_shell(self) -> None:
        client = self._client()
        if client is None:
            return
        command = self.shell_command.text().strip()
        if not command:
            return
        # This diagnostic console accepts a small explicit allow-list only.
        allowed = ("getprop", "pm list packages", "settings get ", "dumpsys meminfo", "df -h", "cat /proc/meminfo")
        if not command.startswith(allowed):
            QMessageBox.warning(self, "Ограничение", "Разрешены только диагностические команды из списка в README.")
            return
        try:
            self.shell_output.setPlainText(client.shell(command))
            self._log(f"Выполнена команда: {command}")
        except Exception as exc:
            QMessageBox.critical(self, "ADB Shell", str(exc))

    def _quick_action(self, action: str) -> None:
        if action == "Создать резервную копию":
            self._export_report()
        elif action == "Открыть ADB Shell":
            self._show_page("Инструменты")
        elif action == "Перезагрузить устройство":
            QMessageBox.information(self, "Перезагрузка", "Эта функция будет включена после отдельной проверки безопасной команды reboot.")
        elif action == "Сделать скриншот":
            QMessageBox.information(self, "Скриншот", "Сначала подключись к устройству. Команда захвата будет добавлена после теста на реальном ТВ.")
        else:
            QMessageBox.information(self, action, "Подключи устройство, чтобы выполнить действие.")

    def _recommendation_action(self, title: str) -> None:
        if "приложения" in title:
            self._show_page("Удаление приложений")
        elif "анимации" in title:
            self._show_page("Оптимизация")
        elif "копию" in title:
            self._show_page("Резервные копии")
        else:
            self._show_page("Анализ системы")

    def _export_report(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "smarttv-toolkit-report.txt", "Text files (*.txt)")
        if not path:
            return
        text = self.analysis_output.toPlainText() if hasattr(self, "analysis_output") else ""
        if not text.strip():
            text = "SMARTTV TOOLKIT\nReport is empty. Run System Analysis first.\n"
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(text)
            self._log(f"Отчёт сохранён: {path}")
        except OSError as exc:
            QMessageBox.critical(self, "Экспорт", str(exc))
