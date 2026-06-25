$mysql = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
if (-not (Test-Path $mysql)) { throw "MySQL client not found at $mysql" }
Write-Host "Enter the MySQL root password when prompted."
Get-Content "$PSScriptRoot\schema.sql" -Raw | & $mysql -u root -p

