@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    python gui_launcher.py
) else (
    py -3 gui_launcher.py
)

set EXIT_CODE=%ERRORLEVEL%
if not %EXIT_CODE%==0 (
    echo.
    echo QueScanner finalizado com erro. Consulte logs\app.log para detalhes.
)

exit /b %EXIT_CODE%
