@echo off
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install pyinstaller tkinterdnd2
python -m PyInstaller --noconfirm --clean --onefile --windowed --icon icone.ico --add-data "icone.ico;." --collect-all tkinterdnd2 --name ConversorMP4 conversor_mp4.py
echo.
echo Se tudo deu certo, o executavel esta em dist\ConversorMP4.exe
pause
