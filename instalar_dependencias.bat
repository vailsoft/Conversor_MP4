@echo off
setlocal
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado. Instale o Python 3.10 ou superior e adicione-o ao PATH.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo Nao foi possivel atualizar o pip.
    pause
    exit /b 1
)

python -m pip install tkinterdnd2 pyinstaller
if errorlevel 1 (
    echo Nao foi possivel instalar as dependencias.
    pause
    exit /b 1
)

echo.
echo Dependencias instaladas com sucesso.
pause
