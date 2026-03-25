# Buduje TechMart_Generuj.exe (PyInstaller, jeden plik).
# Wymaga: pip install pyinstaller pandas numpy
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Nie znaleziono polecenia 'python'. Zainstaluj Python dla Windows i dodaj do PATH."
}

$datas = @(
    "decision_tree.json",
    "custom_events.json",
    "product_lifecycle.json",
    "pricing_rules.json",
    "DimProduct.csv",
    "imiona_i_nazwiska_lista.csv"
)
$addData = @()
foreach ($f in $datas) {
    if (-not (Test-Path -LiteralPath $f)) {
        throw "Brak pliku wymaganego do pakietu: $f"
    }
    $addData += "--add-data"
    $addData += "${f};."
}

# Windows: separator srodka danych w PyInstallerze to srednik
python -m PyInstaller --noconfirm --clean --onefile --console `
    --name "TechMart_Generuj" `
    @addData `
    "run_techmart.py"

Write-Host ""
Write-Host "Gotowe: dist\TechMart_Generuj.exe"
Write-Host "Możesz wyslac sam ten plik. Kolega uruchamia go bez instalowania Pythona."
