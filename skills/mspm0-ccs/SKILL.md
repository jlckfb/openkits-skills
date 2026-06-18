---
name: mspm0-ccs
description: Tool-neutral CLI agent rules for TI MSPM0 development with Code Composer Studio, Keil/uVision, CMake/GCC/OpenOCD, SysConfig, and DriverLib. Use when an agent needs to inspect or modify MSPM0 projects, edit .syscfg configuration, avoid generated SysConfig/build files, use DriverLib APIs, validate SysConfig output, package reusable MSPM0 examples, or work on NUEDC-style MSPM0 embedded firmware.
---

# MSPM0 Agent Skill

Use this skill for TI MSPM0 firmware projects that use SysConfig and DriverLib through CCS / CCS Theia, Keil/uVision, or CMake + Arm GNU Toolchain + OpenOCD workflows. It is intended for Claude Code, OpenCode, OpenClaw, Continue, Cursor, Codex, and similar CLI/editor agents.

## Default Workflow

1. Locate the project `.syscfg` or `system.syscfg`, editable source files, generated `ti_msp_dl_config.h`, and the active project entrypoint: `targetConfigs/*.ccxml` for CCS, `*.uvprojx` plus scatter file for Keil/uVision, or `CMakeLists.txt` plus OpenOCD `.cfg` files for CMake/GCC/OpenOCD.
2. Run `python scripts/check_syscfg.py <project-dir>` when this skill is available.
3. Read `.syscfg` metadata: device, package, SDK product, SysConfig version, modules, instances, pins, clocks, and interrupts.
4. Inspect generated `ti_msp_dl_config.h` for macro names, IRQ names, instance names, and the exact SysConfig init function spelling.
5. Before adding unfamiliar SysConfig fields, inspect the user's existing `.syscfg`, `examples/*/manifest.json`, TI SDK examples, or `source/ti/driverlib/.meta/*.syscfg.js`.
6. Modify the smallest relevant `.syscfg` and application-code surface.
7. Regenerate SysConfig output or rebuild through the active toolchain's generated build flow.
8. If flashing or debugging, confirm the configured probe backend matches the connected hardware and prefer a System Reset after programming.

## Core Rules

- Treat `.syscfg` as the source of truth for pinmux, peripheral setup, clocks, interrupts, DMA ownership, and generated initialization.
- Prefer SysConfig + DriverLib for GPIO, UART, PWM, Timer, ADC, I2C, SPI, DMA, and clock setup.
- Do not hand-edit generated outputs such as `Debug/ti_msp_dl_config.c`, `Debug/ti_msp_dl_config.h`, the project-root `ti_msp_dl_config.c` / `ti_msp_dl_config.h` pair in Keil layouts, `device_linker.cmd`, `Objects/`, `Listings/`, object files, maps, or `.out` files.
- Preserve `.syscfg` metadata such as `@cliArgs`, `@v2CliArgs`, `@versions`, `--device`, `--package`, and `--product`.
- Do not guess generated names. Read `ti_msp_dl_config.h` and use the local macros and the local init function spelling, such as `SYSCFG_DL_init()`.
- Do not invent SysConfig fields, enum values, device metadata, board names, package names, or tool versions. Validate against local examples, SDK metadata, or SysConfig CLI.
- Preserve unrelated user code, comments, copyright headers, project layout, and existing `.syscfg` settings. If a requested feature requires a larger rewrite, explain why before making it when possible.
- Do not change device, package, SDK, compiler, CCS version, board, or debug probe without user confirmation.
- If SysConfig emits warnings, report them separately from build/flash success. Do not call a warning-producing generation "clean".
- If hardware behavior is not verified on a connected board, say that validation stopped at source, SysConfig, or build level.

## Board Skill Workflow Template

Board skills (`mspm0kit-*`) that `requires: [mspm0-ccs]` share the following scaffold → build → flash workflow. Board SKILL.md should only document their **delta** (pin table, clock defaults, board-specific overrides) and reference this section for the common flow.

### Skill Path Discovery

