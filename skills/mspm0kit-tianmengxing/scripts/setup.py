#!/usr/bin/env python3
"""First-time setup: ask for toolchain paths and write config.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "ccs_root": r"D:\TI\CCS\ccs",
    "sdk_root": r"D:\TI\CCS\mspm0_sdk_2_05_01_00",
    "sysconfig_cli": r"D:\TI\CCS\ccs\utils\sysconfig_1.24.0\sysconfig_cli.bat",
    "dslite": r"D:\TI\CCS\ccs\ccs_base\DebugServer\bin\DSLite.exe",
    "gmake": r"D:\TI\CCS\ccs\utils\bin\gmake.exe",
    "compiler": r"D:\TI\CCS\ccs\tools\compiler\ti-cgt-armllvm_4.0.3.LTS",
    "sdk_examples": r"D:\TI\CCS\mspm0_sdk_2_05_01_00\examples\nortos\LP_MSPM0G3507\driverlib",
    "probe": "XDS110",
    "chip": "MSPM0G3507",
}


def _safe_prompt(label: str, default: str) -> str:
    try:
        value = input(f"{label} [{default}]: ").strip()
    except (EOFError, OSError):
        print(f"[非交互模式] 使用默认值: {default}")
        return default
    except (UnicodeEncodeError, UnicodeDecodeError):
        safe = label.encode("ascii", errors="replace").decode("ascii")
        try:
            value = input(f"{safe} [{default}]: ").strip()
        except (EOFError, OSError):
            print(f"[非交互模式] 使用默认值: {default}")
            return default
    return value if value else default


def interactive_config() -> dict:
    print("mspm0kit-tianmengxing Skill Setup")
    print("-" * 34)
    ccs_root = _safe_prompt("CCS install dir", DEFAULTS["ccs_root"])
    sdk_root = _safe_prompt("MSPM0 SDK dir", DEFAULTS["sdk_root"])
    probe = _safe_prompt("Debug probe (XDS110/JLink)", DEFAULTS["probe"])
    return {
        "ccs_root": ccs_root,
        "sdk_root": sdk_root,
        "sysconfig_cli": DEFAULTS["sysconfig_cli"],
        "dslite": DEFAULTS["dslite"],
        "gmake": DEFAULTS["gmake"],
        "compiler": DEFAULTS["compiler"],
        "sdk_examples": str(Path(sdk_root) / "examples/nortos/LP_MSPM0G3507/driverlib"),
        "probe": probe,
        "chip": DEFAULTS["chip"],
    }


def write_config(config: dict) -> Path:
    config_path = CONFIG_DIR / "config.json"
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text(encoding="utf-8"))
            merged = {**existing, **config}
            config = merged
        except (json.JSONDecodeError, OSError):
            pass
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return config_path


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="mspm0kit-tianmengxing first-time setup")
    p.add_argument("--accept-defaults", action="store_true",
                   help="Skip prompts, use all defaults")
    p.add_argument("--ccs-root", default=None)
    p.add_argument("--sdk-root", default=None)
    p.add_argument("--probe", default=None, choices=["XDS110", "JLink"])
    args = p.parse_args()

    if args.accept_defaults:
        config = {
            "ccs_root": args.ccs_root or DEFAULTS["ccs_root"],
            "sdk_root": args.sdk_root or DEFAULTS["sdk_root"],
            "sysconfig_cli": DEFAULTS["sysconfig_cli"],
            "dslite": DEFAULTS["dslite"],
            "gmake": DEFAULTS["gmake"],
            "compiler": DEFAULTS["compiler"],
            "sdk_examples": str(Path(args.sdk_root or DEFAULTS["sdk_root"])
                / "examples/nortos/LP_MSPM0G3507/driverlib"),
            "probe": args.probe or DEFAULTS["probe"],
            "chip": DEFAULTS["chip"],
        }
    else:
        try:
            config = interactive_config()
        except (EOFError, OSError):
            print("[非交互模式] 使用默认配置")
            config = {
                "ccs_root": args.ccs_root or DEFAULTS["ccs_root"],
                "sdk_root": args.sdk_root or DEFAULTS["sdk_root"],
                "sysconfig_cli": DEFAULTS["sysconfig_cli"],
                "dslite": DEFAULTS["dslite"],
                "gmake": DEFAULTS["gmake"],
                "compiler": DEFAULTS["compiler"],
                "sdk_examples": str(Path(args.sdk_root or DEFAULTS["sdk_root"])
                    / "examples/nortos/LP_MSPM0G3507/driverlib"),
                "probe": args.probe or DEFAULTS["probe"],
                "chip": DEFAULTS["chip"],
            }

    path = write_config(config)
    print(f"Config saved to: {path}")
