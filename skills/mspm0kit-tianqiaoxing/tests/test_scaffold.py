import json
import tempfile
from pathlib import Path
import sys
import shutil

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import scaffold


def _make_fake_sdk_example(sdk_examples_dir: Path) -> Path:
    eg = sdk_examples_dir / "uart_rw_multibyte_fifo_poll"
    eg.mkdir(parents=True)
    ticlang = eg / "ticlang"
    ticlang.mkdir()

    (eg / "uart_rw_multibyte_fifo_poll.syscfg").write_text("""\
/**
 * @cliArgs --device "MSPM0G351X" --package "LQFP-100(PZ)" --part "Default"
 * @v2CliArgs --device "MSPM0G3519" --package "LQFP-100(PZ)"
 * @versions {"tool":"1.24.0+4110"}
 */
const GPIO   = scripting.addModule("/ti/driverlib/GPIO", {}, false);
const GPIO1  = GPIO.addInstance();
const SYSCTL = scripting.addModule("/ti/driverlib/SYSCTL");
GPIO1.$name = "GPIO_LEDS";
GPIO1.associatedPins[0].pin.$assign = "PA0";
SYSCTL.forceDefaultClkConfig = true;
SYSCTL.clockTreeEn = true;
""")

    (eg / "uart_rw_multibyte_fifo_poll.c").write_text("""\
#include "ti_msp_dl_config.h"
int main(void) { SYSCFG_DL_init(); while(1){} }
""")

    (ticlang / "uart_rw_multibyte_fifo_poll_LP_MSPM0G3519_nortos_ticlang.projectspec").write_text("""\
<?xml version="1.0" encoding="UTF-8"?>
<projectSpec>
  <project
    title="uart_rw_multibyte_fifo_poll"
    name="uart_rw_multibyte_fifo_poll_LP_MSPM0G3519_nortos_ticlang"
    device="MSPM0G3519"
    toolChain="TICLANG"
    connection="TIXDS110_Connection.xml">
    <file path="../uart_rw_multibyte_fifo_poll.c" action="copy"/>
    <file path="../uart_rw_multibyte_fifo_poll.syscfg" action="copy"/>
  </project>
</projectSpec>
""")

    (ticlang / "device_linker.cmd").write_text("/* linker cmd */")
    return eg


def _make_config(tmp: Path) -> Path:
    cfg = tmp / "config.json"
    cfg.write_text(json.dumps({
        "sdk_examples": str(tmp / "sdk_examples"),
        "probe": "XDS110",
    }))
    return cfg


def test_scaffold_copies_files():
    """scaffold must copy .syscfg, .c, device_linker.cmd to output."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sdk_dir = root / "sdk_examples"
        sdk_dir.mkdir()
        _make_fake_sdk_example(sdk_dir)
        cfg = _make_config(root)

        out_dir = root / "output"
        scaffold.main(
            project_name="my_uart_test",
            sdk_example="uart_rw_multibyte_fifo_poll",
            output_dir=str(out_dir),
            config_path=str(cfg),
            _interactive=False,
        )

        proj = out_dir / "my_uart_test"
        assert (proj / "my_uart_test.syscfg").exists()
        assert (proj / "my_uart_test.c").exists()
        # CCS generates device_linker.cmd via SysConfig — scaffold no longer copies it
        assert (proj / "my_uart_test.projectspec").exists()


def test_scaffold_fixes_package():
    """LQFP-100(PZ) must be replaced with LQFP-64(PM) in syscfg."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sdk_dir = root / "sdk_examples"
        sdk_dir.mkdir()
        _make_fake_sdk_example(sdk_dir)
        cfg = _make_config(root)

        out_dir = root / "output"
        scaffold.main(
            project_name="test_pkg",
            sdk_example="uart_rw_multibyte_fifo_poll",
            output_dir=str(out_dir),
            config_path=str(cfg),
            _interactive=False,
        )

        proj = out_dir / "test_pkg"
        syscfg = (proj / "test_pkg.syscfg").read_text()
        assert 'LQFP-64(PM)' in syscfg
        assert 'LQFP-100(PZ)' not in syscfg


def test_scaffold_rejects_unknown_example():
    """scaffold must fail clearly when SDK example doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sdk_dir = root / "sdk_examples"
        sdk_dir.mkdir()
        cfg = _make_config(root)

        try:
            scaffold.main(
                project_name="bad",
                sdk_example="nonexistent_example",
                output_dir=str(root / "out"),
                config_path=str(cfg),
                _interactive=False,
            )
            assert False, "Should have raised"
        except FileNotFoundError as e:
            assert "nonexistent_example" in str(e)
