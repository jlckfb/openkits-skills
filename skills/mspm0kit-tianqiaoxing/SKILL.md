---
name: mspm0kit-tianqiaoxing
description: One-sentence CCS project generator for the Tianqiaoxing MSPM0G3519 custom board. Create full CCS projects from SDK examples with automatic pin/package adaptation, then build and flash. Use when the user wants to start a new MSPM0 firmware project on this specific board, or needs pin availability information for the Tianqiaoxing G3519.
requires: [mspm0-ccs]
---

# mspm0kit — 天巧星 MSPM0G3519 Skill

**Board**: Tianqiaoxing MSPM0G3519 custom development board (LQFP-64)
**SDK**: MSPM0 SDK 2.05.01.00

> 公共 Workflow / Tools / 延时 API / Macro patterns 见 `mspm0-ccs` skill 的 "Board Skill Workflow Template" 段。以下只记录本板 delta。

## Board Overrides

### Clock Default

默认 **80 MHz** CPUCLK（40 MHz HFXT + PLL）。

### Fast Path (Step 1 前置判断)

如果需求只是 **LED 闪烁 / GPIO 翻转 / 阻塞延时**（含"每 N 毫秒/秒闪一次"），触发快路径：

1. **只配 LED 那一个 GPIO**，用 `delay_cycles(CPUCLK_FREQ / 1000 * N)` 做延时
2. **不要配定时器、不要读 `pwm_timer.md`**
3. **跳过 Step 2 确认和 Step 3 SDK 权限询问** — 直接 scaffold → 写 .syscfg → build → flash
4. 只有主循环要并发做别的事时才需要定时器

快路径代码模板（精确控制亮灭）：
```c
#include "ti_msp_dl_config.h"
int main(void) {
    SYSCFG_DL_init();
    while (1) {
        DL_GPIO_setPins(GPIO_LED_PORT, GPIO_LED_PIN_PIN);
        delay_cycles(CPUCLK_FREQ / 1000 * 100);   // 亮 100ms
        DL_GPIO_clearPins(GPIO_LED_PORT, GPIO_LED_PIN_PIN);
        delay_cycles(CPUCLK_FREQ / 1000 * 100);   // 灭 100ms
    }
}
```

> 用户说"最快速度"/"一句话生成"时，等同于快路径触发 + 自动执行（不等确认）。

### I2C Selection (Step 1 追加)

如果涉及 I2C，询问用户：
- **软件 I2C**（默认）：GPIO 位模拟，任意引脚，用 `scaffold_oled.py` 不加 `--i2c hw`
- **硬件 I2C**：更快更稳定，需使用 I2C 功能引脚，用 `--i2c hw`，验证引脚对照 `references/hw_i2c_pins.md`

### Extra Tool — scaffold_oled.py

```
python <skill_dir>/scripts/scaffold_oled.py <name> [--mode menu] [--with-imu] [--i2c hw]
```
生成 OLED UI 工程（含字库/菜单框架）。

### R4: Generated Macro Verification (SDK 2.04 bug)

SDK 2.04 + SysConfig 1.27 的 LQFP-64(PM) 有引脚映射 bug：`_PORT`/`_PIN` 宏可能指向错误端口。
- SysConfig 后必须 grep `ti_msp_dl_config.h` 验证宏值
- 宏错误时直接用 `GPIOB, DL_GPIO_PIN_22` 等具体值
- `DL_GPIO_initDigitalOutput()` 只配 IOMUX，必须额外调 `DL_GPIO_enableOutput()`
- 升级到 SDK >= 2.05.01.01 可解决

### R5: Pin Table is Authoritative

选引脚前必须查下方 Pin Table。黄色标注引脚不可使用。用户要求占用引脚时须明确警告。

### Architecture

`main.c` → `hal/hal_*.c/h` → `bsp/bsp_*.c/h` → `middleware/` → `app/app_*.c/h`

简单项目保持 `main.c` 即可。

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
