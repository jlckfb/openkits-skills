# SPI on Tianmengxing G3507

## SPI Instances

| Instance | Status | Tianmengxing Usage |
|----------|--------|--------------------|
| SPI0 | Free | Available on any free pins |
| SPI1 | Occupied (shared) | PB6(CS)/PB7(MISO)/PB8(MOSI)/PB9(SCLK) → W25Q64 Flash + LCD 接口 |

## Onboard SPI1 — Shared Bus

SPI1 被板载 Flash（W25Q64）和 LCD 接口共用：

| Pin | Flash 功能 | LCD 功能 |
|-----|-----------|---------|
| PB6 | CS（GPIO 控制） | — |
| PB7 | MISO (POCI) | — |
| PB8 | MOSI (PICO) | LCD_SDA |
| PB9 | SCLK | LCD_SCL |

LCD 独立控制引脚：

| Pin | LCD 功能 |
|-----|---------|
| PB10 | RES（复位） |
| PB11 | DC（数据/命令） |
| PB14 | CS（片选） |
| PB26 | BLK（背光） |

> LCD 接口默认排序：GND, VCC, SCL, SDA, RES, DC, CS, BLK。可通过 0Ω 电阻切换 VCC/GND 顺序。

## SDK Example

`spi_controller_multibyte_fifo_poll` — SPI TX/RX via FIFO with polling

## Pin Mapping (LP → Tianmengxing)

SDK default: SPI1 on PB31(SCLK)/PB8(PICO)/PB7(POCI)/PB6(CS0)
Tianmengxing: SPI1 occupied by Flash + LCD → use **SPI0** on free pins for external devices

## Recommended Free Pins for SPI0

SCLK: PA7, MOSI(PICO): PA8, MISO(POCI): PA9, CS: PA12 (GPIO)

## Generated Macros (example)

```
SPI_0_INST                → SPI0
GPIO_SPI_0_SCLK_PIN       → DL_GPIO_PIN_7
GPIO_SPI_0_PICO_PIN       → DL_GPIO_PIN_8
GPIO_SPI_0_POCI_PIN       → DL_GPIO_PIN_9
```

## Key APIs

```c
DL_SPI_fillTXFIFO8(SPI_0_INST, &txData, len);
while (DL_SPI_isBusy(SPI_0_INST));
rxData = DL_SPI_receiveDataBlocking8(SPI_0_INST);
```

## W25Q64 Flash Notes

- 通过 SPI1 访问，CS 为 PB6 普通 GPIO
- 与 LCD 共享 SPI 总线，同一时间只能操作一个设备（通过各自的 CS 切换）
- W25Q64 容量 8MB，比天巧星的 W25Q128 (16MB) 小一半
