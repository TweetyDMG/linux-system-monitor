"""Сбор метрик системы через psutil."""

import psutil


class SystemMonitor:
    """Потокобезопасный сборщик метрик CPU через psutil.

    Предоставляет данные о загрузке ЦП, тактовой частоте
    и количестве процессов с ведением скользящей истории.
    """

    MAX_HISTORY = 60

    def __init__(self) -> None:
        self._history: list[float] = []

    # ------------------------------------------------------------------
    # Публичные методы получения метрик
    # ------------------------------------------------------------------

    def get_cpu_percent(self) -> float:
        """Загрузка CPU за последнюю секунду (0–100)."""
        return psutil.cpu_percent(interval=1)

    def get_cpu_freq(self) -> float:
        """Текущая тактовая частота CPU в МГц (0.0 при ошибке)."""
        freq = psutil.cpu_freq()
        return round(freq.current, 1) if freq is not None else 0.0

    def get_process_count(self) -> int:
        """Количество работающих процессов в системе."""
        try:
            return len(list(psutil.process_iter()))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    # ------------------------------------------------------------------
    # Комплексный опрос с сохранением истории
    # ------------------------------------------------------------------

    def poll(self) -> dict:
        """Однократный опрос всех метрик с обновлением скользящего окна.

        Returns:
            dict с ключами cpu_percent, cpu_freq, process_count, history.
        """
        cpu = self.get_cpu_percent()

        self._history.append(cpu)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)

        return {
            "cpu_percent": cpu,
            "cpu_freq": self.get_cpu_freq(),
            "process_count": self.get_process_count(),
            "history": list(self._history),
        }

    @property
    def history(self) -> list[float]:
        """Скользящее окно значений загрузки CPU (до 60 срезов)."""
        return list(self._history)
