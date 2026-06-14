# Project: Caelestia Hyprland Cheat Sheet

## Architecture
- **Parser**: A Python module/script that parses Hyprland variables and keybindings, resolving variable expressions, extracting inline descriptions, and writing a structured JSON model to `/home/execorn/.local/state/caelestia/keybinds.json`.
- **Shell Integration**:
  - Adds a new `cheatsheet` visibility property to `DrawerVisibilities.qml`.
  - Instantiates `Cheatsheet.Wrapper` inside `Panels.qml`.
  - Modifies `ContentWindow.qml` to support the background blur blob (`PanelBg`) and focus grab integration (for Escape key and click-outside dismissal).
  - Registers the custom global shortcut `caelestia:cheatsheet` in `Shortcuts.qml`.
- **UI Widget**:
  - A clean QML component using Quickshell, styling tokens (`Tokens.appearance`), and dynamic color schemes (`Colours`).
  - Watches `keybinds.json` dynamically and updates its display model on the fly.
  - Features scrollable layouts grouping hotkeys by section and category.
- **Desktop Binding**:
  - Binds `Super + S` in `/home/execorn/.local/share/caelestia/hypr/hyprland/keybinds.conf` to trigger `global, caelestia:cheatsheet`.

## Code Layout
- **Python Parser**: `/home/execorn/teamwork_projects/hyprland_cheat_sheet/parser/parse_keybinds.py`
- **QML Module**: `/home/execorn/.config/quickshell/caelestia/modules/cheatsheet/`
  - `Wrapper.qml` — Handles drawer placement, visibility, and scale transitions.
  - `Content.qml` — Handles the visual card layout, scroll view, search/filter (optional), and lists of bindings.
- **IPC State & Trigger**:
  - `DrawerVisibilities.qml` modified to include `property bool cheatsheet`.
  - `Shortcuts.qml` modified to include `CustomShortcut { name: "cheatsheet" }`.
  - `ContentWindow.qml` modified to add `PanelBg` for cheatsheet.
  - `Panels.qml` modified to anchor and instantiate the wrapper.
- **Hyprland Configuration**: `/home/execorn/.local/share/caelestia/hypr/hyprland/keybinds.conf`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1. Test Specification & Infra | Define E2E tests, boundary cases, and testing harness (Tier 1-4). | None | PLANNED |
| 2 | M2. Dynamic Parser | Implement the Python parser to read variables.conf and keybinds.conf and generate keybinds.json. | None | PLANNED |
| 3 | M3. QML Integration & UI Widget | Implement Cheatsheet.qml (Wrapper + Content), register property in DrawerVisibilities, update Panels & ContentWindow. | M2 | PLANNED |
| 4 | M4. Shortcuts & Desktop Binding | Register custom global shortcut and bind Super + S in Hyprland config. | M3 | PLANNED |
| 5 | M5. Verification & E2E Validation | Run E2E tests, fix bugs, confirm MD3 colors/fonts, and pass Forensic Auditor validation. | M1, M4 | PLANNED |

## Interface Contracts
### Keybindings JSON schema (`keybinds.json`):
```json
[
  {
    "section": "Shell keybinds",
    "categories": [
      {
        "category": "Launcher",
        "keybinds": [
          {
            "mods": ["Super"],
            "key": "D",
            "action": "global, caelestia:launcher",
            "desc": "Open launcher"
          }
        ]
      }
    ]
  }
]
```
