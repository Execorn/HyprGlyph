"""HyprGlyph: Keybinding parser and cheatsheet generator for Hyprland."""

__version__ = "1.0.0"

from .parse_keybinds import (
    main,
    parse_configs,
    parse_conf_configs,
    parse_lua_configs,
    parse_lua_variables,
    split_inline_comment,
    split_lua_comment,
)

__all__ = [
    "__version__",
    "main",
    "parse_configs",
    "parse_conf_configs",
    "parse_lua_configs",
    "parse_lua_variables",
    "split_inline_comment",
    "split_lua_comment",
]
