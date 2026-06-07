@echo off
chcp 65001 >nul
cd /d "C:\Users\User\Desktop\telegram-ad-exchange\backend"
title Ad Exchange Services

echo ========================================
echo   Aurum Ads Exchange - Service Manager
echo ========================================
echo.

:: Kill old processes
echo [*] Stopping old services...
taskkill /f /im python.exe /fi "WINDOWTITLE eq AurumAPI*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq AurumBot*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq AurumNgrok*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq Ad Exchange*" 2>nul
timeout /t 2 /nobreak >nul

:: Start ngrok
echo [*] Starting ngrok...
start "AurumNgrok" /min "C:\Users\User\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" http 8001 --domain=recount-preheated-runt.ngrok-free.dev

:: Wait for ngrok
echo [*] Waiting for ngrok...
timeout /t 5 /nobreak >nul

:: Start API
echo [*] Starting API (port 8001)...
start "AurumAPI" /min "venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8001

:: Wait for API
echo [*] Waiting for API...
timeout /t 3 /nobreak >nul

:: Start Bot
echo [*] Starting Telegram bot...
start "AurumBot" /min "venv\Scripts\python.exe" -m bot.main

echo.
echo ========================================
echo   All services started!
echo   API:      http://localhost:8001
echo   Public:   https://recount-preheated-runt.ngrok-free.dev
echo   Bot:      @aurumads_bot
echo ========================================
echo.
echo  Close this window to stop all services.
echo.
pause
