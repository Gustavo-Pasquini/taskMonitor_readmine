CHECK_INTERVAL   = 30
CUSTOM_ICON_PATH = "icon_2.png"

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
    "Abertas":                     "#f1f5f9",
    "Total":                       "#ffffff",
}

CONFLICT_STATUSES = {
    "Testar", "Testando", "Refazer", "Refazendo", "Fazer", "Nova",
    "Fazendo", "Em andamento", "Analisar", "Impedimento",
    "Impedimento Desenvolvimento", "Aberta",
}

APPROVED_STATUSES = {"Aprovado (subir Units)"}

REFAZER_STATUSES = {"Refazer", "Refazendo"}

METRICS_STATUSES = [
    "Analisar",
    "Fazer",
    "Fazendo",
    "Testar",
    "Testando",
    "Refazer",
    "Refazendo",
    "Aprovado (subir Units)",
]
