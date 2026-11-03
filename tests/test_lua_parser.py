import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "parser"))
from parse_keybinds import parse_configs, parse_lua_configs, parse_lua_variables

PARSER_SCRIPT = ROOT_DIR / "parser" / "parse_keybinds.py"
REAL_VARS_LUA = Path.home() / ".local/share/caelestia/hypr/variables.lua"
REAL_KEYBINDS_LUA = Path.home() / ".local/share/caelestia/hypr/hyprland/keybinds.lua"

def validate_json_schema(data):
    assert isinstance(data, list), "Root must be a list of sections"
    assert len(data) > 0, "Sections list should not be empty"
    for section in data:
        assert isinstance(section, dict), "Section must be a dict"
        assert "section" in section, "Section must have 'section' key"
        assert isinstance(section["section"], str), "Section name must be string"
        assert "categories" in section, "Section must have 'categories' key"
        assert isinstance(section["categories"], list), "Categories must be list"
        for category in section["categories"]:
            assert isinstance(category, dict), "Category must be a dict"
            assert "category" in category, "Category must have 'category' key"
            assert isinstance(category["category"], str), "Category name must be string"
            assert "keybinds" in category, "Category must have 'keybinds' key"
            assert isinstance(category["keybinds"], list), "Keybinds must be list"
            for kb in category["keybinds"]:
                assert "mods" in kb, "Keybind must have 'mods'"
                assert isinstance(kb["mods"], list), "Mods must be a list"
                assert "key" in kb, "Keybind must have 'key'"
                assert isinstance(kb["key"], str), "Key must be string"
                assert "action" in kb, "Keybind must have 'action'"
                assert isinstance(kb["action"], str), "Action must be string"
                assert "desc" in kb, "Keybind must have 'desc'"
                assert isinstance(kb["desc"], str), "Desc must be string"
                assert "notInstalled" in kb, "Keybind must have 'notInstalled'"
                assert "appName" in kb, "Keybind must have 'appName'"

def test_parse_lua_variables_standalone():
    if not REAL_VARS_LUA.exists():
        pytest.skip("variables.lua not found")
    vars_dict = parse_lua_variables(REAL_VARS_LUA)
    assert isinstance(vars_dict, dict)
    assert "mainMod" in vars_dict or "SUPER" in vars_dict.values()
    assert "terminal" in vars_dict
    assert "browser" in vars_dict
    assert "fileExplorer" in vars_dict

def test_parse_lua_configs_direct():
    if not REAL_KEYBINDS_LUA.exists():
        pytest.skip("keybinds.lua not found")
    sections = parse_lua_configs([REAL_VARS_LUA], REAL_KEYBINDS_LUA)
    validate_json_schema(sections)

    section_names = [s["section"] for s in sections]
    assert "Shell Keybinds" in section_names
    assert "Windows" in section_names
    assert "Applications" in section_names
    assert "Utilities" in section_names
    assert "System" in section_names

    total_keybinds = sum(
        len(c["keybinds"])
        for s in sections
        for c in s["categories"]
    )
    assert total_keybinds >= 100, f"Expected at least 100 keybinds, got {total_keybinds}"

def test_parse_configs_auto_detection_and_fallback(tmp_path):
    if not REAL_KEYBINDS_LUA.exists():
        pytest.skip("keybinds.lua not found")
    
    sections = parse_configs([str(REAL_VARS_LUA)], str(REAL_KEYBINDS_LUA))
    assert len(sections) > 0
    validate_json_schema(sections)

def test_cli_execution_with_lua_defaults(tmp_path):
    if not REAL_KEYBINDS_LUA.exists():
        pytest.skip("Default caelestia Lua config files not found on host")
    out_file = tmp_path / "keybinds_output.json"
    res = subprocess.run(
        ["python3", str(PARSER_SCRIPT), "--output", str(out_file)],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0, f"Parser failed with error: {res.stderr}"
    assert out_file.exists()

    with open(out_file) as f:
        data = json.load(f)
    validate_json_schema(data)
    assert len(data) >= 5

def test_cli_execution_with_custom_lua_snippet(tmp_path):
    sample_vars = tmp_path / "custom_vars.lua"
    sample_vars.write_text('''
return {
    terminal = "alacritty --hold",
    browser = "chromium",
    mainMod = "SUPER",
}
''')
    sample_keys = tmp_path / "custom_keys.lua"
    sample_keys.write_text('''
local function bind(keys, action)
    hl.bind(keys, action)
end

-- Section: Applications
-- Category: Launchers
-- Terminal emulator
bind("SUPER, Return", "exec " .. terminal)
bind("SUPER + SHIFT, B", "exec " .. browser) -- Launch Chromium Browser
''')
    out_file = tmp_path / "custom_out.json"
    res = subprocess.run(
        [
            "python3",
            str(PARSER_SCRIPT),
            "--variables", str(sample_vars),
            "--keybinds", str(sample_keys),
            "--output", str(out_file)
        ],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    with open(out_file) as f:
        data = json.load(f)
    validate_json_schema(data)
    assert data[0]["section"] == "Applications"
    assert data[0]["categories"][0]["category"] == "Launchers"
    kbs = data[0]["categories"][0]["keybinds"]
    assert len(kbs) == 2
    assert kbs[0]["key"] == "Return"
    assert kbs[0]["action"] == "exec alacritty --hold"
    assert kbs[0]["desc"] == "Terminal emulator"
    assert kbs[1]["key"] == "B"
    assert kbs[1]["action"] == "exec chromium"
    assert kbs[1]["desc"] == "Launch Chromium Browser"
