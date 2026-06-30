@echo off
chcp 65001 > nul
title Build - Redmine Tray Monitor

echo ==========================================
echo   Build - Redmine Tray Monitor
echo ==========================================
echo.

set "DEST=%USERPROFILE%\Desktop\redmine_tray.exe"

echo Encerrando instancia em execucao (se houver)...
taskkill /F /IM redmine_tray.exe > nul 2>&1

echo Limpando builds antigos...
if exist "%~dp0dist" rmdir /s /q "%~dp0dist"
if exist "%~dp0build" rmdir /s /q "%~dp0build"

echo Verificando PyInstaller...
python -m PyInstaller --version > nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller --quiet
)

echo.
echo Compilando...
python -m PyInstaller "%~dp0redmine_tray.spec" --noconfirm
if errorlevel 1 (
    echo [ERRO] Falha ao compilar.
    pause
    exit /b 1
)

echo.
echo Copiando para a area de trabalho...
copy /Y "%~dp0dist\redmine_tray.exe" "%DEST%" > nul
if errorlevel 1 (
    echo [ERRO] Falha ao copiar para "%DEST%".
    pause
    exit /b 1
)

echo.
echo Build concluido: %DEST%
echo.

set /p ANSWER="Iniciar o app agora? (S/N): "
if /i "%ANSWER%"=="S" start "" "%DEST%"

pause
