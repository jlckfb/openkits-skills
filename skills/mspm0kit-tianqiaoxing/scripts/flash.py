#!/usr/bin/env python3
"""Flash firmware via DSLite."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main(project_dir: str, config_path: str | None = None) -> None:
    config = _load_config(
        config_path or str(Path(__file__).resolve().parents[1] / "config.json")
    )

    proj = Path(project_dir).resolve()
    out_files = list(proj.glob("ticlang/*.out"))
    if not out_files:
        print("Error: no .out file found. Run build.py first.")
        sys.exit(1)

    out_file = out_files[0]
    ccxml = list(proj.glob("targetConfigs/*.ccxml"))
    if not ccxml:
        print("Warning: no .ccxml found, creating default.")
        target_dir = proj / "targetConfigs"
        target_dir.mkdir(exist_ok=True)
        ccxml_path = target_dir / "MSPM0G3519.ccxml"
        _write_default_ccxml(ccxml_path, config.get("probe", "XDS110"))
    else:
        ccxml_path = ccxml[0]

    # Clean board data cache (stale data causes "invalid processor ID")
    import os
    cache = Path(os.environ.get("LOCALAPPDATA", "")) / "Texas Instruments" / "CCS" / "CCS" / "0" / "1" / "BrdDat"
    if cache.exists():
        for f in cache.glob("ccBoard*.dat"):
            f.unlink()
            print(f"[cache] removed: {f}")

    dslite = config.get("dslite", "DSLite.exe")
    # DSLite 20.x syntax: `DSLite flash -c <ccxml> <firmware>`
    cmd = [dslite, "flash", "-c", str(ccxml_path), str(out_file)]

    print(f"Flashing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Flash failed with exit code {result.returncode}")
        sys.exit(1)


def _load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def _write_default_ccxml(path: Path, probe: str) -> None:
    if probe == "XDS110":
        conn_name = "Texas Instruments XDS110 USB Debug Probe"
        conn_xml = "connections/TIXDS110_Connection.xml"
    else:
        conn_name = "Segger J-Link Emulator"
        conn_xml = "connections/SEGGER_JLink_Emulator_Connection.xml"

    path.write_text(f"""\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<configurations XML_version="1.2" id="configurations_0">
    <configuration XML_version="1.2" id="configuration_0">
        <instance XML_version="1.2" desc="{conn_name}"
                  href="{conn_xml}" id="{conn_name}"
                  xml="{conn_xml.rsplit('/', 1)[-1]}" xmlpath="connections"/>
        <connection XML_version="1.2" id="{conn_name}">
            <instance XML_version="1.2" href="drivers/tixds510cs_dap.xml" id="drivers" xml="tixds510cs_dap.xml" xmlpath="drivers"/>
            <instance XML_version="1.2" href="drivers/tixds510cortexM0.xml" id="drivers" xml="tixds510cortexM0.xml" xmlpath="drivers"/>
            <instance XML_version="1.2" href="drivers/tixds510sec_ap.xml" id="drivers" xml="tixds510sec_ap.xml" xmlpath="drivers"/>
            <property Type="choicelist" Value="1" id="The JTAG TCLK Frequency (MHz)">
                <choice Name="Fixed with user specified value" value="SPECIFIC">
                    <property Type="stringfield" Value="1MHz" id="-- Enter a value from 100.0kHz to 2.5MHz"/>
                </choice>
            </property>
            <property Type="choicelist" Value="2" id="SWD Mode Settings">
                <choice Name="SWD Mode - Aux COM port is target TDO pin" value="nothing"/>
            </property>
            <platform XML_version="1.2" id="platform_0">
                <instance XML_version="1.2" desc="MSPM0G3519"
                          href="devices/MSPM0G3519.xml" id="MSPM0G3519"
                          xml="MSPM0G3519.xml" xmlpath="devices"/>
            </platform>
        </connection>
    </configuration>
</configurations>
""")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Flash MSPM0 firmware")
    p.add_argument("project_dir", help="Path to project directory")
    args = p.parse_args()
    main(args.project_dir)
