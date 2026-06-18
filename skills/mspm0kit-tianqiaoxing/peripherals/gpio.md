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

## 按键状态机（mid_button — 长按/短按/双击）

`middleware/button/mid_button.c/h` 是板载按键的通用去抖+多击检测状态机，5ms ISR 驱动。

### 核心数据结构

```c
#include "mid_button.h"

/* 创建一个按键句柄 */
static Button key0;
button_init(&key0, read_button_gpio, 0, 0);  /* active_level=0 = 低电平有效 */
```

### 事件类型

| 事件 | 触发时机 |
|------|---------|
| `BTN_PRESS_DOWN` | 按键刚按下 |
| `BTN_PRESS_UP` | 按键刚释放 |
| `BTN_SINGLE_CLICK` | 单击完成（按下→释放后 100ms 内未再按） |
| `BTN_DOUBLE_CLICK` | 双击完成（100ms 内连按两次） |
| `BTN_LONG_PRESS_START` | 按住超过 500ms |
| `BTN_LONG_PRESS_HOLD` | 长按保持中（持续触发） |
| `BTN_PRESS_REPEAT` | 连按检测（第二次及以后的按下） |

### 用法模式

```c
#include "mid_button.h"

/* 0. GPIO 读取函数（供状态机调用） */
uint8_t read_button_gpio(uint8_t button_id) {
    switch (button_id) {
        case 0: return DL_GPIO_readPins(KEY_PORT, KEY_ENTER_PIN) ? 1 : 0;
        /* ... */
    }
    return 1;
}

/* 1. 初始化 */
button_init(&key0, read_button_gpio, 0, 0);        /* active_level=0 = 低有效 */
button_attach(&key0, BTN_SINGLE_CLICK,      key0_single_click_Handler);
button_attach(&key0, BTN_LONG_PRESS_START,  key0_long_press_Handler);
button_start(&key0);                                  /* 注册到全局链表 */

/* 2. 回调函数 */
void key0_single_click_Handler(void *btn) {
    /* 单击：执行动作 */
}
void key0_long_press_Handler(void *btn) {
    /* 长按：执行不同动作 */
}

/* 3. 5ms ISR 驱动（必须每 5ms 调用一次） */
void timer_isr(void) {
    button_ticks();   /* 遍历链表，处理所有按键 */
}
```

### 参数配置

```c
#define TICKS_INTERVAL  5     /* ISR 调用间隔 ms */
#define DEBOUNCE_TICKS  3     /* 去抖采样次数 (3×5ms=15ms) */
#define SHORT_TICKS     20    /* 单击/双击窗口 (20×5ms=100ms) */
#define LONG_TICKS      100   /* 长按阈值 (100×5ms=500ms) */
```

## Free Pins (available for user assignment)

PA3, PA4, PA7–PA9, PA12–PA17, PA21–PA23, PA25–PA28,
PB0–PB5, PB10–PB16, PB19, PB20, PB25, PB28
