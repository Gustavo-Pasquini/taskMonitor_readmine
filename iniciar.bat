@echo off
chcp 65001 > nul
title Redmine Tray Monitor

echo ==========================================
echo   Redmine Tray Monitor - Configuracao
echo ==========================================
echo.

:: 1. Verificar Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    echo Instale em: https://python.org
    pause
    exit /b 1
)

:: 2. Verificar config.py
if not exist "%~dp0config.py" (
    echo [AVISO] config.py nao encontrado.
    echo Criando a partir do exemplo...
    copy "%~dp0config.exemplo.py" "%~dp0config.py" > nul
    echo.
    echo Abrindo config.py para voce preencher as credenciais...
    notepad "%~dp0config.py"
    echo.
    echo Pressione qualquer tecla apos salvar o config.py para continuar.
    pause > nul
)

:: 3. Instalar dependencias
echo Instalando dependencias...
pip install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

:: 4. Criar atalho na area de trabalho
set "SHORTCUT=%USERPROFILE%\Desktop\Redmine Tray Monitor.lnk"
if not exist "%SHORTCUT%" (
    echo Criando atalho na area de trabalho...
    powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'pythonw'; $s.Arguments = '\"%~dp0redmine_tray.py\"'; $s.IconLocation = '%~dp0icon_2.png'; $s.WorkingDirectory = '%~dp0'; $s.Save()"
    echo Atalho criado.
)

:: 5. Iniciar o app
echo.
echo Iniciando Redmine Tray Monitor...
start "" pythonw "%~dp0redmine_tray.py"
echo App iniciado na bandeja do sistema.
timeout /t 2 > nul
