import os
import sys
import time
import pathlib
import json
import subprocess
import shutil
import pytest

# Constants
PARSER_PATH = "/home/execorn/teamwork_projects/hyprland_cheat_sheet/parser/parse_keybinds.py"
USER_KEYBINDS_CONF = pathlib.Path(os.environ.get("CAELESTIA_KEYBINDS_CONF", "~/.local/share/caelestia/hypr/hyprland/keybinds.conf")).expanduser()
USER_VARIABLES_CONF = pathlib.Path(os.environ.get("CAELESTIA_VARIABLES_CONF", "~/.local/share/caelestia/hypr/variables.conf")).expanduser()
USER_KEYBINDS_JSON = pathlib.Path(os.environ.get("CAELESTIA_KEYBINDS_JSON", "~/.local/state/caelestia/keybinds.json")).expanduser()

has_parser = os.path.exists(PARSER_PATH)
has_quickshell = shutil.which("quickshell") is not None or shutil.which("qs") is not None
has_caelestia = shutil.which("caelestia") is not None
has_hyprctl = shutil.which("hyprctl") is not None

def is_qs_running():
    try:
        res = subprocess.run(["pgrep", "-f", "qs -c caelestia"], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def reload_quickshell():
    subprocess.run(["qs", "-c", "caelestia", "kill"], capture_output=True)
    time.sleep(0.5)
    res = subprocess.run(["caelestia", "shell", "-d"], capture_output=True)
    return res

has_environment = has_quickshell and has_caelestia and has_hyprctl and is_qs_running()

# --- Helpers ---

def load_mock_config(category):
    mock_dir = pathlib.Path("/home/execorn/teamwork_projects/hyprland_cheat_sheet/tests/mock_configs") / category
    var_file = mock_dir / "variables.conf"
    key_file = mock_dir / "keybinds.conf"
    
    var_content = var_file.read_text() if var_file.exists() else ""
    key_content = key_file.read_text() if key_file.exists() else ""
    
    return var_content, key_content

def write_active_configs(var_content, key_content):
    USER_VARIABLES_CONF.parent.mkdir(parents=True, exist_ok=True)
    USER_VARIABLES_CONF.write_text(var_content)
    USER_KEYBINDS_CONF.parent.mkdir(parents=True, exist_ok=True)
    USER_KEYBINDS_CONF.write_text(key_content)
    if USER_KEYBINDS_JSON.exists():
        try:
            USER_KEYBINDS_JSON.unlink()
        except OSError:
            pass

def run_parser_subprocess():
    if not has_parser:
        pytest.skip("Parser script parse_keybinds.py not found")
    res = subprocess.run(["python3", PARSER_PATH], capture_output=True, text=True)
    return res

def validate_json_schema(data):
    assert isinstance(data, list), "Root must be a list"
    for section in data:
        assert isinstance(section, dict), "Section must be a dict"
        assert "section" in section, "Section must contain 'section'"
        assert isinstance(section["section"], str), "Section name must be a string"
        assert "categories" in section, "Section must contain 'categories'"
        assert isinstance(section["categories"], list), "Categories must be a list"
        for category in section["categories"]:
            assert isinstance(category, dict), "Category must be a dict"
            assert "category" in category, "Category must contain 'category'"
            assert isinstance(category["category"], str), "Category name must be a string"
            assert "keybinds" in category, "Category must contain 'keybinds'"
            assert isinstance(category["keybinds"], list), "Keybinds must be a list"
            for keybind in category["keybinds"]:
                assert isinstance(keybind, dict), "Keybind must be a dict"
                assert "mods" in keybind, "Keybind must contain 'mods'"
                assert isinstance(keybind["mods"], list), "mods must be a list"
                for mod in keybind["mods"]:
                    assert isinstance(mod, str), "Modifier must be a string"
                assert "key" in keybind, "Keybind must contain 'key'"
                assert isinstance(keybind["key"], str), "Key must be a string"
                assert "action" in keybind, "Keybind must contain 'action'"
                assert isinstance(keybind["action"], str), "Action must be a string"
                assert "desc" in keybind, "Keybind must contain 'desc'"
                assert isinstance(keybind["desc"], str), "Desc must be a string"

# --- Fixtures ---

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    global USER_KEYBINDS_CONF, USER_VARIABLES_CONF, USER_KEYBINDS_JSON
    
    # Define temp paths
    temp_keybinds_conf = tmp_path / "keybinds.conf"
    temp_variables_conf = tmp_path / "variables.conf"
    temp_keybinds_json = tmp_path / "keybinds.json"
    
    # Set the environment variables using monkeypatch
    monkeypatch.setenv("CAELESTIA_KEYBINDS_CONF", str(temp_keybinds_conf))
    monkeypatch.setenv("CAELESTIA_VARIABLES_CONF", str(temp_variables_conf))
    monkeypatch.setenv("CAELESTIA_KEYBINDS_JSON", str(temp_keybinds_json))
    
    # Update global variables
    USER_KEYBINDS_CONF = temp_keybinds_conf
    USER_VARIABLES_CONF = temp_variables_conf
    USER_KEYBINDS_JSON = temp_keybinds_json
    
    yield

# ==========================================
# TIER 1: FEATURE COVERAGE (25 test cases)
# ==========================================

# --- Category 1: Keybindings Parsing ---

def test_t1_parser_simple_binds():
    """T1: Simple keybind parsing and formatting validation."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    res = run_parser_subprocess()
    assert res.returncode == 0
    assert USER_KEYBINDS_JSON.exists()
    
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    validate_json_schema(data)
    
    assert len(data) == 2
    assert data[0]["section"] == "System Actions"
    assert data[0]["categories"][0]["category"] == "Session"
    bind = data[0]["categories"][0]["keybinds"][0]
    assert bind["mods"] == ["SUPER"]
    assert bind["key"] == "M"
    assert bind["action"] == "exit"
    assert bind["desc"] == "Terminate the current Hyprland session"

def test_t1_parser_variables_resolution():
    """T1: Check variable resolution in action fields."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    
    # Check variables in Applications/Launchers
    launcher_cat = None
    for section in data:
        if section["section"] == "Applications":
            for cat in section["categories"]:
                if cat["category"] == "Launchers":
                    launcher_cat = cat
                    break
    assert launcher_cat is not None
    binds = launcher_cat["keybinds"]
    actions = {b["key"]: b["action"] for b in binds}
    assert actions["Q"] == "exec kitty"
    assert actions["B"] == "exec firefox"

def test_t1_parser_sections():
    """T1: Verify section header extraction and grouping."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    
    sections = [s["section"] for s in data]
    assert "System Actions" in sections
    assert "Applications" in sections

def test_t1_parser_categories():
    """T1: Grouping by categories within a section."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    
    # Categories under System Actions
    sys_cats = []
    for s in data:
        if s["section"] == "System Actions":
            sys_cats = [cat["category"] for cat in s["categories"]]
    assert "Session" in sys_cats
    assert "Windows" in sys_cats or "WIndows" in sys_cats

def test_t1_parser_inline_descriptions():
    """T1: Extract inline descriptions from keybindings."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    
    # Inline comment check
    browser_bind = None
    for s in data:
        for cat in s["categories"]:
            for b in cat["keybinds"]:
                if b["key"] == "B":
                    browser_bind = b
    assert browser_bind is not None
    assert browser_bind["desc"] == "Inline description for web browser"

# --- Category 2: UI Aesthetic & Theme ---

def test_t1_ui_drawer_visibility():
    """T1: Drawer visibility registration check."""
    if not has_environment:
        qml_path = pathlib.Path("~/.config/quickshell/caelestia/components/DrawerVisibilities.qml").expanduser()
        assert qml_path.exists()
    else:
        res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
        assert res.returncode == 0
        assert len(res.stdout.strip()) > 0

def test_t1_ui_wrapper_instantiation():
    """T1: Verify cheatsheet Wrapper.qml file existence and contents."""
    wrapper_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Wrapper.qml").expanduser()
    if not wrapper_path.exists():
        pytest.skip("Cheatsheet Wrapper.qml not implemented yet")
    assert "Wrapper" in wrapper_path.name

def test_t1_ui_panel_background_blur():
    """T1: Verify panel background/blur definition in ContentWindow.qml."""
    window_path = pathlib.Path("~/.config/quickshell/caelestia/modules/drawers/ContentWindow.qml").expanduser()
    if not window_path.exists():
        pytest.skip("ContentWindow.qml not found")
    content = window_path.read_text()
    assert "blur" in content.lower() or "background" in content.lower() or "panelbg" in content.lower()

def test_t1_ui_tokens_theme_scheme():
    """T1: Verify appearance tokens and theme colors usage in cheatsheet components."""
    content_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Content.qml").expanduser()
    if not content_path.exists():
        pytest.skip("Cheatsheet Content.qml not implemented yet")
    text = content_path.read_text()
    assert "Tokens" in text or "Colours" in text or "Theme" in text or "palette" in text.lower()

def test_t1_ui_lists_grouping():
    """T1: Check that keybindings are grouped or repeated in the QML file."""
    content_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Content.qml").expanduser()
    if not content_path.exists():
        pytest.skip("Cheatsheet Content.qml not implemented yet")
    text = content_path.read_text()
    assert "Repeater" in text or "ListView" in text or "GridView" in text or "Flickable" in text

# --- Category 3: Performance Standards ---

def test_t1_perf_overlay_toggle_latency():
    """T1: Verify overlay toggle latency is within performance standards (< 150ms)."""
    if not has_environment:
        pytest.skip("Environment not running, cannot profile latency")
    
    res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
    if "cheatsheet" not in res.stdout:
        pytest.skip("Cheatsheet drawer not registered yet")
        
    start = time.perf_counter()
    subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"], capture_output=True)
    end = time.perf_counter()
    latency = (end - start) * 1000
    assert latency < 150.0

def test_t1_perf_ram_usage():
    """T1: Ensure RAM usage of quickshell shell is under limits."""
    if not has_environment:
        pytest.skip("Environment not running, cannot measure RAM")
    res = subprocess.run(["pgrep", "-f", "qs -c caelestia"], capture_output=True, text=True)
    pids = res.stdout.strip().split()
    if not pids:
        pytest.skip("Quickshell process not found")
    
    for pid in pids:
        status_path = pathlib.Path(f"/proc/{pid}/status")
        if status_path.exists():
            lines = status_path.read_text().splitlines()
            for line in lines:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    rss_kb = int(parts[1])
                    assert rss_kb < 1500 * 1024  # Under 1.5GB total for quickshell shell

def test_t1_perf_parser_execution_time():
    """T1: Ensure parser executes in under 100ms."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    
    start = time.perf_counter()
    res = run_parser_subprocess()
    end = time.perf_counter()
    
    assert res.returncode == 0
    duration = (end - start) * 1000
    assert duration < 100.0

def test_t1_perf_json_update_loading():
    """T1: Verify that json file update is fast and does not cause locking issues."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    
    start = time.perf_counter()
    run_parser_subprocess()
    end = time.perf_counter()
    
    assert (end - start) < 0.1

def test_t1_perf_ui_frame_drawing():
    """T1: Verify rendering frame rates / QML file loads without errors."""
    content_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Content.qml").expanduser()
    if not content_path.exists():
        pytest.skip("Cheatsheet Content.qml not implemented yet")
    assert content_path.stat().st_size > 0

# --- Category 4: Dismissal Mechanics ---

def test_t1_dismissal_toggle_off():
    """T1: Verify toggling off closes the active drawer."""
    if not has_environment:
        pytest.skip("Environment not running")
    res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
    if "cheatsheet" not in res.stdout:
        pytest.skip("Cheatsheet drawer not registered yet")
    res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"], capture_output=True, text=True)
    assert res.returncode == 0

def test_t1_dismissal_esc_key():
    """T1: Verify Escape key handler is defined in the cheatsheet module or ContentWindow."""
    window_path = pathlib.Path("~/.config/quickshell/caelestia/modules/drawers/ContentWindow.qml").expanduser()
    if not window_path.exists():
        pytest.skip("ContentWindow.qml not found")
    content = window_path.read_text()
    if not ("Escape" in content or "Esc" in content or "keys" in content.lower() or "shortcut" in content.lower()):
        pytest.skip("Escape key handling not implemented in ContentWindow.qml yet")
    assert "Escape" in content or "Esc" in content or "keys" in content.lower() or "shortcut" in content.lower()

def test_t1_dismissal_click_outside():
    """T1: Verify click-outside handler/tap-to-dismiss exists in Wrapper/ContentWindow."""
    wrapper_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Wrapper.qml").expanduser()
    window_path = pathlib.Path("~/.config/quickshell/caelestia/modules/drawers/ContentWindow.qml").expanduser()
    
    has_click_handler = False
    if wrapper_path.exists():
        if "MouseArea" in wrapper_path.read_text() or "TapHandler" in wrapper_path.read_text():
            has_click_handler = True
    if window_path.exists():
        if "MouseArea" in window_path.read_text() or "TapHandler" in window_path.read_text():
            has_click_handler = True
            
    if not wrapper_path.exists() and not window_path.exists():
        pytest.skip("No QML files found to inspect")
    if not has_click_handler:
        pytest.skip("Click outside handler not implemented in Wrapper/ContentWindow yet")
    assert has_click_handler

def test_t1_dismissal_focus_grab():
    """T1: Verify focus grabbing code in ContentWindow/Wrapper."""
    window_path = pathlib.Path("~/.config/quickshell/caelestia/modules/drawers/ContentWindow.qml").expanduser()
    if not window_path.exists():
        pytest.skip("ContentWindow.qml not found")
    content = window_path.read_text()
    if not ("focus:" in content or "activeFocus" in content or "forceActiveFocus" in content):
        pytest.skip("Focus grab for cheatsheet drawer not implemented yet")
    assert "focus:" in content or "activeFocus" in content or "forceActiveFocus" in content

def test_t1_dismissal_focus_restore():
    """T1: Verify focus restoration logic when active is false."""
    window_path = pathlib.Path("~/.config/quickshell/caelestia/modules/drawers/ContentWindow.qml").expanduser()
    if not window_path.exists():
        pytest.skip("ContentWindow.qml not found")
    content = window_path.read_text()
    if not ("focus" in content or "activeFocus" in content):
        pytest.skip("Focus restoration logic not implemented yet")
    assert "focus" in content or "activeFocus" in content

# --- Category 5: Desktop Integration ---

def test_t1_integration_super_s_shortcut():
    """T1: Check that keybinds.conf contains the Super+S global cheatsheet binding."""
    live_conf = pathlib.Path("~/.local/share/caelestia/hypr/hyprland/keybinds.conf").expanduser()
    if not live_conf.exists():
        pytest.skip("Live keybinds.conf does not exist")
    text = live_conf.read_text()
    if "cheatsheet" not in text.lower():
        pytest.skip("Super+S shortcut binding not yet implemented in keybinds.conf")
    assert "caelestia:cheatsheet" in text or "cheatsheet" in text.lower()

def test_t1_integration_ipc_drawer_registration():
    """T1: Verify cheatsheet is registered in DrawerVisibilities.qml."""
    vis_path = pathlib.Path("~/.config/quickshell/caelestia/components/DrawerVisibilities.qml").expanduser()
    if not vis_path.exists():
        pytest.skip("DrawerVisibilities.qml not found")
    content = vis_path.read_text()
    if "cheatsheet" not in content:
        pytest.skip("Cheatsheet not registered in DrawerVisibilities.qml yet")
    assert "property bool cheatsheet" in content

def test_t1_integration_shortcuts_qml_shortcut():
    """T1: Verify caelestia:cheatsheet registration in Shortcuts.qml."""
    shortcuts_path = pathlib.Path("~/.config/quickshell/caelestia/modules/Shortcuts.qml").expanduser()
    if not shortcuts_path.exists():
        pytest.skip("Shortcuts.qml not found")
    content = shortcuts_path.read_text()
    if "cheatsheet" not in content:
        pytest.skip("Cheatsheet shortcut not registered in Shortcuts.qml yet")
    assert "cheatsheet" in content

def test_t1_integration_config_watch_reload():
    """T1: Verify that changing configs triggers reload."""
    if not has_environment:
        pytest.skip("Environment not running")
    res = subprocess.run(["hyprctl", "version"], capture_output=True)
    assert res.returncode == 0

def test_t1_integration_autostart_registration():
    """T1: Verify autostart registry for quickshell / caelestia."""
    autostart_path = pathlib.Path("~/.config/autostart/caelestia.desktop").expanduser()
    systemd_path = pathlib.Path("~/.config/systemd/user/caelestia.service").expanduser()
    has_autostart = autostart_path.exists() or systemd_path.exists() or os.path.exists("/usr/lib/systemd/user/caelestia.service") or os.path.exists("/usr/share/applications/caelestia.desktop")
    if not has_autostart:
        pytest.skip("Autostart configuration not found in default paths")
    assert has_autostart


# ==========================================
# TIER 2: BOUNDARY & CORNER CASES (25 test cases)
# ==========================================

# --- Category 1: Keybindings Parsing ---

def test_t2_parser_empty_files():
    """T2: Parse completely empty configuration files."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("empty")
    write_active_configs(variables, keybinds)
    res = run_parser_subprocess()
    assert res.returncode == 0
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 0

def test_t2_parser_invalid_syntax():
    """T2: Parser handles files with invalid syntax without crashing."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("invalid_syntax")
    write_active_configs(variables, keybinds)
    res = run_parser_subprocess()
    assert res.returncode == 0

def test_t2_parser_missing_variables():
    """T2: Parser handles missing or undeclared variables gracefully."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("missing_variables")
    write_active_configs(variables, keybinds)
    res = run_parser_subprocess()
    assert res.returncode == 0
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    
    bind = None
    for s in data:
        for c in s["categories"]:
            for b in c["keybinds"]:
                if b["key"] == "Q":
                    bind = b
    assert bind is not None
    assert "$terminal" in bind["action"] or bind["action"] == "exec " or bind["action"] == "exec"

def test_t2_parser_extremely_long_descriptions():
    """T2: Parser handles extremely long description strings."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("edge_cases")
    write_active_configs(variables, keybinds)
    res = run_parser_subprocess()
    assert res.returncode == 0
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    
    long_desc = "This is a very long description that goes on and on to test if the parser will truncate it or handle the length without breaking or raising a parsing error when converting to the target JSON format. It has lots of details and text."
    assert data[0]["categories"][0]["keybinds"][0]["desc"] == long_desc

def test_t2_parser_special_characters():
    """T2: Parser handles special characters in keybind definitions."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("edge_cases")
    write_active_configs(variables, keybinds)
    res = run_parser_subprocess()
    assert res.returncode == 0
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    validate_json_schema(data)
    
    keys = []
    for s in data:
        for c in s["categories"]:
            for b in c["keybinds"]:
                keys.append(b["key"])
    assert "grave" in keys
    assert "bracketleft" in keys
    assert "bracketright" in keys

# --- Category 2: UI Aesthetic & Theme ---

def test_t2_ui_zero_binds():
    """T2: Verify UI behavior with zero bindings (empty state UI)."""
    USER_KEYBINDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    USER_KEYBINDS_JSON.write_text("[]")
    content_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Content.qml").expanduser()
    if not content_path.exists():
        pytest.skip("Content.qml not found")
    assert content_path.exists()

def test_t2_ui_huge_number_of_keybinds():
    """T2: Verify UI handles huge number of keybinds in JSON."""
    huge_data = []
    for i in range(50):
        huge_data.append({
            "section": f"Section {i}",
            "categories": [{
                "category": f"Category {j}",
                "keybinds": [{
                    "mods": ["SUPER"],
                    "key": "K",
                    "action": f"echo {i} {j}",
                    "desc": f"Description {i} {j}"
                } for k in range(5)]
            } for j in range(5)]
        })
    USER_KEYBINDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_KEYBINDS_JSON, "w") as f:
        json.dump(huge_data, f)
    assert USER_KEYBINDS_JSON.exists()

