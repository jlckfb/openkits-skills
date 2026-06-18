# I2C on Tianqiaoxing G3519

## Board I2C Bus

| 引脚 | 功能 | 方式 | 设备 |
|------|------|------|------|
| PA0 (SDA) | I2C 数据线 | **软件 I2C**（GPIO 位模拟） | OLED + IMU (LSM6DS3) 共享总线 |
| PA1 (SCL) | I2C 时钟线 | **软件 I2C**（GPIO 位模拟） | 同上 |

板载 2.2kΩ 上拉电阻。OLED 和 IMU 在同一条 I2C 总线上（不是两组独立总线）。

## Software I2C 实现

固件使用 GPIO open-drain 模拟：

```c
#define IIC_SDA_H()    DL_GPIO_setPins(GPIOA, DL_GPIO_PIN_0)
#define IIC_SDA_L()    DL_GPIO_clearPins(GPIOA, DL_GPIO_PIN_0)
#define IIC_SCL_H()    DL_GPIO_setPins(GPIOA, DL_GPIO_PIN_1)
#define IIC_SCL_L()    DL_GPIO_clearPins(GPIOA, DL_GPIO_PIN_1)
#define IIC_SDA_READ() DL_GPIO_readPins(GPIOA, DL_GPIO_PIN_0)
```

## Hardware I2C（可选）

I2C0 也可配为硬件模式（400 kHz），使用 `scaffold_oled.py --i2c hw`。

硬件 I2C 参数：
- Bus Clock: 40 MHz
- Speed: 400 kHz
- Digital Glitch Filter: 8-clock width

## I2C 设备地址

| 设备 | 地址 | 备注 |
|------|------|------|
| OLED (SSD1306/SSD1312) | 0x3C | 128×64 单色 |
| LSM6DS3TRC IMU | 0x6A | SA0 接地 |

## 自由 I2C 引脚

如需额外 I2C 总线，推荐：PA12(SCL)/PA13(SDA) 或 PA3(SCL)/PA4(SDA)。
