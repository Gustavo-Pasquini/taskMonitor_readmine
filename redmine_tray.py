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
CHECK_INTERVAL = 60

# Caminho para sua foto/ícone personalizado (PNG ou JPG, ideal 64x64)
# Coloque o arquivo na mesma pasta do script e ajuste o nome abaixo.
# Se o arquivo não existir, usa o ícone padrão "R".
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
}

# ─────────────────────────────────────────────
# Estado global
# ─────────────────────────────────────────────
task_counts    = {k: 0 for k in STATUS_MAP}
changed_labels = set()   # labels que mudaram desde a última abertura do popup
last_update    = "Nunca"
tray_icon_ref  = None
popup_window   = None
tk_root        = None


# ─────────────────────────────────────────────
# Ícone na bandeja
# ─────────────────────────────────────────────
def make_icon(alert=False):
    """Carrega foto customizada ou gera ícone padrão. Adiciona bolinha vermelha se alert=True."""
    size = 140
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
            draw_e = ImageDraw.Draw(emoji_img)
            fnt_emoji = ImageFont.truetype("seguiemj.ttf", emoji_size - 5)
            draw_e.text((0, 0), "⚠️", font=fnt_emoji, embedded_color=True)
            base.paste(emoji_img, (size - emoji_size, 0), emoji_img) 
        except Exception:
            draw = ImageDraw.Draw(base)
            draw.ellipse([35, 0, 64, 29], fill="#ff0000", outline="white", width=2)

    return base


def _default_icon(size=140):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#1e40af")
    try:
        fnt = ImageFont.truetype("arialbd.ttf", 32)
    except Exception:
        fnt = ImageFont.load_default()
    draw.text((18, 14), "R", fill="white", font=fnt)
    return img


# ─────────────────────────────────────────────
# Popup
# ─────────────────────────────────────────────
def quit_app():
    """Encerra completamente o app."""
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

        # Altura dinâmica conforme número de status
        n_items  = len(STATUS_MAP)
        win_w    = 290
        win_h    = 80 + n_items * 28 + 70
        screen_w = popup_window.winfo_screenwidth()
        screen_h = popup_window.winfo_screenheight()
        px = screen_w - win_w - 20
        py = screen_h - win_h - 60
        popup_window.geometry(f"{win_w}x{win_h}+{px}+{py}")

        outer = tk.Frame(popup_window, bg="#1e3a5f", padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg="#0f172a", padx=14, pady=12)
        inner.pack(fill="both", expand=True)

        # Título
        title_f = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        tk.Label(inner, text="📋  Tarefas Redmine - Murilo", bg="#0f172a", fg="#e2e8f0",
                 font=title_f, anchor="w").pack(fill="x")
        tk.Frame(inner, bg="#1e3a5f", height=1).pack(fill="x", pady=(6, 8))

        row_f   = tkfont.Font(family="Segoe UI", size=10)
        count_f = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        for label, count in task_counts.items():
            color      = STATUS_COLORS.get(label, "#94a3b8")
            has_change = label in changed_labels

            row = tk.Frame(inner, bg="#0f172a")
            row.pack(fill="x", pady=2)

            # Bolinha vermelha se mudou, cor normal caso contrário
            dot_color = "#ef4444" if has_change else color
            dot = tk.Canvas(row, width=10, height=10, bg="#0f172a", highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=dot_color, outline="")
            dot.pack(side="left", padx=(0, 6))

            # Label em negrito e branco se mudou
            lbl_font  = tkfont.Font(family="Segoe UI", size=10, weight="bold" if has_change else "normal")
            lbl_color = "#ffffff" if has_change else "#cbd5e1"
            tk.Label(row, text=label, bg="#0f172a", fg=lbl_color,
                     font=lbl_font, anchor="w").pack(side="left", fill="x", expand=True)

            # Contador vermelho se mudou
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

        # Limpa os alertas após abrir o popup
        changed_labels.clear()
        if tray_icon_ref:
            tray_icon_ref.icon = make_icon(alert=False)

    tk_root.after(0, _build)


# ─────────────────────────────────────────────
# Redmine
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
        print(f"[Redmine] Status encontrados: {list(all_statuses.keys())}")

        new_counts = {k: 0 for k in STATUS_MAP}

        for label, status_name in STATUS_MAP.items():
            status_id = all_statuses.get(status_name)
            if status_id is None:
                print(f"[Redmine] Status '{status_name}' nao encontrado")
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

        # Detecta quais labels mudaram (ignora na primeira execução)
        if any(v > 0 for v in task_counts.values()):
            newly_changed = {k for k in STATUS_MAP if new_counts[k] != task_counts[k]}
            if newly_changed:
                changed_labels.update(newly_changed)
                print(f"[Redmine] Mudanças detectadas: {newly_changed}")

        task_counts = new_counts
        last_update = time.strftime("%H:%M:%S")
        print(f"[Redmine] Atualizado as {last_update}")

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
    print(f"[Redmine Tray] Ícone: {'personalizado ✓ (' + CUSTOM_ICON_PATH + ')' if os.path.exists(CUSTOM_ICON_PATH) else 'padrão (coloque icon.png na pasta para personalizar)'}")
    threading.Thread(target=monitor_loop, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("Ver tarefas", on_show, default=True),
        pystray.MenuItem("Atualizar agora", on_refresh),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Sair", on_quit),
    )

    icon = pystray.Icon("RedmineTray", make_icon(), "Redmine Monitor", menu)
    tray_icon_ref = icon

    threading.Thread(target=icon.run, daemon=True).start()

    tk_root.mainloop()


if __name__ == "__main__":
    main()