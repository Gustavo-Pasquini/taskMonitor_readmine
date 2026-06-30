# Redmine Tray Monitor

App de bandeja (system tray) para Windows que monitora suas tarefas no Redmine em tempo real. Exibe contagens por status, lista todas as tarefas agrupadas, verifica Units/Forms e mostra métricas detalhadas de cada tarefa (tempo por status e quantidade de vezes que foi ao Refazer).

---

## Requisitos

- Windows 10 ou superior
- Python 3.8 até 3.12 — https://python.org (**Python 3.13+ não é suportado**)
- Redmine com API REST habilitada

---

## Instalação e primeiro uso

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd taskMonitor_readmine
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure suas credenciais

Crie o arquivo `config.py` a partir do exemplo:

```bash
copy config.exemplo.py config.py
```

Edite o `config.py` com seus dados:

```python
SECRET_REDMINE_URL = "http://localhost:3000"   # URL do seu Redmine
SECRET_API_KEY     = "sua_chave_aqui"          # Chave de API do Redmine
```

> Para obter a chave: acesse seu Redmine > nome de usuário > **Minha conta** > **Chave de acesso API**

> `config.py` está no `.gitignore` — nunca commite suas credenciais.

### 4. Escolha como executar

#### Opção A — Rodar direto via linha de comando (sem gerar executável)

```bash
pythonw redmine_tray.py
```

Use `pythonw` (sem console) ou `python` (com console, útil para ver erros/logs). Execute sempre a partir da raiz do projeto, pois o app lê `config.py` e `icon.png` por caminho relativo.

#### Opção B — Gerar um executável (.exe)

Requer o PyInstaller instalado (`pip install pyinstaller`):

```bash
pyinstaller redmine_tray.spec --noconfirm
```

O executável é gerado em `dist\redmine_tray.exe`. Ele empacota `icon.png` e `config.py`, então **rebuilde sempre que alterar essas credenciais ou o ícone**. Copie o `.exe` para onde quiser (ex: área de trabalho) — mas rode-o com o diretório de trabalho apontando para a raiz do projeto (ex: via atalho com "Iniciar em"), pois o ícone do tray é resolvido por caminho relativo a `icon.png`.

#### Opção C — Usar o `iniciar.bat` (automatizado)

Dê duplo clique no `iniciar.bat`. Ele irá automaticamente:

1. Verificar se o Python está instalado
2. Criar o `config.py` a partir do exemplo (se não existir) e abrir o Notepad para você preencher
3. Instalar as dependências (`pip install -r requirements.txt`)
4. Criar um atalho **"Redmine Tray Monitor"** na área de trabalho
5. Iniciar o app na bandeja do sistema

Nas próximas vezes, use o atalho da área de trabalho diretamente.

---

## Como usar

### Ícone na bandeja

| Acao | Resultado |
|------|-----------|
| Clique duplo no icone | Abre popup com contagem por status |
| Botao direito > Ver tarefas | Abre popup com contagem por status |
| Botao direito > Verificar Forms | Abre janela de Units/Forms com tarefas |
| Botao direito > Listar Tarefas | Lista todas as tarefas agrupadas por status (clicavel) |
| Botao direito > Atualizar agora | Forca atualizacao imediata |
| Botao direito > Sair | Encerra o app |

| Icone | Significado |
|-------|-------------|
| Normal | Nenhuma mudanca desde a ultima verificacao |
| Com alerta | Houve mudanca em algum status |

### Popup de tarefas

Exibe a contagem de tarefas por status e totalizadores de **Abertas** e **Total**. Status que sofreram alteracao desde a ultima verificacao ficam destacados em vermelho.

### Janela "Listar Tarefas"

Exibe todas as tarefas atribuidas a voce agrupadas por status. Os grupos comecam recolhidos — clique no header do status para expandir. No inicio de cada linha aparece, quando aplicavel, um badge vermelho com o numero de vezes que a tarefa foi ao status Refazer. Clique em qualquer tarefa para abrir as metricas.

### Janela de Metricas

Aberta ao clicar em uma tarefa na listagem. Exibe:

- Quantas vezes a tarefa foi ao status **Refazer**
- Status atual da tarefa (destacado em negrito)
- Tabela com **tempo total** e **quantidade de entradas** em cada status (Analisar, Fazer, Fazendo, Testar, Testando, Refazer, Refazendo, Aprovado)

Apenas uma janela de metricas pode estar aberta por vez. `ESC` fecha a janela.

### Janela "Verificar Forms"

Lista todas as Units/Forms que possuem tarefas atribuidas a voce, agrupadas por form com indicacao visual:

| Badge | Significado |
|-------|-------------|
| Liberada | Todas as tarefas do form estao aprovadas |
| Conflito de tarefas | Ha tarefas em status de bloqueio |
| Em progresso | Tarefas em andamento sem conflito |

---

## Configuracao dos status

Cada Redmine pode ter nomes de status customizados. Edite o dicionario `STATUS_MAP` em `app/settings.py` para corresponder aos nomes exatos do seu Redmine:

```python
STATUS_MAP = {
    "Fazendo":  "Em andamento",   # label exibida -> nome exato no Redmine
    "Fazer":    "A Fazer",
    # ...
}
```

> Veja os nomes exatos em: **Administracao > Status das issues**

O intervalo de atualizacao automatica esta definido em `CHECK_INTERVAL = 30` (segundos) em `app/settings.py`.

---

## Iniciar automaticamente com o Windows

1. Pressione `Win + R` e digite `shell:startup`
2. Copie o atalho criado na area de trabalho para essa pasta (ou crie um novo atalho apontando para `redmine_tray.py`/`redmine_tray.exe`)
3. No atalho, em **Propriedades > Iniciar em**, defina a raiz do projeto (`taskMonitor_readmine`) — necessario para o app encontrar `icon.png` e `config.py` por caminho relativo

---

## Problemas comuns

| Problema | Solucao |
|----------|---------|
| Icone nao aparece | Verifique se `pystray` e `Pillow` foram instalados |
| Contagens sempre zero | Confirme os nomes dos status em `STATUS_MAP` |
| Erro de conexao | Verifique `SECRET_REDMINE_URL` e se a API REST esta habilitada |
| Chave invalida | Regere a chave em "Minha conta" no Redmine |
| Python nao encontrado | Instale o Python em https://python.org e marque "Add to PATH" |
| Erro ao iniciar com Python 3.13+ | Use Python 3.12 ou inferior — versoes acima nao sao suportadas |
