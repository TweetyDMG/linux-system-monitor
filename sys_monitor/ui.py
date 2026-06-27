"""Графический интерфейс системного монитора CPU."""

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import numpy as np
import pyqtgraph as pg

from .monitor import SystemMonitor


class CPUMonitor(QWidget):
    """Главное окно монитора CPU.

    Отображает:
    - текущую загрузку ЦП (%),
    - тактовую частоту (МГц),
    - количество процессов,
    - скользящий график активности за последние 60 с.
    """

    # ── Константы ──────────────────────────────────────────────────
    WINDOW_TITLE = "Системный монитор — ЦП"
    WINDOW_SIZE = (800, 400)

    UPDATE_INTERVAL_MS = 1000  # опрос psutil раз в секунду
    BUFFER_SIZE = 60  # точек на графике
    PLOT_Y_RANGE = (0, 100)

    PLOT_PEN_COLOR = "r"
    PLOT_PEN_WIDTH = 2

    # ── Инициализация ──────────────────────────────────────────────

    def __init__(self) -> None:
        super().__init__()

        self._monitor = SystemMonitor()
        self._running = True
        self._cpu_history: list[float] = []
        self._timer = QTimer(self)

        self._init_ui()
        self._init_timer()

    def _init_ui(self) -> None:
        """Построить компоновку виджетов."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setGeometry(100, 100, *self.WINDOW_SIZE)

        layout = QHBoxLayout()

        # ── Левая панель: текстовая информация ──
        info_layout = QVBoxLayout()
        self._cpu_label = QLabel("Загрузка ЦП: 0%", self)
        self._freq_label = QLabel("Текущая скорость процессора: 0 МГц", self)
        self._proc_label = QLabel("Количество работающих процессов: 0", self)

        info_layout.addWidget(self._cpu_label)
        info_layout.addWidget(self._freq_label)
        info_layout.addWidget(self._proc_label)

        # ── Правая панель: график ──
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.showGrid(x=True, y=True)
        self._plot_widget.setTitle(
            "Активность ЦП",
            size="12pt",
            bold=True,
            italic=False,
            position="top",
            alpha=0.7,
        )

        self._curve = self._plot_widget.plot(
            pen=pg.mkPen(color=self.PLOT_PEN_COLOR, width=self.PLOT_PEN_WIDTH)
        )

        # ── Кнопка Старт / Стоп ──
        self._stop_btn = QPushButton("Стоп")
        self._stop_btn.clicked.connect(self._toggle_running)

        info_layout.addWidget(self._stop_btn)

        layout.addLayout(info_layout)
        layout.addWidget(self._plot_widget)
        self.setLayout(layout)

        self._update_theme()

    def _init_timer(self) -> None:
        """Запустить периодический таймер опроса метрик."""
        self._timer.timeout.connect(self._update_stats)
        self._timer.start(self.UPDATE_INTERVAL_MS)

    # ── Обновление данных ──────────────────────────────────────────

    def _update_stats(self) -> None:
        """Опрос psutil и обновление GUI (вызывается по таймеру)."""
        if not self._running:
            return

        try:
            data = self._monitor.poll()

            self._cpu_history = data["history"]

            self._cpu_label.setText(f"Загрузка ЦП: {data['cpu_percent']}%")
            self._freq_label.setText(
                f"Текущая скорость процессора: {data['cpu_freq']} МГц"
            )
            self._proc_label.setText(
                f"Количество работающих процессов: {data['process_count']}"
            )

            self._update_plot()
        except Exception as exc:
            print(f"[monitor] Ошибка обновления: {exc}")

    def _update_plot(self) -> None:
        """Перерисовать график из актуальной истории."""
        try:
            x = np.arange(len(self._cpu_history))
            y = np.array(self._cpu_history)

            self._curve.setData(x, y)
            self._plot_widget.setYRange(*self.PLOT_Y_RANGE)
        except Exception as exc:
            print(f"[monitor] Ошибка графика: {exc}")

    # ── Управление ─────────────────────────────────────────────────

    def _toggle_running(self) -> None:
        """Приостановить / возобновить сбор метрик."""
        self._running = not self._running
        self._stop_btn.setText("Старт" if not self._running else "Стоп")

        if self._running:
            self._timer.start(self.UPDATE_INTERVAL_MS)
        else:
            self._timer.stop()

    # ── Тема ───────────────────────────────────────────────────────

    def _update_theme(self) -> None:
        """Адаптировать цвета под системную палитру (тёмная / светлая)."""
        palette = QApplication.palette()
        text_color = palette.color(QPalette.WindowText).name()
        bg_color = palette.color(QPalette.Window).name()

        text_style = f"font: 20px; color: {text_color}"
        self._cpu_label.setStyleSheet(text_style)
        self._freq_label.setStyleSheet(text_style)
        self._proc_label.setStyleSheet(text_style)

        self._plot_widget.setBackground(bg_color)
        for axis_name in ("left", "bottom"):
            axis = self._plot_widget.getAxis(axis_name)
            axis.setTextPen(QColor(text_color))
            axis.setPen(QColor(text_color))

    # ── Завершение ─────────────────────────────────────────────────

    def closeEvent(self, event) -> None:  # noqa: N802
        """Остановить таймер при закрытии окна."""
        self._timer.stop()
        event.accept()
