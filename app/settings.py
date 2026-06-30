import json
import os
import sys

CHECK_INTERVAL   = 30
CUSTOM_ICON_PATH = "icon_2.png"

# Mapeamento padrao: label exibida -> nome exato do status no Redmine.
# Pode ser sobrescrito em runtime via janela "Configurar Status" (sem
# precisar editar este arquivo nem recompilar o .exe) — veja get_status_map().
_DEFAULT_STATUS_MAP = {
    "Aprovado (subir Units)":      "Aprovado (subir Units)",
    "Testando":                    "Testando",
    "Testar":                      "Testar",
    "Refazendo":                   "Refazendo",
    "Refazer":                     "Refazer",
    "Fazendo":                     "Fazendo",
    "Fazer":                       "Fazer",
    "Analisar":                    "Analisar",
    "Impedimento":                 "Impedimento",
    "Impedimento Desenvolvimento": "Impedimento Desenvolvimento",
    "Gerar Build":                 "Gerar Build",
}

# Entradas especiais (nao sao status reais do Redmine, sao agregados)
_META_ENTRIES = {
    "Abertas": "__ABERTAS__",
    "Total":   "__TOTAL__",
}


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


STATUS_MAP_FILE = os.path.join(_base_dir(), "status_map.json")


def _load_custom_map():
    if not os.path.exists(STATUS_MAP_FILE):
        return None
    try:
        with open(STATUS_MAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            return data
    except Exception:
        pass
    return None


def get_status_map():
    """Status atual (label -> nome no Redmine), incluindo customizacoes
    salvas via UI. Sempre le do disco para refletir mudancas sem precisar
    reiniciar o app."""
    real = _load_custom_map() or dict(_DEFAULT_STATUS_MAP)
    merged = dict(real)
    merged.update(_META_ENTRIES)
    return merged


def save_status_map(mapping):
    """mapping: dict label -> nome exato do status no Redmine (sem Abertas/Total)."""
    clean = {k: v for k, v in mapping.items() if k not in _META_ENTRIES and v}
    with open(STATUS_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)


def reset_status_map():
    try:
        if os.path.exists(STATUS_MAP_FILE):
            os.remove(STATUS_MAP_FILE)
    except Exception:
        pass


# Mantido para compatibilidade com codigo que ainda importa o valor estatico
# (ex: seed inicial de app/state.py). Para dados sempre atualizados, use
# get_status_map().
STATUS_MAP = get_status_map()

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
    "Gerar Build":                 "#14b8a6",
    "Abertas":                     "#f1f5f9",
    "Total":                       "#ffffff",
}

CONFLICT_STATUSES = {
    "Testar", "Testando", "Refazer", "Refazendo", "Fazer",
    "Fazendo", "Em andamento", "Analisar", "Impedimento",
    "Impedimento Desenvolvimento", "Aberta",
}

APPROVED_STATUSES = {"Aprovado (subir Units)"}

REFAZER_STATUSES = {"Refazer"}

METRICS_STATUSES = [
    "Analisar",
    "Fazer",
    "Fazendo",
    "Testar",
    "Testando",
    "Refazer",
    "Refazendo",
    "Aprovado (subir Units)",
    "Gerar Build",
]
