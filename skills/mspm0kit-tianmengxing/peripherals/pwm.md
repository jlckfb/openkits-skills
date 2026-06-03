# PWM on Tianmengxing G3507

## SDK Example

`timg_32bit_timer_mode_pwm_edge_sleep` — 32-bit PWM edge-aligned with sleep

## Pin Mapping (LP → Tianmengxing)

SDK uses TIMG12 on PB6(C0)/PB7(C1).
Tianmengxing: PB6/PB7 occupied by SPI Flash → use TIMG0 or TIMG2 on free pins.

## Available Timer Instances for PWM

| Timer | Status | Tianmengxing Usage |
|-------|--------|--------------------|
| TIMA0 | Free | PWM, capture |
| TIMA1 | Free | PWM, capture |
| TIMG0 | Free | General PWM |
| TIMG6 | Free | General PWM |
| TIMG8 | Free | General PWM, QEI |
| TIMG12 | Free | General PWM (on free pins) |

## PWM Config Pattern (edge-aligned, 1 kHz on free pin)

```
PWM instance: TIMG0
Pin: PA3 (or any free pin)
Prescale: 80 (80 MHz / 80 = 1 MHz)
Period: 1000 (1 kHz)
Duty: 50%
```

## Generated Macros (example)

```
PWM_0_INST          → TIMG0
PWM_0_INST_CLK_FREQ → 1000000
GPIO_PWM_0_C0_IDX   → DL_TIMER_CC_0_INDEX
```

## IMPORTANT: PWM vs TIMER Module

SysConfig has TWO different modules for timer peripherals. Do NOT confuse them:

| `/ti/driverlib/PWM` | `/ti/driverlib/TIMER` |
|---------------------|----------------------|
| For PWM output (breathing LED, servo, motor control) | For periodic interrupts (tick, timeout) → [timer.md](timer.md) |
| No `timerMode` — PWM mode is implicit | `timerMode`: `ONE_SHOT / PERIODIC / ...` (NO `EDGE_ALIGN_PWM`) |
| `clockPrescale` (one value) | `timerClkDiv` + `timerClkPrescale` (two values) |
| `timerCount` (pure number) | `timerPeriod` (string, e.g. `"5 ms"`) |
| Channels: `PWM_CHANNEL_0.dutyCycle` | No PWM channels |

## SysConfig JS Snippet (PWM output, 1 kHz, 50% duty)

```js
const PWM  = scripting.addModule("/ti/driverlib/PWM", {}, false);
const PWM1 = PWM.addInstance();

PWM1.$name                      = "PWM_0";
PWM1.pwmMode                    = "EDGE_ALIGN_UP";
PWM1.ccIndex                    = [0];
PWM1.clockPrescale              = 80;       // 80 MHz / 80 = 1 MHz
PWM1.timerCount                 = 1000;     // 1 MHz / 1000 = 1 kHz
PWM1.timerStartTimer            = true;
PWM1.peripheral.$assign         = "TIMG0";
PWM1.peripheral.ccp0Pin.$assign = "PA3";
PWM1.PWM_CHANNEL_0.dutyCycle    = 50;
```

## SysConfig Naming Rules

- All `$name` values must be **globally unique** across all instances and pins.
- Pin names within an instance are automatically prefixed: `GPIO_<instance>$name`_`<pin>$name`_PIN`
  - Example: instance `$name = "LEDS"`, pin `$name = "LED"` → `LEDS_LED_PIN`
- Avoid pin names that match their instance name (e.g. instance `$name = "LED"` with pin `$name = "LED"` causes `$name` collision).

## CRITICAL: Timer/PWM Must Be Started Manually

`SYSCFG_DL_init()` 不会自动启动定时器。**必须在 init 后显式调用 startCounter**：

```c
SYSCFG_DL_init();
DL_TimerG_startCounter(PWM_0_INST);   // PWM 定时器
```

## Output Polarity — CRITICAL

**EDGE_ALIGN_UP + INIT_VAL_LOW + INV_OUT_DISABLED** 的输出规则：

| 阶段 | 输出 |
|------|------|
| counter < CC | LOW |
| counter ≥ CC | HIGH |

高电平占比 = `(PERIOD - CC) / PERIOD`：

| CC 值 | 高电平占比 | LED 亮度（active-high） |
|-------|-----------|----------------------|
| 0 | ~100% | **全亮** |
| PERIOD/2 | 50% | 半亮 |
| PERIOD-1 | ~0% | **全灭**（注意：CC=PERIOD 会回绕到全亮！） |
| PERIOD | 100% | ⚠️ 全亮（回绕，需钳制上限到 PERIOD-1） |

> **与 STM32 TIM ARR/CCR 方向相反**：STM32 CC 越大越亮，MSPM0 EDGE_ALIGN_UP 是 CC 越小越亮。

**呼吸灯正确写法**（duty 增加 = 亮度增加）：

```c
#define PWM_PERIOD 5000u

/* CC 取反使亮度随 duty 增加 */
DL_TimerG_setCaptureCompareValue(PWM_0_INST, PWM_PERIOD - duty, DL_TIMER_CC_1_INDEX);
```

## Key APIs

```c
DL_TimerG_setCaptureCompareValue(PWM_0_INST, duty, DL_TIMER_CC_0_INDEX);
DL_TimerG_startCounter(PWM_0_INST);
```

## Common Pitfalls

### P1: Unsigned int underflow in breathing loops

**Bug**: `unsigned int` 递减循环 `for (unsigned i = 999; i >= 1; i -= 5)` 在 `i = 4` 执行后 `4 - 5 = 0xFFFFFFFF`（无符号回绕），`0xFFFFFFFF >= 1` 永远为真 → **死循环**，LED 停在某个固定亮度。

**Fix**: 循环变量用 `int`，传入 API 时显式转换：

```c
for (int duty = PWM_MAX; duty >= PWM_MIN; duty -= FADE_STEP) {
    DL_TimerG_setCaptureCompareValue(
        PWM_0_INST, (unsigned int)duty, GPIO_PWM_0_C1_IDX);
    delay_cycles(FADE_DELAY);
}
```

### P2: `DL_TimerG_startCounter()` is mandatory

`SYSCFG_DL_init()` 配置引脚和时钟后，**定时器计数器不会自动启动**。忘记调用 `startCounter` 会导致 PWM 引脚完全无波形输出（LED 不亮）。参见上文 [CRITICAL: Timer/PWM Must Be Started Manually](#critical-timerpwm-must-be-started-manually)。

### P3: EDGE_ALIGN_UP polarity is opposite to STM32 / common tutorials

| 平台 | 常见行为 | MSPM0 EDGE_ALIGN_UP |
|------|---------|-------------------|
| STM32 TIM | CCR↑ = 占空比↑ = 更亮 | 不适用 |
| MSPM0 EDGE_ALIGN_UP | — | **CC↓ = 高电平占比↑ = 更亮** |

SysConfig PWM 模块默认模式为 **EDGE_ALIGN_UP**。部分在线教程（如某些 wiki）描述的是 EDGE_ALIGN_DOWN 行为（CC↑=亮），直接照搬会导致呼吸方向反转。详见上文 [Output Polarity](#output-polarity--critical)。
