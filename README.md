# Occultech

A Slimefun addon about occult summoning circles, ritual machinery, and custom boss fights
(empowered slimes, withers, guardians, elder guardians), inspired by the Occultism mod.

## Status
Early development. Builds against **Slimefun Legacy** 4.1.61 on **Paper 26.2** (Java 25).

## Development setup (Windows / PowerShell)
Requirements: JDK 25. Unzip one (e.g. Eclipse Temurin 25) into `./.jdk/`; the scripts find it there even if `JAVA_HOME`
points elsewhere. Maven is not needed; `mvnw.cmd` downloads it.

```powershell
# Download Slimefun Legacy + Paper 26.2 into ./libs and ./run (checksums verified).
# -Addons also installs Supreme, InfinityExpansion2, Networks and FluffyMachines (the rest of the bundle goes to run/addons-disabled)
./scripts/setup-dev.ps1 -Addons

# Optional animated boss-model engine for the test server (pinned, checksum verified).
./scripts/setup-bettermodel.ps1

# Accept the Minecraft EULA yourself in run/eula.txt, then:
./scripts/run-server.ps1     # build, copy into run/plugins, start (debug port 5005)

# Build / test from a shell
. ./scripts/java-env.ps1     # select JDK 25 for this session
./mvnw.cmd test
```

Connect with a 26.2 client to `localhost`. Test world: flat, creative, no spawn protection.
Give yourself op from the server console (`op <name>`), then use `/sf guide` or `/sf cheat`.

### Switching Slimefun builds
```powershell
./scripts/setup-dev.ps1 -SlimefunJar path\to\Slimefun.jar -SlimefunVersion prod-26.2
```
Then set `<slimefun.version>` (and `<paper.version>`) in `pom.xml` to match.

## Project layout
See [docs/](docs/) for scope, bosses, recipes and mechanics.

BetterModel installation and workflow: [docs/bettermodel.md](docs/bettermodel.md).
Comprehensive rework plan for all 19 bosses: [docs/boss-rework-plan.md](docs/boss-rework-plan.md).
Boss visual overhaul and Volley model review: [docs/boss-visual-overhaul.md](docs/boss-visual-overhaul.md), [docs/art/bosses/volley/overhaul/s1_silhouettes/README.md](docs/art/bosses/volley/overhaul/s1_silhouettes/README.md).
Modeling and animation references: [docs/boss-model-direction.md](docs/boss-model-direction.md).
