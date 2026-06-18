# GPIO on Tianqiaoxing G3519

## Onboard LED — PB22 (active-LOW)

```c
DL_GPIO_clearPins(GPIOB, DL_GPIO_PIN_22);   // LED ON
DL_GPIO_setPins(GPIOB, DL_GPIO_PIN_22);     // LED OFF
DL_GPIO_togglePins(GPIOB, DL_GPIO_PIN_22);  // Toggle
```

## Buttons

| Pin | Name | Pull | Active | 功能 |
|-----|------|------|--------|------|
| PB21 | ENTER | PULL_UP | Low | 菜单确认 |
| PA18 | BACK | PULL_DOWN | High | 菜单返回（BSL 引脚，正常使用时 PULL_DOWN） |
| PA31 | ENC_SW | PULL_UP | Low | 编码器按下 |
| PA24 | KEY1 | PULL_UP | Low | 用户按键 1（等效 BACK） |
| PB24 | KEY2 | PULL_UP | Low | 用户按键 2（等效 ENTER） |

按键逻辑（固件实现）：
```c
back  = (PA18 == HIGH) || (PA24 == LOW);  // 任一触发即 back
enter = (PB21 == LOW)  || (PB24 == LOW);  // 任一触发即 enter
```

## Critical Notes

1. **`DL_GPIO_initDigitalOutput()` 只配 IOMUX**，必须额外调 `DL_GPIO_enableOutput()` 才能输出
2. **GPIO 中断需手动启用 NVIC**：`NVIC_EnableIRQ(GPIO_xxx_INT_IRQN)`
3. **SDK 2.04 LQFP-64(PM) 有引脚映射 bug** — SysConfig 后 grep `ti_msp_dl_config.h` 验证宏。SDK >= 2.05 已修复。
4. **`.syscfg` 中 `initialValue` 枚举是 `"CLEARED"` / `"SET"`**（不是 `"CLEAR"`）。写错会导致 SysConfig 报错 `No option named CLEAR defined`。

## Simple Blink — delay_cycles

```c
#include "ti_msp_dl_config.h"
int main(void) {
    SYSCFG_DL_init();
    while (1) {
        DL_GPIO_clearPins(GPIO_LED_PORT, GPIO_LED_PIN_PIN);  // ON
        delay_cycles(CPUCLK_FREQ / 1000 * 100);             // 100ms
        DL_GPIO_setPins(GPIO_LED_PORT, GPIO_LED_PIN_PIN);    // OFF
        delay_cycles(CPUCLK_FREQ / 1000 * 100);             // 100ms
    }
}
```

> DriverLib 没有 `DL_Delay_ms()`，唯一延时 API 是 `delay_cycles(n)`。

## Free Pins (available for user assignment)

PA3, PA4, PA7–PA9, PA12–PA17, PA21–PA23, PA25–PA28,
PB0–PB5, PB10–PB16, PB19, PB20, PB25, PB28