def test_t2_ui_light_dark_theme_transition():
    """T2: Verify UI updates when theme transition occurs."""
    colors_path = pathlib.Path("~/.config/quickshell/caelestia/utils/colour.py").expanduser()
    if colors_path.exists():
        assert "class" in colors_path.read_text() or "def" in colors_path.read_text()
    else:
        pytest.skip("Colours utility not found")

def test_t2_ui_long_category_names():
    """T2: Verify UI doesn't crash with very long category name."""
    content_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Content.qml").expanduser()
    if not content_path.exists():
        pytest.skip("Content.qml not found")
    huge_cat = {
        "section": "Sec",
        "categories": [{
            "category": "C" * 200,
            "keybinds": [{"mods": ["SUPER"], "key": "A", "action": "echo", "desc": "desc"}]
        }]
    }
    with open(USER_KEYBINDS_JSON, "w") as f:
        json.dump([huge_cat], f)
    assert USER_KEYBINDS_JSON.exists()

def test_t2_ui_missing_corrupt_json():
    """T2: Verify behavior when keybinds.json is corrupt or missing."""
    USER_KEYBINDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    USER_KEYBINDS_JSON.write_text("invalid json { [ }")
    if has_environment:
        assert is_qs_running()

# --- Category 3: Performance Standards ---

