# GPIO on Tianqiaoxing G3519

## SDK Example

`gpio_toggle_output` — toggles 4 pins (PB22, PB26, PB27, PB14) with delay

## Pin Mapping (LP → Tianqiaoxing)

| SDK Pin | SDK Name | Tianqiaoxing | Action |
|---------|----------|--------------|--------|
| PB22 | USER_LED_1 | PB22 (onboard LED) | Keep |
| PB26 | USER_LED_2 | PB26 (WS2812) | Remove (occupied) |
| PB27 | USER_LED_3 | PB27 (Buzzer) | Remove (occupied) |
| PB14 | USER_TEST | Free | Keep as test output |

## CRITICAL: SysConfig Macro Bug (SDK 2.04 / SysConfig 1.27)

SDK 2.04.00.06 + SysConfig 1.27.0 的 LQFP-64(PM) 封装器件数据存在引脚映射 bug。生成的 `*_PORT` 和 `*_PIN` 宏可能指向错误的 GPIO 端口（例如 `DEBUG_LED_PORT = GPIOA` 实际应该是 `GPIOB`）。

**规则：生成 SysConfig 后，必须验证宏**。用 `grep` 检查 `ti_msp_dl_config.h`：
```c
#define DEBUG_LED_PORT          (GPIOB)      // 期望 GPIOB
#define DEBUG_LED_PIN_22_PIN    (DL_GPIO_PIN_22) // 期望 PIN_22
```

如果宏错误，**在代码中使用直接值**而非生成的宏：
```c
DL_GPIO_setPins(GPIOB, DL_GPIO_PIN_22);   // 正确：直接指定
DL_GPIO_setPins(DEBUG_LED_PORT, DEBUG_LED_PIN_22_PIN); // 可能错误！
```

升级到 SDK >= 2.05.01.01 + SysConfig 1.24 可避免此 bug。

## CRITICAL: Output Enable Required

`DL_GPIO_initDigitalOutput(IOMUX_PINCM)` **只配置 IOMUX** 将引脚设为 GPIO 功能，**不设置输出方向**。必须额外调用：

```c
DL_GPIO_initDigitalOutput(IOMUX_PINCM50);   // 只配 IOMUX
DL_GPIO_enableOutput(GPIOB, DL_GPIO_PIN_22); // 必须！否则引脚高阻态
```

SysConfig 生成的 `SYSCFG_DL_GPIO_init()` 虽然会调用 `enableOutput`，但如果宏映射错误，它使能的是错误的引脚。因此在手动代码中必须显式调用。

## LED Polarity

**PB22 板载 LED：低电平亮（active-LOW）**

```c
DL_GPIO_clearPins(GPIOB, DL_GPIO_PIN_22);   // LOW  → LED ON
DL_GPIO_setPins(GPIOB, DL_GPIO_PIN_22);     // HIGH → LED OFF
```

> 与天猛星（active-HIGH = 高电平亮）**相反**。

## Recommended Pattern

```c
// LED on (active-low)
DL_GPIO_clearPins(GPIOB, DL_GPIO_PIN_22);
// LED off
DL_GPIO_setPins(GPIOB, DL_GPIO_PIN_22);
// Toggle
DL_GPIO_togglePins(GPIOB, DL_GPIO_PIN_22);
```

## Generated Macros

```
GPIO_LEDS_PORT              → GPIOB
GPIO_LEDS_USER_LED_1_PIN    → DL_GPIO_PIN_22
GPIO_LEDS_USER_LED_1_IOMUX  → IOMUX_PINCM50
```

## Free GPIO Pins (all ports)

PA3, PA4, PA7–PA9, PA12–PA17, PA21–PA26
PB0–PB5, PB10–PB16, PB19, PB20, PB24, PB25, PB28

(Excludes any pin listed as occupied in SKILL.md)

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

3. **Always run SysConfig first**, then `grep` the generated `ti_msp_dl_config.h` to **verify** actual macro names AND port values before writing code.

## SysConfig JS Snippet

### Output (LED, active-low)

```js
GPIO1.$name                         = "LED";
GPIO1.associatedPins[0].$name       = "LED";
GPIO1.associatedPins[0].initialValue = "SET";  // HIGH = off for active-low
GPIO1.associatedPins[0].assignedPort = "PORTB";
GPIO1.associatedPins[0].assignedPin  = "22";
GPIO1.associatedPins[0].pin.$assign  = "PB22";
```

### Input (button, pull-up)

```js
GPIO1.$name                              = "BTN";
GPIO1.associatedPins[0].$name            = "ENTER";
GPIO1.associatedPins[0].direction        = "INPUT";
GPIO1.associatedPins[0].internalResistor = "PULL_UP";
GPIO1.associatedPins[0].assignedPort     = "PORTB";
GPIO1.associatedPins[0].assignedPin      = "21";
GPIO1.associatedPins[0].pin.$assign      = "PB21";
```
