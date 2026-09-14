$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv-desktop\Scripts\python.exe'
$buildRoot = Join-Path $projectRoot '.build\desktop'

if (-not (Test-Path -LiteralPath $python)) {
    py -3.11 -m venv (Join-Path $projectRoot '.venv-desktop')
}

& $python -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements-build.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }

Push-Location (Join-Path $projectRoot 'app\web')
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
    npm run build -- --mode desktop --outDir (Join-Path $buildRoot 'web') --emptyOutDir
    if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
} finally { Pop-Location }

& $python (Join-Path $PSScriptRoot 'create_icon.py') (Join-Path $buildRoot 'book.ico')
if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }

Push-Location $projectRoot
try {
    & $python -m PyInstaller --clean --noconfirm (Join-Path $PSScriptRoot 'BookDesktop.spec')
    if ($LASTEXITCODE -ne 0) { throw 'Windows packaging failed.' }
} finally { Pop-Location }

Write-Host "Built: $(Join-Path $projectRoot 'dist\Book-0.1.4-Windows-x64.exe')"
