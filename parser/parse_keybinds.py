#!/usr/bin/env python3
import os
import sys
import re
import json
import argparse
from pathlib import Path
import shutil

# Normalization map for modifiers
MOD_NORMALIZATION = {
    "super": "SUPER",
    "mod4": "SUPER",
    "ctrl": "CTRL",
    "control": "CTRL",
    "alt": "ALT",
    "mod1": "ALT",
    "meta": "ALT",
    "shift": "SHIFT"
}

def normalize_modifier(mod):
    mod_stripped = mod.strip()
    if mod_stripped.startswith('$'):
        return mod_stripped  # Preserve variable name exactly as-is
    m = mod_stripped.lower()
    return MOD_NORMALIZATION.get(m, mod_stripped.upper())

# Friendly descriptions dictionary
FRIENDLY_ACTIONS = {
    "global, caelestia:launcher": "Toggle Launcher",
    "global, caelestia:session": "Toggle Session Menu",
    "global, caelestia:sidebar": "Toggle Sidebar / Notifications",
    "global, caelestia:clearnotifs": "Clear Notifications",
    "global, caelestia:showall": "Toggle Overview / Panels",
    "global, caelestia:lock": "Lock Screen",
    "global, caelestia:brightnessup": "Increase Brightness",
    "global, caelestia:brightnessdown": "Decrease Brightness",
    "global, caelestia:mediatoggle": "Play/Pause Media",
    "global, caelestia:medianext": "Next Track",
    "global, caelestia:mediaprev": "Previous Track",
    "global, caelestia:mediastop": "Stop Media",
    "global, caelestia:screenshotfreeze": "Screenshot Region (Freeze)",
    "global, caelestia:screenshot": "Screenshot Region",
    "global, caelestia:cheatsheet": "Toggle Cheatsheet",
    
    "exec caelestia shell -d": "Start Caelestia Shell",
    "exec qs -c caelestia kill": "Kill Caelestia Shell",
    "exec qs -c caelestia kill; sleep .1; caelestia shell -d": "Restart Caelestia Shell",
    
    "workspace, -1": "Switch to Previous Workspace",
    "workspace, +1": "Switch to Next Workspace",
    "workspace, -10": "Switch to Previous Workspace Group",
    "workspace, +10": "Switch to Next Workspace Group",
    "movetoworkspace, -1": "Move Window to Previous Workspace",
    "movetoworkspace, +1": "Move Window to Next Workspace",
    "movetoworkspace, special:special": "Move Window to Special Workspace",
    "movetoworkspace, e+0": "Move Window from Special Workspace",
    
    "cyclenext": "Focus Next Window",
    "cyclenext, prev": "Focus Previous Window",
    "changegroupactive, f": "Next Window in Group",
    "changegroupactive, b": "Previous Window in Group",
    "togglegroup": "Toggle Window Group",
    "moveoutofgroup": "Move Window Out of Group",
    "lockactivegroup, toggle": "Toggle Lock Active Group",
    
    "swapnext": "Swap with Next Window",
    "swapnext, prev": "Swap with Previous Window",
    
    "focusmonitor, +1": "Focus Next Monitor",
    "focusmonitor, -1": "Focus Previous Monitor",
    "movewindow, mon:+1": "Move Window to Next Monitor",
    "movewindow, mon:-1": "Move Window to Previous Monitor",
    "movecurrentworkspacetomonitor, +1": "Move Workspace to Next Monitor",
    "movecurrentworkspacetomonitor, -1": "Move Workspace to Previous Monitor",
    
    "resizeactive, 5% 0": "Resize: Expand Width",
    "resizeactive, -5% 0": "Resize: Shrink Width",
    "resizeactive, 0 -10%": "Resize: Shrink Height",
    "resizeactive, 0 10%": "Resize: Expand Height",
    "resizeactive, -10% 0": "Resize: Shrink Width",
    "resizeactive, 10% 0": "Resize: Expand Width",
    "movewindow": "Move Window",
    "resizewindow": "Resize Window",
    "centerwindow, 1": "Center Window",
    "resizeactive, exact 55% 70%": "Resize Window to 55%x70%",
    
    "exec caelestia resizer pip": "Toggle Picture-in-Picture Mode",
    "pin": "Pin Window (Show on all Workspaces)",
    "fullscreen, 0": "Toggle Fullscreen",
    "fullscreen, 1": "Toggle Fullscreen (with borders)",
    "togglefloating": "Toggle Floating Mode",
    "killactive": "Close Active Window",
    
    "exec caelestia toggle sysmon": "Toggle System Monitor Workspace",
    "exec caelestia toggle music": "Toggle Music Workspace",
    "exec caelestia toggle communication": "Toggle Communication Workspace",
    "exec caelestia toggle todo": "Toggle Todo Workspace",
    "exec caelestia toggle specialws": "Toggle Special Workspace",
    
    "exec hyprctl switchxkblayout all 0 && app2unit -- $terminal": "Open Terminal",
    "exec app2unit -- $terminal": "Open Terminal",
    "exec app2unit -- $browser": "Open Web Browser",
    "exec app2unit -- $editor": "Open Text Editor",
    "exec app2unit -- antigravity": "Open Antigravity",
    "exec app2unit -- github-desktop": "Open GitHub Desktop",
    "exec app2unit -- $fileexplorer": "Open File Manager",
    "exec app2unit -- nemo": "Open Nemo File Manager",
    "exec app2unit -- qps": "Open Process Manager",
    "exec app2unit -- pavucontrol": "Open Volume Control",
    "exec telegram": "Open Telegram",
    "exec $terminal -e calcurse": "Open Calendar",
    "exec caelestia record -s": "Record Screen (with Sound)",
    "exec caelestia record": "Record Screen",
    "exec caelestia record -r": "Record Region",
    "exec hyprpicker -a": "Open Color Picker",
    
    "exec wpctl set-mute @default_audio_source@ toggle": "Toggle Microphone Mute",
    "exec /home/execorn/scripts/volume_control.sh mute": "Toggle Audio Mute",
    "exec /home/execorn/scripts/volume_control.sh up": "Raise Volume",
    "exec /home/execorn/scripts/volume_control.sh down": "Lower Volume",
    "exec systemctl suspend-then-hibernate": "Suspend PC",
    
    "exec pkill fuzzel || caelestia clipboard": "Open Clipboard Manager",
    "exec pkill fuzzel || caelestia clipboard -d": "Open Clipboard Actions",
    "exec pkill fuzzel || caelestia emoji -p": "Open Emoji Picker",
    "exec sleep 0.5s && ydotool type -d 1 \"$(cliphist list | head -1 | cliphist decode)\"": "Paste from Clipboard"
}

