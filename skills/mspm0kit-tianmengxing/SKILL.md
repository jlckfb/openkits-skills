---
name: mspm0kit-tianmengxing
description: CCS project generator for the Tianmengxing MSPM0G3507 development board. Create full CCS projects from SDK examples with automatic pin/package adaptation, then build and flash. Use when the user wants to start a new MSPM0 firmware project on this specific board, or needs pin availability information for the Tianmengxing G3507.
requires: [mspm0-ccs]
---

# mspm0kit-tianmengxing — 天猛星 MSPM0G3507 Skill

**Board**: Tianmengxing MSPM0G3507 development board (LQFP-64)
**SDK**: MSPM0 SDK（以 `config.json` 中 `sdk_root` 路径为准）

> 公共 Workflow / Tools / 延时 API / Macro patterns 见 `mspm0-ccs` skill 的 "Board Skill Workflow Template" 段。以下只记录本板 delta。

## Board Overrides

### Clock Default

SDK 模板默认 **32 MHz** 内部时钟（`CPUCLK_FREQ = 32000000`）。如需 80 MHz 需在 SysConfig 配 HFXT+PLL。延时公式中使用 `CPUCLK_FREQ` 宏，与频率无关。

安全默认 SysConfig 配置（无需 HFXT）：
```js
const SYSCTL = scripting.addModule("/ti/driverlib/SYSCTL", {}, false);
SYSCTL.forceDefaultClkConfig = true;
SYSCTL.clockTreeEn           = true;
```

需要 80 MHz 时：属性名因 SDK 版本而异，必须参考当前 SDK 的 `LP_MSPM0G3507/.../*.syscfg` 确认写法。

### Flash — XDS110 驱动注意

如果 DSLite 报 `Error initializing emulator: (Error -260)`，检查设备管理器 XDS110 驱动。若显示黄色感叹号，运行 `<ccs_root>/ccs_base/emulation/windows/xds110_drivers/DPInst64.exe` 安装。

### Architecture

`main.c` → `bsp/bsp_*.c/h` → `middleware/` → `app/app_*.c/h`

简单项目保持 `main.c` 即可。

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
