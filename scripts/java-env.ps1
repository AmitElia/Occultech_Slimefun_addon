# Dot-source this (". ./scripts/java-env.ps1") to point JAVA_HOME at a JDK 25+ for the current session.
# Prefers the project-local JDK in ./.jdk, then any installed JDK 25+. Does not change any system settings.

$requiredJdk = 25

function Get-JdkMajor([string]$jdkHome) {
    $release = Join-Path $jdkHome "release"
    if (-not (Test-Path $release)) { return 0 }
    $line = Select-String -Path $release -Pattern '^JAVA_VERSION="(\d+)' | Select-Object -First 1
    if ($line) { return [int]$line.Matches[0].Groups[1].Value }
    return 0
}

$projectJdk = Join-Path (Split-Path -Parent $PSScriptRoot) ".jdk"
$candidates = @($projectJdk, "$env:ProgramFiles\Java", "$env:ProgramFiles\Eclipse Adoptium", "$env:ProgramFiles\Microsoft") |
    Where-Object { Test-Path $_ } |
    ForEach-Object { Get-ChildItem $_ -Directory } |
    Where-Object { (Get-JdkMajor $_.FullName) -ge $requiredJdk } |
    Sort-Object { Get-JdkMajor $_.FullName } -Descending

if ($candidates) {
    $env:JAVA_HOME = $candidates[0].FullName
} elseif (-not $env:JAVA_HOME -or (Get-JdkMajor $env:JAVA_HOME) -lt $requiredJdk) {
    throw "No JDK $requiredJdk+ found. Put one in ./.jdk (see README) and retry."
}

$env:Path = "$env:JAVA_HOME\bin;$env:Path"
Write-Host "Using JDK: $env:JAVA_HOME"
