# mtils

A tool focused on making Minecraft server and mod setup easier, as well as managing them afterwards.

## Features

* **Liquid Glass UI:** Modern interface with glassmorphism effects and theme support.
* **Server Management:** Quick setup for Fabric, Forge, Paper, and Purpur servers.
* **Mod Development:** Tools for initializing and building mod workspaces.
* **Dynamic Autocomplete:** Context-aware terminal suggestions with smooth scrolling.
* **Theme Support:** Easy installation and switching of custom themes from GitHub.

## Quick Start

1. Download the latest version (`mtils.exe`) from the Releases page.
2. Run the executable. Required configuration files and directories will be created automatically.
3. Place custom themes in the `themes/` folder.

## Commands

* `server <name> <loader> <version>` — Create a new server.
* `mod <name> <loader> <version> <lang>` — Initialize a mod workspace.
* `theme set <name>` — Switch the active theme.
* `theme install <user/repo>` — Install a theme from GitHub.
* `help` — Show all available commands.

## Installing Custom Themes

1. Find a theme repository on GitHub.
2. Copy the `user/repo` part of the repository URL.
3. Run:

```text
theme install user/repo
```

## Notes

This is the first public release of mtils. The project is still under active development, so some features and internal implementation details may change.
