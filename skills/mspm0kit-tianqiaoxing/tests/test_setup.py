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
            # All empty input → fall back to defaults (paths auto-searched/validated).
            with patch("builtins.input", side_effect=["", "", ""]):
                cfg = setup._interactive_config()
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
    """User input replaces defaults when the supplied paths exist.

    build_config validates paths and auto-searches when they don't exist, so the
    override semantics can only be asserted with real directories — feed existing
    temp dirs for CCS/SDK; probe is stored verbatim.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ccs_dir = root / "ccs"
        sdk_dir = root / "sdk"
        ccs_dir.mkdir()
        sdk_dir.mkdir()

        orig = setup.CONFIG_DIR
        setup.CONFIG_DIR = root

        try:
            with patch("builtins.input",
                        side_effect=[str(ccs_dir), str(sdk_dir), "JLink"]):
                cfg = setup._interactive_config()
                setup.write_config(cfg)

            cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
            assert cfg["ccs_root"] == str(ccs_dir)
            assert cfg["sdk_root"] == str(sdk_dir)
            assert cfg["probe"] == "JLink"
        finally:
            setup.CONFIG_DIR = orig
