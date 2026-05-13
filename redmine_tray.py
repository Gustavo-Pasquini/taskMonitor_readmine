"""
Monitor de tarefas do Redmine 
====================
App de bandeja (system tray) que monitora suas tarefas no Redmine.
Botao direito > Ver Tarefas (ou clique duplo) para abrir o popup.
"""

import threading
import time
import requests
import tkinter as tk
from tkinter import font as tkfont
import pystray
from PIL import Image, ImageDraw, ImageFont
import os
from config import SECRET_REDMINE_URL, SECRET_API_KEY

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────
REDMINE_URL    = SECRET_REDMINE_URL
API_KEY        = SECRET_API_KEY
CHECK_INTERVAL = 30

CUSTOM_ICON_PATH = "icon.png"

STATUS_MAP = {
    "Aprovado (subir Units)":      "Aprovado (subir Units)",
    "Testando":                    "Testando",
    "Testar":                      "Testar",
    "Refazendo":                   "Refazendo",
    "Refazer":                     "Refazer",
    "Fazendo":                     "Fazendo",
    "Fazer":                       "Nova",
    "Analisar":                    "Analisar",
    "Impedimento":                 "Impedimento",
    "Impedimento Desenvolvimento": "Impedimento Desenvolvimento",
    # ── Totalizadores ──
    "Abertas":                     "__ABERTAS__",
    "Total":                       "__TOTAL__",
}

STATUS_COLORS = {
    "Aprovado (subir Units)":      "#22c55e",
    "Testando":                    "#3b82f6",
    "Testar":                      "#0ea5e9",
    "Refazendo":                   "#f97316",
    "Refazer":                     "#ef4444",
    "Fazendo":                     "#a855f7",
    "Fazer":                       "#64748b",
    "Analisar":                    "#eab308",
    "Impedimento":                 "#dc2626",
    "Impedimento Desenvolvimento": "#dc2626",
    # ── Totalizadores ──
    "Abertas":                     "#f1f5f9",
    "Total":                       "#ffffff",
}

# ─────────────────────────────────────────────
# Estado global
# ─────────────────────────────────────────────
task_counts    = {k: 0 for k in STATUS_MAP}
changed_labels = set()
last_update    = "Nunca"
tray_icon_ref  = None
popup_window   = None
tk_root        = None


# ─────────────────────────────────────────────
# Ícone na bandeja
# ─────────────────────────────────────────────
def make_icon(alert=False):
    size       = 140
    emoji_size = 80

    if os.path.exists(CUSTOM_ICON_PATH):
        try:
            base = Image.open(CUSTOM_ICON_PATH).convert("RGBA").resize((size, size), Image.LANCZOS)
        except Exception:
            base = _default_icon(size)
    else:
        base = _default_icon(size)

    if alert:
        try:
            emoji_img = Image.new("RGBA", (emoji_size, emoji_size), (0, 0, 0, 0))
            draw_e    = ImageDraw.Draw(emoji_img)
            fnt_emoji = ImageFont.truetype("seguiemj.ttf", emoji_size - 5)
            draw_e.text((0, 0), "⚠️", font=fnt_emoji, embedded_color=True)
            base.paste(emoji_img, (size - emoji_size, 0), emoji_img)
        except Exception:
            draw = ImageDraw.Draw(base)
            draw.ellipse([95, 0, 140, 45], fill="#ff0000", outline="white", width=2)

    return base


def _default_icon(size=140):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#1e40af")
    try:
        fnt = ImageFont.truetype("arialbd.ttf", 48)
    except Exception:
        fnt = ImageFont.load_default()
    draw.text((30, 30), "R", fill="white", font=fnt)
    return img


# ─────────────────────────────────────────────
# Popup principal
# ─────────────────────────────────────────────
def quit_app():
    try:
        if tray_icon_ref:
            tray_icon_ref.stop()
    except Exception:
        pass
    try:
        tk_root.quit()
        tk_root.destroy()
    except Exception:
        pass
    os._exit(0)


