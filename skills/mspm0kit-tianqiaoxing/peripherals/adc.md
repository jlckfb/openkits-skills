# ADC on Tianqiaoxing G3519

## ADC Instances

| Instance | Status | Notes |
|----------|--------|-------|
| ADC0 | Free | 12-bit, up to 4 MSPS, 16 channels |
| ADC1 | Free | Secondary ADC, same spec |

## SDK Examples

| Example | What It Does |
|---------|-------------|
| `adc12_single_conversion` | Single channel, interrupt-based, LED threshold |
| `adc12_sequence_conversion` | Multi-channel sequence |
| `adc12_triggered_by_timer_event` | Timer-triggered sampling |
| `adc12_internal_temp_sensor_mathacl` | Internal temperature sensor |

## Pin Mapping (LP → Tianqiaoxing)

SDK default: ADC0 ch12 on PA14, LED on PA0
Tianqiaoxing: PA0 occupied by OLED → LED moved to PB22

## Recommended Free ADC Pins

Any free GPIO with ADC channel: PA3, PA4, PA8, PA9, PA12–PA17, PA22–PA26, PB2–PB5, PB10–PB16, PB24, PB25

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
2. Replace PA0 LED with PB22 in .syscfg
3. Replace PA14 ADC pin with requested free pin
4. Build → flash → read serial output
