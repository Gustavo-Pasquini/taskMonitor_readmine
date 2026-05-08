# 📋 Redmine Tray Monitor

App de bandeja (system tray) para Windows que monitora suas tarefas no Redmine e exibe um resumo por status ao clicar no ícone.

---

## 🚀 Como instalar e configurar

### 1. Pré-requisitos
- Python 3.8+ instalado → https://python.org
- Redmine rodando em localhost com API REST habilitada

### 2. Habilitar a API do Redmine
No seu Redmine:
1. Acesse **Administração → Configurações → API**
2. Marque **"Habilitar API REST"**
3. Salve

### 3. Obter sua chave de API
1. Acesse seu Redmine
2. Clique no seu **nome de usuário** (canto superior direito)
3. Vá em **"Minha conta"**
4. Role até **"Chave de acesso API"** e copie a chave

### 4. Configurar o arquivo `redmine_tray.py`

Abra o arquivo e edite as linhas no topo:

```python
REDMINE_URL = "http://localhost"   # ou http://localhost:3000 conforme sua porta
API_KEY     = "cole_sua_chave_aqui"
CHECK_INTERVAL = 60                # segundos entre verificações
```

### 5. Ajustar os nomes dos status

Cada Redmine tem nomes de status customizados. Edite o dicionário `STATUS_MAP`
para corresponder exatamente aos nomes dos status no **seu** Redmine:

```python
STATUS_MAP = {
    "Aprovadas":   "Aprovada",      # label exibida → nome exato no Redmine
    "Fazendo":     "Em andamento",
    "Fazer":       "Nova",
    # ...
}
```

> **Dica:** Veja os nomes exatos em **Administração → Status das issues**

### 6. Instalar dependências e iniciar

**Opção A — Duplo clique:**
```
iniciar.bat
```

**Opção B — Manual:**
```bash
pip install -r requirements.txt
pythonw redmine_tray.py
```

> Use `pythonw` (sem janela de console) para rodar em background.

---

## 🖱️ Como usar

| Ação | Resultado |
|------|-----------|
| **Clique simples** no ícone | Abre popup com contagem por status |
| **Botão direito** → "Atualizar" | Força atualização imediata |
| **Botão direito** → "Sair" | Encerra o app |
| Ícone **azul** | Tudo normal |
| Ícone **vermelho** com bolinha | Houve mudanças desde a última verificação |

---

## ▶️ Iniciar automaticamente com o Windows

1. Pressione `Win + R` e digite `shell:startup`
2. Crie um atalho do arquivo `redmine_tray.py` nesta pasta
3. No atalho, mude o **"Programa"** para `pythonw.exe` e o argumento para o caminho completo do `.py`

Ou crie um arquivo `autostart.bat` na pasta Startup:
```batch
start /B pythonw "C:\caminho\para\redmine_tray.py"
```

---

## 🐛 Problemas comuns

| Problema | Solução |
|----------|---------|
| Ícone não aparece | Verifique se `pystray` e `Pillow` foram instalados |
| Contagens sempre zero | Confirme os nomes dos status em `STATUS_MAP` |
| Erro de conexão | Verifique `REDMINE_URL` e se a API REST está habilitada |
| Chave inválida | Regere a chave em "Minha conta" no Redmine |
