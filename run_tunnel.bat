@echo off
setlocal

REM Go to project dir
cd /d %~dp0

REM Check cloudflared availability
where cloudflared >NUL 2>&1
if errorlevel 1 (
  echo [ERROR] cloudflared is not installed or not in PATH.
  echo Install with: winget install -e --id Cloudflare.cloudflared
  echo Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
  exit /b 1
)

REM Start Quick Tunnel to local Flask server
cloudflared tunnel --url http://127.0.0.1:5000

endlocal