def clean_category_name(name):
    n = name.strip()
    n = re.sub(r'^Category:\s*', '', n, flags=re.IGNORECASE)
    n_title = n.title()
    if n_title == "Windows":
        return "WIndows"
    return n_title

def collapse_workspace_keybinds(keybinds):
    import re
    
    def get_pattern_and_num(s):
        # Match standalone number (1-10 or 0)
        # Note: 0 is used for workspace 10 in keybinds.conf
        match = re.search(r'\b(10|[0-9])\b', s)
        if match:
            num = int(match.group(1))
            start, end = match.span()
            pattern = s[:start] + "<1-10>" + s[end:]
            return pattern, num
        return s, None

    # Group keybinds by (mods_tuple, action_pattern)
    grouped = {}
    for kb in keybinds:
        mods_tuple = tuple(sorted(kb["mods"]))
        act_pat, act_num = get_pattern_and_num(kb["action"])
        
        if act_num is None:
            grouped[id(kb)] = [(kb, None)]
            continue
            
        group_key = (mods_tuple, act_pat)
        if group_key not in grouped:
            grouped[group_key] = []
        grouped[group_key].append((kb, act_num))

    collapsed = []
    for group_key, members in grouped.items():
        if len(members) == 1:
            collapsed.append(members[0][0])
            continue
            
        nums = {num for kb, num in members}
        # If we have 5 or more keys in this sequence, collapse it
        if len(nums) >= 5:
            mods_tuple, act_pat = group_key
            
            # Find the best description pattern from members
            collapsed_desc = None
            for kb, num in members:
                desc_pat, desc_num = get_pattern_and_num(kb["desc"])
                if desc_num is not None:
                    collapsed_desc = desc_pat
                    break
            
            if not collapsed_desc:
                # Fallback to first member description
                first_desc = members[0][0]["desc"]
                clean_desc = re.sub(r'\s*#\s*$', '', first_desc).strip()
                collapsed_desc = f"{clean_desc} <1-10>"
                
            collapsed.append({
                "mods": list(mods_tuple),
                "key": "1-10",
                "action": act_pat,
                "desc": collapsed_desc
            })
        else:
            for kb, num in members:
                collapsed.append(kb)

    return collapsed

