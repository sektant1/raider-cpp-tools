from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "project": {"name": "raider-proj", "cxx_standard": 20},
    "presets": {"configure": "dev", "build": "dev", "test": "dev"},
    "paths": {"src_dir": "src", "tests_dir": "tests"},
    "tools": {
        "cmake": "cmake",
        "ctest": "ctest",
        "clang_format": "clang-format",
        "clang_tidy": "clang-tidy",
    },
    "run": {"target": None},
    "format": {
        "extensions": [".h", ".hpp", ".c", ".cc", ".cpp", ".cxx"],
        "exclude_dirs": ["build", ".git", ".cache"],
    },
    "deps": {
        "manager": "vcpkg",
        "manifest": "vcpkg.json",
        "vcpkg_root": ".tools/vcpkg",
    },
}

CONFIG_FILENAME = "raider.json"


def deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(dst)
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def config_path(root: Path) -> Path:
    return root / CONFIG_FILENAME


def load_config(root: Path) -> Dict[str, Any]:
    path = config_path(root)
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    user_cfg = json.loads(path.read_text(encoding="utf-8"))
    return deep_merge(DEFAULT_CONFIG, user_cfg)


def save_config(root: Path, cfg: Dict[str, Any]) -> None:
    path = config_path(root)
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
