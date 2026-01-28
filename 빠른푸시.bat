@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo Quick push...
git add .
git commit -m "Update: %date% %time%"
git push

if %errorlevel%==0 (
    echo Push completed!
) else (
    echo Push failed - check network
)

timeout /t 3
