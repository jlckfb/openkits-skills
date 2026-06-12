# QEI Encoder on Tianqiaoxing G3519

**Driver**: `hw_encoder_qei.c` (hardware QEI backend, `USE_QEI_ENCODER = 1`)

## Hardware

- QEI: TIMG8 quadrature encoder on PA29(PHA/CCP0) / PA30(PHB/CCP1)
- Button: PA31 (PULL_UP, active-low press)
- Pins are optional — can be released if encoder not used

## Adding to OLED UI project

```bash
python scripts/scaffold_oled.py <name> --with-encoder
```

Copies: `hw_encoder_qei.c`, `hw_encoder.h`, `mid_timer_stub.c/h` (if not already present)

SysConfig addon: TIMG8 QEI + encoder SW button GPIO + TIMA0 5ms tick

## Generated Macros

```
QEI_ENCODER_INST              → TIMG8
GPIO_QEI_ENCODER_PHA_PIN      → DL_GPIO_PIN_29
GPIO_QEI_ENCODER_PHB_PIN      → DL_GPIO_PIN_30
ENC_SW_SW_PIN                 → DL_GPIO_PIN_31
```

## Key APIs

```c
#include "hw_encoder.h"

HW_Encoder_Init();        // init QEI + GPIO button
HW_Encoder_Enable();      // start counting
int16_t delta = HW_Encoder_GetDelta();  // read and clear accumulator
HW_Encoder_Disable();     // stop counting
```

## Direction Convention

`HW_Encoder_GetDelta()` 返回值方向约定：

| 旋转方向 | delta 符号 | UI 典型映射 |
|---------|-----------|-----------|
| 顺时针（从顶部看） | **正 (+)** | 菜单下移 / 数值增加 |
| 逆时针（从顶部看） | **负 (−)** | 菜单上移 / 数值减少 |

> **注意**：不同编码器的 A/B 相序可能相反。如果实际方向和 UI 显示方向不一致，取反 delta 即可：`delta = -HW_Encoder_GetDelta()`。优先和用户确认期望的方向映射。

## Dependencies

- `mid_timer.h` (5ms system tick for encoder polling)
- Requires TIMA0 periodic timer in syscfg (auto-added)
