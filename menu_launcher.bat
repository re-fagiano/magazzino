@echo off
setlocal
pushd %~dp0

REM Avvio rapido del gestionale di magazzino
REM Il menu consente di scegliere fra interfaccia classica e tabellare

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python non e' stato trovato nel PATH.
    echo Installa Python oppure apri un prompt dove il comando "python" sia disponibile.
    pause
    popd
    endlocal
    exit /b 1
)

set "PYTHON_GUI=pythonw"
where pythonw >nul 2>&1
if %errorlevel% neq 0 set "PYTHON_GUI=python"

%PYTHON_GUI% -m inventory_gui
set "exit_code=%errorlevel%"
if "%exit_code%"=="0" goto end

echo.
echo L'interfaccia grafica non si e' avviata correttamente (codice %exit_code%).
echo Provo ad aprire la versione testuale come ripiego.
echo.
python app.py --interface cli

:end

popd
endlocal
