---
name: mspm0kit
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

### R0: 4-Layer Embedded Architecture (HIGHEST PRIORITY)

All projects must follow the HAL → BSP → Middleware → App 4-layer structure.

```
<project>/
├── main.c                     # Entry point
├── <project>.syscfg           # SysConfig
├── hal/                       # HAL — MCU register abstraction (optional)
│   └── hal_<periph>.c/h       #   e.g. hal_i2c, hal_timer
├── bsp/                       # BSP — Board-level peripheral drivers
│   └── bsp_<device>.c/h       #   e.g. bsp_led, bsp_imu, bsp_i2c
├── middleware/                 # Middleware — Reusable frameworks & protocols
│   ├── oled/                  #   OLED UI framework
│   ├── button/                #   MultiButton library
│   ├── fusion/                #   AHRS attitude fusion
│   ├── wireless/              #   Wireless UART protocol
│   └── timer/                 #   System tick service
├── app/                       # Application — Project-specific tasks & UI
│   └── app_<feature>.c/h      #   e.g. app_cube, app_menu
└── targetConfigs/             # Debug probe config (CCS only)
```

**Each module is self-contained**: `.c` and `.h` live together in the same directory.

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

### R3: External Path Permission

- Every access to external paths (CCS, SDK) requires a permission prompt.


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

The skill stores toolchain paths in `config.json`. When the skill needs to access external paths:

1. **CCS directory**: Ask "是否允许我读取 CCS 配置（`<ccs_root>`）？"
2. **SDK directory**: Ask "是否允许我读取 SDK 内容（`<sdk_root>`）？"

If the user declines, use the built-in peripheral reference docs in `peripherals/` as fallback knowledge.

If `config.json` does not exist, run `python scripts/setup.py` first.

## Tools

| Script | Purpose |
|--------|---------|
| `python scripts/setup.py` | First-time path configuration |
| `python scripts/scaffold.py <name> <example> -o <dir>` | Generate CCS project (searches bundled examples first, then SDK) |
| `python scripts/build.py <project_dir>` | SysConfig CLI + gmake compile |
| `python scripts/flash.py <project_dir>` | DSLite flash |
| `python scripts/serial_console.py <port> -b <baud>` | Serial monitor |
| `python scripts/cleanup.py <project_dir>` | **MANDATORY before build**: fix .c in subdirs, remove generated files from root |
| `python scripts/scaffold_oled.py <name> [--mode menu] [--with-imu] [--i2c hw]` | Generate OLED UI project (bundled, no external repo needed) |

## SDK Example Index

### Standard Peripherals (from MSPM0 SDK)

Key SDK examples (under `examples/nortos/LP_MSPM0G3519/driverlib/`):

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
| QEI | `timg_qei_mode` | — |

### Bundled Board Examples (no SDK dependency)

These are self-contained in the skill's `examples/` directory. They do NOT require the OLED_UI repo or any external source.

| Module | Example Name | Pins | Use |
|--------|-------------|------|-----|
| Wireless UART | `wireless_uart7` | PB17/PB18 | `scaffold.py <name> wireless_uart7` |
| WS2812 RGB LED | `ws2812_rgb` | PB26 | `scaffold.py <name> ws2812_rgb` |
| IMU LSM6DS3 | `imu_lsm6ds3` | PA27/PA28 | `scaffold.py <name> imu_lsm6ds3` |
| QEI Encoder | `encoder_qei` | PA29/PA30/PA31 | `scaffold.py <name> encoder_qei` or `--with-encoder` |

### OLED UI Framework (bundled, no external dependencies)

When the user asks to "移植屏幕UI" or "add OLED display":

1. Run `python scripts/scaffold_oled.py <project_name>` — uses bundled examples, no external repo needed
2. `--mode draw` (default): basic drawing API (OLED_Init, ShowString, PrintfMix)
3. `--mode menu`: full menu engine with pages, cursor, animations
4. Optional: `--with-imu`, `--with-ws2812`, `--with-wireless`, `--i2c hw`
5. Built-in bitmap fonts (F6x8~F10x20 ASCII + CF12x12~CF20x20 Chinese), no Flash required
6. Reference: `peripherals/oled_ui.md` for API

## External Modules

When asked to drive an external sensor, motor, display, or radio:

- Ask for: datasheet, schematic, pin map, supply voltage, logic level, protocol, key timing.
- Before blaming code: check power, ground, pull-ups, level shifting, reset/enable pins, TX/RX crossover, I2C address, SPI mode, PWM polarity, shared pins.
- After repeated failures with correct SysConfig + build + flash: suggest checking wiring, power, module mode, datasheet mismatch.
- Separate "firmware looks correct" from "hardware proved correct".

## Reference

For detailed SysConfig/DriverLib usage and debugging, also refer to the `mspm0-ccs` skill's reference docs.
