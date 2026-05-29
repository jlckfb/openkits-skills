import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import build


def test_build_runs_sysconfig_cli():
    """build.py must call sysconfig_cli.bat with correct arguments."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        proj = root / "my_proj"
        proj.mkdir()
        (proj / "my_proj.syscfg").write_text("// syscfg")
        (proj / "ticlang").mkdir()

        sysconfig_cli = root / "fake_sysconfig_cli.bat"
        sysconfig_cli.write_text("@echo off\necho fake sysconfig")
        cfg = root / "config.json"
        cfg.write_text(json.dumps({
            "sysconfig_cli": str(sysconfig_cli),
            "gmake": str(root / "fake_gmake.exe"),
            "sdk_root": str(root / "sdk"),
        }))

        sdk = root / "sdk" / ".metadata"
        sdk.mkdir(parents=True)
        (sdk / "product.json").write_text("{}")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            ok, _ = build.main(str(proj), config_path=str(cfg), _interactive=False)

            assert ok
            mock_run.assert_called()
            first_call = mock_run.call_args_list[0][0][0]
            assert "sysconfig_cli.bat" in first_call[0]


def test_build_runs_gmake():
    """After SysConfig, build must invoke gmake."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        proj = root / "my_proj"
        proj.mkdir()
        (proj / "my_proj.syscfg").write_text("// syscfg")
        (proj / "ticlang").mkdir()

        sysconfig_cli = root / "sysconfig_cli.bat"
        sysconfig_cli.write_text("@echo off")
        gmake_path = root / "gmake.exe"
        gmake_path.write_text("")

        cfg = root / "config.json"
        cfg.write_text(json.dumps({
            "sysconfig_cli": str(sysconfig_cli),
            "gmake": str(gmake_path),
            "sdk_root": str(root / "sdk"),
        }))

        sdk = root / "sdk" / ".metadata"
        sdk.mkdir(parents=True)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            ok, _ = build.main(str(proj), config_path=str(cfg), _interactive=False)

            assert ok
            gmake_calls = [
                c for c in mock_run.call_args_list
                if "gmake" in str(c[0][0])
            ]
            assert len(gmake_calls) >= 1
