#!/usr/bin/env python3
"""Generate a Tianmengxing-adapted CCS project from an SDK example."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

# Board-specific constants
CHIP = "MSPM0G3507"
CHIP_MACRO = "__MSPM0G3507__"
STARTUP_PATTERN = "mspm0g350x"
LP_BOARD = "LP_MSPM0G3507"


def _load_config(config_path: str) -> dict:
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _clean_project(out: Path, project_name: str, sdk_example: str) -> None:
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
        # Replace SDK example name with project name in makefile references
        # (gcc/makefile, etc. may still reference gpio_toggle_output.obj etc.)
        updated = updated.replace(sdk_example, project_name)

        if updated != content:
            with open(mk, 'w', encoding='utf-8', newline='\n') as f:
                f.write(updated)
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
    pspec_path = out / f"{project_name}.projectspec"
    with open(pspec_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(spec)


def _generate_eclipse_files(out: Path, project_name: str) -> None:
    """Generate CCS IDE Eclipse project files (.project, .cproject, .ccsproject, targetConfigs/).
    
    scaffold.py generates gmake-only projects; CCS IDE needs these XML descriptors
    to recognize the project and configure the toolchain.
    """
    print("[eclipse] generating CCS IDE project files ...")

    # .project
    project_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
\t<name>{project_name}</name>
\t<comment></comment>
\t<projects>
\t</projects>
\t<buildSpec>
\t\t<buildCommand>
\t\t\t<name>org.eclipse.cdt.managedbuilder.core.genmakebuilder</name>
\t\t\t<arguments>
\t\t\t</arguments>
\t\t</buildCommand>
\t</buildSpec>
\t<natures>
\t\t<nature>com.ti.ccstudio.core.ccsNature</nature>
\t\t<nature>org.eclipse.cdt.core.cnature</nature>
\t\t<nature>org.eclipse.cdt.managedbuilder.core.managedBuildNature</nature>
\t\t<nature>org.eclipse.cdt.core.ccnature</nature>
\t</natures>
</projectDescription>'''
    (out / ".project").write_text(project_xml, encoding="utf-8", newline='\n')
    print("  .project ✓")

    # .cproject (TICLANG 5.1 toolchain, Debug config, MSPM0G3507)
    cproject_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?fileVersion 4.0.0?><cproject storage_type_id="org.eclipse.cdt.core.XmlProjectDescriptionStorage">
\t<storageModule moduleId="org.eclipse.cdt.core.settings">
\t\t<cconfiguration id="com.ti.ccstudio.buildDefinitions.TMS470.Debug.177120646">
\t\t\t<storageModule buildSystemId="org.eclipse.cdt.managedbuilder.core.configurationDataProvider" id="com.ti.ccstudio.buildDefinitions.TMS470.Debug.177120646" moduleId="org.eclipse.cdt.core.settings" name="Debug">
\t\t\t\t<externalSettings/>
\t\t\t\t<extensions>
\t\t\t\t\t<extension id="org.eclipse.cdt.core.GmakeErrorParser" point="com.ti.ccs.project.ErrorParser"/>
\t\t\t\t\t<extension id="org.eclipse.cdt.core.GASErrorParser" point="com.ti.ccs.project.ErrorParser"/>
\t\t\t\t\t<extension id="com.ti.ccs.errorparser.SysConfigErrorParser" point="com.ti.ccs.project.ErrorParser"/>
\t\t\t\t\t<extension id="org.eclipse.cdt.core.GCCErrorParser" point="com.ti.ccs.project.ErrorParser"/>
\t\t\t\t\t<extension id="com.ti.ccs.errorparser.CompilerErrorParser_TI" point="com.ti.ccs.project.ErrorParser"/>
\t\t\t\t</extensions>
\t\t\t</storageModule>
\t\t\t<storageModule moduleId="cdtBuildSystem" version="4.0.0">
\t\t\t\t<configuration artifactExtension="out" artifactName="${{ProjName}}" buildProperties="" cleanCommand="${{CG_CLEAN_CMD}}" description="" id="com.ti.ccstudio.buildDefinitions.TMS470.Debug.177120646" name="Debug" parent="com.ti.ccstudio.buildDefinitions.TMS470.Debug">
\t\t\t\t\t<folderInfo id="com.ti.ccstudio.buildDefinitions.TMS470.Debug.177120646." name="/" resourcePath="">
\t\t\t\t\t\t<toolChain id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.DebugToolchain.57600662" name="TI Build Tools" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.DebugToolchain" targetTool="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.linkerDebug.1415947144">
\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.core.OPT_TAGS.247759668" superClass="com.ti.ccstudio.buildDefinitions.core.OPT_TAGS" valueType="stringList">
\t\t\t\t\t\t\t\t<listOptionValue value="DEVICE_CONFIGURATION_ID=Cortex M.MSPM0G3507"/>
\t\t\t\t\t\t\t\t<listOptionValue value="DEVICE_CORE_ID="/>
\t\t\t\t\t\t\t\t<listOptionValue value="DEVICE_ENDIANNESS=little"/>
\t\t\t\t\t\t\t\t<listOptionValue value="OUTPUT_FORMAT=ELF"/>
\t\t\t\t\t\t\t\t<listOptionValue value="CCS_MBS_VERSION=70.0.0"/>
\t\t\t\t\t\t\t\t<listOptionValue value="RUNTIME_SUPPORT_LIBRARY="/>
\t\t\t\t\t\t\t\t<listOptionValue value="OUTPUT_TYPE=executable"/>
\t\t\t\t\t\t\t\t<listOptionValue value="PRODUCTS=MSPM0-SDK:2.10.0.04;sysconfig:1.26.2;"/>
\t\t\t\t\t\t\t\t<listOptionValue value="PRODUCT_MACRO_IMPORTS={{&quot;MSPM0-SDK&quot;:[&quot;${{COM_TI_MSPM0_SDK_INCLUDE_PATH}}&quot;,&quot;${{COM_TI_MSPM0_SDK_LIBRARY_PATH}}&quot;,&quot;${{COM_TI_MSPM0_SDK_LIBRARIES}}&quot;,&quot;${{COM_TI_MSPM0_SDK_SYMBOLS}}&quot;,&quot;${{COM_TI_MSPM0_SDK_SYSCONFIG_MANIFEST}}&quot;],&quot;sysconfig&quot;:[&quot;${{SYSCONFIG_TOOL_INCLUDE_PATH}}&quot;,&quot;${{SYSCONFIG_TOOL_LIBRARY_PATH}}&quot;,&quot;${{SYSCONFIG_TOOL_LIBRARIES}}&quot;,&quot;${{SYSCONFIG_TOOL_SYMBOLS}}&quot;,&quot;${{SYSCONFIG_TOOL_SYSCONFIG_MANIFEST}}&quot;]}}"/>
\t\t\t\t\t\t\t</option>
\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.core.OPT_CODEGEN_VERSION.27094809" superClass="com.ti.ccstudio.buildDefinitions.core.OPT_CODEGEN_VERSION" value="TICLANG_5.1.1.LTS" valueType="string"/>
\t\t\t\t\t\t\t<targetPlatform id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.targetPlatformDebug.1162388228" name="Platform" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.targetPlatformDebug"/>
\t\t\t\t\t\t\t<builder buildPath="${{BuildDirectory}}" id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.builderDebug.1738102857" keepEnvironmentInBuildfile="false" name="GNU Make" parallelBuildOn="true" parallelizationNumber="optimal" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.builderDebug"/>
\t\t\t\t\t\t\t<tool id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.compilerDebug.2105042851" name="Arm Compiler" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.compilerDebug">
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.GENERATE_DWARF_DEBUG.401189189" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.GENERATE_DWARF_DEBUG" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.GENERATE_DWARF_DEBUG.GDWARF_3" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.ENDIAN_NESS__BIG_LITTLE.1796597516" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.ENDIAN_NESS__BIG_LITTLE" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.ENDIAN_NESS__BIG_LITTLE.MLITTLE_ENDIAN" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.INCLUDE_PATH.202069370" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.INCLUDE_PATH" valueType="includePath">
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_INCLUDE_PATH}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{SYSCONFIG_TOOL_INCLUDE_PATH}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{PROJECT_ROOT}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{PROJECT_ROOT}}/${{ConfigName}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source/third_party/CMSIS/Core/Include"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source"/>
\t\t\t\t\t\t\t\t</option>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.DEFINE.1171674967" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.DEFINE" valueType="definedSymbols">
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_SYMBOLS}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{SYSCONFIG_TOOL_SYMBOLS}}"/>
\t\t\t\t\t\t\t\t</option>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.OPT_LEVEL.1611300752" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.OPT_LEVEL" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.OPT_LEVEL.2" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.CMD_FILE.1013797883" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.CMD_FILE" valueType="stringList">
\t\t\t\t\t\t\t\t\t<listOptionValue value="device.opt"/>
\t\t\t\t\t\t\t\t</option>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MCPU.254930875" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MCPU" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MCPU.cortex-m0plus" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MARCH.791115353" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MARCH" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MARCH.thumbv6m" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MFLOAT_ABI.265744036" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MFLOAT_ABI" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.MFLOAT_ABI.soft" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.SELECT_PROCESSOR_MODE__ARM_THUMB.913902047" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.SELECT_PROCESSOR_MODE__ARM_THUMB" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.SELECT_PROCESSOR_MODE__ARM_THUMB.MTHUMB" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.WALL.816110379" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.compilerID.WALL" value="true" valueType="boolean"/>
\t\t\t\t\t\t\t</tool>
\t\t\t\t\t\t\t<tool id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.linkerDebug.1415947144" name="Arm Linker" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.exe.linkerDebug">
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.OUTPUT_FILE.2059858764" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.OUTPUT_FILE" value="${{ProjName}}.out" valueType="string"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.MAP_FILE.1872248760" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.MAP_FILE" value="${{ProjName}}.map" valueType="string"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.XML_LINK_INFO.723197541" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.XML_LINK_INFO" value="${{ProjName}}_linkInfo.xml" valueType="string"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.DISPLAY_ERROR_NUMBER.420099269" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.DISPLAY_ERROR_NUMBER" value="true" valueType="boolean"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.DIAG_WRAP.1027845605" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.DIAG_WRAP" value="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.DIAG_WRAP.off" valueType="enumerated"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.REREAD_LIBS.1467602445" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.REREAD_LIBS" value="false" valueType="boolean"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.SEARCH_PATH.1793770240" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.SEARCH_PATH" valueType="libPaths">
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_LIBRARY_PATH}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{SYSCONFIG_TOOL_LIBRARY_PATH}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{PROJECT_ROOT}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{PROJECT_BUILD_DIR}}/syscfg"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{CG_TOOL_ROOT}}/lib"/>
\t\t\t\t\t\t\t\t</option>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.LIBRARY.1531956989" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.linkerID.LIBRARY" valueType="libs">
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_LIBRARIES}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{SYSCONFIG_TOOL_LIBRARIES}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="device.cmd.genlibs"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="libc.a"/>
\t\t\t\t\t\t\t\t</option>
\t\t\t\t\t\t\t</tool>
\t\t\t\t\t\t\t<tool id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.hex.503727053" name="Arm Hex Utility" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.hex"/>
\t\t\t\t\t\t\t<tool id="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.objcopy.1495648398" name="Arm Objcopy Utility" superClass="com.ti.ccstudio.buildDefinitions.TMS470_TICLANG_5.1.objcopy"/>
\t\t\t\t\t\t\t<tool id="com.ti.ccstudio.buildDefinitions.sysConfig.507511065" name="SysConfig" superClass="com.ti.ccstudio.buildDefinitions.sysConfig">
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.sysConfig.PRODUCTS.1056456156" superClass="com.ti.ccstudio.buildDefinitions.sysConfig.PRODUCTS" valueType="stringList">
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{COM_TI_MSPM0_SDK_SYSCONFIG_MANIFEST}}"/>
\t\t\t\t\t\t\t\t\t<listOptionValue value="${{SYSCONFIG_TOOL_SYSCONFIG_MANIFEST}}"/>
\t\t\t\t\t\t\t\t</option>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.sysConfig.OUTPUT_DIR__MANUAL.391912566" superClass="com.ti.ccstudio.buildDefinitions.sysConfig.OUTPUT_DIR__MANUAL" value="." valueType="string"/>
\t\t\t\t\t\t\t\t<option id="com.ti.ccstudio.buildDefinitions.sysConfig.DIRECTORY_MODE.1174697540" superClass="com.ti.ccstudio.buildDefinitions.sysConfig.DIRECTORY_MODE" value="com.ti.ccstudio.buildDefinitions.sysConfig.DIRECTORY_MODE.manual" valueType="enumerated"/>
\t\t\t\t\t\t\t</tool>
\t\t\t\t\t\t</toolChain>
\t\t\t\t\t</folderInfo>
\t\t\t\t</configuration>
\t\t\t</storageModule>
\t\t\t<storageModule moduleId="org.eclipse.cdt.core.externalSettings"/>
\t\t</cconfiguration>
\t</storageModule>
\t<storageModule moduleId="cdtBuildSystem" version="4.0.0">
\t\t<project id="{project_name}.com.ti.ccstudio.buildDefinitions.TMS470.ProjectType.1180988702" name="TMS470" projectType="com.ti.ccstudio.buildDefinitions.TMS470.ProjectType"/>
\t</storageModule>
</cproject>'''
    (out / ".cproject").write_text(cproject_xml, encoding="utf-8", newline='\n')
    print("  .cproject ✓")

    # .ccsproject
    ccsproject_xml = f'''<?xml version="1.0" encoding="UTF-8" ?>
<?ccsproject version="1.0"?>
<projectOptions>
\t<ccsVariant value="50:Theia-based"/>
\t<ccsVersion value="71.0.0"/>
\t<deviceFamily value="TMS470"/>
\t<connection value="common/targetdb/connections/TIXDS110_Connection.xml"/>
\t<executableActions value=""/>
\t<createSlaveProjects value=""/>
\t<ignoreDefaultDeviceSettings value="true"/>
\t<ignoreDefaultCCSSettings value="true"/>
\t<templateProperties value="id=empty_LP_MSPM0G3507_nortos_ticlang.projectspec.{project_name},buildProfile=release,isHybrid=true"/>
\t<activeTargetConfiguration value="targetConfigs/MSPM0G3507.ccxml"/>
\t<isTargetConfigurationManual value="false"/>
\t<filesToOpen value="{project_name}.syscfg,main.c"/>
</projectOptions>'''
    (out / ".ccsproject").write_text(ccsproject_xml, encoding="utf-8", newline='\n')
    print("  .ccsproject ✓")

    # targetConfigs/MSPM0G3507.ccxml (XDS110 debug probe configuration)
    tc_dir = out / "targetConfigs"
    tc_dir.mkdir(exist_ok=True)
    ccxml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<configurations XML_version="1.2" id="configurations_0">
    <configuration XML_version="1.2" id="configuration_0">
        <instance XML_version="1.2" desc="Texas Instruments XDS110 USB Debug Probe" href="connections/TIXDS110_Connection.xml" id="Texas Instruments XDS110 USB Debug Probe" xml="TIXDS110_Connection.xml" xmlpath="connections"/>
        <connection XML_version="1.2" id="Texas Instruments XDS110 USB Debug Probe">
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
                <instance XML_version="1.2" desc="MSPM0G3507" href="devices/MSPM0G3507.xml" id="MSPM0G3507" xml="MSPM0G3507.xml" xmlpath="devices"/>
            </platform>
        </connection>
    </configuration>
</configurations>'''
    (tc_dir / "MSPM0G3507.ccxml").write_text(ccxml, encoding="utf-8", newline='\n')
    print("  targetConfigs/MSPM0G3507.ccxml ✓")


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
            # Auto-run setup.py to configure paths
            setup_script = Path(__file__).resolve().parent / "setup.py"
            print("[scaffold] config.json 未配置 SDK 路径，自动运行 setup.py --auto-detect ...")
            setup_result = subprocess.run(
                ["python", str(setup_script), "--auto-detect"],
                cwd=str(setup_script.parent),
            )
            if setup_result.returncode == 0:
                config = _load_config(
                    config_path or str(Path(__file__).resolve().parents[1] / "config.json")
                )
                sdk_examples_dir = Path(config.get("sdk_examples", ""))
                if sdk_examples_dir and (sdk_examples_dir / sdk_example).is_dir():
                    source_dir = sdk_examples_dir / sdk_example
            if not source_dir:
                raise FileNotFoundError(
                    f"找不到示例 '{sdk_example}'。setup.py 已运行但仍未找到示例。\n"
                    "请手动检查 config.json 的 sdk_examples 路径。"
                )
        else:
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
            # Fix Board module: {} → () to load full pin definitions (PB22 etc.)
            # Without this, Upper-segment pins disappear from PWM/UART pin lists
            content = re.sub(
                r'scripting\.addModule\("/ti/driverlib/Board",\s*\{\},\s*false\)',
                'scripting.addModule("/ti/driverlib/Board")',
                content,
            )
            # Fix SDK 2.10 GPIO old syntax: remove GPIO1.port = "PORTx" (conflicts with assignedPort)
            content = re.sub(r'^\s*GPIO\d+\.port\s*=\s*"[^"]*";\s*$', '', content, flags=re.MULTILINE)
            # Add header comment: warn about GPIO variable naming
            if "Generated by scaffold" not in content:
                header = (
                    "// ══ Generated by scaffold.py ══\n"
                    "// Adding GPIO instances: use unique variable names (GPIO2, GPIO3, ...)\n"
                    "// Do NOT reuse GPIO1 — it is already declared above.\n"
                    "// Instance $name ≠ pin $name — both must be globally unique.\n"
                    "// Always grep ti_msp_dl_config.h after SysConfig to confirm macro names.\n"
                    "\n"
                )
                content = header + content
            if item.stem == "example":
                dst_file = out / f"{project_name}.syscfg"
            else:
                dst_file = out / item.name.replace(sdk_example, project_name)
            # Normalize to LF (prevents CRLF edit_file matching failures on Windows)
            fixed = content.replace('\r\n', '\n')
            with open(dst_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(fixed)
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
    _clean_project(out, project_name, sdk_example)

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
            pspec_path = out / f"{project_name}.projectspec"
            with open(pspec_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
    else:
        # Generate minimal .projectspec for skill-bundled examples
        _write_projectspec(out, project_name, sdk_example)

    # 4. Generate CCS IDE Eclipse project files
    _generate_eclipse_files(out, project_name)

    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Tianmengxing-adapted CCS project from SDK example"
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
    print(f"  Source:    {result}\\{args.project_name}.c")
    print(f"  SysConfig: {result}\\{args.project_name}.syscfg")
    print(f"  Projects:  {result}\\{args.project_name}.projectspec")
