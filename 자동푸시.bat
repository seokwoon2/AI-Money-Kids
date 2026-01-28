@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   Auto Push to GitHub
echo ========================================
echo.

echo [1/3] Checking changes...
git status
echo.

echo [2/3] Adding all changes...
git add .
echo.

echo [3/3] Committing and pushing...
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=Update: Auto update %date% %time%

git commit -m "%commit_msg%"
echo.

echo Pushing to GitHub...
git push

if %errorlevel%==0 (
    echo.
    echo ========================================
    echo   Success! Pushed to GitHub
    echo   Streamlit Cloud will auto-deploy
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   Error occurred!
    echo   Check network connection
    echo   Or push manually from VS Code
    echo ========================================
)

echo.
pause
