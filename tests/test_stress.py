import os
import sys
import json
import subprocess
import tempfile
import pathlib
import pytest

TESTS_DIR = pathlib.Path(__file__).parent.resolve()
PARSER_PATH = str(TESTS_DIR.parent / "parser" / "parse_keybinds.py")

def run_parser(variables_paths, keybinds_path, output_path):
    cmd = ["python3", PARSER_PATH]
    if variables_paths:
        cmd.extend(["--variables"] + [str(p) for p in variables_paths])
    else:
        cmd.extend(["--variables", "/dev/null"])
    cmd.extend(["--keybinds", str(keybinds_path)])
    cmd.extend(["--output", str(output_path)])
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res

def run_parser_with_content(var_content, keybinds_content):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        var_file = tmp_path / "variables.conf"
        key_file = tmp_path / "keybinds.conf"
        out_file = tmp_path / "keybinds.json"
        
        var_file.write_text(var_content, encoding='utf-8')
        key_file.write_text(keybinds_content, encoding='utf-8')
        
        res = run_parser([var_file], key_file, out_file)
        
        data = None
        if res.returncode == 0 and out_file.exists():
            with open(out_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    pass
                
        return res, data

def test_stress_extremely_long_variables():
    """Stress test: Extremely long variable names and values."""
    var_name = "V" * 5000
    var_val = "A" * 10000
    var_content = f"${var_name} = {var_val}\n"
    keybinds_content = f"bind = SUPER, T, exec, ${var_name}\n"
    
    res, data = run_parser_with_content(var_content, keybinds_content)
    assert res.returncode == 0
    assert data is not None
    bind = data[0]["categories"][0]["keybinds"][0]
    assert bind["action"] == f"exec {var_val}"

def test_stress_deeply_nested_variables():
    """Stress test: 50 nested variable definitions (under recursion limit)."""
    var_lines = []
    for i in range(1, 50):
        var_lines.append(f"$v{i} = $v{i+1}")
    var_lines.append("$v50 = final_val")
    var_content = "\n".join(var_lines)
    keybinds_content = "bind = SUPER, T, exec, $v1"
    
    res, data = run_parser_with_content(var_content, keybinds_content)
    assert res.returncode == 0
    assert data is not None
    bind = data[0]["categories"][0]["keybinds"][0]
    assert bind["action"] == "exec final_val"

def test_stress_recursion_overflow():
    """Stress test: Variable chain exceeding Python recursion limit (1500 nesting) crashes the parser."""
    var_lines = []
    for i in range(1, 1500):
        var_lines.append(f"$v{i} = $v{i+1}")
    var_lines.append("$v1500 = final_val")
    var_content = "\n".join(var_lines)
    keybinds_content = "bind = SUPER, T, exec, $v1"
    
    res, data = run_parser_with_content(var_content, keybinds_content)
    # Parser crashes with RecursionError, which returns code 1
    assert res.returncode == 1
    assert "RecursionError" in res.stderr

def test_stress_circular_variables():
    """Stress test: Circular variable dependencies (infinite loop protection)."""
    var_content = "$v1 = $v2\n$v2 = $v1"
    keybinds_content = "bind = SUPER, T, exec, $v1"
    
    res, data = run_parser_with_content(var_content, keybinds_content)
    assert res.returncode == 0
    assert data is not None
    bind = data[0]["categories"][0]["keybinds"][0]
    # Circle should be detected and variable returned as is
    assert bind["action"] in ("exec $v1", "exec $v2")

def test_stress_special_characters():
    """Stress test: Non-ASCII characters, symbols, and backslashes in all fields."""
    var_content = "$my_var = @#$%^&*()_+{}|:\"<>?[]\\;',./~` \u263A \u4E2D\u6587\n"
    keybinds_content = r"""
# Section: 中文节
# Category: 안녕하세요
# `~!@#$%^&*()_+{}|[]\\:";'<>?,./
bind = SUPER SHIFT ALT, bracketleft, exec, $my_var
"""
    res, data = run_parser_with_content(var_content, keybinds_content)
    assert res.returncode == 0
    assert data is not None
    assert data[0]["section"] == "中文节"
    assert data[0]["categories"][0]["category"] == "안녕하세요"
    bind = data[0]["categories"][0]["keybinds"][0]
    assert bind["desc"] == "`~!@#$%^&*()_+{}|[]\\\\:\";'<>?,./"
    assert bind["action"] == "exec @#$%^&*()_+{}|:\"<>?[]\\;',./~` \u263A \u4E2D\u6587"

def test_stress_whitespace_variations():
    """Stress test: Mixed tabs, spaces, carriage returns, and empty lines."""
    var_content = "\r\n  $mainMod   \t  =   \t SUPER   \r\n\r\n"
    keybinds_content = """\r
\r
# Section:   Spaced Section   \r
# Category: \t Spaced Category \t \r
\t # \t Spaced Description \t \r
bind \t = \t $mainMod \t SHIFT \t , \t space \t , \t exec \t , \t kitty \t \r
"""
    res, data = run_parser_with_content(var_content, keybinds_content)
    assert res.returncode == 0
    assert data is not None
    assert data[0]["section"] == "Spaced Section"
    assert data[0]["categories"][0]["category"] == "Spaced Category"
    bind = data[0]["categories"][0]["keybinds"][0]
    assert bind["mods"] == ["SUPER", "SHIFT"]
    assert bind["key"] == "space"
    assert bind["action"] == "exec kitty"
    assert bind["desc"] == "Spaced Description"

def test_stress_invalid_syntax():
    """Stress test: Partially formed bind statements and bad syntax."""
    var_content = """
$invalid-name = value
$123var = value
$ = value
= value
"""
    keybinds_content = """
bind = 
bind = SUPER
bind = SUPER,
bind = SUPER, K
bind = SUPER, K,
bind = SUPER T exec kitty
bind = SUPER, T, exec, kitty, extra1, extra2, extra3
"""
    res, data = run_parser_with_content(var_content, keybinds_content)
    assert res.returncode == 0
    # Should run and exit 0, ignoring bad lines

def test_stress_directory_input():
    """Stress test: Directory passed as variable file instead of standard file crashes the parser."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        dir_var = tmp_path / "dir_var.conf"
        dir_var.mkdir()
        key_file = tmp_path / "keybinds.conf"
        key_file.write_text("bind = SUPER, T, exec, ls", encoding='utf-8')
        out_file = tmp_path / "keybinds.json"
        
        res = run_parser([dir_var], key_file, out_file)
        assert res.returncode == 1
        assert "IsADirectoryError" in res.stderr
