#!/usr/bin/env python3
"""First-time setup: auto-detect toolchain paths and write config.json.

Agent-friendly: use --auto-detect to scan common locations automatically.
No interactive prompts needed — the agent handles user interaction.

Usage:
  python setup.py --auto-detect --probe JLink          # agent: full auto
  python setup.py --accept-defaults --probe JLink       # agent: use known defaults + CLI overrides
  python setup.py                                       # human: interactive prompts
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

# Force UTF-8 on stdout/stderr so the Chinese hints below never raise
# UnicodeEncodeError on a legacy GBK console or when redirected to a file.
# errors="replace" guarantees the script never crashes on encoding alone.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

CONFIG_DIR = Path(__file__).resolve().parents[1]
CHIP = "MSPM0G3519"

# ── sensible fallback defaults (only used when auto-detect finds nothing) ──
DEFAULTS = {
    "ccs_root": r"D:\TI\CCS\ccs",
    "sdk_root": "",  # auto-detect via _find_sdk(); no hardcoded version
    "probe": "XDS110",
    "chip": CHIP,
}


# ═══════════════════════════════════════════════════════════════════════
#  Auto-detection helpers
# ═══════════════════════════════════════════════════════════════════════

def _is_dir(path: str) -> bool:
    return Path(path).is_dir()


def _is_file(path: str) -> bool:
    return Path(path).is_file()


def _newest_match(pattern: str) -> str | None:
    """Return the newest (last sorted) glob match, or None."""
    matches = sorted(glob.glob(pattern))
    return matches[-1] if matches else None


def _find_ccs() -> str:
    """Search common CCS install locations."""
    candidates = [
        r"D:\TI\CCS\ccs",
        r"C:\ti\ccs",
        r"C:\TI\ccs",
        r"E:\TI\CCS\ccs",
    ]
    for c in candidates:
        # CCS root should contain 'ccs_base' and 'utils'
        if _is_dir(f"{c}\\ccs_base") and _is_dir(f"{c}\\utils"):
            return c
    return DEFAULTS["ccs_root"]


def _find_sdk(ccs_root: str) -> str:
    """Search for MSPM0 SDK, preferring the newest version with valid examples."""
    # Look in CCS directory and common alternate locations
    search_roots = [
        rf"{Path(ccs_root).parent}",  # D:\TI\CCS
        Path(ccs_root).parent,         # same
        r"D:\TI\M0_SDK",
        r"C:\ti",
    ]
    seen = set()
    candidates = []
    for root in search_roots:
        root_str = str(root)
        if root_str in seen:
            continue
        seen.add(root_str)
        if not _is_dir(root_str):
            continue
        for entry in Path(root_str).iterdir():
            if not entry.is_dir():
                continue
            name = entry.name.lower()
            if name.startswith("mspm0_sdk_") or name.startswith("mspm0-sdk-"):
                # Verify it has the expected examples structure
                examples = entry / "examples" / "nortos" / f"LP_{CHIP}" / "driverlib"
                if examples.is_dir():
                    candidates.append((name, str(entry)))
    if not candidates:
        return ""
    # Prefer newest SDK (sort by name, which includes version)
    candidates.sort(reverse=True)
    print(f"[auto-detect] found {len(candidates)} SDK(s): {', '.join(c[0] for c in candidates)}")
    return candidates[0][1]


def _find_sysconfig(ccs_root: str) -> str:
    """Find the newest SysConfig CLI under CCS utils."""
    pattern = rf"{ccs_root}\utils\sysconfig_*\sysconfig_cli.bat"
    match = _newest_match(pattern)
    if match:
        print(f"[auto-detect] SysConfig CLI: {match}")
        return match
    return rf"{ccs_root}\utils\sysconfig_1.24.0\sysconfig_cli.bat"


def _find_compiler(ccs_root: str) -> str:
    """Find the newest TI Arm Clang compiler under CCS."""
    pattern = rf"{ccs_root}\tools\compiler\ti-cgt-armllvm_*\LTS"
    match = _newest_match(pattern)
    if match:
        print(f"[auto-detect] compiler: {match}")
        return match
    return rf"{ccs_root}\tools\compiler\ti-cgt-armllvm_4.0.3.LTS"


def _find_gmake(ccs_root: str) -> str:
    path = rf"{ccs_root}\utils\bin\gmake.exe"
    if _is_file(path):
        return path
    return r"D:\TI\CCS\ccs\utils\bin\gmake.exe"


def _find_dslite(ccs_root: str) -> str:
    path = rf"{ccs_root}\ccs_base\DebugServer\bin\DSLite.exe"
    if _is_file(path):
        return path
    return r"D:\TI\CCS\ccs\ccs_base\DebugServer\bin\DSLite.exe"


def _find_jlink() -> str:
    """Search common SEGGER install locations for JLink.exe (newest version)."""
    patterns = [
        r"C:\Program Files\SEGGER\JLink*\JLink.exe",
        r"C:\Program Files (x86)\SEGGER\JLink*\JLink.exe",
        r"D:\Program Files\SEGGER\JLink*\JLink.exe",
    ]
    for pattern in patterns:
        match = _newest_match(pattern)
        if match:
            print(f"[auto-detect] JLink: {match}")
            return match
    return r"C:\Program Files\SEGGER\JLink\JLink.exe"


# ═══════════════════════════════════════════════════════════════════════
#  Config building (single code path — no duplication)
# ═══════════════════════════════════════════════════════════════════════

def build_config(
    ccs_root: str | None = None,
    sdk_root: str | None = None,
    probe: str | None = None,
) -> dict:
    """Build config dict. Always validates paths — auto-searches when defaults don't exist."""

    # CCS: use provided, validate, or search
    ccs = ccs_root or DEFAULTS["ccs_root"]
    if not _is_dir(ccs):
        print(f"[warn] CCS not found: {ccs} — auto-searching...")
        ccs = _find_ccs()
    if not _is_dir(ccs):
        ccs = DEFAULTS["ccs_root"]
        print(f"[warn] CCS fallback to default: {ccs}")

    # SDK: use provided, validate, or search (prefer newest)
    sdk = sdk_root or DEFAULTS["sdk_root"]
    if not sdk or not _is_dir(sdk):
        if sdk:
            print(f"[warn] SDK not found: {sdk} — auto-searching...")
        sdk = _find_sdk(ccs)
    if not sdk or not _is_dir(sdk):
        print("[warn] SDK auto-detect failed — please provide --sdk-root manually")

    print(f"[setup] CCS  : {ccs}")
    print(f"[setup] SDK  : {sdk}")

    prob = probe or DEFAULTS["probe"]

    return {
        "ccs_root": ccs,
        "sdk_root": sdk,
        "sysconfig_cli": _find_sysconfig(ccs),
        "dslite": _find_dslite(ccs),
        "gmake": _find_gmake(ccs),
        "compiler": _find_compiler(ccs),
        "sdk_examples": str(Path(sdk) / "examples" / "nortos" / f"LP_{CHIP}" / "driverlib"),
        "jlink_path": _find_jlink(),
        "probe": prob,
        "chip": CHIP,
    }


