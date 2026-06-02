# GPIO on Tianmengxing G3507

## SDK Example

`gpio_toggle_output` — toggles 4 pins (PB22, PB26, PB27, PB14) with delay

## Pin Mapping (LP → Tianmengxing)

| SDK Pin | SDK Name | Tianmengxing | Action |
|---------|----------|--------------|--------|
| PB22 | USER_LED_1 | PB22 (onboard LED) | Keep |
| PB26 | USER_LED_2 | PB26 (LCD BLK) | Remove (occupied) |
| PB27 | USER_LED_3 | PB27 | Keep as test output (free) |
| PB14 | USER_TEST | PB14 (LCD_CS) | Remove (occupied) |

## Recommended Pattern

```c
// LED on (active-high)
DL_GPIO_setPins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);
// LED off
DL_GPIO_clearPins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);
// Toggle
DL_GPIO_togglePins(GPIO_LEDS_PORT, GPIO_LEDS_USER_LED_1_PIN);
```

> 注意：天猛星 PB22 LED 为高电平亮，与天巧星相反。

## Button Input

| Button | Pin | Active | Resistor |
|--------|-----|--------|----------|
| 用户按键 | PB21 | 低电平有效 | PULL_UP |
| BSL 按键 | PA18 | 高电平有效 | PULL_DOWN |

```c
// Read user button (active low)
if (!DL_GPIO_readPins(GPIO_BTN_PORT, GPIO_BTN_USER_PIN)) {
    // button pressed
}

// Read BSL button (active high)
if (DL_GPIO_readPins(GPIO_BSL_PORT, GPIO_BSL_BSL_PIN)) {
    // BSL button pressed — but don't hold at reset!
}
```

## Generated Macros (example)

```
GPIO_LEDS_PORT              → GPIOB
GPIO_LEDS_USER_LED_1_PIN    → DL_GPIO_PIN_22
GPIO_BTN_PORT               → GPIOB
GPIO_BTN_USER_PIN            → DL_GPIO_PIN_21
```

## Free GPIO Pins

PA0, PA1, PA3, PA4, PA7, PA8, PA9, PA12–PA17, PA22, PA24–PA31,
PB0–PB5, PB12, PB13, PB15–PB20, PB23–PB25, PB27

PA21, PA23 可用于纯 GPIO（输入/输出），但不可用于高速通信外设（PWM/I2C/SPI/UART）。

## SysConfig Enum Values

> **CRITICAL**: `initialValue` 的有效值是 `"CLEARED"`，不是 `"CLEAR"`。写错会报：
> `Error: cannot set 'initialValue' to 'CLEAR': No option named CLEAR defined`

| Field | Valid Values | NOT Valid |
|-------|-------------|-----------|
| `initialValue` | `"SET"` (HIGH), **`"CLEARED"`** (LOW) | ~~`"CLEAR"`~~, `"LOW"`, `"HIGH"`, `"1"`, `"0"` |
| `direction` | `"OUTPUT"`, `"INPUT"` | — |
| `internalResistor` | `"PULL_UP"`, `"PULL_DOWN"`, `"NONE"` | — |
| `ioStructure` | `"OD"` (open-drain), omitted for push-pull | — |

## Naming Rules

1. **GPIO instance `$name` and pin `$name` MUST NOT be equal** — SysConfig treats them as globally unique identifiers.
   - WRONG: instance=`"LED"`, pin=`"LED"` → Duplicate name error
   - CORRECT: instance=`"LED"`, pin=`"PIN"` or `"OUT"`

2. **Generated macro format**:
   - Port macro: `<INSTANCE>_PORT` → e.g. `LED_PORT` = `GPIOB`
   - Pin macro: `<INSTANCE>_<PIN>_PIN` → e.g. `LED_PIN_PIN` = `DL_GPIO_PIN_22`
   - IOMUX macro: `<INSTANCE>_<PIN>_IOMUX` → e.g. `LED_PIN_IOMUX` = `IOMUX_PINCM50`

3. **Always run SysConfig first**, then `grep` the generated `ti_msp_dl_config.h` to confirm actual macro names before writing code.

## SysConfig JS Snippet

> **重要**：GPIO 模块用 `associatedPins` 数组模式，必须先 `.create(N)` 再用索引访问。
> 不存在 `GPIO1.port` / `GPIO1.assignedPin` 这类直接属性。

