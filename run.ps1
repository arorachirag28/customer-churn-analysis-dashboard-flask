$ErrorActionPreference = "Stop"
$python = "C:\Program Files\PostgreSQL\18\pgAdmin 4\python\python.exe"
Set-Location $PSScriptRoot
& $python app.py
