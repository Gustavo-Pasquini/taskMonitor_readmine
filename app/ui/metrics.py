import threading
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime, timezone
import app.state as state
import app.api as api
from app.settings import STATUS_COLORS, METRICS_STATUSES, REFAZER_STATUSES

_current_window = None


def _parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _format_duration(seconds):
    if seconds <= 0:
        return "—"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min" if minutes > 0 else "< 1 min"
    hours = int(seconds // 3600)
    days  = hours // 24
    if days == 0:
        return f"{hours}h {int((seconds % 3600) // 60)}min"
    months = days // 30
    if months == 0:
        return f"{days}d {hours % 24}h"
    rem_days = days % 30
    return f"{months}mes {rem_days}d" if rem_days else f"{months} mes"


def _compute_metrics(issue, statuses_by_id):
    created_on     = _parse_dt(issue["created_on"])
    current_status = issue["status"]["name"]
    now            = datetime.now(timezone.utc)

    changes = []
    for j in sorted(issue.get("journals", []), key=lambda x: x["created_on"]):
        for detail in j.get("details", []):
            if detail.get("name") == "status_id":
                changes.append({
                    "dt":  _parse_dt(j["created_on"]),
                    "old": statuses_by_id.get(str(detail.get("old_value", "")), "?"),
                    "new": statuses_by_id.get(str(detail.get("new_value", "")), "?"),
                })

    if not changes:
        segments = [{"status": current_status, "start": created_on, "end": now}]
    else:
        segments = [{"status": changes[0]["old"], "start": created_on, "end": changes[0]["dt"]}]
        for i, ch in enumerate(changes):
            end = changes[i + 1]["dt"] if i + 1 < len(changes) else now
            segments.append({"status": ch["new"], "start": ch["dt"], "end": end})

    time_per    = {}
    entries_per = {}
    for seg in segments:
        name     = seg["status"]
        duration = (seg["end"] - seg["start"]).total_seconds()
        time_per[name]    = time_per.get(name, 0) + max(duration, 0)
        entries_per[name] = entries_per.get(name, 0) + 1

    refazer_count = sum(1 for ch in changes if ch["new"] in REFAZER_STATUSES)
    return time_per, entries_per, refazer_count, current_status


def _close_current():
    global _current_window
    if _current_window:
        try:
            _current_window.destroy()
        except Exception:
            pass
        _current_window = None


def open_metrics(issue_id, issue_title=""):
    global _current_window
    _close_current()

    def _build():
        global _current_window

        win = tk.Toplevel(state.tk_root)
        _current_window = win
        win.title(f"#{issue_id} — Métricas")
        win.attributes("-topmost", True)
        win.configure(bg="#0f172a")
        win.resizable(True, True)
        win.protocol("WM_DELETE_WINDOW", _close_current)
        win.bind("<Escape>", lambda e: _close_current())

        win_w, win_h = 540, 500
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{win_w}x{win_h}+{(sw - win_w) // 2}+{(sh - win_h) // 2}")

        id_f     = tkfont.Font(family="Segoe UI", size=9)
        title_f  = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        header_f = tkfont.Font(family="Segoe UI", size=9,  weight="bold")
        value_f  = tkfont.Font(family="Segoe UI", size=9)
        badge_f  = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        badge_lf = tkfont.Font(family="Segoe UI", size=8)
        cur_f    = tkfont.Font(family="Segoe UI", size=15, weight="bold")
        load_f   = tkfont.Font(family="Segoe UI", size=10)

        hdr = tk.Frame(win, bg="#0f172a", padx=16, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"#{issue_id}", bg="#0f172a", fg="#475569", font=id_f).pack(anchor="w")
        display_title = issue_title if issue_title else f"Tarefa #{issue_id}"
        tk.Label(hdr, text=display_title, bg="#0f172a", fg="#e2e8f0",
                 font=title_f, wraplength=500, justify="left").pack(anchor="w")
        tk.Frame(win, bg="#1e3a5f", height=1).pack(fill="x", padx=16)

        content = tk.Frame(win, bg="#0f172a", padx=16, pady=12)
        content.pack(fill="both", expand=True)

        loading = tk.Label(content, text="Carregando métricas...", bg="#0f172a",
                           fg="#64748b", font=load_f)
        loading.pack(pady=30)

        esc_hint = tk.Label(win, text="ESC para fechar", bg="#0f172a", fg="#334155",
                            font=tkfont.Font(family="Segoe UI", size=8))
        esc_hint.pack(side="bottom", pady=4)

        def _fetch():
            try:
                issue          = api.get_issue_with_journals(issue_id)
                statuses_name  = api.get_statuses()
                statuses_by_id = {str(v): k for k, v in statuses_name.items()}
                result         = _compute_metrics(issue, statuses_by_id)
                state.tk_root.after(0, lambda: _render(*result))
            except Exception as e:
                state.tk_root.after(0, lambda: loading.config(text=f"Erro: {e}", fg="#ef4444"))

        def _render(time_per, entries_per, refazer_count, current_status):
            loading.destroy()
            for w in content.winfo_children():
                w.destroy()

            badges = tk.Frame(content, bg="#0f172a")
            badges.pack(fill="x", pady=(0, 14))

            cur_color = STATUS_COLORS.get(current_status, "#94a3b8")
            cur_card  = tk.Frame(badges, bg="#0c1a2e", padx=18, pady=10)
            cur_card.pack(side="left", padx=(0, 10), fill="both", expand=True)
            tk.Label(cur_card, text="Status atual", bg="#0c1a2e",
                     fg="#475569", font=badge_lf).pack(anchor="center")
            tk.Label(cur_card, text=current_status, bg="#0c1a2e",
                     fg=cur_color, font=cur_f, wraplength=220, justify="center").pack(anchor="center")

            ref_color = "#ef4444" if refazer_count > 0 else "#22c55e"
            ref_bg    = "#2d0a0a"  if refazer_count > 0 else "#052e16"
            ref_card  = tk.Frame(badges, bg=ref_bg, padx=18, pady=10)
            ref_card.pack(side="left", fill="both", expand=True)
            tk.Label(ref_card, text=str(refazer_count), bg=ref_bg,
                     fg=ref_color, font=badge_f).pack()
            tk.Label(ref_card, text="vezes no Refazer", bg=ref_bg,
                     fg=ref_color, font=badge_lf).pack()

            tk.Frame(content, bg="#1e293b", height=1).pack(fill="x", pady=(0, 8))

            th = tk.Frame(content, bg="#0f172a")
            th.pack(fill="x", pady=(0, 4))
            tk.Label(th, text="Status", bg="#0f172a", fg="#475569",
                     font=header_f, anchor="w").pack(side="left", fill="x", expand=True)
            tk.Label(th, text="Tempo total", bg="#0f172a", fg="#475569",
                     font=header_f, width=16, anchor="center").pack(side="left")
            tk.Label(th, text="Entradas", bg="#0f172a", fg="#475569",
                     font=header_f, width=9, anchor="e").pack(side="right")

            tk.Frame(content, bg="#1e293b", height=1).pack(fill="x", pady=(0, 4))

            has_any = False
            for idx, status_name in enumerate(METRICS_STATUSES):
                seconds = time_per.get(status_name, 0)
                entries = entries_per.get(status_name, 0)
                if seconds <= 0 and entries == 0:
                    continue
                has_any = True

                row_bg = "#111827" if idx % 2 == 0 else "#0f172a"
                color  = STATUS_COLORS.get(status_name, "#94a3b8")

                row = tk.Frame(content, bg=row_bg, pady=6, padx=4)
                row.pack(fill="x")

                dot = tk.Canvas(row, width=10, height=10, bg=row_bg, highlightthickness=0)
                dot.create_oval(1, 1, 9, 9, fill=color, outline="")
                dot.pack(side="left", padx=(0, 8))

                tk.Label(row, text=status_name, bg=row_bg, fg="#cbd5e1",
                         font=value_f, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Label(row, text=_format_duration(seconds), bg=row_bg, fg="#94a3b8",
                         font=value_f, width=16, anchor="center").pack(side="left")
                tk.Label(row, text=str(entries), bg=row_bg, fg="#64748b",
                         font=value_f, width=8, anchor="e").pack(side="right")

            if not has_any:
                tk.Label(content, text="Nenhum histórico de status encontrado.",
                         bg="#0f172a", fg="#475569", font=value_f).pack(pady=12)

        threading.Thread(target=_fetch, daemon=True).start()

    state.tk_root.after(0, _build)


def count_refazer_from_journals(issue, statuses_by_id):
    """Utilitário reutilizado por tasks.py para contar refazeres sem abrir janela."""
    return sum(
        1
        for j in issue.get("journals", [])
        for detail in j.get("details", [])
        if detail.get("name") == "status_id"
        and statuses_by_id.get(str(detail.get("new_value", "")), "") in REFAZER_STATUSES
    )