Scripts live in the skill install directory, NOT in the project directory. Locate once, reuse everywhere:
- Claude Code (Linux/macOS): `~/.claude/skills/<skill-name>/scripts/`
- Claude Code (Windows): `C:/Users/<user>/.claude/skills/<skill-name>/scripts/`
- Reasonix (Windows): `C:/Users/<user>/.reasonix/skills/<skill-name>/scripts/`
- Codex/其他 Agent: `C:/Users/<user>/.agents/skills/<skill-name>/scripts/`
- 通用自发现: `ls ~/.claude/skills/<skill-name>/scripts 2>/dev/null || ls ~/.reasonix/skills/<skill-name>/scripts 2>/dev/null || ls ~/.agents/skills/<skill-name>/scripts 2>/dev/null`

> ⚠️ 不要用 `cmd /c "python ..."` 包裹脚本调用 — `cmd /c` 会吞掉 stdout。直接 `python "<全路径>/script.py" ...` 即可。

### Common Workflow Steps

**Step 1 — Think**: Identify peripherals → check board pin table → read `peripherals/<name>.md` → confirm clock.

**Step 2 — Plan**: Tell the user: project name, SDK example template, pin configuration, clock config. Wait for confirmation. If the user rejects, restate revised plan before writing code.

**Step 3 — Code**:
1. Run scaffold: `python <skill_dir>/scripts/scaffold.py <name> <example> -o <dir>`
2. Edit `.syscfg` if custom behavior is needed.
3. **Before writing `.c`**, fetch ground-truth macros: `python <skill_dir>/scripts/build.py <project_dir> --sysconfig-only`
4. Write `.c` using EXACT macro names from output.
5. Ask: "工程已生成，是否要我帮你编译测试？"

**Step 4 — Verify**:
1. Build: `python <skill_dir>/scripts/build.py <project_dir> --yes` (`--yes` 跳过交互确认，agent 必须加。build.py 内置自动清理：仅在检测到 stale 文件时才执行，新项目零开销)
2. If build fails: read error, fix, retry (max 3).
3. If build succeeds: report `.out` path + provide flash command.

**Flash**: `python <skill_dir>/scripts/flash.py <project_dir>` — auto-selects DSLite (XDS110) or JLink based on `config.json` probe field.

### Delay API

MSPM0 DriverLib **没有** `DL_Delay_ms()` / `DL_Delay_us()`。唯一延时 API: `delay_cycles(n)` (定义在 `dl_core.h`)。

**简单延时（闪烁/消抖）直接用 `delay_cycles`，不要配定时器外设**：
```c
delay_cycles(CPUCLK_FREQ / 1000 * N);  // 延时 N 毫秒
```
只有需要**非阻塞/并发触发**时才用 Timer 中断。

### STOP2 Trap

使用 SysTick/Timer 中断驱动实时任务时，**禁止** `SYSCTL.powerPolicy = "STOP2"` 或 `__WFI()`。STOP2 关闭 MCLK，所有 ISR 停止。默认保持 RUN 模式。

### Macro Name Patterns (reference — always verify against `ti_msp_dl_config.h`)

| 外设 | `$name` 示例 | 典型宏 |
|------|-------------|--------|
| UART | `UART_0` | `UART_0_INST`, `UART_0_INST_INT_IRQN` |
| GPIO 输出 | `GPIO_LED` | `GPIO_LED_PORT`, `GPIO_LED_PIN_PIN` |
| GPIO 输入 | `GPIO_BTN` | `GPIO_BTN_PORT`, `GPIO_BTN_BTN_PIN_PIN`, `GPIO_BTN_INT_IIDX` |
| Timer | `TIMER_TICK` | `TIMER_TICK_INST`, `TIMER_TICK_INST_IRQHandler` |
| PWM | `PWM_0` | `PWM_0_INST`, `GPIO_PWM_0_C0_IDX` |
| ADC | `ADC12_0` | `ADC12_0_INST`, `ADC12_0_INST_INT_IRQN` |

### Board Skill Tools (common set)