def get_section_for_category(cat_name):
    c = cat_name.lower()
    def match(keywords):
        return any(re.search(r'\b' + re.escape(x), c) for x in keywords)
    if match(["workspace", "window", "resize", "resiz", "cyclenext", "swapnext", "focusmonitor", "group", "swapping", "monitor", "client"]):
        return "Windows"
    if match(["app", "terminal", "browser", "editor", "telegram", "calcurse"]):
        return "Applications"
    if match(["utility", "screenshot", "record", "picker", "clipboard", "emoji"]):
        return "Utilities"
    if match(["volume", "brightness", "media", "sleep", "suspend", "hibernate"]):
        return "System"
    if match(["launcher", "sidebar", "cheatsheet", "session", "lock", "notif", "misc"]):
        return "Shell Keybinds"
    return "General"


def get_friendly_action_desc(action, variables=None):
    act_lower = action.strip().lower()
    
    # Try resolved map first
    if variables:
        resolved_map = {resolve_variables(k, variables).lower().strip(): v for k, v in FRIENDLY_ACTIONS.items()}
        if act_lower in resolved_map:
            return resolved_map[act_lower]
            
    # Try unresolved map
    unresolved_map = {k.lower().strip(): v for k, v in FRIENDLY_ACTIONS.items()}
    if act_lower in unresolved_map:
        return unresolved_map[act_lower]
        
    wsaction_match = re.match(r'exec\s+.*?wsaction\.fish\s+(-g\s+)?(workspace|movetoworkspace)\s+(\d+)', act_lower)
    if wsaction_match:
        is_group = bool(wsaction_match.group(1))
        cmd_type = wsaction_match.group(2)
        num = wsaction_match.group(3)
        if cmd_type == "workspace":
            return f"Switch to Workspace {'Group ' if is_group else ''}{num}"
        else:
            return f"Move Window to Workspace {'Group ' if is_group else ''}{num}"

    if act_lower.startswith("workspace,"):
        arg = act_lower.split(",", 1)[1].strip()
        if arg == "-1" or arg == "m-1":
            return "Previous Workspace"
        elif arg == "+1" or arg == "m+1":
            return "Next Workspace"
        elif arg == "-10":
            return "Previous Workspace Group"
        elif arg == "+10":
            return "Next Workspace Group"
        else:
            return f"Switch to Workspace {arg.upper()}"
            
    if act_lower.startswith("movetoworkspace,"):
        arg = act_lower.split(",", 1)[1].strip()
        if arg == "-1" or arg == "m-1":
            return "Move Window to Previous Workspace"
        elif arg == "+1" or arg == "m+1":
            return "Move Window to Next Workspace"
        elif arg == "special:special":
            return "Move Window to Special Workspace"
        elif arg == "e+0":
            return "Move Window from Special Workspace"
        else:
            return f"Move Window to Workspace {arg.upper()}"

    if act_lower.startswith("exec ") or act_lower == "exec":
        cmd = act_lower[5:].strip()
        if cmd:
            cmd_name = os.path.basename(cmd.split()[0])
            return f"Launch {cmd_name.capitalize()}"
            
    return action

def split_inline_comment(line):
    """
    Separates the functional part of a line from an inline comment.
    Inline comments start with a # preceded by whitespace, ignoring those inside quotes.
    """
    in_single_quote = False
    in_double_quote = False
    i = 0
    n = len(line)
    while i < n:
        char = line[i]
        if char == '\\':
            i += 2
            continue
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == '#' and not in_single_quote and not in_double_quote:
            if i == 0 or line[i-1].isspace():
                code = line[:i]
                comment = line[i+1:].strip()
                return code, comment
        i += 1
    return line, ""

