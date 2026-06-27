"""Точка входа: python -m sys_monitor"""

import sys

from PyQt5.QtWidgets import QApplication

from .ui import CPUMonitor


def main() -> None:
    """Запустить GUI приложение системного монитора."""
    app = QApplication(sys.argv)
    monitor = CPUMonitor()
    monitor.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
