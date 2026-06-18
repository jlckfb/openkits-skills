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

## 音高控制（mid_music 中间件）

MIDI 音符号 `note_t` → 频率表 `MusicNoteFrequency[]` → `Set_Musical_Note()` 换算 timer reload 值：

```
reload = 1_000_000 / freq_hz      // 1 MHz clock
duty   = reload / (100 - loud)     // loud=50 即 50% 占空
```

```c
// 常用频率：
NOTE_C4=262,  NOTE_D4=294,  NOTE_E4=330,  NOTE_F4=349,  NOTE_G4=392,
NOTE_A4=440,  NOTE_B4=494,  NOTE_C5=523,  NOTE_C6=1047
```

## 旋律播放（TONE 数组 + Beeper_Proc ISR）

**TONE 结构体**（音符 + 时长）：

```c
typedef struct { note_t Note; uint16_t Delay; } TONE;
// Delay 单位：10ms（由 Beeper_Proc 在 10ms ISR 中计数）
```

**播放旋律**（应用层调用一次即可，异步播放）：

```c
Beeper_Perform(BEEPER_KEYPRESS);   // 播放按键短音
Beeper_Perform(BEEPER_TRITONE);    // 播放三连音
Beeper_Perform(BEEPER_WARNING);    // 播放警告音
```

**10ms ISR 驱动**（必须在定时器中断中调）：

```c
void TIMER_TICK_IRQHandler(void) {
    Beeper_Proc();   /* 每 10ms 调用一次，自动推进音序器 */
}
```

## 预置旋律

| 名称 | 音符序列 | 含义 |
|------|---------|------|
| `BEEPER_KEYPRESS` | C6, 70ms | 按键短音 |
| `BEEPER_TRITONE` | B5→rest→D6→rest→F6, 0.21s | 三连上升音 |
| `BEEPER_WARNING` | F4×2, 0.14s | 两声短促警告 |
| `BEEP1` | C5-G5-A5-G5-F6-D8-C5, ~1.4s | 旋律 1 |
| `BEEP2` | C5-D5-C5...C5-B4-A4...E5-A5..., ~1.8s | 长旋律 |

## 自定义旋律

```c
#include "mid_music.h"

/* 用 CHECK_NOTE 结尾标记结束 */
const TONE myMelody[] = {
    {NOTE_C5, 10},    /* C5, 100ms */
    {NOTE_E5, 10},    /* E5, 100ms */
    {NOTE_G5, 15},    /* G5, 150ms */
    {CHECK_NOTE, 0}   /* end */
};

/* 触发播放 */
Beeper_Perform(myMelody);
```

## 注意

- `SYSCFG_DL_init()` 后定时器**不会自动启动**，`mid_music` 内部调用 `buzzer_on/off/set_*` 控制
- `Beeper_Proc()` 必须从 10ms 定时器 ISR 调用，和按键的 5ms tick 独立
- 同时只能播放一条旋律（`Beeper_Perform` 会覆盖当前播放）
