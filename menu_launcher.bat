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

python app.py
set "exit_code=%errorlevel%"
if not "%exit_code%"=="0" (
    echo.
    echo Il programma si e' chiuso con codice %exit_code%.
    echo Premi un tasto per continuare...
    pause >nul
)

popd
endlocal
