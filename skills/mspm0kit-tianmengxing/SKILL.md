---
name: mspm0kit-tianmengxing
description: CCS project generator for the Tianmengxing MSPM0G3507 development board. Create full CCS projects from SDK examples with automatic pin/package adaptation, then build and flash. Use when the user wants to start a new MSPM0 firmware project on this specific board, or needs pin availability information for the Tianmengxing G3507.
requires: [mspm0-ccs]
---

# mspm0kit-tianmengxing — 天猛星 MSPM0G3507 Skill

**Board**: Tianmengxing MSPM0G3507 development board (LQFP-64)
**Toolchain**: CCS Theia + TI Arm Clang + SysConfig + DriverLib
**SDK**: MSPM0 SDK 2.10.00.04

## Workflow

When the user requests a new project, follow these four steps:

### Step 1 — Think

1. Identify the peripheral(s) the user wants (UART, GPIO, PWM, SPI, ADC, Timer).
2. Check the pin table below to confirm target pins are available.
3. Read the corresponding `peripherals/<peripheral>.md` for the SDK example name and pin mapping.
4. Confirm clock needs (default: 80 MHz CPUCLK with 40 MHz HFXT).

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
2. On approval, run:
   ```
   python scripts/scaffold.py <project_name> <sdk_example_name> -o <cwd>
   ```
3. If the user needs custom behavior beyond the SDK example, edit the generated `.syscfg` and `.c` file.
4. All pin changes go through `.syscfg` — never hand-edit generated `ti_msp_dl_config.*` files.
5. **After scaffold completes, ask the user:** "工程已生成，是否要我帮你编译测试？"
   - If yes → proceed to Step 4 (build + report errors)
   - If no → just print the project path and usage instructions

### Step 4 — Verify

0. **MANDATORY: Run cleanup before building (every time):**
   ```bash
   python scripts/cleanup.py <project_dir>
   ```
   This automatically:
   - Moves .c files from subdirectories to root (CCS flat rule)
   - Deletes duplicate .c files
   - Removes generated files from root (device_linker.cmd, ti_msp_dl_config.*, etc.)
   - Removes ticlang/ directory (conflicts with CCS Debug/)
   **Build MUST NOT proceed until cleanup returns success.**

1. Run build:
   ```
   python scripts/build.py <project_dir>
   ```
   This asks for confirmation before each tool invocation (SysConfig CLI, gmake).
2. If build fails: read the error, fix the issue, retry (max 3 times).
3. If build succeeds: report the `.out` file path and provide the flash command.
4. On first build failure, read `ti_msp_dl_config.h` to confirm generated macro names — never guess them.

## Core Rules

### R0: 3-Layer Embedded Architecture

All projects should follow a clean layered structure:

```
<project>/
├── main.c                     # Entry point
├── <project>.syscfg           # SysConfig
├── bsp/                       # BSP — Board-level peripheral drivers
│   └── bsp_<device>.c/h       #   e.g. bsp_led, bsp_flash
├── middleware/                 # Middleware — Reusable frameworks
│   └── ...
├── app/                       # Application — Project-specific tasks
│   └── app_<feature>.c/h
└── targetConfigs/             # Debug probe config (CCS only)
```

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
| PB6, PB7, PB8, PB9 | SPI1 — W25Q64 Flash + LCD 接口（共用 SPI 总线） |
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

The skill stores toolchain paths in `config.json`.

**Do NOT pre-emptively ask the user for paths or permission.** Follow this order:

1. **Try first.** Run the script (scaffold/build/flash) without asking for paths.
2. **If it fails** because `config.json` is missing or paths are invalid, ask the user to provide the paths:
   - "请提供 CCS 安装目录（例如 `C:/ti/ccstheia140`）："
   - "请提供 MSPM0 SDK 示例目录（例如 `C:/ti/mspm0_sdk_2_10_00_04/examples/nortos`）："
3. **Update `config.json`** via `python scripts/setup.py` or by writing directly.
4. **If the user-provided path does not exist or lacks expected files** (e.g. no `LP_MSPM0G3507/` subdirectory, no `.syscfg` files), do NOT silently accept it. Say:
   - "在 `<user_path>` 中没有发现 MSPM0G3507 的 SDK 示例（预期存在 `LP_MSPM0G3507/` 目录）。是否需要我自动搜索？"
5. **If the user says yes**, use `scripts/setup.py` or search common install locations (e.g. `C:/ti/`, `C:/Program Files/Texas Instruments/`) for the correct path.
6. **Retry** the failed script after paths are fixed.

## Tools

| Script | Purpose |
|--------|---------|
| `python scripts/setup.py` | First-time path configuration |
| `python scripts/scaffold.py <name> <example> -o <dir>` | Generate CCS project（优先搜索 SDK 示例） |
| `python scripts/build.py <project_dir>` | SysConfig CLI + gmake compile |
| `python scripts/flash.py <project_dir>` | DSLite flash |
| `python scripts/serial_console.py -p <port> -b <baud>` | Serial monitor |
| `python scripts/cleanup.py <project_dir>` | **MANDATORY before build**: fix .c in subdirs, remove generated files from root |

## SDK Example Index

### Standard Peripherals (from MSPM0 SDK)

Key SDK examples (under `examples/nortos/LP_MSPM0G3507/driverlib/`):

| Peripheral | SDK Example | Default Pins |
|-----------|-------------|--------------|
| GPIO Output | `gpio_toggle_output` | PB22, PB26, PB27, PB14 |
| UART TX/RX | `uart_rw_multibyte_fifo_poll` | PA10(TX), PA11(RX) |
| UART Console | `uart_tx_console_multibyte_repeated_fifo_dma` | PA10(TX), PA11(RX) |
| UART Echo | `uart_echo_interrupts_standby` | PA10/PA11 |
| SPI Controller | `spi_controller_multibyte_fifo_poll` | PB7, PB8, PB31, PB6 |
| SPI Controller DMA | `spi_controller_fifo_dma_interrupts` | PB7, PB8, PB31, PB6 |
| I2C Controller | `i2c_controller_rw_multibyte_fifo_poll` | PC2(SCL), PC3(SDA) |
| ADC Single | `adc12_single_conversion` | PA14 (ADC0 ch12) |
| ADC Internal Temp | `adc12_internal_temp_sensor_mathacl` | — |
| PWM Timer | `timg_32bit_timer_mode_pwm_edge_sleep` | PB6, PB7 (TIMG12) |
| Timer Periodic | `tima_timer_mode_periodic_repeat_count` | — |

> SDK 默认 pin 中 PB26, PB27, PB14, PB31 在天猛星上已被占用或有限制，scaffold 后需要按 pin 表调整。

## External Modules

When asked to drive an external sensor, motor, display, or radio:

- Ask for: datasheet, schematic, pin map, supply voltage, logic level, protocol, key timing.
- Before blaming code: check power, ground, pull-ups, level shifting, reset/enable pins, TX/RX crossover, I2C address, SPI mode, PWM polarity, shared pins.
- After repeated failures with correct SysConfig + build + flash: suggest checking wiring, power, module mode, datasheet mismatch.
- Separate "firmware looks correct" from "hardware proved correct".

## Reference

For detailed SysConfig/DriverLib usage and debugging, also refer to the `mspm0-ccs` skill's reference docs.
