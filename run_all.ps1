$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host '==> Installing Python dependencies (app)'
Push-Location "$root\app"
python -m pip install -r requirements.txt
Pop-Location

Write-Host '==> Installing Node dependencies (server)'
Push-Location "$root\server"
npm install
if (-not (Test-Path '.env')) {
  if (Test-Path '.env.example') {
    Copy-Item .env.example .env
    Write-Host 'Created server/.env from .env.example. Please add SUPABASE and GEMINI keys if missing.' -ForegroundColor Yellow
  } else {
    Write-Host 'Missing server/.env.example. Create server/.env manually.' -ForegroundColor Yellow
  }
}
Pop-Location

Write-Host '==> Installing Node dependencies (client)'
Push-Location "$root\client"
npm install
Pop-Location

Write-Host '==> Starting Python API on port 8000'
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root\app'; python -m uvicorn app.main:app --reload --port 8000"

Write-Host '==> Starting Node API on port 3001'
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root\server'; node src/index.js"

Write-Host '==> Starting Frontend on port 5173'
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root\client'; npm run dev"

Write-Host '==> Waiting 8 seconds for services to warm up...'
Start-Sleep -Seconds 8

Write-Host '==> Running parser POST test and saving output'
$inputPath = "$root\app\tests\fixtures\sample_resume_input.json"
$outputPath = "$root\app\tests\fixtures\sample_resume_output.json"

if (-not (Test-Path $inputPath)) {
  throw "Input JSON not found at $inputPath"
}

$body = Get-Content $inputPath -Raw
$response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/parse-resume' -Method Post -ContentType 'application/json' -Body $body
$response | ConvertTo-Json -Depth 30 | Out-File $outputPath -Encoding utf8

Write-Host "Saved parser output to: $outputPath" -ForegroundColor Green
Write-Host '==> Opening frontend in browser'
Start-Process 'http://localhost:5173'

Write-Host 'Done. Keep the opened terminal windows running while testing upload flow.' -ForegroundColor Green
