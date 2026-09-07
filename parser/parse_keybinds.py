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
    "global, caelestia:overview": "Toggle Overview",
    "global, caelestia:ocr": "OCR Screen Region",
    "global, caelestia:newsfeed": "Toggle Newsfeed",
    
    "exec caelestia shell -d": "Start Caelestia Shell",
    "exec qs -c caelestia kill": "Kill Caelestia Shell",
    "exec qs -c caelestia kill; sleep .1; caelestia shell -d": "Restart Caelestia Shell",
    
    "workspace, -1": "Switch to Previous Workspace",
    "workspace, +1": "Switch to Next Workspace",
    "workspace, -10": "Switch to Previous Workspace Group",
    "workspace, +10": "Switch to Next Workspace Group",
    "workspace, previous": "Switch to Previous Workspace",
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
    
    "movefocus, left": "Focus Left Window",
    "movefocus, right": "Focus Right Window",
    "movefocus, up": "Focus Window Above",
    "movefocus, down": "Focus Window Below",
    "movewindow, left": "Move Window Left",
    "movewindow, right": "Move Window Right",
    "movewindow, up": "Move Window Up",
    "movewindow, down": "Move Window Down",
    
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
    "exec hyprctl switchxkblayout all 0 && alacritty": "Open Terminal",
    "exec app2unit -- $terminal": "Open Terminal",
    "exec app2unit -- $browser": "Open Web Browser",
    "exec app2unit -- $editor": "Open Text Editor",
    "exec app2unit -- antigravity": "Open Antigravity",
    "exec app2unit -- github-desktop": "Open GitHub Desktop",
    "exec app2unit -- $fileexplorer": "Open File Manager",
    "exec app2unit -- nemo": "Open Nemo File Manager",
    "exec app2unit -- qps": "Open Process Manager",
    "exec app2unit -- pavucontrol": "Open Volume Control",
    "exec alacritty": "Open Terminal",
    "exec firefox": "Open Web Browser",
    "exec code": "Open Text Editor",
    "exec antigravity": "Open Antigravity",
    "exec github-desktop": "Open GitHub Desktop",
    "exec thunar": "Open File Manager",
    "exec qps": "Open Process Manager",
    "exec pwvucontrol": "Open Volume Control",
    "exec telegram": "Open Telegram",
    "exec $terminal -e calcurse": "Open Calendar",
    "exec alacritty -e calcurse": "Open Calendar",
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
    "exec sleep 0.5s && ydotool type -d 1 \"$(cliphist list | head -1 | cliphist decode)\"": "Paste from Clipboard",
    "exec notify-send -u low -i dialog-information-symbolic 'Test notification' [[\"Here's a really long message to test truncation and wrapping\\nYou can middle click or flick this notification to dismiss it!\"]] -a 'Shell' -A 'Test1=I got it!' -A 'Test2=Another action'": "Test Notification"
}

def clean_category_name(name):
    n = name.strip()
    n = re.sub(r'^Category:\s*', '', n, flags=re.IGNORECASE)
    n_title = n.title()
    if n_title == "Windows":
        return "WIndows"
    return n_title

def collapse_workspace_keybinds(keybinds):
    def get_pattern_and_num(s):
        match = re.search(r'\b(10|[0-9])\b', s)
        if match:
            num = int(match.group(1))
            start, end = match.span()
            pattern = s[:start] + "<1-10>" + s[end:]
            return pattern, num
        return s, None

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
        if len(nums) >= 5:
            mods_tuple, act_pat = group_key
            
            collapsed_desc = None
            for kb, num in members:
                desc_pat, desc_num = get_pattern_and_num(kb["desc"])
                if desc_num is not None:
                    collapsed_desc = desc_pat
                    break
            
            if not collapsed_desc:
                first_desc = members[0][0]["desc"]
                clean_desc = re.sub(r'\s*#\s*$', '', first_desc).strip()
                collapsed_desc = f"{clean_desc} <1-10>"
                
            collapsed.append({
                "mods": list(mods_tuple),
                "key": "1-10",
                "action": act_pat,
                "desc": collapsed_desc,
                "notInstalled": False,
                "appName": ""
            })
        else:
            for kb, num in members:
                collapsed.append(kb)

    return collapsed

