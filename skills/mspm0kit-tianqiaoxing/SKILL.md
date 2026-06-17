---
name: mspm0kit-tianqiaoxing
description: One-sentence CCS project generator for the Tianqiaoxing MSPM0G3519 custom board. Create full CCS projects from SDK examples with automatic pin/package adaptation, then build and flash. Use when the user wants to start a new MSPM0 firmware project on this specific board, or needs pin availability information for the Tianqiaoxing G3519.
requires: [mspm0-ccs]
---

# mspm0kit — 天巧星 MSPM0G3519 Skill

**Board**: Tianqiaoxing MSPM0G3519 custom development board (LQFP-64)
**Toolchain**: CCS Theia + TI Arm Clang + SysConfig + DriverLib
**SDK**: MSPM0 SDK 2.05.01.00

## Workflow

When the user requests a new project, follow these four steps:

### Step 1 — Think

1. Identify the peripheral(s) the user wants (UART, GPIO, PWM, SPI, I2C, ADC, Timer).
2. Check the pin table below to confirm target pins are available.
3. Read the corresponding `peripherals/<peripheral>.md` for the SDK example name and pin mapping.
4. **If I2C is involved:** Ask the user: "你需要软件 I2C（默认，GPIO 位模拟，任意引脚）还是硬件 I2C（更快更稳定，需使用 I2C 功能引脚）？"
   - Software I2C (default): use `scaffold_oled.py` without `--i2c hw`
   - Hardware I2C: use `--i2c hw`, verify pins against `references/hw_i2c_pins.md`
5. Confirm clock needs (default: 80 MHz CPUCLK with 40 MHz HFXT).

### Step 2 — Plan

Tell the user what you're going to create:

- Project name and target directory
- Which SDK example will be used as the template
- Which pins will be configured
- Clock configuration (default 80 MHz)

Wait for confirmation before creating files, OR proceed if the user has indicated they want automatic execution.

**If the user is not satisfied with the plan:** Revise it based on their feedback, then **restate the complete revised plan** before writing any code. Do NOT jump straight to implementation — the user must see and approve the changes first. Repeat this loop until the user approves.

### Step 3 — Code

1. Ask: "是否允许我读取 SDK 目录（`<sdk_root>`）来复制例程模板？"
2. On approval, run scaffold using the **full path** to the skill's scripts directory:
   ```
   python C:/Users/<user>/.claude/skills/mspm0kit-tianqiaoxing/scripts/scaffold.py <project_name> <sdk_example_name> -o <project_parent_dir>
   ```
   The scripts live in the skill install directory, NOT in the project directory. Use the full path every time.
   To locate the scripts: `find ~ -path "*/mspm0kit-tianqiaoxing/scripts/scaffold.py" 2>/dev/null`
3. If the user needs custom behavior beyond the SDK example, edit the generated `.syscfg` first.
4. **After editing `.syscfg`, BEFORE writing the `.c`, fetch the ground-truth macro names** — never guess them:
   ```
   python <skill_dir>/scripts/build.py <project_dir> --sysconfig-only
   ```
   This runs SysConfig once and prints every generated macro (`*_PORT`, `*_PIN`, `*_INST`, `*_IIDX`, ...) from `ti_msp_dl_config.h`. Write the `.c` using those EXACT names. This eliminates the first-build failure caused by guessed macros.
5. All pin changes go through `.syscfg` — never hand-edit generated `ti_msp_dl_config.*` files.
6. **After scaffold completes, ask the user:** "工程已生成，是否要我帮你编译测试？"
   - If yes → proceed to Step 4 (build + report errors)
   - If no → just print the project path and usage instructions

### Step 4 — Verify

0. **MANDATORY: Run cleanup before building (every time):**
   ```bash
   python C:/Users/<user>/.claude/skills/mspm0kit-tianqiaoxing/scripts/cleanup.py <project_dir>
   ```
   Use the **full path** to cleanup.py (same directory as scaffold.py above).
   This automatically:
   - Moves .c files from subdirectories to root (CCS flat rule)
   - Deletes duplicate .c files
   - Removes generated files from root (device_linker.cmd, ti_msp_dl_config.*, etc.)
   - Removes ticlang/ directory (conflicts with CCS Debug/)
   **Build MUST NOT proceed until cleanup returns success.**

1. Run build:
   ```
   python C:/Users/<user>/.claude/skills/mspm0kit-tianqiaoxing/scripts/build.py <project_dir> --yes
   ```
   `--yes` 跳过交互确认。非交互环境下必须加此参数，否则 `input()` 会抛 EOFError。
2. If build fails: read the error, fix the issue, retry (max 3 times).
3. If build succeeds: report the `.out` file path and provide the flash command.
4. Macro names should already be correct (Step 3 fetched them via `--sysconfig-only` before the `.c` was written). If you skipped that step and hit an undefined-macro error, read `ti_msp_dl_config.h` to confirm the real names — never guess them.

## Core Rules

### R0: 4-Layer Embedded Architecture (HIGHEST PRIORITY)

`main.c` → `hal/hal_*.c/h` → `bsp/bsp_*.c/h` → `middleware/` → `app/app_*.c/h` → `targetConfigs/`

Each module is self-contained: `.c` and `.h` live together. For simple projects, `main.c` is acceptable.

### R1: Generated Files

- **Never edit** generated files: `ti_msp_dl_config.c`, `ti_msp_dl_config.h`.
- **Never create** `device_linker.cmd`, `device.cmd.genlibs`, `device.opt` — CCS auto-generates them in `Debug/`.
- **Never create** a `ticlang/` directory — it conflicts with CCS's `Debug/` build system.
- If CCS left stale generated files in root after a failed import, delete them before building.