| Script | Purpose |
|--------|---------|
| `setup.py` | First-time path configuration (`--auto-detect --probe JLink`) |
| `scaffold.py <name> <example> -o <dir>` | Generate CCS project |
| `build.py <project_dir> --sysconfig-only` | Run SysConfig only, print generated macros |
| `build.py <project_dir> --yes` | SysConfig CLI + gmake compile |
| `flash.py <project_dir>` | Flash (XDS110: DSLite / JLINK: JLink.exe) |
| `serial_console.py -p <port> -b <baud>` | Serial monitor |
| `cleanup.py <project_dir>` | Legacy standalone cleanup (now built into build.py) |

### Path Configuration

`config.json` 存储工具链路径，位于 skill 根目录。

**自动扫描（推荐）**: `python <skill_dir>/scripts/setup.py --auto-detect --probe JLink`

**手动指定**: `python <skill_dir>/scripts/setup.py --accept-defaults --ccs-root <path> --sdk-root <path> --probe JLink`

Agent 应先尝试直接 scaffold/build，失败后再跑 setup。

## Project Shape Checks

- Simple projects usually keep most logic in `main.c`, `empty.c`, or a small number of files. It is acceptable to make narrowly scoped edits there.
- Framework projects often have multiple source directories such as `app/`, `bsp/`, `components/`, `core/`, `drivers/`, `hal/`, `middleware/`, or `tasks/`. First identify ownership boundaries before adding peripherals or changing control logic.
- Do not assume every MSPM0 project is CCS-like or single-file. A framework project can still use CCS, Keil, or CMake/GCC/OpenOCD.
- For control code, confirm whether timing comes from a timer ISR, RTOS task delay, hardware PWM/ADC trigger chain, or a main-loop poll before changing periods or priorities.

## Keil Project Checks

- Treat `system.syscfg` and `ti_msp_dl_config.c` / `ti_msp_dl_config.h` as the configuration source surface for Keil-based MSPM0 projects that keep SysConfig outputs at the project root.
- Treat a Keil `.uvprojx` as the project entrypoint, the scatter file as the linker source of truth, and `Objects/`, `Listings/`, `*.uvoptx`, build logs, and generated outputs as inspection-only unless a request explicitly targets them.
- For a project's application code, follow its own source layout rather than assuming CCS defaults.

## CMake / GCC / OpenOCD Checks

- Treat `CMakeLists.txt`, toolchain files, and OpenOCD `.cfg` files as the project entrypoints for CMake/GCC/OpenOCD projects.
- Build through the existing CMake build directory when present, for example `cmake --build cmake-build-debug --target <target>`.
- MSPM0 OpenOCD flashing usually requires a TI MSPM0-capable OpenOCD build or TI extension branch. If OpenOCD reports `unable to find a matching CMSIS-DAP device`, report that as probe discovery failure rather than firmware failure.
- Do not require CCS `targetConfigs/*.ccxml` when the active project uses OpenOCD instead of DSLite.

## FreeRTOS Checks

- If `FreeRTOSConfig.h`, `FreeRTOS.h`, `task.h`, `xTaskCreate`, or `vTaskStartScheduler` are present, treat the project as RTOS-aware.
- Keep RTOS handling lightweight: respect existing task, queue, ISR, and blocking-call boundaries; do not impose a specific framework architecture unless the user asks.

## Ambiguous Requests

If the user omits important hardware parameters, do not silently choose risky values.

- For low-risk defaults, use this skill's `examples/` or local TI SDK examples, then tell the user which defaults were applied.
- For important parameters, ask before editing and offer a concrete recommendation.
- Important missing parameters include pin, peripheral instance, UART baud/data/parity/stop bits, Timer period, PWM frequency/duty/polarity, ADC channel/reference/sample time, DMA direction/source/destination, interrupt priority, and external-module power/logic levels.

Example: if the user asks "add a timer interrupt", ask which timer and period they want, and recommend a starter such as TIMG at 1 ms or 10 ms if they are unsure.

## External Modules And Hardware Debugging

When asked to drive an external module, sensor, motor driver, servo, display, radio, or custom board:

