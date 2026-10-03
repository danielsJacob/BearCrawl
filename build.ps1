$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$browserDir = Join-Path $projectRoot "build\playwright-browsers"
$entryPoint = Join-Path $projectRoot "src\bearcrawl\__main__.py"

New-Item -ItemType Directory -Force -Path (Split-Path $browserDir) | Out-Null
if (Test-Path -LiteralPath $browserDir) {
    Remove-Item -LiteralPath $browserDir -Recurse -Force
}

$env:PLAYWRIGHT_BROWSERS_PATH = $browserDir
Push-Location $projectRoot
try {
    uv sync
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    uv run playwright install chromium
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    uv run pyinstaller `
        --clean `
        --noconfirm `
        --onedir `
        --name Bearcrawl `
        --icon "C:\Users\PC\Downloads\Smiley.ico" `
        --paths (Join-Path $projectRoot "src") `
        --collect-all playwright `
        --add-data "$browserDir;playwright-browsers" `
        $entryPoint
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
