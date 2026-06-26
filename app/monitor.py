import time
import threading
import app.state as state
import app.api as api
from app.settings import STATUS_MAP, CHECK_INTERVAL
from app.tray import make_icon


def fetch_tasks():
    try:
        user     = api.get_current_user()
        user_id  = user["id"]
        if not state.current_user:
            state.current_user = user
        statuses = api.get_statuses()

        new_counts = {k: 0 for k in STATUS_MAP}

        for label, status_name in STATUS_MAP.items():
            if status_name.startswith("__"):
                continue
            status_id = statuses.get(status_name)
            if status_id is None:
                continue
            data = api.get_issues(user_id, status_id=status_id, limit=1)
            new_counts[label] = data.get("total_count", 0)

        new_counts["Abertas"] = api.get_issues(user_id, status_id="open", limit=1).get("total_count", 0)
        new_counts["Total"]   = api.get_issues(user_id, status_id="*",    limit=1).get("total_count", 0)

        if any(v > 0 for v in state.task_counts.values()):
            newly_changed = {
                k for k in STATUS_MAP
                if not STATUS_MAP[k].startswith("__") and new_counts[k] != state.task_counts[k]
            }
            if newly_changed:
                state.changed_labels.update(newly_changed)

        state.task_counts = new_counts
        state.last_update = time.strftime("%H:%M:%S")

        if state.tray_icon_ref:
            state.tray_icon_ref.icon = make_icon(alert=bool(state.changed_labels))

    except Exception as e:
        state.last_update = f"Erro {time.strftime('%H:%M:%S')}"
        print(f"[Monitor] ERRO: {e}")


def monitor_loop():
    while True:
        fetch_tasks()
        time.sleep(CHECK_INTERVAL)
