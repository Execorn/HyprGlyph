# ⌨️ HyprGlyph

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python: >=3.11](https://img.shields.io/badge/Python-%3E%3D3.11-blue.svg)](https://python.org)
[![Test Suite](https://img.shields.io/badge/Tests-80%20Passed-success.svg)](#testing)
[![Shell Integration](https://img.shields.io/badge/Desktop-Hyprland-turquoise.svg)](https://hyprland.org)

**HyprGlyph** is a clean, lightning-fast, and automated keybinding parser and cheatsheet generator for the Hyprland compositor. 

Instead of maintaining duplicate cheatsheet tables that go out of sync every time you modify your window manager config, **HyprGlyph** extracts keybindings dynamically directly from your configuration files. It resolves variables, filters out system actions, groups related shortcuts, and outputs a structured JSON schema ready to power stunning desktop overlays (like QML, Eww, or AGS drawers).

---

## 📸 Preview

![HyprGlyph Cheatsheet UI](assets/screenshot.png)

---

## ✨ Features

*   **Dual-Engine Parsing:** Complete native support for both traditional Hyprland configuration files (`.conf`) and native Hyprland Lua configurations (`keybinds.lua` and `variables.lua`), with automatic extension detection and fallback.
*   **Lua Scripting & Constructs:** Seamlessly interprets `hl.bind(...)`, `create_bind(...)`, loop constructs (such as `for i = 1, 10 do` and direction table iterators), string concatenation, and trailing inline `-- comment` strings.
*   **Recursion-Safe Variable Resolution:** Automatically parses your `$variable` and Lua variable definitions and recursively resolves nested references (with built-in circular dependency protection).
*   **Intelligent Auto-Routing:** Inspects binds on the fly and dynamically groups them into clean logical sections (`Windows`, `Applications`, `Utilities`, `System`, `Shell`) based on keywords and syntax signatures.
*   **Smart Range Collapsing:** Automatically detects numeric bindings sequences (like `Super + 1` through `Super + 0`) and collapses them into clean single entries (e.g., `Super + 1-10` ➔ `Switch to Workspace 1-10`) to prevent UI clutter.
*   **Desktop Package Detection:** Leverages `shutil.which` to scan system binaries for `exec` dispatchers, flagging shortcuts for applications that aren't installed on the local system (ideal for rices shared across machines).
*   **Atomic Output Safety:** Writes output atomically utilizing temporary file swapping, eliminating JSON corruption risks and preventing UI flickering in active watchers.
*   **Friendly Description Fallback:** Automatically translates raw window manager actions into readable friendly labels (e.g., `workspace, +1` becomes `Switch to Next Workspace`) if no inline comment exists.

---

## 🛠️ How it Works

```mermaid
graph TD
    A["variables.conf / variables.lua"] --> C(HyprGlyph Parser)
    B["keybinds.conf / keybinds.lua"] --> C
    C -->|1. Parse & Resolve| D[Variable Map]
    C -->|2. Categorize & Clean| E[Section Matrix]
    C -->|3. Collapse Ranges| F[Collapsed Binds]
    C -->|4. Detect Binaries| G[Install Status Check]
    G --> H[keybinds.json]
    H -->|Dynamic Watcher| I[Desktop HUD / Overlay QML/Eww]
```

---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/Execorn/HyprGlyph.git ~/programming/projects/HyprGlyph
cd ~/programming/projects/HyprGlyph
```

### 2. Install package
Install locally or in editable mode using `pip` or `uv`:
```bash
pip install .
# or for development:
pip install -e .
```
This installs the `hyprglyph` executable entry point into your environment.

### 3. Configure defaults or environment variables
By default, the script looks for your configuration files under `~/.local/share/caelestia/` (auto-detecting `.lua` or `.conf`) and outputs to `~/.local/state/caelestia/keybinds.json`.

You can override these paths using CLI arguments or environment variables:

**Traditional `.conf` configurations:**
```bash
export CAELESTIA_VARIABLES_CONF="/path/to/variables.conf"
export CAELESTIA_KEYBINDS_CONF="/path/to/keybinds.conf"
export CAELESTIA_KEYBINDS_JSON="/path/to/output.json"
```

**Native Lua `.lua` configurations:**
```bash
export CAELESTIA_VARIABLES_LUA="/path/to/variables.lua"
export CAELESTIA_KEYBINDS_LUA="/path/to/hyprland/keybinds.lua"
export CAELESTIA_KEYBINDS_JSON="/path/to/output.json"
```

---

## 📖 CLI Usage

### Using the Installed CLI
```bash
hyprglyph \
  --variables ~/.config/hypr/variables.lua ~/.config/hypr/scheme/current.lua \
  --keybinds ~/.config/hypr/hyprland/keybinds.lua \
  --output ~/.local/state/caelestia/keybinds.json
```

### Direct Script Invocation
```bash
python3 parser/parse_keybinds.py \
  --variables ~/.config/hypr/variables.conf ~/.config/hypr/scheme/current.conf \
  --keybinds ~/.config/hypr/hyprland/keybinds.conf \
  --output ~/.local/state/caelestia/keybinds.json
```

### Options
*   `--variables`: One or more paths to configurations declaring variables (e.g. `$terminal = kitty` or Lua tables).
*   `--keybinds`: Path to the main keybindings configuration file (`.conf` or `.lua`).
*   `--output`: Output location for the generated cheatsheet JSON.

---

## 📝 Documenting Your Keybinds

The parser extracts keybindings and attempts to generate friendly descriptions automatically. To customize what is shown in the cheatsheet, you can add comments to your config:

### Traditional `.conf` Configuration

```ini
# Inline comments (Highest priority)
bind = Super, Return, exec, alacritty # Open terminal emulator

# Block comments (Fallback)
# Switch focus to the next window
bind = Super, J, cyclenext,

# Explicit Sections and Categories
# ## Shell keybinds
# Category: Launcher
bind = Super, D, global, caelestia:launcher
```

### Native Lua Configuration

```lua
-- Inline comments (Highest priority)
hl.bind("SUPER + Return", "exec " .. terminal) -- Open terminal emulator

-- Block comments
-- Focus next window
create_bind("SUPER, J", "cyclenext")

-- Explicit Sections and Categories
-- ## Shell Keybinds
-- Category: Launcher
hl.bind("SUPER, D", "global, caelestia:launcher")

-- Iterated loops (Automatically collapsed to 1-10 in cheatsheet)
for i = 1, 10 do
    -- binds for workspace switching and moving
end
```

---

## 📦 JSON Schema Output

The generated structured JSON follows a simple nested structure:
```json
[
  {
    "section": "Shell Keybinds",
    "categories": [
      {
        "category": "Launcher",
        "keybinds": [
          {
            "mods": ["SUPER"],
            "key": "D",
            "action": "global, caelestia:launcher",
            "desc": "Open launcher",
            "notInstalled": false,
            "appName": ""
          }
        ]
      }
    ]
  }
]
```

---

## 🧪 Testing

The repository comes with a comprehensive test suite (80 tests across unit, boundary, stress, and Lua parser suites) verifying parser edge cases, recursion limits, stress layouts, and output atomicity.

To run the test suite, install `pytest` and execute:
```bash
pip install pytest
pytest -v
```

---

## 📄 License
This project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for details.