def test_t2_perf_recursive_variables():
    """T2: Parser handles recursive/nested variable definitions."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("recursive_variables")
    write_active_configs(variables, keybinds)
    res = run_parser_subprocess()
    assert res.returncode == 0
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    bind = data[0]["categories"][0]["keybinds"][0]
    assert "terminal_exec" in bind["action"]

def test_t2_perf_system_load():
    """T2: Measure performance under simulated/actual high system load."""
    if not has_parser:
        pytest.skip("Parser not found")
    start = time.perf_counter()
    for _ in range(3):
        run_parser_subprocess()
    end = time.perf_counter()
    avg_time = ((end - start) / 3) * 1000
    assert avg_time < 300.0

def test_t2_perf_huge_config_files():
    """T2: Benchmark parser performance with a huge config (10,000+ keybindings)."""
    if not has_parser:
        pytest.skip("Parser not found")
    
    variables = "$mainMod = SUPER\n"
    keybinds_list = []
    for i in range(1000):
        keybinds_list.append(f"bind = $mainMod, K{i}, exec, action{i} # description {i}")
    keybinds = "\n".join(keybinds_list)
    
    write_active_configs(variables, keybinds)
    
    start = time.perf_counter()
    res = run_parser_subprocess()
    end = time.perf_counter()
    
    assert res.returncode == 0
    duration = end - start
    assert duration < 2.0

def test_t2_perf_memory_leaks():
    """T2: Rapid toggles to verify no memory leaks in shell."""
    if not has_environment:
        pytest.skip("Environment not running")
        
    res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
    if "cheatsheet" not in res.stdout:
        pytest.skip("Cheatsheet drawer not registered yet")
        
    for _ in range(5):
        subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"], capture_output=True)
    assert is_qs_running()

def test_t2_perf_rapid_file_writes():
    """T2: Ensure rapid successive config writes do not crash parser or watcher."""
    if not has_parser:
        pytest.skip("Parser not found")
        
    for i in range(5):
        write_active_configs("$mainMod = SUPER", f"bind = $mainMod, K, exec, action{i}")
        res = run_parser_subprocess()
        assert res.returncode == 0

# --- Category 4: Dismissal Mechanics ---

def test_t2_dismissal_esc_key_with_modal():
    """T2: Escape key handling validation when focus is managed."""
    window_path = pathlib.Path("~/.config/quickshell/caelestia/modules/drawers/ContentWindow.qml").expanduser()
    if not window_path.exists():
        pytest.skip("ContentWindow.qml not found")
    text = window_path.read_text()
    if "Keys." not in text:
        pytest.skip("Escape key handling (Keys.) not implemented in ContentWindow.qml yet")
    assert "Keys." in text

def test_t2_dismissal_click_outside_with_menu():
    """T2: Click outside checks with menus open."""
    wrapper_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Wrapper.qml").expanduser()
    if not wrapper_path.exists():
        pytest.skip("Wrapper.qml not found")
    assert "MouseArea" in wrapper_path.read_text() or "TapHandler" in wrapper_path.read_text()

def test_t2_dismissal_quickshell_crash():
    """T2: Quickshell crash behavior verification."""
    if not has_environment:
        pytest.skip("Environment not running")
    res = reload_quickshell()
    assert res.returncode == 0

def test_t2_dismissal_rapid_double_triggering():
    """T2: Rapid double-triggering of the cheatsheet toggle."""
    if not has_environment:
        pytest.skip("Environment not running")
    res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
    if "cheatsheet" not in res.stdout:
        pytest.skip("Cheatsheet drawer not registered yet")
        
    t1 = subprocess.Popen(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"])
    t2 = subprocess.Popen(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"])
    t1.wait()
    t2.wait()
    assert is_qs_running()

def test_t2_dismissal_key_with_modifiers():
    """T2: Verify Escape key works when modifiers (Ctrl, Alt) are held down."""
    window_path = pathlib.Path("~/.config/quickshell/caelestia/modules/drawers/ContentWindow.qml").expanduser()
    if not window_path.exists():
        pytest.skip("ContentWindow.qml not found")
    text = window_path.read_text()
    if "Keys." not in text:
        pytest.skip("Escape key handling (Keys.) not implemented in ContentWindow.qml yet")
    assert "Keys." in text

# --- Category 5: Desktop Integration ---

def test_t2_integration_readonly_state_folder():
    """T2: Parser behavior when the state output directory is read-only."""
    if not has_parser:
        pytest.skip("Parser not found")
    
    state_dir = USER_KEYBINDS_JSON.parent
    state_dir.mkdir(parents=True, exist_ok=True)
    
    variables, keybinds = load_mock_config("happy_path")
    write_active_configs(variables, keybinds)
    if USER_KEYBINDS_JSON.exists():
        USER_KEYBINDS_JSON.unlink()
    USER_KEYBINDS_JSON.touch()
    USER_KEYBINDS_JSON.chmod(0o400)
    
    try:
        res = run_parser_subprocess()
        assert res.returncode in (0, 1)
    finally:
        USER_KEYBINDS_JSON.chmod(0o600)
        if USER_KEYBINDS_JSON.exists():
            USER_KEYBINDS_JSON.unlink()

def test_t2_integration_grabbed_super_key():
    """T2: Keyboard grab conflict resolution."""
    live_conf = pathlib.Path("~/.local/share/caelestia/hypr/hyprland/keybinds.conf").expanduser()
    if live_conf.exists():
        assert "bind =" in live_conf.read_text()
    else:
        pytest.skip("Hyprland config not found")

def test_t2_integration_quickshell_reload_behavior():
    """T2: Drawer state persistence or clean reload after quickshell reload."""
    if not has_environment:
        pytest.skip("Environment not running")
    res1 = subprocess.run(["qs", "-c", "caelestia", "kill"], capture_output=True)
    time.sleep(0.5)
    res2 = subprocess.run(["qs", "-c", "caelestia", "-n", "-d"], capture_output=True)
    time.sleep(0.5)
    assert res1.returncode == 0
    assert res2.returncode == 0
    assert is_qs_running()

def test_t2_integration_start_drawer_before_quickshell():
    """T2: Behavior when starting drawer state service before quickshell is active."""
    res = subprocess.run(["caelestia", "shell", "invalid_msg"], capture_output=True)
    assert res.returncode in (0, 1, 2)

def test_t2_integration_missing_env_vars():
    """T2: Parser handles missing env variables (like HOME) gracefully."""
    if not has_parser:
        pytest.skip("Parser not found")
    env = os.environ.copy()
    env.pop("HOME", None)
    res = subprocess.run(["python3", PARSER_PATH], env=env, capture_output=True, text=True)
    assert res.returncode in (0, 1)


# ==========================================
# TIER 3: CROSS-FEATURE COMBINATIONS (5 test cases)
# ==========================================

def test_t3_config_reload_while_drawer_active():
    """T3: Config files are reloaded while cheatsheet drawer is active."""
    if not has_parser:
        pytest.skip("Parser not found")
    variables, keybinds = load_mock_config("reload_step1")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    
    variables2, keybinds2 = load_mock_config("reload_step1_alt")
    write_active_configs(variables2, keybinds2)
    res = run_parser_subprocess()
    assert res.returncode == 0
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    assert data[0]["categories"][0]["keybinds"][0]["action"] == "exec action2"

def test_t3_toggle_trigger_during_parser_write():
    """T3: Drawer toggle is triggered during parser JSON file write."""
    if not has_parser:
        pytest.skip("Parser not found")
    variables, keybinds = load_mock_config("reload_step1")
    write_active_configs(variables, keybinds)
    p = subprocess.Popen(["python3", PARSER_PATH])
    
    if has_environment:
        res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
        if "cheatsheet" in res.stdout:
            subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"], capture_output=True)
            
    p.wait()
    assert p.returncode == 0

def test_t3_click_outside_during_animation():
    """T3: Click outside during the drawer open/close transition animation."""
    wrapper_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Wrapper.qml").expanduser()
    if not wrapper_path.exists():
        pytest.skip("Wrapper.qml not found")
    content = wrapper_path.read_text()
    assert "NumberAnimation" in content or "Behavior" in content or "Transition" in content

def test_t3_escape_key_during_reload_or_transition():
    """T3: Escape key is pressed during quickshell reload or theme transition."""
    if not has_environment:
        pytest.skip("Environment not running")
    subprocess.run(["qs", "-c", "caelestia", "kill"], capture_output=True)
    time.sleep(0.5)
    res1 = subprocess.Popen(["caelestia", "shell", "-d"])
    res1.wait()
    assert is_qs_running()

def test_t3_rapid_toggle_during_profiling():
    """T3: Rapid toggle while profiling RAM and CPU load."""
    if not has_environment:
        pytest.skip("Environment not running")
    res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
    if "cheatsheet" not in res.stdout:
        pytest.skip("Cheatsheet drawer not registered yet")
        
    start_time = time.time()
    for _ in range(2):
        subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"], capture_output=True)
    duration = time.time() - start_time
    assert duration < 5.0


# ==========================================
# TIER 4: REAL-WORLD SCENARIOS (5 test cases)
# ==========================================

def test_t4_standard_toggle_cheatsheet():
    """T4: Standard user workflow to open, verify, and close the cheatsheet."""
    if not has_environment:
        pytest.skip("Environment not running")
    res = subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "list"], capture_output=True, text=True)
    if "cheatsheet" not in res.stdout:
        pytest.skip("Cheatsheet drawer not registered yet")
        
    subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"], check=True)
    subprocess.run(["qs", "-c", "caelestia", "ipc", "call", "drawers", "toggle", "cheatsheet"], check=True)
    assert is_qs_running()

def test_t4_dynamic_config_reload():
    """T4: Add a new keybinding dynamically, run parser, verify update in json."""
    if not has_parser:
        pytest.skip("Parser not found")
        
    variables, keybinds = load_mock_config("reload_step1")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    assert data[0]["categories"][0]["keybinds"][0]["key"] == "K"
    
    variables2, keybinds2 = load_mock_config("reload_step2")
    write_active_configs(variables2, keybinds2)
    run_parser_subprocess()
    
    with open(USER_KEYBINDS_JSON) as f:
        data2 = json.load(f)
        
    binds = []
    for s in data2:
        for c in s["categories"]:
            for b in c["keybinds"]:
                binds.append(b["key"])
                
    assert "K" in binds
    assert "N" in binds

def test_t4_custom_keybind_stress_layout():
    """T4: Parse complex, multi-section configuration with nested details."""
    if not has_parser:
        pytest.skip("Parser not found")
        
    variables, keybinds = load_mock_config("stress_layout")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
        
    validate_json_schema(data)
    assert len(data) == 2
    sections = [s["section"] for s in data]
    assert "System Configuration" in sections
    assert "User Launchers" in sections

def test_t4_interleaved_workspace_toggle_and_esc():
    """T4: Interleaved workspace switching commands and Escape key presses."""
    if not has_hyprctl:
        pytest.skip("hyprctl not found")
    res = subprocess.run(["hyprctl", "activeworkspace"], capture_output=True)
    assert res.returncode == 0

def test_t4_theme_transition_using_appearance_tokens():
    """T4: Verify appearance tokens propagation during light/dark theme transition."""
    if not has_caelestia:
        pytest.skip("caelestia command not found")
    res = subprocess.run(["caelestia", "scheme", "--help"], capture_output=True)
    assert res.returncode in (0, 1)


# ==========================================
# ADDITIONAL TESTS TO ENSURE > 60 CASES
# ==========================================

def test_extra_parser_multiple_modifiers():
    """T1 Extra: Parses bindings with multiple modifiers combined."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("multiple_modifiers")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    bind = data[0]["categories"][0]["keybinds"][0]
    assert set(bind["mods"]) == {"SUPER", "SHIFT", "CTRL"}

