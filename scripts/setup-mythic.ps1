# Install the pinned free MythicMobs release for the local Paper 26.2 test server.
# Restart the server normally after installing; do not use Bukkit /reload.
param([string]$ServerDirectory = "", [switch]$Force)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$root = Split-Path -Parent $PSScriptRoot
if (-not $ServerDirectory) { $ServerDirectory = Join-Path $root "run" }
$plugins = Join-Path $ServerDirectory "plugins"
$version = "5.13.0"
$url = "https://cdn.modrinth.com/data/NLuc7Jjh/versions/YVgkWAjK/MythicMobs-5.13.0.jar"
$sha512 = "3883999f5d1321127cd998819d7f1cea22f9a9b7119ee82fd25db172ea967758c05dc6b6dce9a0bcc6a358cedf3380d7ec81e3d20816de010aedec71d8e50b2a"
New-Item -ItemType Directory -Force $plugins | Out-Null
$plugins = (Resolve-Path -LiteralPath $plugins).Path
$destination = Join-Path $plugins "MythicMobs-$version.jar"
$otherVersions = @(Get-ChildItem -LiteralPath $plugins -File -Filter '*MythicMobs*.jar' |
    Where-Object { $_.FullName -ne $destination })
if ($otherVersions.Count) {
    throw "Another MythicMobs jar is installed. Move it out of plugins before proceeding: $($otherVersions.Name -join ', ')"
}
if ((Test-Path -LiteralPath $destination) -and -not $Force) {
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA512).Hash.ToLowerInvariant() -ne $sha512) {
        throw "Existing MythicMobs jar failed verification; rerun with -Force to replace it."
    }
    Write-Host "MythicMobs $version is already installed and verified."
    exit 0
}
$download = "$destination.download"
try {
    Invoke-WebRequest -Uri $url -OutFile $download -Headers @{ 'User-Agent' = 'Occultech-dev-setup' }
    if ((Get-FileHash -LiteralPath $download -Algorithm SHA512).Hash.ToLowerInvariant() -ne $sha512) {
        throw "MythicMobs download failed SHA-512 verification."
    }
    Move-Item -LiteralPath $download -Destination $destination -Force
} finally {
    if (Test-Path -LiteralPath $download) { Remove-Item -LiteralPath $download }
}
Write-Host "Installed MythicMobs $version (SHA-512 verified) to $destination"
Write-Host "Restart the test server normally to enable it."
