# Buzzer on Tianqiaoxing G3519

## Hardware

- PWM: TIMG6 CCP1 on **PB27**
- Clock: 1 MHz (80 MHz / prescale 80)
- 控制方式：改 load value 调频率，改 CC value 调音量，start/stop 控制开关

## SysConfig 配置

```js
const PWM  = scripting.addModule("/ti/driverlib/PWM", {}, false);
const PWM1 = PWM.addInstance();

PWM1.$name                          = "BUZZER";
PWM1.pwmMode                        = "EDGE_ALIGN_UP";
PWM1.ccIndex                        = [1];
PWM1.clockPrescale                  = 80;       // 80 MHz / 80 = 1 MHz
PWM1.timerCount                     = 1000;     // 默认 1 kHz
PWM1.timerStartTimer                = false;    // 手动 start/stop
PWM1.peripheral.$assign             = "TIMG6";
PWM1.peripheral.ccp1Pin.$assign     = "PB27";
PWM1.PWM_CHANNEL_1.dutyCycle        = 50;
```

## Key APIs

```c
// 播放指定频率
void Beeper_SetFreq(uint32_t freq_hz) {
    uint32_t period = 1000000 / freq_hz;  // 1 MHz clock
    DL_TimerG_setLoadValue(BUZZER_INST, period);
    DL_TimerG_setCaptureCompareValue(BUZZER_INST, period / 2, DL_TIMER_CC_1_INDEX);
    DL_TimerG_startCounter(BUZZER_INST);
}

// 停止
void Beeper_Stop(void) {
    DL_TimerG_stopCounter(BUZZER_INST);
}
```

## 注意

- `SYSCFG_DL_init()` 后定时器**不会自动启动**，需要 `DL_TimerG_startCounter()` 显式开启
- 频率范围：约 100 Hz – 20 kHz（1 MHz / period）
