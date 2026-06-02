#!/usr/bin/env python3
"""Flash firmware via DSLite (XDS110) or J-Link Commander (JLINK).

probe == "JLINK": convert .out -> .hex with tiarmobjcopy, flash via JLink.exe
probe == "XDS110" (default): flash via DSLite with a generated .ccxml
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def main(project_dir: str, config_path: str | None = None) -> None:
    cfg_path = config_path or str(Path(__file__).resolve().parents[1] / "config.json")
    if not Path(cfg_path).exists():
        print("config.json 不存在。请先运行 `python scripts/setup.py` 配置工具链路径。")
        sys.exit(1)
    config = _load_config(cfg_path)

    chip = config.get("chip", "MSPM0G3507")
    probe = config.get("probe", "XDS110").upper()

    proj = Path(project_dir).resolve()
    out_files = list(proj.glob("ticlang/*.out"))
    if not out_files:
        print("Error: no .out file found. Run build.py first.")
        sys.exit(1)
    out_file = out_files[0]

    if probe in ("JLINK", "J-LINK", "JLINK_COMMANDER"):
        _flash_jlink(out_file, chip, config)
    else:
        _flash_dslite(out_file, proj, chip, config)


def _find_jlink() -> str | None:
    """Search common SEGGER install locations for JLink.exe."""
    import glob
    patterns = [
        r"C:\Program Files\SEGGER\JLink*\JLink.exe",
        r"C:\Program Files (x86)\SEGGER\JLink*\JLink.exe",
        r"D:\Program Files\SEGGER\JLink*\JLink.exe",
    ]
    for pattern in patterns:
        matches = sorted(glob.glob(pattern), reverse=True)  # newest version first
        if matches:
            return matches[0]
    return None


def _flash_jlink(out_file: Path, chip: str, config: dict) -> None:
    """Convert .out to .hex and flash with JLink Commander."""
    compiler_bin = Path(config.get("compiler", "")) / "bin"
    objcopy = compiler_bin / "tiarmobjcopy.exe"
    jlink = config.get("jlink_path", "")

    # Auto-search if not configured or not found
    if not jlink or not Path(jlink).exists():
        found = _find_jlink()
        if found:
            print(f"[flash] JLink.exe 自动找到：{found}")
            jlink = found
        else:
            print(
                "Error: JLink.exe 未找到。\n"
                "请在 config.json 中添加 jlink_path 字段，例如：\n"
                '  "jlink_path": "C:/Program Files/SEGGER/JLink_V798/JLink.exe"'
            )
            sys.exit(1)

    if not objcopy.exists():
        print(f"Error: tiarmobjcopy 未找到：{objcopy}\n请检查 config.json 的 compiler 路径。")
        sys.exit(1)

    # 1. .out -> .hex
    hex_file = out_file.with_suffix(".hex")
    objcopy_cmd = [str(objcopy), "-O", "ihex", str(out_file), str(hex_file)]
    print(f"[objcopy] {' '.join(objcopy_cmd)}")
    r = subprocess.run(objcopy_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"objcopy failed:\n{r.stderr}\n{r.stdout}")
        sys.exit(1)

    # 2. JLink command file
    jlink_script = out_file.parent / "flash.jlink"
    jlink_script.write_text(
        f"si SWD\n"
        f"speed 1000\n"
        f"device {chip}\n"
        f"connect\n"
        f"r\n"
        f"h\n"
        f"loadfile {hex_file.name}\n"
        f"r\n"
        f"g\n"
        f"qc\n",
        encoding="utf-8",
    )

    # 3. Flash — capture output to detect JLink failures even when exit code is 0
    jlink_cmd = [jlink, "-CommandFile", str(jlink_script)]
    print(f"[JLink] {' '.join(jlink_cmd)}")
    r = subprocess.run(jlink_cmd, capture_output=True, text=True, cwd=str(out_file.parent))
    output = r.stdout + r.stderr
    print(output)

    # JLink sometimes exits 0 even on connection failure — check output for error keywords
    failure_keywords = [
        "Cannot connect",
        "Could not connect",
        "FAILED:",
        "Error: Failed",
        "Programming failed",
        "Verification failed",
        "Unable to connect",
    ]
    found_failure = [kw for kw in failure_keywords if kw.lower() in output.lower()]
    if r.returncode != 0 or found_failure:
        if found_failure:
            print(f"J-Link flash failed (detected: {found_failure[0]})")
        else:
            print(f"J-Link flash failed with exit code {r.returncode}")
        sys.exit(1)
    print("J-Link flash complete.")


def _flash_dslite(out_file: Path, proj: Path, chip: str, config: dict) -> None:
    """Flash via DSLite (XDS110)."""
    ccxml = list(proj.glob("targetConfigs/*.ccxml"))
    if not ccxml:
        print("Warning: no .ccxml found, creating default.")
        target_dir = proj / "targetConfigs"
        target_dir.mkdir(exist_ok=True)
        ccxml_path = target_dir / f"{chip}.ccxml"
        _write_default_ccxml(ccxml_path, "XDS110", chip)
    else:
        ccxml_path = ccxml[0]

    # Clean board data cache (stale data causes "invalid processor ID")
    cache = Path(os.environ.get("LOCALAPPDATA", "")) / "Texas Instruments" / "CCS" / "CCS" / "0" / "1" / "BrdDat"
    if cache.exists():
        for f in cache.glob("ccBoard*.dat"):
            f.unlink()
            print(f"[cache] removed: {f}")

    dslite = config.get("dslite", "DSLite.exe")
    cmd = [dslite, "flash", "-c", str(ccxml_path), str(out_file)]
    print(f"Flashing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Flash failed with exit code {result.returncode}")
        sys.exit(1)


def _write_default_ccxml(path: Path, probe: str, chip: str) -> None:
    conn_name = "Texas Instruments XDS110 USB Debug Probe"
    conn_xml = "connections/TIXDS110_Connection.xml"
    driver_dap = "tixds510cs_dap.xml"
    driver_cortex = "tixds510cortexM0.xml"
    driver_sec = "tixds510sec_ap.xml"

    path.write_text(f"""\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<configurations XML_version="1.2" id="configurations_0">
    <configuration XML_version="1.2" id="configuration_0">
        <instance XML_version="1.2" desc="{conn_name}"
                  href="{conn_xml}" id="{conn_name}"
                  xml="{conn_xml.rsplit('/', 1)[-1]}" xmlpath="connections"/>
        <connection XML_version="1.2" id="{conn_name}">
            <instance XML_version="1.2" href="drivers/{driver_dap}" id="drivers" xml="{driver_dap}" xmlpath="drivers"/>
            <instance XML_version="1.2" href="drivers/{driver_cortex}" id="drivers" xml="{driver_cortex}" xmlpath="drivers"/>
            <instance XML_version="1.2" href="drivers/{driver_sec}" id="drivers" xml="{driver_sec}" xmlpath="drivers"/>
            <property Type="choicelist" Value="1" id="The JTAG TCLK Frequency (MHz)">
                <choice Name="Fixed with user specified value" value="SPECIFIC">
                    <property Type="stringfield" Value="1MHz" id="-- Enter a value from 100.0kHz to 2.5MHz"/>
                </choice>
            </property>
            <property Type="choicelist" Value="2" id="SWD Mode Settings">
                <choice Name="SWD Mode - Aux COM port is target TDO pin" value="nothing"/>
            </property>
            <platform XML_version="1.2" id="platform_0">
                <instance XML_version="1.2" desc="{chip}"
                          href="devices/{chip}.xml" id="{chip}"
                          xml="{chip}.xml" xmlpath="devices"/>
            </platform>
        </connection>
    </configuration>
</configurations>
""")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Flash MSPM0 firmware (DSLite or J-Link)")
    p.add_argument("project_dir", help="Path to project directory")
    p.add_argument("-y", "--yes", action="store_true", help="Skip interactive prompts")
    args = p.parse_args()
    main(args.project_dir)
