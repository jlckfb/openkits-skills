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
3. If the user needs custom behavior beyond the SDK example, edit the generated `.syscfg` first.
4. **After editing `.syscfg`, BEFORE writing the `.c`, fetch the ground-truth macro names** — never guess them:
   ```
   python <skill_dir>/scripts/build.py <project_dir> --sysconfig-only
   ```
   This runs SysConfig once and prints every generated macro (`*_PORT`, `*_PIN`, `*_INST`, `*_IIDX`, ...) from `ti_msp_dl_config.h`. Write the `.c` using those EXACT names. This eliminates the first-build failure caused by guessed macros.
5. All pin changes go through `.syscfg` — never hand-edit generated `ti_msp_dl_config.*` files.

   > ⚠️ **延时函数陷阱**：MSPM0 DriverLib **没有** `DL_Delay_ms()` / `DL_Delay_us()`。唯一的延时 API 是 `delay_cycles(n)`（定义在 `dl_core.h`），不要凭 ARM/STM32 经验猜函数名。
   >
   > **简单延时（闪烁、消抖、上电冒烟测试）直接用 `delay_cycles`，不要配定时器外设**——除 LED 用的那个 GPIO 外，无需任何 SysConfig 外设，也就没有宏要校验。ms 数直接套公式（与时钟频率无关）：
   > ```c
   > // 延时 N 毫秒：N * (每毫秒的时钟周期数)
   > delay_cycles(CPUCLK_FREQ / 1000 * 200);   // 例：200 ms
   > ```
   > 只有当你需要**主循环并发做别的事**、或**周期性非阻塞触发**时，才用 Timer (TIMG/TIMA) 中断。纯闪烁不属于这种情况。

6. **After scaffold completes, ask the user:** "工程已生成，是否要我帮你编译测试？"
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
4. Macro names should already be correct (Step 3 fetched them via `--sysconfig-only` before the `.c` was written). If you skipped that step and hit an undefined-macro error, read `ti_msp_dl_config.h` to confirm the real names — never guess them.

### Flash

```
python scripts/flash.py <project_dir>
```

flash.py 根据 config.json 的 `probe` 字段自动选择烧录方式：
- `probe = "XDS110"`：用 DSLite 烧录
- `probe = "JLINK"`：用 tiarmobjcopy 转 hex + JLink.exe 烧录（DSLite 对 J-Link 支持不稳定，会报 block verification error）

> ⚠️ **XDS110 首次使用**：如果 DSLite 报 `Error initializing emulator: (Error -260)`，检查 Windows 设备管理器中的 XDS110 驱动状态。若显示 "Unknown" 黄色感叹号，驱动未安装。运行 `<ccs_root>/ccs_base/emulation/windows/xds110_drivers/DPInst64.exe` 安装驱动（需管理员权限）。安装后板载 XDS110 重新枚举为 Serial Port 和 Data Port 即正常。

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

`config.json` 存储工具链路径，位于 skill 根目录（如 `~/.claude/skills/mspm0kit-tianmengxing/config.json`）。

**Agent 首次使用（推荐）** — 一条命令自动扫描：

```bash
python <skill_dir>/scripts/setup.py --auto-detect --probe JLink
```

`--auto-detect` 会自动搜索 C/D/E 盘的 CCS、SDK（选最新版）、SysConfig CLI、编译器、J-Link，无需用户介入。
Agent 也可以先尝试直接 scaffold/build，失败后再跑 setup。

**手动指定路径**：

```bash
python <skill_dir>/scripts/setup.py --accept-defaults --ccs-root D:/TI/CCS/ccs --sdk-root D:/TI/CCS/mspm0_sdk_2_05_01_00 --probe JLink
```

**用户交互模式**（人工在终端运行）：

```bash
python <skill_dir>/scripts/setup.py
```

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

> All scripts are in the skill install directory（路径因 Agent 平台而异，见 Step 3 中的路径列表）。Use full path when calling.

## Clock Configuration

SYSCTL 时钟属性名随 SDK 版本变化（例如 `HFXT_Range` 在 SDK 2.05 中不存在）。如不确定属性名，先用**安全默认配置**（系统默认时钟，无需 HFXT）：

```js
const SYSCTL = scripting.addModule("/ti/driverlib/SYSCTL", {}, false);
SYSCTL.forceDefaultClkConfig = true;
SYSCTL.clockTreeEn           = true;
```

这会用内部时钟（约 32 MHz），无需外部晶振，适合 GPIO/UART/定时器等多数场景。

> ⚠️ **STOP2 / 睡眠模式陷阱**：如果使用 SysTick 或定时器中断驱动实时任务（PWM 呼吸灯、按键轮询等），**禁止**使用 `SYSCTL.powerPolicy = "STOP2"` 或 `__WFI()`。STOP2 模式关闭 CPU 时钟（MCLK），SysTick 和所有依赖 MCLK 的 ISR 将完全停止。主循环中的 `delay_cycles()` 也失效。**默认不要加 `powerPolicy`，保持 RUN 模式即可。**

**需要 80 MHz HFXT 时**：属性名因 SDK 版本而异，必须参考当前 SDK 的示例 `.syscfg`（如 `LP_MSPM0G3507/.../*.syscfg`）确认确切写法，不要凭记忆填属性名。

## Reference

For detailed SysConfig/DriverLib usage and debugging, also refer to the `mspm0-ccs` skill's reference docs.
