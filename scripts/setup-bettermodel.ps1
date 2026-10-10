# Installs the pinned Paper 26.2-compatible stable release into the local test server.
# Restart the server normally after installing; do not use Bukkit /reload.
param([string]$ServerDirectory = "", [switch]$Force)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$root = Split-Path -Parent $PSScriptRoot
if (-not $ServerDirectory) { $ServerDirectory = Join-Path $root "run" }
$plugins = Join-Path $ServerDirectory "plugins"
$version = "3.5.0"
$url = "https://cdn.modrinth.com/data/4h8rX3rt/versions/QTU9HP83/bettermodel-3.5.0-paper.jar"
$sha512 = "e67ebd7e83a31d651d86baa1c39c6ec7995f786d1fac1a1f45e16e276521154e2f07b6ec3b428d86e978d955865d668c38ccb6bf19ec226e8b3c785c1d451aef"
New-Item -ItemType Directory -Force $plugins | Out-Null
$plugins = (Resolve-Path -LiteralPath $plugins).Path
$destination = Join-Path $plugins "bettermodel-$version-paper.jar"
$otherVersions = @(Get-ChildItem -LiteralPath $plugins -Filter '*bettermodel*.jar' | Where-Object { $_.FullName -ne $destination })
if ($otherVersions.Count) { throw "Another BetterModel jar is installed. Move it out of plugins before proceeding: $($otherVersions.Name -join ', ')" }
if ((Test-Path -LiteralPath $destination) -and -not $Force) {
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA512).Hash.ToLowerInvariant() -ne $sha512) {
        throw "Existing BetterModel jar failed verification; rerun with -Force to replace it."
    }
    Write-Host "BetterModel $version is already installed and verified."
    exit 0
}
$download = "$destination.download"
try {
    Invoke-WebRequest -Uri $url -OutFile $download -Headers @{ 'User-Agent' = 'Occultech-dev-setup' }
    if ((Get-FileHash -LiteralPath $download -Algorithm SHA512).Hash.ToLowerInvariant() -ne $sha512) {
        throw "BetterModel download failed SHA-512 verification."
    }
    Move-Item -LiteralPath $download -Destination $destination -Force
} finally {
    if (Test-Path -LiteralPath $download) { Remove-Item -LiteralPath $download }
}
Write-Host "Installed BetterModel $version (SHA-512 verified) to $destination"
Write-Host "Restart the test server normally to enable it. See docs/bettermodel.md."
