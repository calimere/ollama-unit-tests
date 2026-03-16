@echo off
:: Script batch pour utiliser facilement le générateur de tests unitaires

setlocal EnableDelayedExpansion

if "%~1"=="" (
    echo Usage: %~nx0 ^<source_directory^> [options]
    echo.
    echo Exemples:
    echo   %~nx0 ./example
    echo   %~nx0 C:\mon\projet --output-dir ./tests --model llama3.2
    echo   %~nx0 ./src --dry-run --verbose
    echo.
    goto :eof
)

:: Construction de la commande
set cmd=python run.py %*

echo Execution de: !cmd!
echo.

:: Execution du générateur
!cmd!

if !ERRORLEVEL! equ 0 (
    echo.
    echo ✅ Generation terminee avec succes!
) else (
    echo.
    echo ❌ Erreur lors de la generation (code: !ERRORLEVEL!^)
)