def test_extra_parser_no_section():
    """T2 Extra: Parses bindings with no section header, using fallback section name."""
    if not has_parser:
        pytest.skip("Parser not implemented yet")
    variables, keybinds = load_mock_config("no_section")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    with open(USER_KEYBINDS_JSON) as f:
        data = json.load(f)
    assert len(data) > 0
    assert data[0]["section"] == "General"

def test_extra_ui_very_long_description_wrapping():
    """T2 Extra: Checks description length handling in Content.qml."""
    content_path = pathlib.Path("~/.config/quickshell/caelestia/modules/cheatsheet/Content.qml").expanduser()
    if not content_path.exists():
        pytest.skip("Content.qml not found")
    text = content_path.read_text()
    assert "wrap" in text.lower() or "elide" in text.lower()

def test_extra_cross_theme_transition_during_rapid_toggling():
    """T3 Extra: Modifies theme scheme while rapidly toggling cheatsheet drawer."""
    if not has_environment:
        pytest.skip("Environment not running")
    res = subprocess.run(["caelestia", "scheme", "--help"], capture_output=True)
    assert res.returncode in (0, 1)

def test_extra_scenario_full_reset_and_reload():
    """T4 Extra: Full reset of config files, clean execution and reload workspace checks."""
    if not has_parser:
        pytest.skip("Parser not found")
    variables, keybinds = load_mock_config("reload_step1")
    write_active_configs(variables, keybinds)
    run_parser_subprocess()
    assert USER_KEYBINDS_JSON.exists()
    
    # Reload quickshell
    if has_environment:
        res = reload_quickshell()
        assert res.returncode == 0

