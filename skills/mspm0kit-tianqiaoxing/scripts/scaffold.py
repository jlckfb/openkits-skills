#!/usr/bin/env python3
"""Generate a Tianqiaoxing-adapted CCS project from an SDK example."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def _load_config(config_path: str) -> dict:
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _copy_and_rename(src: Path, dst: Path, old_name: str, new_name: str) -> None:
    """Copy file, replacing the old project name stem in filename and content."""
    new_stem = src.stem.replace(old_name, new_name)
    dst_file = dst / f"{new_stem}{src.suffix}"
    dst.mkdir(parents=True, exist_ok=True)
    content = src.read_text(encoding="utf-8", errors="replace")
    content = content.replace(old_name, new_name)
    dst_file.write_text(content, encoding="utf-8")


def _write_projectspec(out: Path, project_name: str, example_name: str) -> None:
    """Generate minimal .projectspec for skill-bundled examples."""
    src_files = ' '.join(
        f'<file path="{f.relative_to(out)}" openOnCreation="false" excludeFromBuild="false" action="copy"/>'
        for f in sorted(out.rglob("*.c")) if "ticlang" not in str(f)
    )
    spec = f'''<?xml version="1.0" encoding="UTF-8"?>
<projectSpec>
    <applicability><when><context deviceFamily="ARM" deviceId="MSPM0G3519"/></when></applicability>
    <project
        title="{project_name}" name="{project_name}"
        configurations="Debug" toolChain="TICLANG"
        connection="TIXDS110_Connection.xml" device="MSPM0G3519"
        ignoreDefaultDeviceSettings="true" ignoreDefaultCCSSettings="true"
        products="MSPM0-SDK;sysconfig"
        compilerBuildOptions="
            -I${{PROJECT_ROOT}} -I${{PROJECT_ROOT}}/${{ConfigName}} -I${{PROJECT_ROOT}}/src
            -O2 @device.opt
            -I${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source/third_party/CMSIS/Core/Include
            -I${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source
            -gdwarf-3 -mcpu=cortex-m0plus -march=thumbv6m -mfloat-abi=soft -mthumb"
        linkerBuildOptions="
            -ldevice.cmd.genlibs
            -L${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source
            -L${{PROJECT_ROOT}} -L${{PROJECT_BUILD_DIR}}/syscfg
            -Wl,--rom_model -Wl,--warn_sections
            -L${{CG_TOOL_ROOT}}/lib -llibc.a"
        sysConfigBuildOptions="
            --output . --product ${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/.metadata/product.json
            --compiler ticlang"
        description="{example_name} for MSPM0G3519">
        <property name="buildProfile" value="release"/>
        <property name="isHybrid" value="true"/>
        <file path="{project_name}.syscfg" openOnCreation="true" excludeFromBuild="false" action="copy"/>
        {src_files}
    </project>
</projectSpec>'''
    (out / f"{project_name}.projectspec").write_text(spec, encoding="utf-8")


def main(
    project_name: str,
    sdk_example: str,
    output_dir: str | None = None,
    config_path: str | None = None,
    _interactive: bool = True,
) -> Path:
    config = _load_config(
        config_path or str(Path(__file__).resolve().parents[1] / "config.json")
    )

    # Search order: skill bundled examples first, then SDK examples
    skill_examples_dir = Path(__file__).resolve().parents[1] / "examples"
    sdk_examples_dir = Path(config.get("sdk_examples", ""))

    source_dir = None
    if (skill_examples_dir / sdk_example).is_dir():
        source_dir = skill_examples_dir / sdk_example
    elif sdk_examples_dir and (sdk_examples_dir / sdk_example).is_dir():
        source_dir = sdk_examples_dir / sdk_example

    if not source_dir:
        raise FileNotFoundError(
            f"Example not found: {sdk_example}\n"
            f"  Looked in: {skill_examples_dir}\n"
            f"  Looked in: {sdk_examples_dir}"
        )

    out = Path(output_dir or Path.cwd()) / project_name
    out.mkdir(parents=True, exist_ok=True)

    is_skill_example = (skill_examples_dir / sdk_example).is_dir()

    # 1. Copy ALL files preserving directory structure (skip Debug/ticlang)
    skip_dirs = {"Debug", "ticlang", "targetConfigs"}
    for item in source_dir.rglob("*"):
        if item.is_dir() or any(s in item.parts for s in skip_dirs):
            continue
        rel = item.relative_to(source_dir)
        if rel.parts[0] in skip_dirs:
            continue
        dst_file = out / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        if item.suffix == ".syscfg":
            content = item.read_text(encoding="utf-8", errors="replace")
            content = re.sub(r'--package\s+"LQFP-100\(PZ\)"', '--package "LQFP-64(PM)"', content)
            if item.stem == "example":
                dst_file = out / f"{project_name}.syscfg"
            else:
                dst_file = out / item.name.replace(sdk_example, project_name)
            dst_file.write_text(content, encoding="utf-8")
        elif item.suffix == ".c":
            if item.stem == "main":
                shutil.copy2(item, out / "main.c")
            elif item.stem == sdk_example:
                shutil.copy2(item, out / f"{project_name}.c")
            elif item.stem != "example":
                shutil.copy2(item, dst_file)
        elif item.suffix == ".h":
            if item.stem != "example":
                shutil.copy2(item, dst_file)
        else:
            shutil.copy2(item, dst_file)

    # 2. Generate .projectspec
    pspec_files = list((source_dir / "ticlang").glob("*.projectspec")) if (source_dir / "ticlang").is_dir() else []
    if pspec_files:
        for ps in pspec_files:
            content = ps.read_text(encoding="utf-8", errors="replace")
            content = content.replace(
                f"{sdk_example}_LP_MSPM0G3519_nortos_ticlang", project_name
            )
            content = content.replace(sdk_example, project_name)
            content = re.sub(
                r'path="\.\./.*?\.c"', f'path="{project_name}.c"', content
            )
            content = re.sub(
                r'path="\.\./.*?\.syscfg"',
                f'path="{project_name}.syscfg"',
                content,
            )
            content = re.sub(r'path="\.\./README\.md"', 'path="README.md"', content)
            content = re.sub(
                r'path="\.\./README\.html"', 'path="README.html"', content
            )
            content = re.sub(
                r'name=".*?_LP_MSPM0G3519_nortos_ticlang"',
                f'name="{project_name}"',
                content,
            )
            content = re.sub(
                r'title=".*?"', f'title="{project_name}"', content
            )
            (out / f"{project_name}.projectspec").write_text(content, encoding="utf-8")
    else:
        # Generate minimal .projectspec for skill-bundled examples
        _write_projectspec(out, project_name, sdk_example)

    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Tianqiaoxing-adapted CCS project from SDK example"
    )
    parser.add_argument("project_name", help="Name for the new project")
    parser.add_argument("sdk_example", help="SDK example directory name")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Parent output directory (default: current dir)",
    )
    args = parser.parse_args()

    result = main(
        project_name=args.project_name,
        sdk_example=args.sdk_example,
        output_dir=args.output,
    )
    print(f"Project created: {result}")
