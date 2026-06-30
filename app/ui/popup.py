import tkinter as tk
from tkinter import font as tkfont
import app.state as state
from app.settings import STATUS_COLORS
from app.tray import make_icon
from app.ui.utils import quit_app


def close_popup():
    if state.popup_window:
        try:
            state.popup_window.destroy()
        except Exception:
            pass
        state.popup_window = None


def open_popup():
    if state.popup_window:
        state.tk_root.after(0, close_popup)
        return

    def _build():
        state.popup_window = tk.Toplevel(state.tk_root)
        w = state.popup_window
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.attributes("-alpha", 0.97)
        w.configure(bg="#0f172a")

        n_items  = len(state.task_counts)
        win_w    = 290
        win_h    = 80 + n_items * 28 + 55
        screen_w = w.winfo_screenwidth()
        screen_h = w.winfo_screenheight()
        w.geometry(f"{win_w}x{win_h}+{screen_w - win_w - 20}+{screen_h - win_h - 60}")

        outer = tk.Frame(w, bg="#1e3a5f", padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg="#0f172a", padx=14, pady=12)
        inner.pack(fill="both", expand=True)

        title_f = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        first_name = state.current_user.get("firstname", "")
        tk.Label(inner, text=f"📋  Tarefas Redmine{' - ' + first_name if first_name else ''}",
                 bg="#0f172a", fg="#e2e8f0", font=title_f, anchor="w").pack(fill="x")
        tk.Frame(inner, bg="#1e3a5f", height=1).pack(fill="x", pady=(6, 8))

        count_f = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        total_f = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        for label, count in state.task_counts.items():
            if label == "Abertas":
                tk.Frame(inner, bg="#1e3a5f", height=1).pack(fill="x", pady=(6, 6))

            color      = STATUS_COLORS.get(label, "#94a3b8")
            has_change = label in state.changed_labels
            is_total   = label in ("Abertas", "Total")

            row = tk.Frame(inner, bg="#0f172a")
            row.pack(fill="x", pady=2)

            if is_total:
                tk.Label(row, text=label + ":", bg="#0f172a", fg=color,
                         font=total_f, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Label(row, text=str(count), bg="#0f172a", fg=color,
                         font=total_f, width=4, anchor="e").pack(side="right")
            else:
                dot_color = "#ef4444" if has_change else color
                dot = tk.Canvas(row, width=10, height=10, bg="#0f172a", highlightthickness=0)
                dot.create_oval(1, 1, 9, 9, fill=dot_color, outline="")
                dot.pack(side="left", padx=(0, 6))

                lbl_font  = tkfont.Font(family="Segoe UI", size=10, weight="bold" if has_change else "normal")
                lbl_color = "#ffffff" if has_change else "#cbd5e1"
                tk.Label(row, text=label, bg="#0f172a", fg=lbl_color,
                         font=lbl_font, anchor="w").pack(side="left", fill="x", expand=True)

                cnt_color = "#ef4444" if has_change else color
                tk.Label(row, text=str(count), bg="#0f172a", fg=cnt_color,
                         font=count_f, width=4, anchor="e").pack(side="right")

        tk.Frame(inner, bg="#1e3a5f", height=1).pack(fill="x", pady=(8, 6))

        foot_f     = tkfont.Font(family="Segoe UI", size=8)
        foot_color = "#22c55e" if "Erro" not in state.last_update else "#ef4444"
        tk.Label(inner, text=f"Atualizado: {state.last_update}", bg="#0f172a",
                 fg=foot_color, font=foot_f, anchor="w").pack(fill="x")

        btn_frame = tk.Frame(inner, bg="#0f172a")
        btn_frame.pack(fill="x", pady=(8, 0))

        btn_f = tkfont.Font(family="Segoe UI", size=8, weight="bold")
        tk.Button(btn_frame, text="✕  Fechar", bg="#1e293b", fg="#94a3b8",
                  font=btn_f, relief="flat", cursor="hand2",
                  command=close_popup).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(btn_frame, text="⏻  Encerrar app", bg="#3f1212", fg="#ef4444",
                  font=btn_f, relief="flat", cursor="hand2",
                  command=quit_app).pack(side="left", fill="x", expand=True)

        w.focus_force()
        state.changed_labels.clear()
        if state.tray_icon_ref:
            state.tray_icon_ref.icon = make_icon(alert=False)

    state.tk_root.after(0, _build)
