# Sets up the local dev environment:
#  1. Downloads the Slimefun jar and installs it into ./libs (in-project Maven repo) for compiling
#  2. Downloads a Paper server into ./run and puts Slimefun in ./run/plugins for testing
#
# Re-run with -Force to re-download. To switch to the custom 26.2 server build later, use
# -SlimefunJar <path> -SlimefunVersion <name> and update <slimefun.version> in pom.xml.
param(
    [string]$PaperVersion = "1.21.1",
    [string]$SlimefunUrl = "https://blob.build/dl/Slimefun4/Experimental/latest",
    [string]$SlimefunVersion = "experimental-3ea21da",
    [string]$SlimefunJar = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$run = Join-Path $root "run"
$plugins = Join-Path $run "plugins"
New-Item -ItemType Directory -Force $plugins | Out-Null

# --- Slimefun jar ---
$sfCache = Join-Path $run "Slimefun4-$SlimefunVersion.jar"
if ($SlimefunJar) {
    Copy-Item $SlimefunJar $sfCache -Force
} elseif ($Force -or -not (Test-Path $sfCache)) {
    Write-Host "Downloading Slimefun ($SlimefunVersion)..."
    Invoke-WebRequest $SlimefunUrl -OutFile $sfCache
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

# --- Paper server ---
$paperJar = Join-Path $run "paper.jar"
if ($Force -or -not (Test-Path $paperJar)) {
    Write-Host "Downloading Paper $PaperVersion..."
    $build = Invoke-RestMethod "https://fill.papermc.io/v3/projects/paper/versions/$PaperVersion/builds/latest" -Headers @{ "User-Agent" = "Occultech-dev-setup" }
    Invoke-WebRequest $build.downloads."server:default".url -OutFile $paperJar
}

Write-Host ""
Write-Host "Done. Before the first server start, read https://aka.ms/MinecraftEULA and set eula=true in run/eula.txt yourself."
