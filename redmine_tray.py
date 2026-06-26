"""
Redmine Tray Monitor
"""
import threading
import tkinter as tk
import pystray

import app.state as state
from app.tray import make_icon
from app.monitor import fetch_tasks, monitor_loop
from app.ui.popup import open_popup
from app.ui.forms import open_verify
from app.ui.tasks import open_tasks
from app.ui.utils import quit_app


def main():
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
        pystray.MenuItem("Sair",            lambda i, it: quit_app()),
    )

    icon = pystray.Icon("RedmineTray", make_icon(), "Redmine Monitor", menu)
    state.tray_icon_ref = icon

    threading.Thread(target=icon.run, daemon=True).start()
    state.tk_root.mainloop()


if __name__ == "__main__":
    main()
