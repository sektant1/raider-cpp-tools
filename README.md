# Raider tools (WIP)

Mythic raider grade CLI tool for C++ projects with CMake, clang tools and dependencies using vcpkg manifest.

## Install (dev)

```sh
pip install -e .
```

## Usage

```sh
raider init --name demo
raider configure --preset dev
raider build --preset dev
raider test --preset dev
raider fmt
raider tidy --preset dev
raider deps add fmt
```

### Just for fun WoW commands

```sh
raider raid check
raider raid consumes
raider raid pull <time in seconds>
raider raid meters
```

## Trivia

**Based on World of Warcraft mythic raiding tools :)**
