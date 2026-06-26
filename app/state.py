from app.settings import STATUS_MAP

task_counts    = {k: 0 for k in STATUS_MAP}
changed_labels = set()
last_update    = "Nunca"
tray_icon_ref  = None
popup_window   = None
tk_root        = None
current_user   = {}  # preenchido pelo monitor após o primeiro fetch
