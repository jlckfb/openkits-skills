---
name: mspm0kit-tianmengxing
description: CCS project generator for the Tianmengxing MSPM0G3507 development board. Create full CCS projects from SDK examples with automatic pin/package adaptation, then build and flash. Use when the user wants to start a new MSPM0 firmware project on this specific board, or needs pin availability information for the Tianmengxing G3507.
requires: [mspm0-ccs]
---

# mspm0kit-tianmengxing — 天猛星 MSPM0G3507 Skill

**Board**: Tianmengxing MSPM0G3507 development board (LQFP-64)
**Toolchain**: CCS Theia + TI Arm Clang + SysConfig + DriverLib
**SDK**: MSPM0 SDK（以 `config.json` 中实际配置为准，默认 2.05.01.00；文档声明的版本可能与实际安装不同，请以 `sdk_root` 路径为准）

## Workflow

When the user requests a new project, follow these four steps:

### Step 1 — Think

1. Identify the peripheral(s) the user wants (UART, GPIO, PWM, SPI, ADC, Timer).
2. Check the pin table below to confirm target pins are available.
3. Read the corresponding `peripherals/<peripheral>.md` for the SDK example name and pin mapping.
4. Confirm clock needs. SDK 模板默认使用内部时钟 **32 MHz**（`CPUCLK_FREQ = 32000000`）。如需 80 MHz，需在 SysConfig 中显式配置 HFXT+PLL。延时计算应使用 `CPUCLK_FREQ` 宏而非硬编码常量。

### Step 2 — Plan

Tell the user what you're going to create:

- Project name and target directory
- Which SDK example will be used as the template
- Which pins will be configured
- Clock configuration（SDK 模板默认 32 MHz 内部时钟，延时用 `CPUCLK_FREQ`）

Wait for confirmation before creating files, OR proceed if the user has indicated they want automatic execution.

**If the user is not satisfied with the plan:** Revise it based on their feedback, then **restate the complete revised plan** before writing any code. Do NOT jump straight to implementation — the user must see and approve the changes first. Repeat this loop until the user approves.

### Step 3 — Code

1. Ask: "是否允许我读取 SDK 目录（`<sdk_root>`）来复制例程模板？"
2. On approval, run scaffold using the **full path** to the skill's scripts directory:
   ```
   python <skill_install_dir>/scripts/scaffold.py <project_name> <sdk_example_name> -o <project_parent_dir>
   ```
   The scripts live in the skill install directory, NOT in the project directory. Use the full path every time.

   **Skill install path varies by agent platform** — locate it first:
   - Claude Code (Linux/macOS): `~/.claude/skills/mspm0kit-tianmengxing/scripts/`
   - Claude Code (Windows): `C:/Users/<user>/.claude/skills/mspm0kit-tianmengxing/scripts/`
   - Reasonix (Windows): `C:/Users/<user>/.reasonix/skills/mspm0kit-tianmengxing/scripts/`
   - Codex/其他 Agent: `C:/Users/<user>/.agents/skills/mspm0kit-tianmengxing/scripts/`
   - 通用查找: `ls ~/.claude/skills/mspm0kit-tianmengxing/scripts/` 或 `ls ~/.reasonix/skills/mspm0kit-tianmengxing/scripts/` 或 `ls ~/.agents/skills/mspm0kit-tianmengxing/scripts/`
3. If the user needs custom behavior beyond the SDK example, edit the generated `.syscfg` and `.c` file.
4. All pin changes go through `.syscfg` — never hand-edit generated `ti_msp_dl_config.*` files.

   > ⚠️ **延时函数陷阱**：MSPM0 DriverLib **没有** `DL_Delay_ms()` 或 `DL_Delay_us()` 函数。唯一可用的延时 API 是 `delay_cycles(n)`（定义在 `dl_core.h`）。不要凭 ARM/STM32 经验猜测 API 名称。如需 ms 级精确延时，使用 Timer 定时器中断。

5. **After scaffold completes, ask the user:** "工程已生成，是否要我帮你编译测试？"
   - If yes → proceed to Step 4 (build + report errors)
   - If no → just print the project path and usage instructions

### Step 4 — Verify

0. **MANDATORY: Run cleanup before building (every time):**
   ```bash
   python C:/Users/<user>/.claude/skills/mspm0kit-tianmengxing/scripts/cleanup.py <project_dir>
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
   python C:/Users/<user>/.claude/skills/mspm0kit-tianmengxing/scripts/build.py <project_dir> --yes
   ```
   `--yes` 跳过交互确认。非交互环境（AI agent 调用）下必须加此参数，否则 `input()` 会抛 EOFError。
2. If build fails: read the error, fix the issue, retry (max 3 times).
3. If build succeeds: report the `.out` file path and provide the flash command.
4. On first build failure, read `ti_msp_dl_config.h` to confirm generated macro names — never guess them.

