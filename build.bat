@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Building executable...
pyinstaller --noconsole --onefile --name "OurMemories" app.py
echo.
echo Done! Find your app in: dist\OurMemories.exe
pause
