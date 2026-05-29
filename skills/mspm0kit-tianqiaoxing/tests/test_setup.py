import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import setup


def test_config_json_written():
    """setup.py must write config.json with all required keys."""
    with tempfile.TemporaryDirectory() as tmp:
        orig = setup.CONFIG_DIR
        setup.CONFIG_DIR = Path(tmp)

        try:
            with patch("builtins.input", side_effect=["", "", ""]):
                cfg = setup.interactive_config()
                setup.write_config(cfg)

            cfg_path = Path(tmp) / "config.json"
            assert cfg_path.exists()
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

            for k in ("ccs_root", "sdk_root", "sysconfig_cli",
                       "dslite", "gmake", "compiler", "sdk_examples",
                       "probe"):
                assert k in cfg, f"Missing key: {k}"
        finally:
            setup.CONFIG_DIR = orig


def test_user_override():
    """User input replaces defaults."""
    with tempfile.TemporaryDirectory() as tmp:
        orig = setup.CONFIG_DIR
        setup.CONFIG_DIR = Path(tmp)

        try:
            with patch("builtins.input",
                        side_effect=[r"C:\my\ccs", r"C:\my\sdk", "JLink"]):
                cfg = setup.interactive_config()
                setup.write_config(cfg)

            cfg = json.loads((Path(tmp) / "config.json").read_text(encoding="utf-8"))
            assert cfg["ccs_root"] == r"C:\my\ccs"
            assert cfg["sdk_root"] == r"C:\my\sdk"
            assert cfg["probe"] == "JLink"
        finally:
            setup.CONFIG_DIR = orig
