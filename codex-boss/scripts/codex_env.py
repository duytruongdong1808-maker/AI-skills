"""Locate the Codex CLI and list the models it currently offers.

Usage:  python codex_env.py            # human-readable summary
        python codex_env.py --json     # machine-readable

The Codex desktop app installs the CLI under a hashed folder that changes on
update, so never hard-code the path: run this script and use what it prints.
Models come from ~/.codex/models_cache.json, which the CLI refreshes itself.
"""
import glob
import json
import os
import shutil
import subprocess
import sys


def find_codex():
    on_path = shutil.which("codex")
    if on_path:
        return on_path
    local = os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))
    hits = glob.glob(os.path.join(local, "OpenAI", "Codex", "bin", "*", "codex.exe"))
    # Newest build wins: the app leaves older hashed folders behind after updates.
    hits.sort(key=os.path.getmtime, reverse=True)
    return hits[0] if hits else None


def codex_version(exe):
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
        return out.stdout.strip() or out.stderr.strip()
    except Exception as exc:  # report, don't crash: the model list is still useful
        return f"unknown ({exc})"


def load_models():
    home = os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))
    path = os.path.join(home, "models_cache.json")
    if not os.path.exists(path):
        return path, []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    models = []
    for m in data.get("models", []):
        if m.get("visibility") != "list":
            continue  # hidden/internal models (auto-review etc.) are not for delegation
        models.append({
            "slug": m["slug"],
            "name": m.get("display_name"),
            "description": m.get("description"),
            "default_effort": m.get("default_reasoning_level"),
            "efforts": [e["effort"] for e in m.get("supported_reasoning_levels", [])],
            "context_window": m.get("context_window"),
            "fast_tier": "fast" in (m.get("additional_speed_tiers") or []),
        })
    return path, models


def default_model():
    home = os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))
    path = os.path.join(home, "config.toml")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("model ") or line.strip().startswith("model="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def main():
    exe = find_codex()
    cache, models = load_models()
    info = {
        "codex_exe": exe,
        "version": codex_version(exe) if exe else None,
        "config_default_model": default_model(),
        "models_cache": cache,
        "models": models,
    }
    if "--json" in sys.argv:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return
    print(f"codex exe : {exe or 'NOT FOUND'}")
    print(f"version   : {info['version']}")
    print(f"default   : {info['config_default_model']}")
    print(f"models    : (from {cache})")
    for m in models:
        print(f"  {m['slug']:<16} ctx={m['context_window']!s:<7} efforts={','.join(m['efforts'])}")
        print(f"  {'':<16} {m['description']}")


if __name__ == "__main__":
    main()
