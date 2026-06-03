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

## SPI LCD Driver Notes (ST7789V / 兼容屏)

### CS 必须整块持低 — 适用于所有多字节命令（CRITICAL）

ST7789V 要求 **CS 在命令的全部参数字节期间保持低电平**。这不只是 Memory Write（0x2C），还包括 **CASET（0x2A）、RASET（0x2B）** 等所有多字节参数命令。逐字节翻转 CS 会截断参数，导致窗口设置无效。

```c
/* ❌ 错误：每字节独立翻转 CS（CASET/RASET 参数被截断，窗口偏移无效） */
lcd_write_cmd(0x2A);          // CS↓ CS↑
lcd_write_data16(x_start);     // CS↓ 发 2 字节 CS↑
lcd_write_data16(x_end);       // CS↓ 发 2 字节 CS↑  ← ST7789V 已截断，参数丢失

/* ✅ 正确：CASET/RASET 整块持低 */
void lcd_set_window(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
    uint16_t xe = x + w - 1;
    uint16_t ye = y + h - 1;
    lcd_cs_low();
    lcd_dc_cmd();
    DL_SPI_transmitDataBlocking8(SPI1, 0x2A);       // CASET
    lcd_dc_data();
    DL_SPI_transmitDataBlocking8(SPI1, x >> 8);      // 4 个参数字节
    DL_SPI_transmitDataBlocking8(SPI1, x & 0xFF);    // CS 全程保持低
    DL_SPI_transmitDataBlocking8(SPI1, xe >> 8);
    DL_SPI_transmitDataBlocking8(SPI1, xe & 0xFF);
    lcd_cs_high();
    // RASET 同样模式...
}
```

> **铁律**：任何需要多字节参数的命令（CASET、RASET、RAMWR），CS 必须在全部参数字节之间保持低电平。推荐分层设计：底层 `lcd_spi_cmd()`/`lcd_spi_data()` 只发数据不管 CS，上层命令函数统一管理 CS 翻转。

### CS 拉高前必须等待 SPI 发送完成

`DL_SPI_transmitDataBlocking8` 只等 TX FIFO 有空位，**不等移位寄存器完成**。最后 1-2 字节可能还在硬件中传输，立刻拉高 CS 会截断数据。

```c
// lcd_cs_high() 内部实现
void lcd_cs_high(void) {
    while (DL_SPI_isBusy(SPI_LCD_INST));  // 等移位寄存器清空
    DL_GPIO_setPins(LCD_CS_PORT, LCD_CS_PIN);
}
```

### SPI 帧格式 vs 传输 API — 必须匹配（CRITICAL）

SysConfig 中 SPI 帧格式和代码中的传输 API 必须一致。不匹配会导致花屏/乱码：

| SysConfig `dataSize` | 必须使用的 API | 不可用 |
|---------------------|---------------|--------|
| `DL_SPI_DATA_SIZE_8` | `DL_SPI_transmitDataBlocking8()` / `DL_SPI_fillTXFIFO8()` | ~~`DL_SPI_transmitDataBlocking16()`~~ |
| `DL_SPI_DATA_SIZE_16` | `DL_SPI_transmitDataBlocking16()` | ~~`DL_SPI_transmitDataBlocking8()`~~ |

> 8-bit 帧格式下调用 16-bit API 会产生未定义行为（屏幕花屏/乱码）。

### SPI API 选择指南

| API | 适用场景 | 行为 |
|-----|---------|------|
| `DL_SPI_transmitDataBlocking8(SPI, data)` | 单字节发送（LCD 命令/参数） | 阻塞等待一字节发送完成 |
| `DL_SPI_fillTXFIFO8(SPI, &buf, len)` | 批量数据（像素填充） | 填充 FIFO，需配合 `isBusy()` 检查完成 |

> LCD 驱动推荐：命令/参数用 `transmitDataBlocking8`（简单可靠），像素数据用 `fillTXFIFO8`（性能更好）。

### SysConfig SPI 属性类型陷阱

- **`dataSize` 是 number，不是 string**：写 `dataSize = 8`，**不要**写 `dataSize = "8"`
- **波特率属性名是 `targetBitRate`**，不是 `bitRate`
- **SPI 最大频率 = BUSCLK/2**：32MHz BUSCLK → 最高 16MHz。设 20MHz 会报 `input clock frequency must be at least 2x faster`

### LCD 全屏填充性能警告

`lcd_fill()` 全屏填充 170×320×2 = 108,800 字节，SPI 16MHz 下约需 **54ms**，默认 4MHz 约需 **218ms**。在 `while(1)` 主循环中每轮调用会导致其他实时任务（PWM 呼吸灯、按键轮询）严重阻塞。

```c
/* ❌ 错误：每轮都刷屏，呼吸灯被阻塞 */
while (1) {
    lcd_fill(color);    // 54-218ms 阻塞
    pwm_breathe();      // 永远得不到 CPU
}

/* ✅ 正确：仅在状态变化时刷屏 */
while (1) {
    if (pressed != last_state) {
        last_state = pressed;
        lcd_fill(pressed ? GREEN : RED);
    }
    pwm_breathe();
    delay_ms(5);
}
```

### ST7789V 170×320 面板参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 分辨率 | 170×320 | 可视区域 |
| GRAM | 240×320 | ST7789V 原生 |
| COL_OFFSET | **35** | `(240-170)/2`，CASET 需加此偏移 |
| ROW_OFFSET | 0 | 无需偏移 |
| MADCTL | 0x00 | 竖屏默认，如需旋转调整 MX/MY 位 |
| COLMOD | 0x55 | RGB565, 16-bit/pixel |

```c
#define LCD_WIDTH      170
#define LCD_HEIGHT     320
#define LCD_COL_OFFSET 35

void lcd_set_window(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
    uint16_t xe = x + LCD_COL_OFFSET + w - 1;
    uint16_t ye = y + h - 1;
    lcd_cs_low();
    lcd_cmd(0x2A);  // CASET
    lcd_dat(x + LCD_COL_OFFSET >> 8);
    lcd_dat((x + LCD_COL_OFFSET) & 0xFF);
    lcd_dat(xe >> 8);
    lcd_dat(xe & 0xFF);
    // RASET 类似...
    lcd_cs_high();
}
```

- 通过 SPI1 访问，CS 为 PB6 普通 GPIO
- 与 LCD 共享 SPI 总线，同一时间只能操作一个设备（通过各自的 CS 切换）
- W25Q64 容量 8MB，比天巧星的 W25Q128 (16MB) 小一半

### SysConfig SPI 属性名（SDK 版本差异）

SDK 2.10 使用旧命名 `mosiPin` / `misoPin`，**不是** `picoPin` / `pociPin`：

```js
// ✅ SDK 2.10 正确写法
SPI1.targetBitRate            = 16000000;  // 最大 BUSCLK/2
SPI1.dataSize                 = 8;          // number，不是 "8"
SPI1.peripheral.mosiPin.$assign = "PB8";   // 不是 picoPin
SPI1.peripheral.misoPin.$assign = "PB7";   // 不是 pociPin
SPI1.peripheral.sclkPin.$assign = "PB9";
```

- 通过 SPI1 访问，CS 为 PB6 普通 GPIO
- 与 LCD 共享 SPI 总线，同一时间只能操作一个设备（通过各自的 CS 切换）
- W25Q64 容量 8MB，比天巧星的 W25Q128 (16MB) 小一半
