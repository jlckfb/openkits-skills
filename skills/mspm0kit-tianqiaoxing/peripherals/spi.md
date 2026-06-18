# SPI on Tianqiaoxing G3519

## Board SPI — W25Q64 Flash

| Pin | Function |
|-----|----------|
| PB9 | SCLK |
| PB8 | MOSI (PICO) |
| PB7 | MISO (POCI) |
| PB6 | CS (GPIO 手动控制) |

- Instance: SPI1
- Clock: **20 MHz**（需 CPUCLK ≥ 40 MHz，即 80 MHz 时钟下才能跑满速；32 MHz 下 SysConfig 会报 "input clock must be 2x faster"，需降到 ≤16 MHz）
- Mode: Motorola SPI Mode 3 (MOTO3, POL1/PHA1)
- Data: 8-bit, MSB first
- Chip: **W25Q64**（64 Mbit = 8 MB），批量产品标配

> 设备 ID（命令 0x90）：**0xEF16**（0xEF=Winbond, 0x16=W25Q64）。W25Q128 是 0xEF17。

Flash 分区（W25Q64 = 8 MB，最大地址 0x7FFFFF）：
| 地址范围 | 内容 |
|----------|------|
| 0x000000–0x03FFFF | HZK16 中文字库 (256 KB) |
| 0x040000–0x04A3FF | Unicode→GB2312 映射 (42 KB) |
| 0x050000–0x07FFFF | HZK12 中文字库 (192 KB) |
| 0x080000–0x0F7FFF | HZK20 中文字库 (480 KB) |
| 0x7FF000–0x7FFFFF | 系统参数 (4 KB，W25Q64 末尾扇区) |

> ⚠️ **分区注意**：参考全功能固件原本用 `0xFFF000` 存系统参数，那是 W25Q128（16 MB）的末尾。**W25Q64 只有 8 MB（最大 0x7FFFFF）**，`0xFFF000` 超界访问会回绕或失败。移植到 W25Q64 时，系统参数地址改为 **0x7FF000**（末尾扇区）。

## Key APIs

```c
// CS 控制
#define SPI_CS(x) ((x) ? DL_GPIO_setPins(FLASH_PORT, FLASH_CS_PIN) \
                       : DL_GPIO_clearPins(FLASH_PORT, FLASH_CS_PIN))

// 单字节读写
static uint8_t spi_xfer(uint8_t dat) {
    DL_SPI_transmitDataBlocking8(SPI_FLASH_INST, dat);
    while (DL_SPI_isBusy(SPI_FLASH_INST));
    return DL_SPI_receiveDataBlocking8(SPI_FLASH_INST);
}

// 读设备 ID（验证芯片在位）
uint16_t flash_read_id(void) {
    uint16_t id;
    SPI_CS(0);
    spi_xfer(0x90); spi_xfer(0); spi_xfer(0); spi_xfer(0);
    id  = spi_xfer(0xFF) << 8;
    id |= spi_xfer(0xFF);
    SPI_CS(1);
    return id;   // W25Q64 → 0xEF16
}
```

## Free SPI Instance

SPI0 可自由使用。推荐引脚：PA7(SCLK), PA8(MOSI), PA9(MISO), PA12(CS)。
