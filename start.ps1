$ErrorActionPreference = "SilentlyContinue"

Write-Host "=== Aurum Ads Exchange - Запуск ===" -ForegroundColor Cyan

# Kill old processes
Get-Process -Name python* -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2

$venv = ".\backend\venv\Scripts"
$ngrok = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"

# Start API
Write-Host "Starting API on port 8001..." -ForegroundColor Yellow
Start-Process -FilePath "$venv\python.exe" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001" -WindowStyle Hidden
Start-Sleep 3

# Start Bot
Write-Host "Starting Bot (@aurumads_bot)..." -ForegroundColor Yellow
Start-Process -FilePath "$venv\python.exe" -ArgumentList "-m", "bot.main" -WindowStyle Hidden

# Start ngrok
Write-Host "Starting ngrok tunnel..." -ForegroundColor Yellow
([WMICLASS]"\\localhost\ROOT\CIMV2:Win32_Process").Create("$ngrok http 8001 --log=stdout") | Out-Null

Write-Host ""
Write-Host "=== Всё запущено! ===" -ForegroundColor Green
Write-Host "API:  http://localhost:8001"
Write-Host "Бот: @aurumads_bot"
Write-Host ""
Write-Host "Mini App URL (узнать): http://localhost:4040/api/tunnels" -ForegroundColor Cyan
