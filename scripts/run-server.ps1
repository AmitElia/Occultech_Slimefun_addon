# Builds the addon, copies it into the test server and starts it.
# A Java debugger can attach on port 5005 (IntelliJ: Remote JVM Debug).
param(
    [switch]$SkipBuild,
    [string]$Memory = "4G"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$run = Join-Path $root "run"
$plugins = Join-Path $run "plugins"

. (Join-Path $PSScriptRoot "java-env.ps1")

if (-not (Test-Path (Join-Path $run "paper.jar"))) {
    throw "Test server not set up yet. Run ./scripts/setup-dev.ps1 first."
}

# Test-friendly defaults, only written on first run so manual edits are kept
$props = Join-Path $run "server.properties"
if (-not (Test-Path $props)) {
    Copy-Item (Join-Path $PSScriptRoot "server-template/server.properties") $props
}

if (-not $SkipBuild) {
    Push-Location $root
    try {
        & (Join-Path $root "mvnw.cmd") -q -B package
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    } finally {
        Pop-Location
    }
}

Get-ChildItem $plugins -Filter "Occultech*.jar" -ErrorAction SilentlyContinue | Remove-Item
$jar = Get-ChildItem (Join-Path $root "target") -Filter "Occultech-*.jar" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $jar.FullName $plugins
Write-Host "Deployed $($jar.Name)"

Push-Location $run
try {
    & "$env:JAVA_HOME\bin\java.exe" "-Xmx$Memory" "-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005" -jar paper.jar --nogui
} finally {
    Pop-Location
}