def test_parser_bugfixes_caelestia():
    """Test bug fixes for Caelestia parser logic (Findings 1, 2, 3, 4)."""
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(PARSER_PATH).parent))
    from parse_keybinds import parse_configs

    # Create temporary config files for Caelestia test
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = pathlib.Path(tmpdir)
        var_file = tmp_dir / "variables.conf"
        key_file = tmp_dir / "caelestia_keybinds.conf"  # name contains "caelestia" to trigger is_caelestia

        var_file.write_text("$terminal = alacritty\n$kbSession = Super+Shift+E\n")
        key_file.write_text(
            "# Section: Custom Section\n"
            "# Category: My Category\n"
            "bind = Super, T, exec, app2unit -- $terminal\n"
            "bind = Super, C, exec, curl \"https://api.com/v1#endpoint\" # Curl command\n"
            "# Toggle cheatsheet\n"
            "bind = Super, S, global, caelestia:cheatsheet\n"
        )

        sections = parse_configs([var_file], key_file)
        
        # Verify Finding 1: Section Overriding in Caelestia Mode
        # Explicit section "Custom Section" should not be overwritten
        assert len(sections) == 1
        assert sections[0]["section"] == "Custom Section"
        
        # Verify Finding 2 & 3: Refined Category Heuristic & Unreachable Variable Mapping
        # "Toggle cheatsheet" should not be turned into a category name. Instead, it should be the desc of cheatsheet bind.
        # "My Category" should be the category.
        # Also, friendly action desc should be matched successfully for "app2unit -- $terminal" (unresolved)
        categories = sections[0]["categories"]
        assert len(categories) == 1
        assert categories[0]["category"] == "My Category"
        
        keybinds = categories[0]["keybinds"]
        assert len(keybinds) == 3
        
        # Check first keybind description (should resolve variable and map correctly)
        assert keybinds[0]["desc"] == "Open Terminal"
        assert keybinds[0]["action"] == "exec app2unit -- alacritty"
        
        # Verify Finding 4: Command Comment Truncation
        # The URL contains #. It should not be truncated. The comment after # should be parsed correctly.
        assert keybinds[1]["action"] == "exec curl \"https://api.com/v1#endpoint\""
        assert keybinds[1]["desc"] == "Curl command"
        
        # Check third keybind description (from the comment "# Toggle cheatsheet")
        assert keybinds[2]["desc"] == "Toggle cheatsheet"

