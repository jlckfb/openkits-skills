#!/usr/bin/env python3
"""Clean up a CCS project: remove duplicate .c, generated files in root, stale ticlang/,
and fix IAR/Keil references in makefiles."""
from __future__ import annotations

import re
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

    # 3. Save startup files from ticlang/ before removing the directory
    ticlang = proj / "ticlang"
    if ticlang.is_dir():
        for sf in ticlang.glob("startup_*.c"):
            dest = proj / sf.name
            if not dest.exists():
                shutil.copy2(sf, dest)
                print(f"[startup] copied {sf.name} to root")
                fixed += 1
        try:
            shutil.rmtree(ticlang)
            print("[dir] removed ticlang/")
            fixed += 1
        except PermissionError as e:
            print(f"[warn] could not remove ticlang/ (file in use): {e}")
            print("[warn] ticlang/ left intact — build will overwrite it, this is safe to ignore")

    # 3b. Remove gcc/ (GCC linker scripts — ticlang can't parse them, and CCS
    #     linker will fail with "cannot find file REGION_ALIAS" if present)
    gcc_dir = proj / "gcc"
    if gcc_dir.is_dir():
        try:
            shutil.rmtree(gcc_dir)
            print("[dir] removed gcc/ (GCC linker scripts not needed for ticlang)")
            fixed += 1
        except PermissionError as e:
            print(f"[warn] could not remove gcc/: {e}")

    # 4. Remove leftover src/ directory (from old flat-structure scaffold)
    src_dir = proj / "src"
    if src_dir.is_dir():
        shutil.rmtree(src_dir)
        print("[dir] removed src/ (old flat structure)")
        fixed += 1

    # 5. Fix makefiles: remove IAR startup file references
    for mk in list(proj.glob("*.mak")) + list(proj.glob("makefile*")) + list(proj.glob("*.mk")):
        content = mk.read_text(encoding="utf-8", errors="replace")
        updated = content

        # Remove IAR startup files from OBJECTS
        updated = re.sub(r'startup_mspm0g350x_iar\.o\s*', '', updated)
        # Remove IAR object rules (entire line containing ../iar/)
        updated = re.sub(r'^.*\.\./iar/.*$\n?', '', updated, flags=re.MULTILINE)
        # Remove -I../iar include paths
        updated = re.sub(r'-I\.\./iar\s*', '', updated)
        # Remove Keil startup references
        updated = re.sub(r'startup_mspm0g350x_keil\.o\s*', '', updated)
        updated = re.sub(r'^.*\.\./keil/.*$\n?', '', updated, flags=re.MULTILINE)
        updated = re.sub(r'-I\.\./keil\s*', '', updated)

        if updated != content:
            mk.write_text(updated, encoding="utf-8")
            print(f"[mk] cleaned {mk.name}: removed IAR/Keil references")
            fixed += 1

    print(f"Cleanup complete: {fixed} issue(s) fixed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup.py <project_dir>")
        print("Fixes: duplicate .c between root and subdirs, generated files in root, ticlang/, src/ leftovers, IAR/Keil makefile references")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
