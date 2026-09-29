# Occultech

A Slimefun addon about occult summoning circles, ritual machinery, and custom boss fights
(empowered slimes, withers, guardians, elder guardians), inspired by the Occultism mod.

## Status
Early scaffold. Currently builds against Slimefun **experimental** (commit `3ea21da`, MC 1.21–1.21.2)
on Paper 1.21.1. The final target is MC 26.2 on a server with a custom Slimefun port.

## Development setup (Windows / PowerShell)
Requirements: a JDK 21+ installed (the scripts find it automatically even if `JAVA_HOME` points at an older one).
Maven is not needed; `mvnw.cmd` downloads it.

```powershell
# Download Slimefun + Paper into ./libs and ./run
./scripts/setup-dev.ps1

# Accept the Minecraft EULA yourself in run/eula.txt, then:
./scripts/run-server.ps1     # build, copy into run/plugins, start (debug port 5005)

# Build / test from a shell
. ./scripts/java-env.ps1     # select JDK 21+ for this session
./mvnw.cmd test
```

Connect with a 1.21.1 client to `localhost`. Test world: flat, creative, no spawn protection.
Give yourself op from the server console (`op <name>`), then use `/sf guide` or `/sf cheat`.

### Switching Slimefun builds
```powershell
./scripts/setup-dev.ps1 -SlimefunJar path\to\Slimefun.jar -SlimefunVersion custom-26.2
```
Then set `<slimefun.version>` (and `<paper.version>`) in `pom.xml` to match.

## Project layout
See [CLAUDE.md](CLAUDE.md) for architecture and conventions, and [docs/design.md](docs/design.md) for the content design.
