@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ====================================
echo   RECOMPILANDO FinancasPro
echo ====================================
echo.
echo Diretorio atual: %CD%
echo.
echo [1/3] Limpando arquivos antigos...
rd /s /q build 2>nul
rd /s /q dist 2>nul
del /q FinancasPro.spec 2>nul
echo.
echo [2/3] Compilando o executavel...
python -m PyInstaller --onefile --windowed --name "FinancasPro" --clean controle_finanças.py
echo.
echo [3/3] Verificando...
if exist "dist\FinancasPro.exe" (
    echo.
    echo ====================================
    echo   SUCESSO! Executavel atualizado!
    echo ====================================
    echo.
    echo Local: dist\FinancasPro.exe
    dir dist\FinancasPro.exe | find "FinancasPro.exe"
) else (
    echo.
    echo ERRO: Executavel nao foi gerado!
)
echo.
pause
