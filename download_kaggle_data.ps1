$ErrorActionPreference = "Stop"
$dataset = if ($env:KAGGLE_DATASET) { $env:KAGGLE_DATASET } else { "blastchar/telco-customer-churn" }
$target = Join-Path $PSScriptRoot "data"
if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target | Out-Null }
$localKaggle = Join-Path $PSScriptRoot ".python_packages\bin\kaggle.exe"
$kaggleCommand = if (Test-Path $localKaggle) { $localKaggle } else { "kaggle" }
Write-Host "Downloading Kaggle dataset: $dataset"
Write-Host "This requires Kaggle API credentials in %USERPROFILE%\.kaggle\kaggle.json"
& $kaggleCommand datasets download -d $dataset -p $target --unzip
$csv = Get-ChildItem $target -Filter *.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $csv) { throw "No CSV file was found after Kaggle download." }
Copy-Item -LiteralPath $csv.FullName -Destination (Join-Path $target "kaggle_churn.csv") -Force
Write-Host "Saved Kaggle CSV as data\kaggle_churn.csv"
