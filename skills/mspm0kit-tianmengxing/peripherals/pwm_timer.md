# PWM / Timer on Tianmengxing G3507

## SDK Examples

| Example | What It Does |
|---------|-------------|
| `timg_32bit_timer_mode_pwm_edge_sleep` | 32-bit PWM edge-aligned with sleep |
| `tima_timer_mode_periodic_repeat_count` | Periodic timer with repeat count |

## Pin Mapping (LP → Tianmengxing)

SDK uses TIMG12 on PB6(C0)/PB7(C1).
Tianmengxing: PB6/PB7 occupied by SPI Flash → use TIMG0 or TIMG2 on free pins.

## Available Timer Instances

| Timer | Status | Tianmengxing Usage |
|-------|--------|--------------------|
| TIMA0 | Free | System tick, PWM, capture |
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
| For PWM output (breathing LED, servo, etc.) | For periodic interrupts (tick, timeout) |
| No `timerMode` — PWM mode is implicit | `timerMode`: `ONE_SHOT / PERIODIC / ...` (NO `EDGE_ALIGN_PWM`) |
| `clockPrescale` (one value) | `timerClkDiv` + `timerClkPrescale` (two values) |
| `timerCount` (pure number) | `timerPeriod` (string, e.g. `"5 ms"`) |
| Channels: `PWM_CHANNEL_0.dutyCycle` | No PWM channels |

## SysConfig JS Snippets

### PWM output (1 kHz, 50% duty on TIMG0 free pin)

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

## SysConfig Naming Rules

- All `$name` values must be **globally unique** across all instances and pins.
- Pin names within an instance are automatically prefixed: `GPIO_<instance>$name`_`<pin>$name`_PIN`
  - Example: instance `$name = "LEDS"`, pin `$name = "LED"` → `LEDS_LED_PIN`
- Avoid pin names that match their instance name (e.g. instance `$name = "LED"` with pin `$name = "LED"` causes `$name` collision).