def _interactive_config() -> dict:
    """Interactive prompts for human users. Agents should use --auto-detect instead."""
    print("mspm0kit-tianqiaoxing Skill Setup")
    print("-" * 34)

    def _prompt(label: str, default: str) -> str:
        try:
            value = input(f"{label} [{default}]: ").strip()
        except (EOFError, OSError):
            print(f"[非交互模式] 使用默认值: {default}")
            return default
        return value if value else default

    ccs = _prompt("CCS install dir", DEFAULTS["ccs_root"])
    sdk = _prompt("MSPM0 SDK dir", DEFAULTS["sdk_root"])
    probe = _prompt("Debug probe (XDS110/JLink)", DEFAULTS["probe"])
    return build_config(ccs_root=ccs, sdk_root=sdk, probe=probe)


def write_config(config: dict) -> Path:
    config_path = CONFIG_DIR / "config.json"
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text(encoding="utf-8"))
            # Merge: new values take precedence, keep existing keys not in new config
            merged = {**existing, **config}
            config = merged
        except (json.JSONDecodeError, OSError):
            pass
    config_json = json.dumps(config, indent=2, ensure_ascii=False)
    with open(config_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(config_json)
    return config_path


# ═══════════════════════════════════════════════════════════════════════
#  CLI entry point
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="mspm0kit-tianqiaoxing first-time setup",
        epilog="Agent usage: python setup.py --auto-detect --probe JLink"
    )
    p.add_argument(
        "--auto-detect", action="store_true",
        help="(默认行为) 自动搜索工具链，路径不存在时自动扫描"
    )
    p.add_argument(
        "--accept-defaults", action="store_true",
        help="非交互模式，自动验证路径；不存在则搜索"
    )
    p.add_argument("--ccs-root", default=None, help="CCS install directory")
    p.add_argument("--sdk-root", default=None, help="MSPM0 SDK directory")
    p.add_argument("--probe", default=None, choices=["XDS110", "JLink", "JLINK"],
                   help="Debug probe type")
    args = p.parse_args()

    if args.accept_defaults or args.auto_detect:
        # Non-interactive mode — always validates and auto-searches if paths don't exist
        config = build_config(
            ccs_root=args.ccs_root,
            sdk_root=args.sdk_root,
            probe=args.probe,
        )
    else:
        try:
            config = _interactive_config()
        except (EOFError, OSError):
            print("[非交互模式] 自动搜索工具链路径...")
            config = build_config(
                ccs_root=args.ccs_root,
                sdk_root=args.sdk_root,
                probe=args.probe,
            )

    path = write_config(config)
    print(f"Config saved to: {path}")
