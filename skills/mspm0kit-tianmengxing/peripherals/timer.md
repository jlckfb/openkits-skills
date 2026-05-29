# Timer on Tianmengxing G3507

For PWM output, see [pwm.md](pwm.md). This doc covers periodic interrupt timers.

## SDK Example

`tima_timer_mode_periodic_repeat_count` — Periodic timer with repeat count

## Available Timer Instances for Periodic Interrupt

| Timer | Status | Tianmengxing Usage |
|-------|--------|--------------------|
| TIMA0 | Free | System tick, periodic interrupt |
| TIMA1 | Free | Periodic interrupt |
| TIMG0–TIMG12 | Free | Dual-use (PWM or timer, not both) |

## Periodic Interrupt Config Pattern (5 ms tick)

```
Timer instance: TIMA0
Clock divider: 8
Prescale: 10
Result: 80 MHz / 8 / 10 = 1 MHz → 5000 counts = 5 ms
Interrupt: ZERO (fires when counter reaches 0)
Priority: 3
```

## Generated Macros (example)

```
TIMER_TICK_INST               → TIMA0
TIMER_TICK_INST_IRQHandler    → TIMA0_IRQHandler
TIMER_TICK_INST_LOAD_VALUE    → 4999
```

## SysConfig JS Snippet (Periodic timer interrupt, 5 ms)

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

## Key APIs

```c
DL_TimerA_startCounter(TIMER_TICK_INST);
// ISR: void TIMA0_IRQHandler(void) { ... }
```

## Usage Pattern

1. scaffold from `tima_timer_mode_periodic_repeat_count`
2. Configure timer period and clock dividers in .syscfg
3. Add interrupt handler in main.c or app code
4. Build → flash → test with LED toggle or UART output
