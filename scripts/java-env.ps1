# Dot-source this (". ./scripts/java-env.ps1") to point JAVA_HOME at a JDK 21+ for the current session.
# Leaves JAVA_HOME alone if it already is 21+. Does not change any system settings.

function Get-JdkMajor([string]$jdkHome) {
    $release = Join-Path $jdkHome "release"
    if (-not (Test-Path $release)) { return 0 }
    $line = Select-String -Path $release -Pattern '^JAVA_VERSION="(\d+)' | Select-Object -First 1
    if ($line) { return [int]$line.Matches[0].Groups[1].Value }
    return 0
}

if (-not $env:JAVA_HOME -or (Get-JdkMajor $env:JAVA_HOME) -lt 21) {
    $candidates = @("$env:ProgramFiles\Java", "$env:ProgramFiles\Eclipse Adoptium", "$env:ProgramFiles\Microsoft") |
        Where-Object { Test-Path $_ } |
        ForEach-Object { Get-ChildItem $_ -Directory } |
        Where-Object { (Get-JdkMajor $_.FullName) -ge 21 } |
        Sort-Object { Get-JdkMajor $_.FullName } -Descending

    if (-not $candidates) { throw "No JDK 21+ found. Install one (e.g. Temurin 21) and retry." }
    $env:JAVA_HOME = $candidates[0].FullName
}

$env:Path = "$env:JAVA_HOME\bin;$env:Path"
Write-Host "Using JDK: $env:JAVA_HOME"
