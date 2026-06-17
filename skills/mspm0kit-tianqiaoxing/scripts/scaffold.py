#!/usr/bin/env python3
"""Generate a Tianqiaoxing-adapted CCS project from an SDK example."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

# Board-specific constants
CHIP = "MSPM0G3519"
CHIP_MACRO = "__MSPM0G3519__"
STARTUP_PATTERN = "mspm0g351x"
LP_BOARD = "LP_MSPM0G3519"


def _load_config(config_path: str) -> dict:
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _clean_project(out: Path) -> None:
    """Remove IAR/Keil startup files and fix up project for ticlang-only build."""

    # Remove IAR/Keil startup directories and files
    for p in out.rglob("*"):
        if any(k in str(p).lower() for k in ["iar", "keil", "uvision"]):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.is_file():
                p.unlink()

    # Remove IAR/Keil startup .c/.s files at any level (both family and specific patterns)
    for pattern in ["*iar*.c", "*iar*.s", "*keil*.c", "*keil*.s",
                    f"startup_{STARTUP_PATTERN}_iar*", f"startup_{STARTUP_PATTERN}_keil*",
                    "startup_mspm0g350x_iar*", "startup_mspm0g350x_keil*",
                    "startup_mspm0g351x_iar*", "startup_mspm0g351x_keil*"]:
        for f in out.rglob(pattern):
            f.unlink()

    # Fix makefiles: remove IAR/Keil OBJECTS and rules, fix chip macro
    for mk in list(out.rglob("*.mak")) + list(out.rglob("makefile*")) + list(out.rglob("*.mk")):
        content = mk.read_text(encoding="utf-8", errors="replace")
        updated = content

        # Remove IAR/Keil startup .o from OBJECTS (any variant)
        updated = re.sub(rf'startup_{STARTUP_PATTERN}_iar\.o\s*', '', updated)
        updated = re.sub(rf'startup_{STARTUP_PATTERN}_keil\.o\s*', '', updated)
        updated = re.sub(r'startup_mspm0g350x_iar\.o\s*', '', updated)
        updated = re.sub(r'startup_mspm0g350x_keil\.o\s*', '', updated)
        updated = re.sub(r'startup_mspm0g351x_iar\.o\s*', '', updated)
        updated = re.sub(r'startup_mspm0g351x_keil\.o\s*', '', updated)
        # Remove IAR/Keil build rules (lines referencing ../iar/ ../keil/)
        updated = re.sub(r'^.*\.\./iar/.*$\n?', '', updated, flags=re.MULTILINE)
        updated = re.sub(r'^.*\.\./keil/.*$\n?', '', updated, flags=re.MULTILINE)
        # Remove -I../iar and -I../keil include paths
        updated = re.sub(r'-I\.\./iar\s*', '', updated)
        updated = re.sub(r'-I\.\./keil\s*', '', updated)
        # Fix chip macro
        updated = re.sub(r'-D__MSPM0G3519__', f'-D{CHIP_MACRO}', updated)
        updated = re.sub(r'-D__MSPM0G3507__', f'-D{CHIP_MACRO}', updated)
        # Fix ticlang startup path: ../startup_xxx.c → ticlang/startup_xxx.c
        updated = re.sub(rf'\.\./startup_{STARTUP_PATTERN}_ticlang\.c',
                         f'ticlang/startup_{STARTUP_PATTERN}_ticlang.c', updated)

        if updated != content:
            mk.write_text(updated, encoding="utf-8")
            print(f"[makefile] cleaned {mk.relative_to(out)}")


def _write_projectspec(out: Path, project_name: str, example_name: str) -> None:
    """Generate minimal .projectspec for skill-bundled examples."""
    src_files = ' '.join(
        f'<file path="{f.relative_to(out)}" openOnCreation="false" excludeFromBuild="false" action="copy"/>'
        for f in sorted(out.rglob("*.c")) if "ticlang" not in str(f) and "iar" not in str(f).lower() and "keil" not in str(f).lower()
    )
    spec = f'''<?xml version="1.0" encoding="UTF-8"?>
<projectSpec>
    <applicability><when><context deviceFamily="ARM" deviceId="{CHIP}"/></when></applicability>
    <project
        title="{project_name}" name="{project_name}"
        configurations="Debug" toolChain="TICLANG"
        connection="TIXDS110_Connection.xml" device="{CHIP}"
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
        description="{example_name} for {CHIP}">
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
        if not config.get("sdk_examples"):
            raise FileNotFoundError(
                f"找不到示例 '{sdk_example}'，且 config.json 未配置 SDK 路径。\n"
                "请先运行 `python scripts/setup.py` 配置工具链路径，\n"
                "或提供 SDK 示例目录（例如 D:/TI/CCS/mspm0_sdk_2_05_01_00/examples/nortos/LP_MSPM0G3519/driverlib）。"
            )
        raise FileNotFoundError(
            f"Example not found: {sdk_example}\n"
            f"  Looked in: {skill_examples_dir}\n"
            f"  Looked in: {sdk_examples_dir}\n"
            "请确认示例名称正确，或检查 config.json 的 sdk_examples 路径。"
        )

    out = Path(output_dir or Path.cwd()) / project_name
    out.mkdir(parents=True, exist_ok=True)

    # 1. Copy ALL files preserving directory structure (skip Debug/ticlang/targetConfigs)
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
            # Add header comment: warn about GPIO instance/pin naming (gpio.md rule).
            # ASCII-only: a Chinese comment here can crash tools that read the
            # .syscfg under a GBK locale on Windows.
            if "Generated by scaffold" not in content:
                header = (
                    "// == Generated by scaffold.py ==\n"
                    "// GPIO instance $name != pin $name, and every $name is globally unique.\n"
                    "//   WRONG: instance=\"LED\", pin=\"LED\"  -> Duplicate name error\n"
                    "//   OK:    instance=\"LED\", pin=\"PIN\"\n"
                    "// SDK example may carry extra pins (PB26/PB27/PB14 are occupied on this\n"
                    "// board) -- delete the ones you don't need.\n"
                    "// After SysConfig runs, grep ti_msp_dl_config.h to confirm macro names.\n"
                    "\n"
                )
                content = header + content
            if item.stem == "example":
                dst_file = out / f"{project_name}.syscfg"
            else:
                dst_file = out / item.name.replace(sdk_example, project_name)
            # Normalize to LF (prevents CRLF edit_file matching failures on Windows)
            content = content.replace('\r\n', '\n')
            with open(dst_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
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

    # 2. Clean up IAR/Keil files and fix makefiles
    _clean_project(out)

    # 3. Generate .projectspec
    pspec_files = list((source_dir / "ticlang").glob("*.projectspec")) if (source_dir / "ticlang").is_dir() else []
    if pspec_files:
        for ps in pspec_files:
            content = ps.read_text(encoding="utf-8", errors="replace")
            content = content.replace(
                f"{sdk_example}_{LP_BOARD}_nortos_ticlang", project_name
            )
            content = content.replace(sdk_example, project_name)
            # Fix chip macro in any preprocessor defines
            content = re.sub(r'-D__MSPM0G3519__', f'-D{CHIP_MACRO}', content)
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
                r'name=".*?_{LP_BOARD}_nortos_ticlang"',
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
    print("\n注意：SDK 例程可能包含多余的默认引脚（如 PB26/PB27/PB14 在天巧星上已被占用）。")
    print("   请编辑 .syscfg 检查引脚分配，确保不会与板载外设冲突。")
