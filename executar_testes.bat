@echo off
setlocal
cd /d "%~dp0"
title Testes do Compilador Mini-Lisp

where python >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado. Instale em https://www.python.org/downloads/
  echo Durante a instalacao, marque "Add Python to PATH".
  pause
  exit /b 1
)

for %%F in (exemplos\*.lisp) do (
  cls
  echo ================================================================
  echo TESTE: %%~nxF
  echo ================================================================
  type "%%F"
  echo.
  echo ----------------------------- SAIDA -----------------------------
  python compilador.py "%%F"
  echo.
  
  pause
)

echo Todos os exemplos foram executados.
pause