def close_popup():
    global popup_window
    if popup_window:
        try:
            popup_window.destroy()
        except Exception:
            pass
        popup_window = None


def open_popup():
    global popup_window, tk_root, changed_labels

    if popup_window:
        tk_root.after(0, close_popup)
        return

    def _build():
        global popup_window

        popup_window = tk.Toplevel(tk_root)
        popup_window.overrideredirect(True)
        popup_window.attributes("-topmost", True)
        popup_window.attributes("-alpha", 0.97)
        popup_window.configure(bg="#0f172a")

        n_items  = len(STATUS_MAP)
        win_w    = 290
        win_h    = 80 + n_items * 28 + 55  # +20 para o separador dos totalizadores
        screen_w = popup_window.winfo_screenwidth()
        screen_h = popup_window.winfo_screenheight()
        px = screen_w - win_w - 20
        py = screen_h - win_h - 60
        popup_window.geometry(f"{win_w}x{win_h}+{px}+{py}")

        outer = tk.Frame(popup_window, bg="#1e3a5f", padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg="#0f172a", padx=14, pady=12)
        inner.pack(fill="both", expand=True)

        title_f = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        tk.Label(inner, text="📋  Tarefas Redmine - Murilo", bg="#0f172a", fg="#e2e8f0",
                 font=title_f, anchor="w").pack(fill="x")
        tk.Frame(inner, bg="#1e3a5f", height=1).pack(fill="x", pady=(6, 8))

        row_f   = tkfont.Font(family="Segoe UI", size=10)
        count_f = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        total_f = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        for label, count in task_counts.items():

            # Separador visual antes dos totalizadores
            if label == "Abertas":
                tk.Frame(inner, bg="#1e3a5f", height=1).pack(fill="x", pady=(6, 6))

            color      = STATUS_COLORS.get(label, "#94a3b8")
            has_change = label in changed_labels
            is_total   = label in ("Abertas", "Total")

            row = tk.Frame(inner, bg="#0f172a")
            row.pack(fill="x", pady=2)

            if is_total:
                # Totalizadores: sem bolinha, label maior e destacada
                tk.Label(row, text=label + ":", bg="#0f172a", fg=color,
                         font=total_f, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Label(row, text=str(count), bg="#0f172a", fg=color,
                         font=total_f, width=4, anchor="e").pack(side="right")
            else:
                # Status normais
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
        foot_color = "#22c55e" if "Erro" not in last_update else "#ef4444"
        tk.Label(inner, text=f"Atualizado: {last_update}", bg="#0f172a",
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

        popup_window.focus_force()

        changed_labels.clear()
        if tray_icon_ref:
            tray_icon_ref.icon = make_icon(alert=False)

    tk_root.after(0, _build)


# ─────────────────────────────────────────────
# Tela Verificar Tarefas por Unit/Form
# ─────────────────────────────────────────────
verify_window = None

CONFLICT_STATUSES = {
    "Testar", "Testando", "Refazer", "Refazendo", "Fazer", "Nova",
    "Fazendo", "Em andamento", "Analisar", "Impedimento",
    "Impedimento Desenvolvimento", "Aberta",
}
APPROVED_STATUSES = {"Aprovado (subir Units)"}


def close_verify():
    global verify_window
    if verify_window:
        try:
            verify_window.destroy()
        except Exception:
            pass
        verify_window = None


def _get_status_color(status_name):
    for label, color in STATUS_COLORS.items():
        if label.lower() in status_name.lower() or status_name.lower() in label.lower():
            return color
    return "#94a3b8"


def open_verify():
    global verify_window, tk_root

    if verify_window:
        tk_root.after(0, close_verify)
        return

    def _build():
        global verify_window

        verify_window = tk.Toplevel(tk_root)
        verify_window.title("Verificar Tarefas por Unit/Form — Murilo Varoto")
        verify_window.attributes("-topmost", True)
        verify_window.configure(bg="#0f172a")
        verify_window.resizable(True, True)
        verify_window.protocol("WM_DELETE_WINDOW", close_verify)

        win_w, win_h = 980, 620
        screen_w = verify_window.winfo_screenwidth()
        screen_h = verify_window.winfo_screenheight()
        px = (screen_w - win_w) // 2
        py = (screen_h - win_h) // 2
        verify_window.geometry(f"{win_w}x{win_h}+{px}+{py}")

        title_f  = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        header_f = tkfont.Font(family="Segoe UI", size=9,  weight="bold")
        small_f  = tkfont.Font(family="Segoe UI", size=9)
        btn_f    = tkfont.Font(family="Segoe UI", size=9,  weight="bold")

        # Topo
        top = tk.Frame(verify_window, bg="#0f172a", padx=16, pady=14)
        top.pack(fill="x")
        tk.Label(top, text="🔍  Units / Forms com tarefas — Murilo Varoto",
                 bg="#0f172a", fg="#e2e8f0", font=title_f).pack(side="left")
        btn_refresh = tk.Button(top, text="🔄  Atualizar", font=btn_f,
                                bg="#1e40af", fg="white", relief="flat",
                                cursor="hand2", padx=12, pady=4)
        btn_refresh.pack(side="right")

        # Barra de status
        status_bar = tk.Frame(verify_window, bg="#0f172a", padx=16, pady=4)
        status_bar.pack(fill="x")
        status_lbl = tk.Label(status_bar, text="", bg="#0f172a",
                              font=tkfont.Font(family="Segoe UI", size=10, weight="bold"))
        status_lbl.pack(side="left")
        loading_lbl = tk.Label(status_bar, text="", bg="#0f172a",
                               font=tkfont.Font(family="Segoe UI", size=9), fg="#64748b")
        loading_lbl.pack(side="right")

        # Área com scroll
        outer = tk.Frame(verify_window, bg="#0f172a", padx=16, pady=8)
        outer.pack(fill="both", expand=True)
        canvas    = tk.Canvas(outer, bg="#0f172a", highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = tk.Frame(canvas, bg="#0f172a")
        canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        def do_load():
            for w in content.winfo_children():
                w.destroy()
            status_lbl.config(text="🔄  Buscando tarefas...", fg="#94a3b8")
            loading_lbl.config(text="")
            verify_window.update()

            def _fetch():
                try:
                    headers  = {"X-Redmine-API-Key": API_KEY}
                    me       = requests.get(f"{REDMINE_URL}/users/current.json", headers=headers, timeout=10)
                    me.raise_for_status()
                    user_id  = me.json()["user"]["id"]

                    all_issues = []
                    offset = 0
                    while True:
                        r = requests.get(
                            f"{REDMINE_URL}/issues.json",
                            headers=headers,
                            params={"assigned_to_id": user_id, "status_id": "*", "limit": 100, "offset": offset},
                            timeout=15,
                        )
                        r.raise_for_status()
                        data   = r.json()
                        issues = data.get("issues", [])
                        all_issues.extend(issues)
                        if len(all_issues) >= data.get("total_count", 0):
                            break
                        offset += 100

                    # Agrupa por Units/Forms (cf id=8)
                    form_map = {}
                    for issue in all_issues:
                        cf = next((f for f in issue.get("custom_fields", []) if f["id"] == 8), None)
                        if not cf or not cf.get("value", "").strip():
                            continue
                        forms = [f.strip() for f in cf["value"].split("\n") if f.strip()]
                        for form in forms:
                            form_map.setdefault(form, []).append(issue)

                    tk_root.after(0, lambda: _render(all_issues, form_map))
                except Exception as e:
                    tk_root.after(0, lambda: status_lbl.config(text=f"❌  Erro: {e}", fg="#ef4444"))

            threading.Thread(target=_fetch, daemon=True).start()

        def _render(all_issues, form_map):
            for w in content.winfo_children():
                w.destroy()

            if not form_map:
                status_lbl.config(text="Nenhuma tarefa com Unit/Form encontrada.", fg="#ef4444")
                return

            def sort_key(item):
                _, iss = item
                statuses = [i.get("status", {}).get("name", "") for i in iss]
                has_conf = any(s in CONFLICT_STATUSES for s in statuses)
                return (0 if has_conf else 1, item[0])

            sorted_forms = sorted(form_map.items(), key=sort_key)
            total_lib    = sum(1 for _, iss in sorted_forms
                               if all(i.get("status", {}).get("name", "") in APPROVED_STATUSES for i in iss))
            total_conf   = len(sorted_forms) - total_lib

            status_lbl.config(
                text=f"📦  {len(sorted_forms)} forms  |  ✅ {total_lib} liberados  |  ⚠️ {total_conf} com conflito",
                fg="#e2e8f0",
            )
            loading_lbl.config(text=f"{len(all_issues)} tarefas carregadas")

            for form_name, form_issues in sorted_forms:
                statuses = [i.get("status", {}).get("name", "") for i in form_issues]
                all_appr = all(s in APPROVED_STATUSES for s in statuses)
                has_conf = any(s in CONFLICT_STATUSES for s in statuses)

                if all_appr:
                    badge_text, badge_color, header_bg = "✅  Liberada",             "#22c55e", "#052e16"
                elif has_conf:
                    badge_text, badge_color, header_bg = "⚠️  Conflito de tarefas", "#ef4444", "#2d0a0a"
                else:
                    badge_text, badge_color, header_bg = "🔵  Em progresso",        "#3b82f6", "#0c1a2e"

                card = tk.Frame(content, bg="#111827")
                card.pack(fill="x", pady=(0, 6))

                ch = tk.Frame(card, bg=header_bg, padx=10, pady=6)
                ch.pack(fill="x")
                tk.Label(ch, text=form_name, bg=header_bg, fg="#e2e8f0",
                         font=header_f, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Label(ch, text=badge_text, bg=header_bg, fg=badge_color,
                         font=header_f).pack(side="right")

                for idx, issue in enumerate(form_issues):
                    row_bg      = "#111827" if idx % 2 == 0 else "#0f172a"
                    status_name = issue.get("status", {}).get("name", "—")
                    s_color     = _get_status_color(status_name)
                    updated     = issue.get("updated_on", "")[:16].replace("T", " ")

                    row = tk.Frame(card, bg=row_bg, padx=10, pady=3)
                    row.pack(fill="x")
                    tk.Label(row, text=f"#{issue.get('id')}",
                             bg=row_bg, fg="#64748b", font=small_f, width=7, anchor="w").pack(side="left")
                    tk.Label(row, text=issue.get("subject", "")[:70],
                             bg=row_bg, fg="#cbd5e1", font=small_f, anchor="w").pack(side="left", fill="x", expand=True)
                    tk.Label(row, text=updated,
                             bg=row_bg, fg="#475569", font=small_f, width=17, anchor="e").pack(side="right")
                    tk.Label(row, text=status_name,
                             bg=row_bg, fg=s_color, font=small_f, width=24, anchor="e").pack(side="right")

        btn_refresh.config(command=do_load)
        verify_window.after(100, do_load)

    tk_root.after(0, _build)


# ─────────────────────────────────────────────
# Redmine — busca de tarefas
# ─────────────────────────────────────────────
def fetch_tasks():
    global task_counts, last_update, changed_labels

    headers = {"X-Redmine-API-Key": API_KEY}

    try:
        me = requests.get(f"{REDMINE_URL}/users/current.json", headers=headers, timeout=10)
        me.raise_for_status()
        user_id = me.json()["user"]["id"]
        print(f"[Redmine] Usuário ID: {user_id}")

        st = requests.get(f"{REDMINE_URL}/issue_statuses.json", headers=headers, timeout=10)
        st.raise_for_status()
        all_statuses = {s["name"]: s["id"] for s in st.json()["issue_statuses"]}
        print(f"[Redmine] Status: {list(all_statuses.keys())}")

        new_counts = {k: 0 for k in STATUS_MAP}

        # Contagem por status
        for label, status_name in STATUS_MAP.items():
            if status_name.startswith("__"):
                continue  # totalizadores calculados depois
            status_id = all_statuses.get(status_name)
            if status_id is None:
                print(f"[Redmine] Status '{status_name}' não encontrado")
                continue
            r = requests.get(
                f"{REDMINE_URL}/issues.json",
                headers=headers,
                params={"assigned_to_id": user_id, "status_id": status_id, "limit": 1},
                timeout=10,
            )
            r.raise_for_status()
            new_counts[label] = r.json().get("total_count", 0)
            print(f"[Redmine] {label}: {new_counts[label]}")

        # Totalizadores
        r_open = requests.get(
            f"{REDMINE_URL}/issues.json",
            headers=headers,
            params={"assigned_to_id": user_id, "status_id": "open", "limit": 1},
            timeout=10,
        )
        r_open.raise_for_status()
        new_counts["Abertas"] = r_open.json().get("total_count", 0)

        r_total = requests.get(
            f"{REDMINE_URL}/issues.json",
            headers=headers,
            params={"assigned_to_id": user_id, "status_id": "*", "limit": 1},
            timeout=10,
        )
        r_total.raise_for_status()
        new_counts["Total"] = r_total.json().get("total_count", 0)

        print(f"[Redmine] Abertas: {new_counts['Abertas']} | Total: {new_counts['Total']}")

        # Detecta mudanças (ignora primeira execução)
        if any(v > 0 for v in task_counts.values()):
            newly_changed = {
                k for k in STATUS_MAP
                if not STATUS_MAP[k].startswith("__") and new_counts[k] != task_counts[k]
            }
            if newly_changed:
                changed_labels.update(newly_changed)
                print(f"[Redmine] Mudanças: {newly_changed}")

        task_counts = new_counts
        last_update = time.strftime("%H:%M:%S")
        print(f"[Redmine] Atualizado às {last_update}")

        if tray_icon_ref:
            tray_icon_ref.icon = make_icon(alert=bool(changed_labels))

    except Exception as e:
        print(f"[Redmine] ERRO: {e}")
        last_update = f"Erro {time.strftime('%H:%M:%S')}"


def monitor_loop():
    while True:
        fetch_tasks()
        time.sleep(CHECK_INTERVAL)


# ─────────────────────────────────────────────
# Tray
# ─────────────────────────────────────────────
def on_show(icon, item):
    open_popup()


def on_verify(icon, item):
    open_verify()


def on_refresh(icon, item):
    threading.Thread(target=fetch_tasks, daemon=True).start()


def on_quit(icon, item):
    quit_app()


def main():
    global tray_icon_ref, tk_root

    tk_root = tk.Tk()
    tk_root.withdraw()
    tk_root.title("RedmineTray")

    print("[Redmine Tray] Iniciando...")
    print(f"[Redmine Tray] Ícone: {'personalizado ✓ (' + CUSTOM_ICON_PATH + ')' if os.path.exists(CUSTOM_ICON_PATH) else 'padrão'}")
    threading.Thread(target=monitor_loop, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("Ver tarefas",      on_show,    default=True),
        pystray.MenuItem("Verificar Forms",  on_verify),
        pystray.MenuItem("Atualizar agora",  on_refresh),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Sair",             on_quit),
    )

    icon = pystray.Icon("RedmineTray", make_icon(), "Redmine Monitor", menu)
    tray_icon_ref = icon

    threading.Thread(target=icon.run, daemon=True).start()

    tk_root.mainloop()


if __name__ == "__main__":
    main()