### Output (LED, active-high)

```js
const GPIO  = scripting.addModule("/ti/driverlib/GPIO", {}, false);
const GPIO1 = GPIO.addInstance();

GPIO1.$name                          = "GPIO_LED";
GPIO1.associatedPins.create(1);              // 必须先 create
GPIO1.associatedPins[0].$name        = "LED_PIN";
GPIO1.associatedPins[0].initialValue = "CLEARED";
GPIO1.associatedPins[0].assignedPort = "PORTB";
GPIO1.associatedPins[0].assignedPin  = "22";
GPIO1.associatedPins[0].pin.$assign  = "PB22";
```

### Input (button, pull-up, active-low)

```js
GPIO1.$name                              = "BTN";
GPIO1.associatedPins.create(1);
GPIO1.associatedPins[0].$name            = "USER";
GPIO1.associatedPins[0].direction        = "INPUT";
GPIO1.associatedPins[0].internalResistor = "PULL_UP";
GPIO1.associatedPins[0].assignedPort     = "PORTB";
GPIO1.associatedPins[0].assignedPin      = "21";
GPIO1.associatedPins[0].pin.$assign      = "PB21";
```

## GPIO 中断分组（CRITICAL）

MSPM0 的 GPIO 中断**不是每引脚一个 IRQ**，而是按端口分组：

| 中断组 | 包含 |
|--------|------|
| GROUP0 | GPIOA + 部分外设 |
| GROUP1 | GPIOB + 部分外设 |

天猛星按键在 PB21（GPIOB）→ 走 **GROUP1_IRQHandler**，不是 `GPIO_BTN_IRQHandler`。

```c
void GROUP1_IRQHandler(void)
{
    switch (DL_Interrupt_getPendingGroup(DL_INTERRUPT_GROUP_1)) {
        case GPIO_BTN_INT_IIDX:
            if (DL_GPIO_getEnabledInterruptStatus(GPIO_BTN_PORT, GPIO_BTN_USER_PIN)) {
                DL_GPIO_clearInterruptStatus(GPIO_BTN_PORT, GPIO_BTN_USER_PIN);
                // 业务逻辑
            }
            break;
    }
}
```

SysConfig 中需开启引脚中断：
```js
GPIO1.associatedPins[0].interruptEn  = true;
GPIO1.associatedPins[0].polarity     = "FALL";  // 下降沿（按键按下）
```

### NVIC 必须手动启用（CRITICAL）

`SYSCFG_DL_init()` 只调用外设层的 `DL_GPIO_enableInterrupt()`，**不会自动调用 `NVIC_EnableIRQ()`**。忘记加这一行则中断永远不会触发。

```c
int main(void)
{
    SYSCFG_DL_init();
    NVIC_EnableIRQ(BTN_INT_IRQN);  /* 必须！SysConfig 不生成这行 */
    // ...
}
```

> **所有中断外设均适用此规则**，不只是 GPIO。Timer、UART、SPI 等中断也需在 `SYSCFG_DL_init()` 后手动调用对应的 `NVIC_EnableIRQ(XXX_INST_INT_IRQN)`。

### 按键消抖与多操作（单击 / 双击 / 长按）

推荐使用 **MultiButton** 库，不要自己写消抖逻辑：

> 仓库：https://github.com/0x1abin/MultiButton

**接入方式**：
1. 将 `multi_button.c` / `multi_button.h` 复制到项目根目录
2. 实现引脚读取回调（低电平有效）：

```c
uint8_t btn_read_pin(void *btn)
{
    return DL_GPIO_readPins(BTN_PORT, BTN_USER_PIN) ? 1 : 0;
}
```

3. 初始化并注册事件：

```c
Button btn;
button_init(&btn, btn_read_pin, 0, 0);  /* active_level=0（低电平有效） */
button_attach(&btn, SINGLE_CLICK,     on_single_click);
button_attach(&btn, DOUBLE_CLICK,     on_double_click);
button_attach(&btn, LONG_PRESS_START, on_long_press);
button_start(&btn);
```

4. 主循环每 5 ms 调用一次（用 SysTick 或 Timer 中断驱动）：

```c
button_ticks();
```

> MultiButton 已内置消抖，无需额外处理抖动。