def get_section_for_category(cat_name):
    c = cat_name.lower()
    def match(keywords):
        return any(re.search(r'\b' + re.escape(x), c) for x in keywords)
    if match(["workspace", "window", "windows", "resize", "resiz", "cyclenext", "swapnext", "focusmonitor", "group", "swapping", "monitor", "client"]):
        return "Windows"
    if match(["app", "apps", "terminal", "browser", "editor", "telegram", "calcurse"]):
        return "Applications"
    if match(["utility", "utilities", "screenshot", "record", "picker", "clipboard", "emoji"]):
        return "Utilities"
    if match(["volume", "brightness", "media", "sleep", "suspend", "hibernate"]):
        return "System"
    if match(["launcher", "sidebar", "cheatsheet", "session", "lock", "notif", "misc", "shell", "global", "kill", "restart", "test", "testing"]):
        return "Shell Keybinds"
    return "General"

def get_friendly_action_desc(action, variables=None):
    act_lower = action.strip().lower()
    
    if variables:
        resolved_map = {resolve_variables(k, variables).lower().strip(): v for k, v in FRIENDLY_ACTIONS.items()}
        if act_lower in resolved_map:
            return resolved_map[act_lower]
            
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
        if arg in ("-1", "m-1"):
            return "Previous Workspace"
        elif arg in ("+1", "m+1"):
            return "Next Workspace"
        elif arg == "-10":
            return "Previous Workspace Group"
        elif arg == "+10":
            return "Next Workspace Group"
        elif arg == "previous":
            return "Switch to Previous Workspace"
        else:
            return f"Switch to Workspace {arg.upper()}"
            
    if act_lower.startswith("movetoworkspace,"):
        arg = act_lower.split(",", 1)[1].strip()
        if arg in ("-1", "m-1"):
            return "Move Window to Previous Workspace"
        elif arg in ("+1", "m+1"):
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
    if visited is None:
        visited = set()
    
    pattern = r'\$([a-zA-Z0-9_]+)'
    
    def repl(match):
        var_name = match.group(1)
        full_match = match.group(0)
        if var_name in visited:
            return full_match
        if var_name in variables:
            visited.add(var_name)
            res = resolve_variables(variables[var_name], variables, visited)
            visited.remove(var_name)
            return res
        return full_match

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
    if (
        len(comment_text) < 40
        and not comment_text.endswith('.')
        and is_title_case(comment_text)
    ):
        return True
    
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

