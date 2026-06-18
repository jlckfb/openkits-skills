# PWM / Timer on Tianqiaoxing G3519

> ⚠️ **先确认你真的需要定时器**：LED 闪烁、消抖、上电冒烟测试这类**阻塞延时**，直接用 `delay_cycles(CPUCLK_FREQ / 1000 * 毫秒数)` 即可（见 [gpio.md](gpio.md) 的闪烁范本），**不要配 TIMER 外设**——省掉整个 SysConfig 配置和宏校验。
> "200ms 闪烁"**不算** periodic interrupt：只有当主循环要**并发做别的事**、不能被延时阻塞时，才用定时器中断。下方的 TIMER 模块用于这种非阻塞周期任务（tick、timeout 轮询），不是用来做简单闪烁的。

## SDK Examples

| Example | What It Does |
|---------|-------------|
| `timg_32bit_timer_mode_pwm_edge_sleep` | 32-bit PWM edge-aligned with sleep |
| `tima_timer_mode_periodic_repeat_count` | Periodic timer with repeat count |
| `timg_qei_mode` | Quadrature encoder (QEI) |

## Pin Mapping (LP → Tianqiaoxing)

SDK uses TIMG12 on PB6(C0)/PB7(C1).
Tianqiaoxing: PB6/PB7 occupied by SPI Flash → use TIMG0 or TIMG2 on free pins.

## Available Timer Instances

| Timer | Status | Tianqiaoxing Usage |
|-------|--------|--------------------|
| TIMA0 | System tick | 5ms 周期中断（mid_timer），全功能固件已占用 |
| TIMA1 | CC0 used | CC0 = WS2812 on PB26 (+ DMA) |
| TIMG0 | Free | General PWM |
| TIMG6 | CC1 used | CCP1 = Buzzer on PB27 (1 MHz clock) |
| TIMG8 | QEI used | PA29/PA30 encoder (optional) |
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
| For PWM output (breathing LED, buzzer, WS2812, servo) | For periodic interrupts (tick, timeout) |
| No `timerMode` — PWM mode is implicit | `timerMode`: `ONE_SHOT / PERIODIC / ...` (NO `EDGE_ALIGN_PWM`) |
| `clockPrescale` (one value) | `timerClkDiv` + `timerClkPrescale` (two values) |
| `timerCount` (pure number) | `timerPeriod` (string, e.g. `"5 ms"`) |
| Channels: `PWM_CHANNEL_0.dutyCycle` | No PWM channels |

## SysConfig JS Snippets

### PWM output (1 kHz, 50% duty on TIMG0 PA3)

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

### Periodic timer interrupt (5 ms interval)

```js
const TIMER  = scripting.addModule("/ti/driverlib/TIMER", {}, false);
const TIMER1 = TIMER.addInstance();

TIMER1.timerClkDiv        = 8;
TIMER1.timerClkPrescale   = 10;      // 80 MHz / 8 / 10 = 1 MHz
TIMER1.timerStartTimer    = true;
TIMER1.timerMode          = "PERIODIC";
TIMER1.interrupts         = ["ZERO"];
TIMER1.interruptPriority  = "3";
TIMER1.$name              = "TIMER_TICK";
TIMER1.timerPeriod        = "5 ms";  // 1 MHz * 0.005 = 5000 counts
TIMER1.peripheral.$assign = "TIMA0";
```

### Buzzer PWM (TIMG6 CCP1 on PB27)

```js
const PWM  = scripting.addModule("/ti/driverlib/PWM", {}, false);
const PWM1 = PWM.addInstance();

PWM1.ccIndex               = [1];
PWM1.pwmMode               = "EDGE_ALIGN_UP";
PWM1.$name                 = "BUZZER";
PWM1.timerStartTimer       = true;
PWM1.clockPrescale         = 80;      // 1 MHz
PWM1.timerCount            = 1000;    // 1 kHz tone (change for different pitch)
PWM1.peripheral.$assign    = "TIMG6";
PWM1.peripheral.ccp1Pin.$assign = "PB27";
PWM1.PWM_CHANNEL_1.dutyCycle = 50;
```

