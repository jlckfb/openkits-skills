# ADC on Tianqiaoxing G3519

## ADC Instances

| Instance | Status | Notes |
|----------|--------|-------|
| ADC0 | Free | 12-bit, up to 4 MSPS, 16 channels |
| ADC1 | Free | Secondary ADC, same spec |

## SDK Examples

| Example | What It Does |
|---------|-------------|
| `adc12_single_conversion` | Single channel, interrupt-based |
| `adc12_sequence_conversion` | Multi-channel sequence |
| `adc12_triggered_by_timer_event` | Timer-triggered sampling |
| `adc12_internal_temp_sensor_mathacl` | Internal temperature sensor |

## Recommended Free ADC Pins

PA3, PA4, PA8, PA9, PA12–PA17, PA22, PA23, PA25–PA28, PB2–PB5, PB10–PB16, PB25

> PA24/PB24 已被按键占用，不可用于 ADC。

## Key APIs

```c
DL_ADC12_startConversion(ADC12_0_INST);
uint16_t result = DL_ADC12_getMemResult(ADC12_0_INST, DL_ADC12_MEM_IDX_0);
DL_ADC12_enableConversions(ADC12_0_INST);
```

## Usage Pattern

1. scaffold from `adc12_single_conversion`
2. Edit .syscfg: replace PA0 LED → PB22, replace ADC pin → your free pin
3. Build → flash → read serial output