def parse_conf_configs(variables_files, keybinds_file):
    variables = {}
    
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
                match = re.match(r'^\s*\$([a-zA-Z0-9_]+)\s*=\s*(.*?)$', content)
                if match:
                    var_name = match.group(1).strip()
                    var_value = match.group(2).strip()
                    variables[var_name] = var_value

    for var_name in list(variables.keys()):
        variables[var_name] = resolve_variables(variables[var_name], variables)

    keybinds_path = Path(keybinds_file)
    if not keybinds_path.exists():
        print(f"Error: Keybinds file not found at {keybinds_path}", file=sys.stderr)
        return []

    with open(keybinds_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

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

        if stripped.startswith('#'):
            comment_text = stripped[1:].strip()
            
            is_decorative = re.match(r'^[#\-\*\s]+$', comment_text) or '###' in stripped or len(comment_text) == 0
            if is_decorative:
                continue
                
            section_match = re.match(r'^(?:##|Section:)\s*(.*)$', comment_text, re.IGNORECASE)
            category_match = re.match(r'^Category:\s*(.*)$', comment_text, re.IGNORECASE)
            
            if section_match:
                sec_name = section_match.group(1).strip()
                get_or_create_section(sec_name)
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

        content, inline_comment = split_inline_comment(line)
        content = content.strip()
        if not content:
            continue

        var_match = re.match(r'^\s*\$([a-zA-Z0-9_]+)\s*=\s*(.*?)$', content)
        if var_match:
            var_name = var_match.group(1).strip()
            var_value = var_match.group(2).strip()
            variables[var_name] = resolve_variables(var_value, variables)
            accumulated_comments.clear()
            continue

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
            
            key_lower = key_str.lower().strip()
            act_lower = action.lower().strip()
            if "interrupt" in act_lower or "catchall" in key_lower or key_lower.startswith("mouse:") or key_lower.startswith("mouse_"):
                accumulated_comments.clear()
                continue

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
                parts_un = [p.strip() for p in bind_body.split(',', 3)]
                if len(parts_un) >= 3:
                    disp_un = parts_un[2]
                    args_un = parts_un[3] if len(parts_un) == 4 else ""
                    act_un = f"exec {args_un}" if disp_un == "exec" else (f"{disp_un}, {args_un}" if args_un else disp_un)
                else:
                    act_un = action
                if desc == action and act_un != action:
                    desc = get_friendly_action_desc(act_un, variables)
            
            is_window_bind = False
            act_lower = action.lower().strip()
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

def parse_lua_variables(var_paths):
    variables = {}
    if isinstance(var_paths, (str, Path)):
        var_paths = [var_paths]
    for var_path in var_paths:
        p = Path(var_path)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.split("--")[0].strip()
            if not line:
                continue
            m = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*(.*?),?$", line)
            if m:
                k = m.group(1).strip()
                v = m.group(2).strip()
                if v.startswith(('"', "'")) and v.endswith(('"', "'")):
                    variables[k] = v[1:-1]
                elif v.startswith("{") and v.endswith("}"):
                    items = re.findall(r'["\']([^"\']+)["\']', v)
                    variables[k] = items
                elif v in ("true", "false"):
                    variables[k] = (v == "true")
                else:
                    variables[k] = v
    return variables

def split_lua_args(arg_str):
    args = []
    current = []
    depth_paren = 0
    depth_brace = 0
    in_quote = False
    quote_char = ''
    i = 0
    n = len(arg_str)
    while i < n:
        c = arg_str[i]
        if c == '\\':
            current.append(c)
            if i + 1 < n:
                current.append(arg_str[i+1])
                i += 1
            i += 1
            continue
        if c in ('"', "'"):
            if not in_quote:
                in_quote = True
                quote_char = c
            elif quote_char == c:
                in_quote = False
            current.append(c)
        elif in_quote:
            current.append(c)
        elif c == '(':
            depth_paren += 1
            current.append(c)
        elif c == ')':
            depth_paren -= 1
            current.append(c)
        elif c == '{':
            depth_brace += 1
            current.append(c)
        elif c == '}':
            depth_brace -= 1
            current.append(c)
        elif c == ',' and depth_paren == 0 and depth_brace == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(c)
        i += 1
    if current:
        args.append("".join(current).strip())
    return args

def eval_lua_key_expr(expr, variables):
    expr = expr.strip()
    if expr.startswith("{") and expr.endswith("}"):
        inner = expr[1:-1].strip()
        items = split_lua_args(inner)
        res = []
        for it in items:
            res.extend(eval_lua_key_expr(it, variables))
        return res
    
    if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
        return [expr[1:-1]]
    
    m = re.match(r'extend_keybind\s*\(\s*vars\.([a-zA-Z0-9_]+)\s*,\s*([a-zA-Z0-9_]+)\s*\)', expr)
    if m:
        base_var = m.group(1)
        suffix = m.group(2)
        base_val = variables.get(base_var, "")
        return [f"{base_val} + {suffix}"]

    if expr.startswith("vars."):
        var_name = expr[5:].strip()
        val = variables.get(var_name)
        if isinstance(val, list):
            return val
        elif isinstance(val, str):
            return [val]
        return []

    if ".." in expr:
        parts = [p.strip() for p in expr.split("..")]
        resolved_parts = []
        for p in parts:
            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                resolved_parts.append(p[1:-1])
            elif p.startswith("vars."):
                resolved_parts.append(str(variables.get(p[5:].strip(), p)))
            elif p in variables:
                resolved_parts.append(str(variables[p]))
            else:
                resolved_parts.append(p)
        return ["".join(resolved_parts)]

    if expr in variables:
        val = variables[expr]
        if isinstance(val, list):
            return val
        return [str(val)]

    return [expr]

def eval_lua_action_expr(expr, variables):
    expr = expr.strip()
    
    m = re.search(r'hl\.dsp\.global\s*\(\s*["\']([^"\']+)["\']\s*\)', expr)
    if m:
        return f"global, {m.group(1)}"
        
    m = re.search(r'hl\.dsp\.exec_cmd\s*\(\s*(.*?)\s*\)', expr, re.DOTALL)
    if m:
        inner = m.group(1).strip()
        if ".." in inner:
            parts = [p.strip() for p in inner.split("..")]
            resolved_parts = []
            for p in parts:
                if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                    resolved_parts.append(p[1:-1])
                elif p.startswith("vars."):
                    resolved_parts.append(str(variables.get(p[5:].strip(), p)))
                elif p in variables:
                    resolved_parts.append(str(variables[p]))
                else:
                    resolved_parts.append(p)
            return f"exec {''.join(resolved_parts)}"
        elif (inner.startswith('"') and inner.endswith('"')) or (inner.startswith("'") and inner.endswith("'")):
            return f"exec {inner[1:-1]}"
        elif inner.startswith("vars."):
            val = variables.get(inner[5:].strip(), "")
            return f"exec {val}"
        elif inner in variables:
            return f"exec {variables[inner]}"
        return f"exec {inner}"

    if ".." in expr:
        parts = [p.strip() for p in expr.split("..")]
        resolved_parts = []
        for p in parts:
            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                resolved_parts.append(p[1:-1])
            elif p.startswith("vars."):
                resolved_parts.append(str(variables.get(p[5:].strip(), p)))
            elif p in variables:
                resolved_parts.append(str(variables[p]))
            else:
                resolved_parts.append(p)
        return "".join(resolved_parts)

    m = re.search(r'hl\.dsp\.focus\s*\(\s*\{\s*workspace\s*=\s*["\']([^"\']+)["\']\s*\}\s*\)', expr)
    if m:
        return f"workspace, {m.group(1)}"
    m = re.search(r'hl\.dsp\.focus\s*\(\s*\{\s*direction\s*=\s*([a-zA-Z0-9_\.]+)\s*\}\s*\)', expr)
    if m:
        d = m.group(1).strip('"\'')
        return f"movefocus, {d}"

    m = re.search(r'hl\.dsp\.window\.move\s*\(\s*\{\s*workspace\s*=\s*["\']([^"\']+)["\']\s*\}\s*\)', expr)
    if m:
        return f"movetoworkspace, {m.group(1)}"
    m = re.search(r'hl\.dsp\.window\.move\s*\(\s*\{\s*direction\s*=\s*([a-zA-Z0-9_\.]+)\s*\}\s*\)', expr)
    if m:
        d = m.group(1).strip('"\'')
        return f"movewindow, {d}"
    if "out_of_group" in expr:
        return "moveoutofgroup"

    if "cycle_next" in expr:
        if "next = false" in expr:
            return "cyclenext, prev"
        return "cyclenext"
    if "group.next" in expr:
        return "changegroupactive, f"
    if "group.prev" in expr:
        return "changegroupactive, b"
    if "group.toggle" in expr:
        return "togglegroup"
    if "group.lock_active" in expr:
        return "lockactivegroup, toggle"

    if "window.drag" in expr:
        return "movewindow"
    if "window.resize" in expr and "resize_active_window" not in expr:
        return "resizewindow"
    if "window.center" in expr:
        return "centerwindow, 1"
    if "window.pin" in expr:
        return "pin"
    if "window.fullscreen" in expr:
        if "maximized" in expr:
            return "fullscreen, 1"
        return "fullscreen, 0"
    if "window.float" in expr:
        return "togglefloating"
    if "window.close" in expr:
        return "killactive"

    m = re.search(r'fn\.toggle\s*\(\s*["\']([^"\']+)["\']\s*\)', expr)
    if m:
        return f"exec caelestia toggle {m.group(1)}"

    m = re.search(r'fn\.resize_active_window\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)', expr)
    if m:
        x, y = m.group(1), m.group(2)
        return f"resizeactive, {x}% {y}%"

    if "workspace previous" in expr:
        return "workspace, previous"
    if "resizer pip" in expr or "pip" in expr:
        return "exec caelestia resizer pip"
    if "55, 70" in expr:
        return "resizeactive, exact 55% 70%"
    if "restoreLock" in expr or "caelestia shell -d" in expr:
        return "exec caelestia shell -d"

    return expr

def parse_lua_configs(var_paths, keybinds_path):
    variables = parse_lua_variables(var_paths)
    text = Path(keybinds_path).read_text(encoding="utf-8")
    
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

    def get_or_create_category(name, sec_name=None):
        nonlocal current_category
        if sec_name:
            get_or_create_section(sec_name)
        elif current_section is None:
            get_or_create_section("General")
        for c in current_section["categories"]:
            if c["category"] == name:
                current_category = c
                return c
        new_c = {"category": name, "keybinds": []}
        current_section["categories"].append(new_c)
        current_category = new_c
        return new_c

    def add_keybind(raw_keys, raw_action, inline_comment="", force_category=None, force_section=None):
        nonlocal accumulated_comments
        if not current_category and not force_category:
            return

        keys_list = eval_lua_key_expr(raw_keys, variables) if isinstance(raw_keys, str) else raw_keys
        action = eval_lua_action_expr(raw_action, variables)
        
        for full_key in keys_list:
            parts = [p.strip() for p in re.split(r'[\+\s]+', full_key) if p.strip()]
            if not parts:
                continue
            key = parts[-1]
            mod_parts = parts[:-1]
            
            key_lower = key.lower().strip()
            act_lower = action.lower().strip()
            if "interrupt" in act_lower or "catchall" in key_lower or key_lower.startswith("mouse:") or key_lower.startswith("mouse_"):
                continue

            mods = []
            for m in mod_parts:
                norm = normalize_modifier(m)
                if norm not in mods:
                    mods.append(norm)

            desc = inline_comment if inline_comment else " ".join(accumulated_comments)
            if not desc or not desc.strip():
                desc = get_friendly_action_desc(action, variables)

            not_installed = False
            app_name = ""
            if action.startswith("exec"):
                binary = get_executable_from_action(action, variables)
                if binary:
                    binary_clean = os.path.basename(binary.split()[0]) if not os.path.isabs(binary) else binary
                    if not shutil.which(binary_clean) and not shutil.which(binary):
                        not_installed = True
                        app_name = binary_clean

            if force_category:
                target_cat = get_or_create_category(force_category, force_section)
            else:
                is_window_bind = False
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

                curr_cat_name = (current_category["category"] if current_category else "").lower()
                if is_window_bind and (not current_category or curr_cat_name in ("media", "general", "windows", "kill/restart")):
                    target_cat = get_or_create_category("WIndows", "Windows")
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

    lines = text.splitlines()
    i = 0
    n = len(lines)
    started_keybinds = False

    while i < n:
        line = lines[i].strip()
        if not line:
            accumulated_comments.clear()
            i += 1
            continue

        if line.startswith("--"):
            comment_text = line[2:].strip()
            if re.match(r'^[#\-\*\s]+$', comment_text) or len(comment_text) == 0:
                i += 1
                continue

            if not started_keybinds and comment_text.lower() in ("flags", "functions", "setup"):
                i += 1
                continue

            sec_match = re.match(r'^(?:##|Section:)\s*(.*)$', comment_text, re.IGNORECASE)
            cat_match = re.match(r'^Category:\s*(.*)$', comment_text, re.IGNORECASE)

            if sec_match:
                sec_name = sec_match.group(1).strip()
                get_or_create_section(sec_name)
                section_explicitly_set = comment_text.lower().startswith("section:") and sec_name != "General"
                accumulated_comments.clear()
                started_keybinds = True
                i += 1
                continue
            elif cat_match:
                cat_name = clean_category_name(cat_match.group(1))
                if not section_explicitly_set:
                    sec_name = get_section_for_category(cat_name)
                    get_or_create_section(sec_name)
                    section_explicitly_set = False
                get_or_create_category(cat_name)
                accumulated_comments.clear()
                started_keybinds = True
                i += 1
                continue

            if "workspace" in comment_text.lower():
                get_or_create_category("WIndows", "Windows")
                accumulated_comments.clear()
                started_keybinds = True
                i += 1
                continue

            if is_header(comment_text) or comment_text.lower() in ("shell globals", "utilities", "testing", "brightness", "launcher"):
                cat_name = clean_category_name(comment_text)
                if not section_explicitly_set:
                    sec_name = get_section_for_category(cat_name)
                    get_or_create_section(sec_name)
                    section_explicitly_set = False
                get_or_create_category(cat_name)
                accumulated_comments.clear()
                started_keybinds = True
            else:
                accumulated_comments.append(comment_text)
            i += 1
            continue

        if not started_keybinds:
            i += 1
            continue

        if "for i = 1, 10 do" in line:
            for ws_num in range(1, 11):
                key_digit = str(ws_num % 10)
                add_keybind(f"{variables.get('kbGoToWs', 'SUPER')} + {key_digit}", f"exec ~/.config/hypr/scripts/wsaction.fish workspace {ws_num}", force_category="WIndows", force_section="Windows")
                add_keybind(f"{variables.get('kbMoveWinToWs', 'SUPER + SHIFT')} + {key_digit}", f"exec ~/.config/hypr/scripts/wsaction.fish movetoworkspace {ws_num}", force_category="WIndows", force_section="Windows")
                add_keybind(f"{variables.get('kbGoToWsGroup', 'CTRL + SUPER')} + {key_digit}", f"exec ~/.config/hypr/scripts/wsaction.fish -g workspace {ws_num}", force_category="WIndows", force_section="Windows")
                add_keybind(f"{variables.get('kbMoveWinToWsGroup', 'CTRL + SUPER + ALT')} + {key_digit}", f"exec ~/.config/hypr/scripts/wsaction.fish -g movetoworkspace {ws_num}", force_category="WIndows", force_section="Windows")
            while i < n and not lines[i].strip().startswith("end"):
                i += 1
            i += 1
            accumulated_comments.clear()
            continue

        if 'for _, dir in ipairs({ "left", "right", "up", "down" })' in line or "for _, dir in ipairs" in line:
            for d in ["left", "right", "up", "down"]:
                add_keybind(f"SUPER + {d}", f"movefocus, {d}")
                add_keybind(f"SUPER + SHIFT + {d}", f"movewindow, {d}")
            while i < n and not lines[i].strip().startswith("end"):
                i += 1
            i += 1
            accumulated_comments.clear()
            continue

        if "create_bind" in line or "hl.bind" in line or (re.search(r'\bbind\s*\(', line) and "function" not in line):
            call_lines = []
            open_parens = 0
            started = False
            while i < n:
                cur_l = lines[i]
                for ch in cur_l:
                    if ch == '(':
                        open_parens += 1
                        started = True
                    elif ch == ')':
                        open_parens -= 1
                call_lines.append(cur_l)
                if started and open_parens <= 0:
                    break
                i += 1
            full_call = " ".join(call_lines)
            
            m = re.search(r'(?:create_bind|hl\.bind|\bbind)\s*\((.*)\)', full_call, re.DOTALL)
            if m:
                inner_call = m.group(1).strip()
                call_args = split_lua_args(inner_call)
                if len(call_args) >= 2:
                    raw_keys = call_args[0]
                    raw_action = call_args[1]
                    if raw_keys.strip() not in ("key", "keybinds"):
                        add_keybind(raw_keys, raw_action)
            accumulated_comments.clear()
            i += 1
            continue

        i += 1

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

def parse_configs(variables_files, keybinds_file):
    keybinds_path = Path(keybinds_file)
    if not keybinds_path.exists():
        if keybinds_path.suffix == ".conf":
            alt = keybinds_path.with_suffix(".lua")
            if alt.exists():
                keybinds_path = alt
        elif keybinds_path.suffix == ".lua":
            alt = keybinds_path.with_suffix(".conf")
            if alt.exists():
                keybinds_path = alt

    if keybinds_path.suffix == ".lua":
        resolved_vars = []
        for vf in variables_files:
            vp = Path(vf)
            if not vp.exists() and vp.suffix == ".conf":
                alt_vp = vp.with_suffix(".lua")
                if alt_vp.exists():
                    resolved_vars.append(alt_vp)
                    continue
            resolved_vars.append(vp)
        return parse_lua_configs(resolved_vars, keybinds_path)
    else:
        return parse_conf_configs(variables_files, keybinds_path)

def main():
    parser = argparse.ArgumentParser(description="Parse Hyprland keybindings and variables configurations.")
    home = Path.home()
    
    lua_keybinds = home / ".local/share/caelestia/hypr/hyprland/keybinds.lua"
    conf_keybinds = home / ".local/share/caelestia/hypr/hyprland/keybinds.conf"
    
    if lua_keybinds.exists():
        default_keybinds = str(lua_keybinds)
        default_variables = [
            str(home / ".local/share/caelestia/hypr/variables.lua"),
            str(home / ".local/share/caelestia/hypr/scheme/current.lua")
        ]
    else:
        default_keybinds = str(conf_keybinds)
        default_variables = [
            str(home / ".local/share/caelestia/hypr/variables.conf"),
            str(home / ".local/share/caelestia/hypr/scheme/current.conf")
        ]

    env_var_conf = os.environ.get("CAELESTIA_VARIABLES_CONF") or os.environ.get("CAELESTIA_VARIABLES_LUA")
    if env_var_conf:
        default_variables = [p.strip() for p in env_var_conf.replace(",", " ").split() if p.strip()]
        
    default_keybinds = os.environ.get("CAELESTIA_KEYBINDS_CONF") or os.environ.get("CAELESTIA_KEYBINDS_LUA") or default_keybinds
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
