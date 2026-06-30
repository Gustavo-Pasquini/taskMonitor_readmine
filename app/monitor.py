import time
import threading
import app.state as state
import app.api as api
import app.settings as settings
from app.settings import CHECK_INTERVAL
from app.tray import make_icon

_MAX_TOASTS_PER_CYCLE = 5


def _detect_transitions(prev_status_by_id, issues):
    """Compara o snapshot anterior com a lista atual e retorna as tarefas
    que mudaram de status (id, titulo, status antigo -> novo)."""
    transitions = []
    for issue in issues:
        issue_id   = issue.get("id")
        new_status = issue.get("status", {}).get("name", "")
        prev       = prev_status_by_id.get(issue_id)
        if prev and prev.get("status") and prev["status"] != new_status:
            transitions.append({
                "id":      issue_id,
                "subject": issue.get("subject", ""),
                "old":     prev["status"],
                "new":     new_status,
            })
    return transitions


def _notify_transitions(transitions):
    if not transitions or not state.tray_icon_ref:
        return

    shown = transitions[:_MAX_TOASTS_PER_CYCLE]
    for t in shown:
        try:
            state.tray_icon_ref.notify(
                f"{t['old']} → {t['new']}\n{t['subject'][:90]}",
                f"Tarefa #{t['id']}",
            )
        except Exception as e:
            print(f"[Monitor] Falha ao notificar: {e}")

    extra = len(transitions) - len(shown)
    if extra > 0:
        try:
            state.tray_icon_ref.notify(
                f"+{extra} outra(s) tarefa(s) tambem mudaram de status",
                "Redmine Tray Monitor",
            )
        except Exception:
            pass


def fetch_tasks():
    try:
        user    = api.get_current_user()
        user_id = user["id"]
        if not state.current_user:
            state.current_user = user

        status_map    = settings.get_status_map()
        name_to_label = {v: k for k, v in status_map.items() if not v.startswith("__")}

        all_issues = api.get_all_issues(user_id, status_id="*")

        new_counts = {k: 0 for k in status_map}
        for issue in all_issues:
            label = name_to_label.get(issue.get("status", {}).get("name", ""))
            if label:
                new_counts[label] += 1

        new_counts["Abertas"] = api.get_issues(user_id, status_id="open", limit=1).get("total_count", 0)
        new_counts["Total"]   = len(all_issues)

        if any(v > 0 for v in state.task_counts.values()):
            newly_changed = {
                k for k in status_map
                if not status_map[k].startswith("__")
                and new_counts.get(k, 0) != state.task_counts.get(k, 0)
            }
            if newly_changed:
                state.changed_labels.update(newly_changed)

        new_status_by_id = {
            issue.get("id"): {
                "status":  issue.get("status", {}).get("name", ""),
                "subject": issue.get("subject", ""),
            }
            for issue in all_issues
        }

        if state.task_status_by_id:
            transitions = _detect_transitions(state.task_status_by_id, all_issues)
            _notify_transitions(transitions)
        state.task_status_by_id = new_status_by_id

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