- Ask for the module datasheet, schematic, pin map, supply voltage, logic level, communication protocol, and key parameters when they are not available.
- Verify wiring assumptions before blaming code: power, ground, pull-ups, level shifting, reset/enable pins, boot pins, chip select, UART TX/RX crossover, I2C address, SPI mode, PWM polarity, and shared pins.
- If repeated attempts fail and SysConfig, build, flash, and code logic look correct, explicitly raise the possibility of wiring, power, module mode, datasheet mismatch, damaged hardware, or wrong test procedure.
- Separate "firmware looks correct" from "hardware proved correct".

## Reference Selection

Read references only when needed:

- `references/sysconfig_ccs_workflow.md`: `.syscfg` editing, CCS / Keil / CMake project layout, SysConfig CLI, gmake, CMake build, DSLite/J-Link, and OpenOCD.
- `references/driverlib_runtime_rules.md`: DriverLib usage, interrupts, clock tree, delays, and common runtime mistakes.
- `references/sdk_schema_lookup.md`: how to find official SysConfig fields and examples in the local MSPM0 SDK.
- `references/hardware_validation_notes.md`: verified Tianmengxing MSPM0G3507 lessons, HFXT warnings, flash/reset behavior, and real-board caveats.
- `references/ccs_dss_debug.md`: CCS Debug Server Scripting (`ccs-dss`) debug workflow, breakpoints, register reads, and current limitations.

Use `examples/` as the main source for reusable tested patterns. Prefer `scripts/list_examples.py` to inspect available examples before opening individual example files.

## Examples

Each reusable example should contain:

```text
examples/<name>/
├─ example.syscfg
├─ README.md
├─ manifest.json
└─ src/
   └─ source files copied from the minimal relevant project surface
```

Do not require users to drop full CCS projects into `examples/`. Use `scripts/capture_example.py` to extract a compact example package from a real project.

## Tools

- `python scripts/check_syscfg.py <project-dir>`: static project check for `.syscfg`, generated files, pins, init spelling, project shape, CCS/Keil/CMake/OpenOCD clues, build output, target config, and validation hints.
- `python scripts/list_examples.py`: list packaged examples from `examples/*/manifest.json`.
- `python scripts/capture_example.py <project-dir> --name <example-name> --include <glob>`: package selected source files and `.syscfg` from a user project into `examples/<example-name>/`.
- `python scripts/index_syscfg_examples.py <mspm0-sdk-root> --board LP_MSPM0G3507 --module UART`: search local TI SDK examples and module metadata.
- `python scripts/serial_console.py --list`: list serial ports.
- `python scripts/ccs_dss_debug.py <project-dir> probe --leave-running`: connect through CCS Debug Server Scripting, read reset/register state, verify the configured `.ccxml` debug path, and continue the target before disconnecting.

For the verified CH340 setup, use `python scripts/serial_console.py -p COM6 -b 115200 --timestamp --duration 10` after closing other serial tools such as VOFA+.

## Flash Backends

The verified CCS flash path is DSLite / UniFlash with J-Link. For automated flashing after clock-tree changes, prefer DSLite System Reset:

```text
dslite -c <target.ccxml> -e -r 2 -u <project.out>
```

For CMake/GCC/OpenOCD projects, use the project's existing flash target or explicit OpenOCD config. Keep the backend explicit and report probe-discovery errors separately from build success.

## Debug Backends

The currently packaged automated debug helper is the CCS Debug Server Scripting backend (`ccs-dss`):

```text
python scripts/ccs_dss_debug.py <project-dir> probe --leave-running
python scripts/ccs_dss_debug.py <project-dir> run-to-symbol --symbol main --load --reset "System Reset"
```

Use it only for CCS / CCS Theia / UniFlash-style projects with a valid `targetConfigs/*.ccxml`. The physical probe is selected by `.ccxml`, so the backend is not inherently J-Link-only; it can also work with CCS-supported probes such as XDS110 when the project configuration matches the hardware.

Do not treat `ccs-dss` as the OpenOCD path. For CMake/GCC/OpenOCD projects, keep future debugging under a separate `openocd-gdb` backend. Debug actions can halt the CPU, so report that risk before using breakpoints or register inspection on real-time control hardware.
