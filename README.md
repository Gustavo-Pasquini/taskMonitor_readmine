# Redmine Tray Monitor

App de bandeja (system tray) para Windows que monitora suas tarefas no Redmine em tempo real. Exibe contagens por status, lista todas as tarefas agrupadas, verifica Units/Forms, mostra métricas detalhadas de cada tarefa (tempo por status e quantidade de vezes que foi ao Refazer) e notifica quando uma tarefa muda de status. So permite uma instancia rodando por vez.

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

Use `pythonw` (sem console) ou `python` (com console, útil para ver erros/logs).

#### Opção B — Gerar um executável (.exe)

Requer o PyInstaller instalado (`pip install pyinstaller`):

```bash
pyinstaller redmine_tray.spec --noconfirm
```

O executável é gerado em `dist\redmine_tray.exe`. Ele empacota `icon_2.png` e `config.py`, então **rebuilde sempre que alterar essas credenciais ou o ícone**. Pode copiar o `.exe` para onde quiser (ex: área de trabalho) e rodar direto — o ícone e as credenciais são resolvidos automaticamente, sem depender do diretório de trabalho.

> A configuração de status (`status_map.json`) e gravada do lado do `.exe` em execução, então editar status pela UI (veja [Configuração dos status](#configuracao-dos-status)) **não precisa de rebuild**.

#### Opção C — Usar o `iniciar.bat` (automatizado)

Dê duplo clique no `iniciar.bat`. Ele irá automaticamente:

1. Verificar se o Python está instalado
2. Criar o `config.py` a partir do exemplo (se não existir) e abrir o Notepad para você preencher
3. Instalar as dependências (`pip install -r requirements.txt`)
4. Criar um atalho **"Redmine Tray Monitor"** na área de trabalho
5. Iniciar o app na bandeja do sistema

Nas próximas vezes, use o atalho da área de trabalho diretamente.

#### Opção D — Usar o `build.bat` (recompilar o `.exe`)

Dê duplo clique no `build.bat` sempre que alterar o código e precisar de um novo executável. Ele automaticamente:

1. Encerra qualquer instância do `redmine_tray.exe` em execução
2. Limpa `dist/` e `build/` antigos
3. Roda o PyInstaller (`redmine_tray.spec`)
4. Copia o novo `.exe` para a área de trabalho (`%USERPROFILE%\Desktop\redmine_tray.exe`)
5. Pergunta se deseja iniciar o app na hora

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
| Botao direito > Configurar Status | Abre a janela para editar o mapeamento de status (veja abaixo) |
| Botao direito > Sair | Encerra o app |

| Icone | Significado |
|-------|-------------|
| Normal | Nenhuma mudanca desde a ultima verificacao |
| Com alerta | Houve mudanca em algum status |

Tentar abrir uma segunda instancia (ex: clicar de novo no atalho) mostra um aviso e nao abre uma bandeja duplicada.

### Notificacoes de mudanca de status

Sempre que uma tarefa atribuida a voce mudar de status entre uma verificacao e outra, uma notificacao nativa do Windows aparece com o numero da tarefa e a transicao (ex: `#10310` — `Testando → Refazer`). Se varias tarefas mudarem no mesmo ciclo, as 5 primeiras geram notificacao individual e o restante e resumido em uma notificacao extra.

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

Cada Redmine pode ter nomes de status customizados (foi exatamente isso que causou a tarefa "Fazer" sumir do monitor em uma versao anterior). Em vez de editar codigo e recompilar, use **Botao direito na bandeja > Configurar Status**:

1. Para cada label exibida (Fazer, Fazendo, Testar...), digite o nome exato do status no seu Redmine
2. Clique em **Verificar nomes** para validar contra os status reais do Redmine (campos invalidos ficam destacados em vermelho)
3. Clique em **Salvar** — aplica na proxima atualizacao automatica (ou em "Atualizar agora"), sem precisar reiniciar o app

> Veja os nomes exatos em: **Administracao > Status das issues**, no seu Redmine.

A configuração fica salva em `status_map.json`, ao lado do `.exe` (ou na raiz do projeto, se rodando via `python`/`pythonw`). Esse arquivo é específico de cada máquina e está no `.gitignore`. **Restaurar padrão** apaga essa customização e volta aos valores padrão do código.

> Editar `STATUS_MAP` diretamente em `app/settings.py` (e recompilar) ainda funciona como fallback/padrão de fábrica, mas não é mais necessário no dia a dia.

O intervalo de atualizacao automatica esta definido em `CHECK_INTERVAL = 30` (segundos) em `app/settings.py`.

---

## Iniciar automaticamente com o Windows

1. Pressione `Win + R` e digite `shell:startup`
2. Copie o atalho criado na area de trabalho para essa pasta (ou crie um novo atalho apontando para `redmine_tray.exe` ou para `redmine_tray.py`)

---

## Problemas comuns

| Problema | Solucao |
|----------|---------|
| Icone nao aparece | Verifique se `pystray` e `Pillow` foram instalados |
| Contagens sempre zero | Confirme os nomes dos status em **Configurar Status** (use "Verificar nomes") |
| Erro de conexao | Verifique `SECRET_REDMINE_URL` e se a API REST esta habilitada |
| Chave invalida | Regere a chave em "Minha conta" no Redmine |
| Python nao encontrado | Instale o Python em https://python.org e marque "Add to PATH" |
| Erro ao iniciar com Python 3.13+ | Use Python 3.12 ou inferior — versoes acima nao sao suportadas |
| "App ja esta em execucao" ao abrir | Ja existe uma instancia rodando — procure o icone na bandeja (pode estar oculto no menu de icones ocultos do Windows) |
| Notificacoes nao aparecem | Confira se as notificacoes do Windows estao habilitadas para apps em segundo plano (Configuracoes > Sistema > Notificacoes) |
