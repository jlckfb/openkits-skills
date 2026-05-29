# ADC on Tianmengxing G3507

## ADC Instances

| Instance | Status | Notes |
|----------|--------|-------|
| ADC0 | Free | 12-bit, up to 4 MSPS, 16 channels |
| ADC1 | Free | Secondary ADC, same spec |

## VREF 引脚说明

| Pin | 功能 | 限制 |
|-----|------|------|
| PA21 | VREF- | 串联电容到地，仅限 GPIO 使用 |
| PA23 | VREF+ | 串联电容到地，仅限 GPIO 使用 |

> PA21/PA23 串联了电容，用作 ADC 参考电压输入会产生问题。使用内部参考电压（VDDA）即可。

## SDK Examples

| Example | What It Does |
|---------|-------------|
| `adc12_single_conversion` | Single channel, interrupt-based, LED threshold |
| `adc12_sequence_conversion` | Multi-channel sequence |
| `adc12_triggered_by_timer_event` | Timer-triggered sampling |
| `adc12_internal_temp_sensor_mathacl` | Internal temperature sensor |

## Pin Mapping (LP → Tianmengxing)

SDK default: ADC0 ch12 on PA14, LED on PA0
Tianmengxing: PA0 free → LED can stay on PB22

## Recommended Free ADC Pins

Any free GPIO with ADC channel: PA0, PA1, PA3, PA4, PA8, PA9, PA12–PA17, PA22, PA24–PA26, PB2–PB5, PB12, PB13, PB15, PB16

## Generated Macros (example)

```
ADC12_0_INST              → ADC0
GPIO_LEDS_USER_LED_1_PIN  → DL_GPIO_PIN_22
ADC12_0_INST_INT_IRQN     → ADC0_INT_IRQn
```

## Key APIs

```c
DL_ADC12_startConversion(ADC12_0_INST);
gAdcResult = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_0);
DL_ADC12_enableConversions(ADC12_0_INST);
```

## Usage Pattern

1. scaffold from `adc12_single_conversion`
2. Replace SDK default LED pin with PB22 in .syscfg
3. Replace SDK default ADC pin with requested free pin
4. Build → flash → read serial output
