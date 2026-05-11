@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "MINICONDA=%USERPROFILE%\miniconda3"
if exist "%MINICONDA%\python.exe" (
    set "PATH=%MINICONDA%;%MINICONDA%\Scripts;%MINICONDA%\Library\bin;%PATH%"
)

set "PYTHON="
where python >nul 2>nul && set "PYTHON=python"
if not defined PYTHON (
    where python3 >nul 2>nul && set "PYTHON=python3"
)
if not defined PYTHON if exist "%MINICONDA%\python.exe" (
    set "PYTHON=%MINICONDA%\python.exe"
)

if not defined PYTHON (
    echo Hittar varken python eller python3.
    echo Installera Python eller lagg till det i PATH.
    echo.
    pause
    exit /b 1
)

echo Bygger sokindex...
%PYTHON% "%ROOT%\app\build_search_index.py" --root "%ROOT%" --output "%ROOT%\app\search-index.json"
if errorlevel 1 goto :fail

for /f %%P in ('%PYTHON% -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1]); s.close()"') do set "PORT=%%P"
if not defined PORT goto :fail

set "URL=http://127.0.0.1:%PORT%/app/index.html"
echo Startar lokal server pa %URL%
echo Tryck Ctrl+C for att stoppa servern.
start "" "%URL%"

%PYTHON% "%ROOT%\app\search_server.py" --root "%ROOT%" --port "%PORT%" --bind 127.0.0.1
if errorlevel 1 goto :fail
exit /b 0

:fail
echo.
echo Start misslyckades.
pause
exit /b 1
