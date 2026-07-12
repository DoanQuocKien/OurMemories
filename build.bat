@echo off
echo Installing / updating dependencies...
pip install -r requirements.txt
echo.
echo Building OurMemories.exe...
pyinstaller --noconsole --onefile --name OurMemories --add-data ".env;." --collect-all pywebview --collect-all pythonnet --hidden-import pywebview.platforms.winforms --hidden-import clr --hidden-import bottle --hidden-import proxy_tools app.py
echo.
echo Done! Exe is at: dist\OurMemories.exe
pause
