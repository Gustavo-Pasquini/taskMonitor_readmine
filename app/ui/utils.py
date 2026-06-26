import os
import app.state as state
from app.settings import STATUS_COLORS


def quit_app():
    try:
        if state.tray_icon_ref:
            state.tray_icon_ref.stop()
    except Exception:
        pass
    try:
        state.tk_root.quit()
        state.tk_root.destroy()
    except Exception:
        pass
    os._exit(0)


def get_status_color(status_name):
    for label, color in STATUS_COLORS.items():
        if label.lower() in status_name.lower() or status_name.lower() in label.lower():
            return color
    return "#94a3b8"