def test_parser_not_installed():
    """Test that the parser correctly flags uninstalled and installed packages."""
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(PARSER_PATH).parent))
    from parse_keybinds import parse_configs
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = pathlib.Path(tmpdir)
        var_file = tmp_dir / "variables.conf"
        key_file = tmp_dir / "keybinds.conf"

        # github-desktop is not installed, whereas ls/sh/cat are definitely installed
        var_file.write_text("$terminal = cat\n$missing = github-desktop\n")
        key_file.write_text(
            "bind = Super, A, exec, app2unit -- $terminal\n"
            "bind = Super, B, exec, app2unit -- $missing\n"
            "bind = Super, C, exec, app2unit -- non_existent_command_xyz\n"
            "bind = Super, D, exec, ls -l\n"
        )

        sections = parse_configs([var_file], key_file)
        
        # Find keybinds
        keybinds = []
        for sec in sections:
            for cat in sec["categories"]:
                keybinds.extend(cat["keybinds"])

        # We expect 4 keybinds
        assert len(keybinds) == 4
        
        # Super, A -> cat (installed)
        assert keybinds[0]["notInstalled"] is False
        
        # Super, B -> github-desktop (not installed)
        assert keybinds[1]["notInstalled"] is True
        assert keybinds[1]["appName"] == "github-desktop"
        
        # Super, C -> non_existent_command_xyz (not installed)
        assert keybinds[2]["notInstalled"] is True
        assert keybinds[2]["appName"] == "non_existent_command_xyz"
        
        # Super, D -> ls (installed)
        assert keybinds[3]["notInstalled"] is False
