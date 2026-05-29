#!/usr/bin/env python3
"""Clean up a CCS project: remove duplicate .c, generated files in root, stale ticlang/."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main(project_dir: str) -> int:
    proj = Path(project_dir).resolve()
    if not proj.is_dir():
        print(f"ERROR: {proj} not found")
        return 1

    fixed = 0
    skip_dirs = {"Debug", "ticlang", "targetConfigs", ".settings", ".git"}

    # 1. Remove duplicate .c files between root and subdirectories
    #    (AI sometimes puts a copy in root by mistake; keep the subdir version)
    root_c_files = {f.name for f in proj.glob("*.c")}
    for d in proj.iterdir():
        if not d.is_dir() or d.name in skip_dirs:
            continue
        for cf in d.rglob("*.c"):
            if cf.name in root_c_files:
                root_dup = proj / cf.name
                if root_dup.exists():
                    if root_dup.read_text() == cf.read_text():
                        root_dup.unlink()
                        print(f"[dup] removed root/{cf.name} (keep {cf.relative_to(proj)})")
                        fixed += 1
                    else:
                        print(f"[warn] root/{cf.name} differs from {cf.relative_to(proj)} — review manually")

    # 2. Remove generated files that belong in Debug/
    for name in ["device_linker.cmd", "device.cmd.genlibs", "device.opt",
                  "ti_msp_dl_config.c", "ti_msp_dl_config.h"]:
        gen_file = proj / name
        if gen_file.exists():
            gen_file.unlink()
            print(f"[gen] removed root/{name}")
            fixed += 1

    # 3. Remove ticlang/ directory (conflicts with CCS Debug/)
    ticlang = proj / "ticlang"
    if ticlang.is_dir():
        shutil.rmtree(ticlang)
        print("[dir] removed ticlang/")
        fixed += 1

    # 4. Remove leftover src/ directory (from old flat-structure scaffold)
    src_dir = proj / "src"
    if src_dir.is_dir():
        shutil.rmtree(src_dir)
        print("[dir] removed src/ (old flat structure)")
        fixed += 1

    print(f"Cleanup complete: {fixed} issue(s) fixed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup.py <project_dir>")
        print("Fixes: duplicate .c between root and subdirs, generated files in root, ticlang/, src/ leftovers")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
