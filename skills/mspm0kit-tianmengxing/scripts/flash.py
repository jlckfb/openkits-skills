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

    chip = config.get("chip", "MSPM0G3507")

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
        ccxml_path = target_dir / f"{chip}.ccxml"
        _write_default_ccxml(ccxml_path, config.get("probe", "XDS110"), chip)
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
    cmd = [dslite, "flash", "-c", str(ccxml_path), str(out_file)]

    print(f"Flashing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Flash failed with exit code {result.returncode}")
        sys.exit(1)


def _load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def _write_default_ccxml(path: Path, probe: str, chip: str) -> None:
    if probe == "XDS110":
        conn_name = "Texas Instruments XDS110 USB Debug Probe"
        conn_xml = "connections/TIXDS110_Connection.xml"
        driver_dap = "tixds510cs_dap.xml"
        driver_cortex = "tixds510cortexM0.xml"
        driver_sec = "tixds510sec_ap.xml"
    else:
        conn_name = "Segger J-Link Emulator"
        conn_xml = "connections/segger_j-link_connection.xml"
        driver_dap = "jlinkcs_dap.xml"
        driver_cortex = "jlinkcortexm0p.xml"
        driver_sec = "jlinksec_ap.xml"

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
    p = argparse.ArgumentParser(description="Flash MSPM0 firmware")
    p.add_argument("project_dir", help="Path to project directory")
    args = p.parse_args()
    main(args.project_dir)
