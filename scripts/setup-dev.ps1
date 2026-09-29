# Sets up the local dev environment:
#  1. Downloads the Slimefun jar and installs it into ./libs (in-project Maven repo) for compiling
#  2. Downloads a Paper server into ./run and puts Slimefun in ./run/plugins for testing
#  3. Optionally (-Addons) installs the Slimefun Legacy addon bundle (Supreme, InfinityExpansion2, Networks, ...)
#
# Every download is checked against its published SHA-256. Re-run with -Force to re-download.
# To use a different Slimefun build (e.g. the production server's jar):
#   -SlimefunJar <path> -SlimefunVersion <name>   and update <slimefun.version> in pom.xml.
param(
    [string]$PaperVersion = "26.2",
    [string]$SlimefunUrl = "https://github.com/wickidcow/Slimefun-Legacy/releases/download/v4.1.61/Slimefun-Legacy4.1.61.jar",
    [string]$SlimefunSha256 = "329e22688557fbd0e0d51dba02fdc1e2e8d9f363774b29dafb0a502f41d6024f",
    [string]$SlimefunVersion = "legacy-4.1.61",
    [string]$SlimefunJar = "",
    [switch]$Addons,
    [string]$AddonsUrl = "https://github.com/wickidcow/Slimefun-Legacy/releases/download/v4.1.61/SF_Addons_1.21.11-26.3.zip",
    [string]$AddonsSha256 = "933dabbe3a20ed830266ff41fa5f3092fd4909b649ce785d4791e5cd568878a5",
    # Addons enabled in run/plugins (matching the production server); the rest go to run/addons-disabled
    [string[]]$EnabledAddons = @("SF_Supreme", "SF_InfinityExpansion2", "SF_Networks", "SF_FluffyMachines"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$root = Split-Path -Parent $PSScriptRoot
$run = Join-Path $root "run"
$plugins = Join-Path $run "plugins"
New-Item -ItemType Directory -Force $plugins | Out-Null

function Get-Verified([string]$url, [string]$out, [string]$sha256) {
    Write-Host "Downloading $(Split-Path -Leaf $out)..."
    Invoke-WebRequest $url -OutFile $out -Headers @{ "User-Agent" = "Occultech-dev-setup" }
    if ($sha256) {
        $actual = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
        if ($actual -ne $sha256.ToLower()) {
            Remove-Item $out
            throw "Checksum mismatch for $out (expected $sha256, got $actual)"
        }
    }
}

# --- Slimefun jar ---
$sfCache = Join-Path $run "Slimefun4-$SlimefunVersion.jar"
if ($SlimefunJar) {
    Copy-Item $SlimefunJar $sfCache -Force
} elseif ($Force -or -not (Test-Path $sfCache)) {
    Get-Verified $SlimefunUrl $sfCache $SlimefunSha256
}

# Install into ./libs using Maven repository layout
$libDir = Join-Path $root "libs/com/github/Slimefun/Slimefun4/$SlimefunVersion"
New-Item -ItemType Directory -Force $libDir | Out-Null
Copy-Item $sfCache (Join-Path $libDir "Slimefun4-$SlimefunVersion.jar") -Force
@"
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.github.Slimefun</groupId>
  <artifactId>Slimefun4</artifactId>
  <version>$SlimefunVersion</version>
</project>
"@ | Set-Content -Encoding utf8 (Join-Path $libDir "Slimefun4-$SlimefunVersion.pom")

Get-ChildItem $plugins -Filter "Slimefun*.jar" | Remove-Item
Copy-Item $sfCache (Join-Path $plugins "Slimefun.jar") -Force

# --- Addon bundle (optional) ---
if ($Addons) {
    $zip = Join-Path $run "sf-addons.zip"
    if ($Force -or -not (Test-Path $zip)) {
        Get-Verified $AddonsUrl $zip $AddonsSha256
    }
    $tmp = Join-Path $run "sf-addons"
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    Expand-Archive $zip $tmp
    $disabled = Join-Path $run "addons-disabled"
    New-Item -ItemType Directory -Force $disabled | Out-Null
    Get-ChildItem $tmp -Recurse -Filter "*.jar" | ForEach-Object {
        $name = $_.Name
        $enabled = $EnabledAddons | Where-Object { $name.StartsWith($_) }
        Copy-Item $_.FullName ($(if ($enabled) { $plugins } else { $disabled })) -Force
        if ($enabled) { Write-Host "  enabled addon: $name" }
    }
    Remove-Item -Recurse -Force $tmp
}

# --- Paper server ---
$paperJar = Join-Path $run "paper.jar"
if ($Force -or -not (Test-Path $paperJar)) {
    $build = Invoke-RestMethod "https://fill.papermc.io/v3/projects/paper/versions/$PaperVersion/builds/latest" -Headers @{ "User-Agent" = "Occultech-dev-setup" }
    $dl = $build.downloads."server:default"
    Write-Host "Paper $PaperVersion build $($build.id) ($($build.channel))"
    Get-Verified $dl.url $paperJar $dl.checksums.sha256
}

Write-Host ""
Write-Host "Done. Before the first server start, read https://aka.ms/MinecraftEULA and set eula=true in run/eula.txt yourself."