def resolve_variables(val, variables, visited=None):
    """
    Recursively resolves variable references ($var) within the given string.
    Guards against circular dependencies/cycles (leaving unresolved elements as-is).
    Keeps undefined variables as-is.
    """
    if visited is None:
        visited = set()
    
    pattern = r'\$([a-zA-Z0-9_]+)'
    
    def repl(match):
        var_name = match.group(1)
        full_match = match.group(0)
        if var_name in visited:
            return full_match  # Cycle detected: return as is
        if var_name in variables:
            visited.add(var_name)
            res = resolve_variables(variables[var_name], variables, visited)
            visited.remove(var_name)
            return res
        return full_match  # Undefined: return as is

    return re.sub(pattern, repl, val)

def is_title_case(s):
    words = s.split()
    if not words:
        return False
    if not any(c.isalnum() for c in s):
        return False
    minor_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "in", "at", "to", "by", "of", "with"}
    for i, word in enumerate(words):
        w = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', word)
        if not w:
            continue
        if i == 0:
            if not w[0].isupper() and not w[0].isdigit():
                return False
        else:
            if w.islower() and w not in minor_words:
                return False
    return True

def is_header(comment_text):
    # Allow title-cased comments
    if (
        len(comment_text) < 40
        and not comment_text.endswith('.')
        and is_title_case(comment_text)
    ):
        return True
    
    # Also explicitly allow the specific lowercase category comments from keybinds.conf
    comment_lower = comment_text.strip().lower()
    known_headers = [
        "window groups",
        "window actions",
        "client index focus",
        "screen focus",
        "resizing",
        "special workspace toggles",
        "migrated apps"
    ]
    if any(kh in comment_lower for kh in known_headers):
        return True
        
    return False

def get_executable_from_action(action, variables=None):
    act = action.strip()
    if not act.startswith("exec "):
        return None
        
    cmd = act[5:].strip()
    if variables:
        cmd = resolve_variables(cmd, variables)
        
    # Match app2unit -- <app>
    match = re.search(r'app2unit\s+.*--\s+([a-zA-Z0-9_\-\.\$]+)', cmd)
    if match:
        return match.group(1).strip()
        
    words = cmd.split()
    if not words:
        return None
        
    first_word = words[0]
    if "=" in first_word:
        for word in words[1:]:
            if "=" not in word:
                first_word = word
                break
                
    first_word = re.split(r'[&\|;><]', first_word)[0].strip()
    
    if first_word.startswith('$'):
        return None
        
    return first_word

