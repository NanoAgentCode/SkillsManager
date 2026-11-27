"""Configuration helpers for wechat-format scripts."""

from __future__ import annotations

import json
from pathlib import Path


def default_config() -> dict:
    output_root = Path.cwd() / "output"
    return {
        "output_dir": str(output_root / "wechat-format" / "tmp"),
        "vault_root": str(Path.home()),
        "image_search_paths": [],
        "settings": {
            "default_theme": "newspaper",
            "auto_open_browser": True,
        },
        "wechat": {
            "app_id": "",
            "app_secret": "",
            "author": "",
        },
        "cover": {
            "output_dir": str(output_root / "wechat-cover"),
            "image_generation_script": "",
        },
        "ai": {
            "url": "",
            "api_key": "",
            "model": "",
        },
    }


def deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(skill_dir: Path) -> dict:
    config_path = skill_dir / "config.json"
    defaults = default_config()
    if not config_path.exists():
        return defaults

    with open(config_path, encoding="utf-8") as f:
        user_config = json.load(f)
    config = deep_merge(defaults, user_config)
    # An installed config is shared across projects. Keep each invocation's output local.
    config["output_dir"] = defaults["output_dir"]
    cover_config = config.get("cover")
    if isinstance(cover_config, dict):
        cover_config["output_dir"] = defaults["cover"]["output_dir"]
    return config
