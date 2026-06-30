"""
Redmine Tray Monitor
"""
import ctypes
import sys
import threading
import tkinter as tk
import pystray

import app.state as state
from app.tray import make_icon
from app.monitor import fetch_tasks, monitor_loop
from app.ui.popup import open_popup
from app.ui.forms import open_verify
from app.ui.tasks import open_tasks
from app.ui.status_config import open_status_config
from app.ui.utils import quit_app

_MUTEX_NAME           = "Global\\RedmineTrayMonitor_SingleInstance"
_ERROR_ALREADY_EXISTS = 183


def _ensure_single_instance():
    """Impede abrir uma segunda instancia. Retorna o handle do mutex
    (precisa ficar vivo ate o processo encerrar) ou None se nao for Windows."""
    try:
        kernel32 = ctypes.windll.kernel32
        mutex    = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if kernel32.GetLastError() == _ERROR_ALREADY_EXISTS:
            ctypes.windll.user32.MessageBoxW(
                None,
                "O Redmine Tray Monitor ja esta em execucao.\nVerifique o icone na bandeja do sistema.",
                "Redmine Tray Monitor",
                0x40,  # MB_ICONINFORMATION
            )
            sys.exit(0)
        return mutex
    except Exception:
        return None


def main():
    _single_instance_mutex = _ensure_single_instance()  # noqa: F841 (mantem o handle vivo)

    state.tk_root = tk.Tk()
    state.tk_root.withdraw()
    state.tk_root.title("RedmineTray")

    threading.Thread(target=monitor_loop, daemon=True).start()

    def _refresh(icon, item):
        threading.Thread(target=fetch_tasks, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("Ver tarefas",     lambda i, it: open_popup(),   default=True),
        pystray.MenuItem("Verificar Forms", lambda i, it: open_verify()),
        pystray.MenuItem("Listar Tarefas",  lambda i, it: open_tasks()),
        pystray.MenuItem("Atualizar agora", _refresh),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Configurar Status", lambda i, it: open_status_config()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Sair",            lambda i, it: quit_app()),
    )

    icon = pystray.Icon("RedmineTray", make_icon(), "Redmine Monitor", menu)
    state.tray_icon_ref = icon

    threading.Thread(target=icon.run, daemon=True).start()
    state.tk_root.mainloop()


if __name__ == "__main__":
    main()
