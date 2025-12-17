@echo off
REM Script de Deploy para Vercel - TR4CTION Agent
REM Este script prepara e faz commit do código para deploy automático

setlocal enabledelayedexpansion

echo.
echo ======================================================
echo  🚀 DEPLOY VERCEL - TR4CTION Agent
echo ======================================================
echo.

REM Verificar se está no diretório correto
if not exist ".git" (
    echo ❌ Erro: Não encontrei .git neste diretório
    echo Use este script do diretório raiz do projeto
    exit /b 1
)

REM Mostrar status atual
echo 📊 Status do Git:
git status --short
echo.

REM Perguntar se quer fazer commit
set /p COMMIT="Deseja fazer commit e push? (S/N) "
if /i not "%COMMIT%"=="S" (
    echo ⏭️  Deploy cancelado
    exit /b 0
)

REM Fazer commit
set /p MSG="Digite a mensagem do commit: "
if "!MSG!"=="" (
    set MSG=Deploy para Vercel - %date%
)

echo.
echo ⏳ Fazendo commit...
git add .
git commit -m "!MSG!"

if errorlevel 1 (
    echo ❌ Erro ao fazer commit
    exit /b 1
)

echo ✅ Commit realizado

echo.
echo ⏳ Fazendo push para GitHub...
git push origin main

if errorlevel 1 (
    echo ❌ Erro ao fazer push
    exit /b 1
)

echo ✅ Push realizado!

echo.
echo ======================================================
echo ✅ PRONTO PARA DEPLOY!
echo ======================================================
echo.
echo 🔗 GitHub: https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent
echo 🚀 Vercel: https://vercel.com/dashboard
echo.
echo Próximos passos:
echo 1. Acesse Vercel Dashboard
echo 2. Verifique se o deploy foi acionado automaticamente
echo 3. Espere a build completar
echo 4. Verifique as variáveis de ambiente
echo.
pause