### R2: SysConfig is the Source of Truth

- `.syscfg` is the sole source of truth for pins, peripherals, clocks, interrupts, and DMA.
- Prefer SysConfig + DriverLib over register-level code.
- Don't guess generated macro names. Read the generated header after SysConfig runs.
- If SysConfig emits warnings, report them — don't call it "clean".
- If hardware behavior is unverified, say "verification stopped at compile level".

**Macro name patterns (reference only — always verify against `ti_msp_dl_config.h`):**

| 外设 | `$name` 示例 | 典型宏 |
|------|-------------|--------|
| UART | `UART_0` | `UART_0_INST`, `UART_0_INST_INT_IRQN` |
| GPIO 输出 | `GPIO_LED` | `GPIO_LED_PORT`, `GPIO_LED_PIN_PIN` |
| GPIO 输入 | `GPIO_BTN` | `GPIO_BTN_PORT`, `GPIO_BTN_BTN_PIN_PIN`, `GPIO_BTN_INT_IIDX` |
| Timer | `TIMER_TICK` | `TIMER_TICK_INST`, `TIMER_TICK_INST_IRQHandler` |
| PWM | `PWM_0` | `PWM_0_INST`, `GPIO_PWM_0_C0_IDX` |
| ADC | `ADC12_0` | `ADC12_0_INST`, `ADC12_0_INST_INT_IRQN` |

### R3: External Path Access

- Do NOT ask for path permission upfront. Try the operation first.
- Only when a script fails due to missing/invalid paths, follow the Path Configuration flow above.
- After paths are configured, access CCS/SDK files without re-prompting each time.

### R4: Generated Macro Verification (CRITICAL)

SDK 2.04 + SysConfig 1.27 的 LQFP-64(PM) 有引脚映射 bug：生成的 `_PORT`/`_PIN` 宏可能指向错误端口。
- SysConfig 后必须 grep `ti_msp_dl_config.h` 验证宏值
- 宏错误时直接用 `GPIOB, DL_GPIO_PIN_22` 等具体值
- `DL_GPIO_initDigitalOutput()` 只配 IOMUX，必须额外调 `DL_GPIO_enableOutput()`
- 升级到 SDK >= 2.05.01.01 解决此 bug

### R5: Pin Table is Authoritative

选引脚前必须查 Pin Table。黄色标注（外设引脚功能标注表.xlsx）的引脚不可使用。用户要求占用引脚时须明确警告。


## Pin Table — Tianqiaoxing MSPM0G3519

### Completely Unusable (never assign)

| Pin | Reason |
|-----|--------|
| PA2 | Frequency accuracy control, not routed |
| PA5 | HFXT crystal input (40 MHz) |
| PA6 | HFXT crystal output (40 MHz) |
| PA19 | SWDIO debug interface |
| PA20 | SWCLK debug interface |

### Conditional

| Pin | Condition |
|-----|-----------|
| PA18 | BSL entry pin — must be LOW at reset. Board BACK button (PULL_DOWN) |

### Board Peripheral Pins (occupied, do not reassign)

| Pin(s) | Occupied by |
|--------|-------------|
| PA0, PA1 | Hardware I2C0 — OLED + IMU (shared bus, 2.2kΩ pull-up on board) |
| PA10, PA11 | UART0 to CH340 USB-C (排针 can share TX/RX) |
| PB6, PB7, PB8, PB9 | SPI1 — W25Q128 Flash (CS/MISO/MOSI/SCLK) |
| PB17, PB18 | UART7 — wireless UART module |
| PB21 | ENTER button (PULL_UP, active-low) |
| PB22 | Onboard LED (PULL_DOWN, active-low) |
| PB23 | Wireless link status input |
| PB26 | TIMA1 CCP0 — WS2812 RGB LED |
| PB27 | TIMG6 CCP1 — Buzzer PWM |

### Optional (can release if unused)

| Pin(s) | Function |
|--------|----------|
| PA29, PA30 | QEI encoder (TIMG8 CCP0/CCP1) |
| PA31 | Encoder button (PULL_UP) |

### Free Pins (available for user assignment)

All other pins not listed above. The board uses LQFP-64(PM) package.

## Path Configuration

`config.json` 存储工具链路径。流程：先直接运行脚本 → 失败了再问用户路径 → 路径不存在时问是否自动搜索 → 用户同意后搜索 C/D/E 盘常见位置（`D:/TI/CCS/ccs`, `mspm0_sdk*` 等）→ 找到后写入 config.json → 重试。

## Tools

| Script | Purpose |
|--------|---------|
| `setup.py` | First-time path configuration |
| `scaffold.py <name> <example> -o <dir>` | Generate CCS project |
| `build.py <project_dir> --sysconfig-only` | Run SysConfig only, print generated macros (call BEFORE writing the .c) |
| `build.py <project_dir> --yes` | SysConfig CLI + gmake compile |
| `flash.py <project_dir>` | Flash (XDS110: DSLite / JLINK: JLink.exe) |
| `serial_console.py -p <port> -b <baud>` | Serial monitor |
| `cleanup.py <project_dir>` | **MANDATORY before build** |
| `scaffold_oled.py <name> [--mode menu] [--with-imu] [--i2c hw]` | Generate OLED UI project |

> All scripts are in the skill install directory: `~/.claude/skills/mspm0kit-tianqiaoxing/scripts/`. Use full path when calling.

## Reference

For detailed SysConfig/DriverLib usage and debugging, also refer to the `mspm0-ccs` skill's reference docs.