### Flash

```
python scripts/flash.py <project_dir>
```

flash.py 根据 config.json 的 `probe` 字段自动选择烧录方式：
- `probe = "XDS110"`：用 DSLite 烧录
- `probe = "JLINK"`：用 tiarmobjcopy 转 hex + JLink.exe 烧录（DSLite 对 J-Link 支持不稳定，会报 block verification error）

## Core Rules

### R0: 3-Layer Embedded Architecture

`main.c` → `bsp/bsp_*.c/h` → `middleware/` → `app/app_*.c/h` → `targetConfigs/`

For simple projects, keeping most logic in `main.c` is acceptable.

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

## Pin Table — Tianmengxing MSPM0G3507

### Completely Unusable (never assign)

| Pin | Reason |
|-----|--------|
| PA2 | Frequency accuracy control, not routed |
| PA5 | HFXT crystal input (40 MHz) |
| PA6 | HFXT crystal output (40 MHz) |
| PA19 | SWDIO debug interface |
| PA20 | SWCLK debug interface |

### Conditional / Special Caution

| Pin | Condition |
|-----|-----------|
| PA18 | BSL entry pin — must be LOW at reset. Board BSL button (active high). |
| PA21 | VREF- —串联电容到地，只能做 GPIO，不可用于 PWM/I2C/SPI/UART 等高速通信 |
| PA23 | VREF+ —串联电容到地，只能做 GPIO，不可用于 PWM/I2C/SPI/UART 等高速通信 |
| PA10, PA11 | 板载 CH340 串口，排针可共用，用户亦可单独使用 |

### Board Peripheral Pins (occupied, do not reassign)

| Pin(s) | Occupied by |
|--------|-------------|
| PA10, PA11 | UART0 to CH340 USB-C（排针可共用 TX/RX） |
| PB6 | W25Q64 Flash CS（GPIO 控制） |
| PB7 | SPI1 MISO（Flash 专用，LCD 无需） |
| PB8 | SPI1 MOSI / LCD_SDA |
| PB9 | SPI1 SCLK / LCD_SCL |
| PB10 | LCD_RES |
| PB11 | LCD_DC |
| PB14 | LCD_CS |
| PB26 | LCD 背光 BLK |
| PB21 | 用户按键（PULL_UP，低电平有效） |
| PB22 | 板载 LED（高电平亮，低电平灭） |
| NRST | 复位按键 |

### Free Pins (available for user assignment)

PA0, PA1, PA3, PA4, PA7, PA8, PA9, PA12–PA17, PA22, PA24–PA31,
PB0–PB5, PB12, PB13, PB15–PB20, PB23–PB25, PB27

(Excludes occupied pins and PA21/PA23 with capacitor limitation unless for GPIO-only use.)

## Path Configuration

`config.json` 存储工具链路径。流程：先直接运行脚本 → 失败了再问用户路径 → 路径不存在时问是否自动搜索 → 用户同意后搜索 C/D/E 盘常见位置（`D:/TI/CCS/ccs`, `mspm0_sdk*` 等）→ 找到后写入 config.json → 重试。

## Tools

| Script | Purpose |
|--------|---------|
| `setup.py` | First-time path configuration |
| `scaffold.py <name> <example> -o <dir>` | Generate CCS project |
| `build.py <project_dir> --yes` | SysConfig CLI + gmake compile |
| `flash.py <project_dir>` | Flash (XDS110: DSLite / JLINK: JLink.exe) |
| `serial_console.py -p <port> -b <baud>` | Serial monitor |
| `cleanup.py <project_dir>` | **MANDATORY before build** |

> All scripts are in the skill install directory（路径因 Agent 平台而异，见 Step 3 中的路径列表）。Use full path when calling.

## Clock Configuration

SYSCTL 时钟属性名随 SDK 版本变化（例如 `HFXT_Range` 在 SDK 2.05 中不存在）。如不确定属性名，先用**安全默认配置**（系统默认时钟，无需 HFXT）：

```js
const SYSCTL = scripting.addModule("/ti/driverlib/SYSCTL", {}, false);
SYSCTL.forceDefaultClkConfig = true;
SYSCTL.clockTreeEn           = true;
```

这会用内部时钟（约 32 MHz），无需外部晶振，适合 GPIO/UART/定时器等多数场景。

**需要 80 MHz HFXT 时**：属性名因 SDK 版本而异，必须参考当前 SDK 的示例 `.syscfg`（如 `LP_MSPM0G3507/.../*.syscfg`）确认确切写法，不要凭记忆填属性名。

## Reference

For detailed SysConfig/DriverLib usage and debugging, also refer to the `mspm0-ccs` skill's reference docs.