def parse_configs(variables_files, keybinds_file):
    variables = {}
    
    # 1. Parse all variable files
    for var_file in variables_files:
        var_path = Path(var_file)
        if not var_path.exists():
            continue
        with open(var_path, 'r', encoding='utf-8') as f:
            for line in f:
                content, _ = split_inline_comment(line)
                content = content.strip()
                if not content:
                    continue
                # Extract variables using regex matching ^\s*\$([a-zA-Z0-9_]+)\s*=\s*(.*?)$
                match = re.match(r'^\s*\$([a-zA-Z0-9_]+)\s*=\s*(.*?)$', content)
                if match:
                    var_name = match.group(1).strip()
                    var_value = match.group(2).strip()
                    variables[var_name] = var_value

    # Pre-resolve loaded variables to handle cross-references within variables files
    for var_name in list(variables.keys()):
        variables[var_name] = resolve_variables(variables[var_name], variables)

    # 2. Parse keybinds file
    keybinds_path = Path(keybinds_file)
    if not keybinds_path.exists():
        print(f"Error: Keybinds file not found at {keybinds_path}", file=sys.stderr)
        return []

    with open(keybinds_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Pre-scan for explicit Category: comment to determine explicit/implicit mode
    has_explicit_categories = any(re.match(r'^\s*#\s*Category:', line, re.IGNORECASE) for line in lines)

    sections = []
    current_section = None
    current_category = None
    section_explicitly_set = False
    accumulated_comments = []

    def get_or_create_section(name):
        nonlocal current_section, current_category
        for s in sections:
            if s["section"] == name:
                current_section = s
                return s
        new_s = {"section": name, "categories": []}
        sections.append(new_s)
        current_section = new_s
        current_category = None
        return new_s

    def get_or_create_category(name):
        nonlocal current_category
        if current_section is None:
            get_or_create_section("General")
        for c in current_section["categories"]:
            if c["category"] == name:
                current_category = c
                return c
        new_c = {"category": name, "keybinds": []}
        current_section["categories"].append(new_c)
        current_category = new_c
        return new_c

    for line in lines:
        stripped = line.strip()
        if not stripped:
            accumulated_comments.clear()
            continue

        # Handle comments
        if stripped.startswith('#'):
            comment_text = stripped[1:].strip()
            
            # Skip decorative comments
            is_decorative = re.match(r'^[#\-\*\s]+$', comment_text) or '###' in stripped or len(comment_text) == 0
            if is_decorative:
                continue
                
            # Check if explicit section or category header
            section_match = re.match(r'^(?:##|Section:)\s*(.*)$', comment_text, re.IGNORECASE)
            category_match = re.match(r'^Category:\s*(.*)$', comment_text, re.IGNORECASE)
            
            if section_match:
                sec_name = section_match.group(1).strip()
                get_or_create_section(sec_name)
                # Only disable auto-routing if it is an explicit 'Section:' comment and not General
                section_explicitly_set = comment_text.lower().startswith("section:") and sec_name != "General"
                accumulated_comments.clear()
                continue
            elif category_match:
                cat_name = clean_category_name(category_match.group(1))
                should_auto_route = not section_explicitly_set
                if should_auto_route:
                    sec_name = get_section_for_category(cat_name)
                    get_or_create_section(sec_name)
                    section_explicitly_set = False
                get_or_create_category(cat_name)
                accumulated_comments.clear()
                continue
            
            # Standard comments
            is_implicit_header = False
            if not has_explicit_categories:
                is_implicit_header = is_header(comment_text)
            else:
                is_implicit_header = is_header(comment_text) and get_section_for_category(comment_text) != "General"
                
            if is_implicit_header:
                cat_name = clean_category_name(comment_text)
                should_auto_route = not section_explicitly_set
                if should_auto_route:
                    sec_name = get_section_for_category(cat_name)
                    get_or_create_section(sec_name)
                    section_explicitly_set = False
                get_or_create_category(cat_name)
                accumulated_comments.clear()
            else:
                accumulated_comments.append(comment_text)
            continue

        # Split inline comment from code
        content, inline_comment = split_inline_comment(line)
        content = content.strip()
        if not content:
            continue

        # Handle inline variable declarations
        var_match = re.match(r'^\s*\$([a-zA-Z0-9_]+)\s*=\s*(.*?)$', content)
        if var_match:
            var_name = var_match.group(1).strip()
            var_value = var_match.group(2).strip()
            # Resolve immediately using currently known variables
            variables[var_name] = resolve_variables(var_value, variables)
            accumulated_comments.clear()
            continue

        # Handle bindings
        bind_match = re.match(r'^\s*bind[a-z]*\s*=\s*(.*)$', content)
        if bind_match:
            bind_body = bind_match.group(1).strip()
            resolved_body = resolve_variables(bind_body, variables)
            
            parts = [p.strip() for p in resolved_body.split(',', 3)]
            if len(parts) < 3:
                accumulated_comments.clear()
                continue
                
            mods_str = parts[0]
            key_str = parts[1]
            dispatcher = parts[2]
            arguments = parts[3] if len(parts) == 4 else ""
            
            if dispatcher == "exec":
                action = f"exec {arguments}" if arguments else "exec"
            else:
                action = f"{dispatcher}, {arguments}" if arguments else dispatcher
                
            not_installed = False
            app_name = ""
            if dispatcher == "exec":
                binary = get_executable_from_action(action, variables)
                if binary:
                    binary_clean = os.path.basename(binary.split()[0]) if not os.path.isabs(binary) else binary
                    if not shutil.which(binary_clean) and not shutil.which(binary):
                        not_installed = True
                        app_name = binary_clean
            
            # Filter internal/unwanted keybindings (catchalls, mouse binds, interrupts)
            key_lower = key_str.lower().strip()
            act_lower = action.lower().strip()
            if "interrupt" in act_lower or "catchall" in key_lower or key_lower.startswith("mouse:") or key_lower.startswith("mouse_"):
                accumulated_comments.clear()
                continue

            # Split modifiers by '+' or space
            mods = []
            for m in re.split(r'[\+\s]+', mods_str.strip()):
                if m.strip():
                    norm = normalize_modifier(m)
                    if norm not in mods:
                        mods.append(norm)
            key = key_str
            
            desc = inline_comment if inline_comment else " ".join(accumulated_comments)
                
            if not desc or not desc.strip():
                desc = get_friendly_action_desc(action, variables)
                # Unresolved action for friendly description mapping fallback
                parts_un = [p.strip() for p in bind_body.split(',', 3)]
                if len(parts_un) >= 3:
                    disp_un = parts_un[2]
                    args_un = parts_un[3] if len(parts_un) == 4 else ""
                    act_un = f"exec {args_un}" if disp_un == "exec" else (f"{disp_un}, {args_un}" if args_un else disp_un)
                else:
                    act_un = action
                if desc == action and act_un != action:
                    desc = get_friendly_action_desc(act_un, variables)
            
            # Check if this is a window/workspace/resize bind
            is_window_bind = False
            act_lower = action.lower().strip()
            
            # Keywords indicating window/workspace management
            window_keywords = [
                "workspace", "movetoworkspace", "cyclenext", "swapnext", 
                "focusmonitor", "movewindow", "resizewindow", 
                "movecurrentworkspacetomonitor", "resizeactive", 
                "togglegroup", "moveoutofgroup", "lockactivegroup", 
                "movefocus", "centerwindow", "pin", "fullscreen", 
                "togglefloating", "killactive", "changegroupactive"
            ]
            
            if any(kw in act_lower for kw in window_keywords) or "caelestia toggle" in act_lower or "resizer" in act_lower:
                is_window_bind = True
                
            if is_window_bind and (current_category is None or current_category["category"] in ("Media", "General", "WIndows")):
                # WIndows category
                if not section_explicitly_set:
                    sec_name = get_section_for_category("WIndows")
                    get_or_create_section(sec_name)
                
                target_cat = None
                for c in current_section["categories"]:
                    if c["category"] == "WIndows":
                        target_cat = c
                        break
                if not target_cat:
                    target_cat = {"category": "WIndows", "keybinds": []}
                    current_section["categories"].append(target_cat)
            else:
                if current_category is None:
                    get_or_create_category("General")
                target_cat = current_category
                
            target_cat["keybinds"].append({
                "mods": mods,
                "key": key,
                "action": action,
                "desc": desc,
                "notInstalled": not_installed,
                "appName": app_name
            })
            accumulated_comments.clear()
            continue
            
        accumulated_comments.clear()


    # Clean up empty categories or sections
    cleaned_sections = []
    for sec in sections:
        cleaned_categories = []
        for cat in sec["categories"]:
            if cat["keybinds"]:
                cat["keybinds"] = collapse_workspace_keybinds(cat["keybinds"])
                cleaned_categories.append(cat)
        if cleaned_categories:
            sec["categories"] = cleaned_categories
            cleaned_sections.append(sec)

    return cleaned_sections
def main():
    parser = argparse.ArgumentParser(description="Parse Hyprland keybindings and variables configurations.")
    home = Path.home()
    env_var_conf = os.environ.get("CAELESTIA_VARIABLES_CONF")
    if env_var_conf:
        default_variables = [p.strip() for p in env_var_conf.replace(",", " ").split() if p.strip()]
    else:
        default_variables = [
            str(home / ".local/share/caelestia/hypr/variables.conf"),
            str(home / ".local/share/caelestia/hypr/scheme/current.conf")
        ]
        
    default_keybinds = os.environ.get("CAELESTIA_KEYBINDS_CONF", str(home / ".local/share/caelestia/hypr/hyprland/keybinds.conf"))
    default_output = os.environ.get("CAELESTIA_KEYBINDS_JSON", str(home / ".local/state/caelestia/keybinds.json"))

    parser.add_argument("--variables", nargs="+", default=default_variables, help="Path to variables configurations")
    parser.add_argument("--keybinds", default=default_keybinds, help="Path to keybindings configuration")
    parser.add_argument("--output", default=default_output, help="Path to output JSON file")
    args = parser.parse_args()

    var_paths = [Path(p) for p in args.variables]
    keybinds_path = Path(args.keybinds)
    output_path = Path(args.output)

    sections = parse_configs(var_paths, keybinds_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output_path.with_suffix(".json.tmp")
    with open(tmp_output, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=2)
    os.replace(tmp_output, output_path)

if __name__ == "__main__":
    main()