### TIMA1 PWM (for WS2812, 80 MHz no prescale)

```js
const PWM  = scripting.addModule("/ti/driverlib/PWM", {}, false);
const PWM1 = PWM.addInstance();

PWM1.pwmMode               = "EDGE_ALIGN_UP";
PWM1.ccIndex               = [0];
PWM1.timerCount            = 100;     // 80 MHz / 100 = 800 kHz NZR period
PWM1.timerStartTimer       = true;
PWM1.peripheral.$assign    = "TIMA1";
PWM1.peripheral.ccp0Pin.$assign = "PB26";
PWM1.PWM_CHANNEL_0.initVal = "HIGH";
PWM1.PWM_CHANNEL_0.shadowUpdateMode = "ZERO_EVT";
```

## CRITICAL: Timer/PWM Must Be Started Manually

`SYSCFG_DL_init()` 不会自动启动定时器。**必须在 init 后显式调用 startCounter**：

```c
SYSCFG_DL_init();
DL_TimerG_startCounter(PWM_0_INST);         // PWM 定时器
DL_TimerA_startCounter(TIMER_TICK_INST);    // 周期中断定时器
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

## SysConfig PWM Module Crash (SDK 2.04 / SysConfig 1.27)

SDK 2.04.00.06 + SysConfig 1.27.0 下，PWM 模块使用单通道 `ccIndex=[1]` 时 `Common.js` 可能崩溃。如遇崩溃，改用代码手动初始化 TIMG PWM：

```c
DL_TimerG_reset(TIMG6);
DL_TimerG_enablePower(TIMG6);
delay_cycles(160);
DL_GPIO_initPeripheralOutputFunction(IOMUX_PINCM58, IOMUX_PINCM58_PF_TIMG6_CCP1);
DL_GPIO_enableOutput(GPIOB, DL_GPIO_PIN_27);
DL_TimerG_setClockConfig(TIMG6, &(DL_TimerG_ClockConfig){
    .clockSel = DL_TIMER_CLOCK_BUSCLK, .divideRatio = DL_TIMER_CLOCK_DIVIDE_1, .prescale = 0U});
DL_TimerG_initPWMMode(TIMG6, &(DL_TimerG_PWMConfig){
    .pwmMode = DL_TIMER_PWM_MODE_EDGE_ALIGN, .period = 16000,
    .isTimerWithFourCC = false, .startTimer = DL_TIMER_STOP});
DL_TimerG_setCounterControl(TIMG6, DL_TIMER_CZC_CCCTL1_ZCOND,
    DL_TIMER_CAC_CCCTL1_ACOND, DL_TIMER_CLC_CCCTL1_LCOND);
DL_TimerG_setCaptureCompareValue(TIMG6, 0, DL_TIMER_CC_1_INDEX);
DL_TimerG_enableClock(TIMG6);
DL_TimerG_setCCPDirection(TIMG6, DL_TIMER_CC1_OUTPUT);
```

升级到 SDK >= 2.05.01.01 可避免此问题。

## SysConfig Naming Rules

- All `$name` values must be **globally unique** across all instances and pins.
- Pin names within an instance are automatically prefixed: `GPIO_<instance>$name`_`<pin>$name`_PIN`
  - Example: instance `$name = "LEDS"`, pin `$name = "LED"` → `LEDS_LED_PIN`
- Avoid pin names that match their instance name (e.g. instance `$name = "LED"` with pin `$name = "LED"` causes `$name` collision).

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

`SYSCFG_DL_init()` 配置引脚和时钟后，**定时器计数器不会自动启动**。参见上文 [CRITICAL: Timer/PWM Must Be Started Manually](#critical-timerpwm-must-be-started-manually)。

### P3: EDGE_ALIGN_UP polarity is opposite to STM32 / some tutorials

SysConfig PWM 模块默认模式为 **EDGE_ALIGN_UP**，与 STM32 的 TIM ARR/CCR 方向相反（CC↓=更亮）。部分在线教程描述的是 EDGE_ALIGN_DOWN 行为，直接照搬会导致呼吸方向反转。详见上文 [Output Polarity](#output-polarity--critical)。
