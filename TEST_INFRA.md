# E2E Test Infra: Caelestia Hyprland Cheat Sheet

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source | Tier 1 | Tier 2 | Tier 3 |
|---|---------|--------|:------:|:------:|:------:|
| 1 | Keybindings Parsing | R1. Dynamic Keybindings Parser | 5 | 5 | ✓ |
| 2 | UI Aesthetic & Theme | R2. UI Overlay & Theme Integration | 5 | 5 | ✓ |
| 3 | Performance Standards | R2. Performance Standards | 5 | 5 | ✓ |
| 4 | Dismissal Mechanics | R2. Overlay Dismissal | 5 | 5 | ✓ |
| 5 | Desktop Integration | R3. Desktop Environment Integration | 5 | 5 | ✓ |

## Test Architecture
- **Test Runner**: A Python test suite located at `/home/execorn/teamwork_projects/hyprland_cheat_sheet/tests/test_suite.py` that can be run with `pytest`.
- **Mock Configs**: Under `/home/execorn/teamwork_projects/hyprland_cheat_sheet/tests/mock_configs/`, we store various test inputs for keybinds.conf and variables.conf to feed into the parser.
- **UI Validation**: Checks properties of the quickshell IPC layer via `caelestia drawers list` or `hyprctl` window states to verify toggles.
- **Resource Profiling**: Reads `/proc/<pid>/status` for RAM and checks time delta for toggle latency.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Standard Cheat Sheet Toggle | F3, F4, F5 | Low |
| 2 | Dynamic Reload Verification | F1, F2, F5 | Medium |
| 3 | Stress-Testing with Custom Configs | F1, F3 | High |
| 4 | Interleaved Workspace Toggle & Esc | F4, F5 | Medium |
| 5 | Theme Transition and Color Matching | F2, F3 | Medium |

## Coverage Thresholds
- Tier 1: 25 test cases (5 per feature)
- Tier 2: 25 boundary/corner test cases (5 per feature)
- Tier 3: 5 pairwise feature combination test cases
- Tier 4: 5 realistic application-level scenarios
- Total: 60 test cases
