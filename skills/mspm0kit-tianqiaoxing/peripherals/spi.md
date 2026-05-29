# SPI on Tianqiaoxing G3519

## SPI Instances

| Instance | Status | Tianqiaoxing Usage |
|----------|--------|--------------------|
| SPI0 | Free | Available on any free pins |
| SPI1 | Occupied | PB6(CS)/PB7(MISO)/PB8(MOSI)/PB9(SCLK) → W25Q128 Flash |

## SDK Example

`spi_controller_multibyte_fifo_poll` — SPI TX/RX via FIFO with polling

## Pin Mapping (LP → Tianqiaoxing)

SDK default: SPI1 on PB31(SCLK)/PB8(PICO)/PB7(POCI)/PB6(CS0)
Tianqiaoxing: SPI1 occupied by Flash → use SPI0 on free pins (e.g., PA7/PA8/PA9)

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
