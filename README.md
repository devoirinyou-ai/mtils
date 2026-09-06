# mtils

Project focused on making easier setup of minecraft servers/mods and managing them after.

## Features

- **Liquid Glass UI:** Modern interface with glassmorphism effects and theme support.
- **Server Management:** Quick setup for Fabric, Forge, Paper, and Purpur servers.
- **Mod Development:** Tools to initialize and build mod workspaces.
- **Dynamic Autocomplete:** Context-aware terminal suggestions with smooth scrolling.
- **Theme Support:** Easy installation and switching of custom themes via GitHub.

## Quick Start

1. Download the latest version (`mtils.exe`) from the Releases page.
2. Run the executable. All necessary configuration files and directories will be created automatically.
3. Place any custom themes into the `themes/` folder.

## Commands

- `server <name> <loader> <version>` - Create a new server.
- `mod <name> <loader> <version> <lang>` - Initialize a mod workspace.
- `theme set <name>` - Switch active theme.
- `theme install <user/repo>` - Install a theme from GitHub.
- `help` - Show all available commands.

## Installing Custom Themes

To add new themes to your terminal:
1. Find a theme repository on GitHub.
2. Copy the user/repo part of the repository link.
3. Type the following command in the terminal:
   `theme install user/repo`
