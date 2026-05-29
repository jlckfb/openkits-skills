# Hardware I2C Pin Availability — Tianqiaoxing MSPM0G3519

Source: `外设引脚功能标注表.xlsx` (yellow cells = blocked/unusable)

## I2C0

| Function | Available Pins | Blocked Pins |
|----------|---------------|--------------|
| SDA | PA0, PA8, PA10, PA28, PB20, PB1 | PB22, PB18 |
| SCL | PA1, PA9, PA11, PA22, PA31 | PB1, PB17 |

**Default:** PA0(SDA) + PA1(SCL) — same pins as software I2C, shared by OLED + IMU

## I2C1

| Function | Available Pins | Blocked Pins |
|----------|---------------|--------------|
| SDA | PA3, PA10, PA16, PA30 | PA5, PA18, PA19(SWDIO) |
| SCL | PA4, PA11, PA15, PA17, PA29 | PA20(SWCLK), PB3 |

## I2C2

| Function | Available Pins | Blocked Pins |
|----------|---------------|--------------|
| SDA | PA16, PA24, PA30, PB16 | PB7, PB9, PB29 |
| SCL | PA29, PB15 | PA23, PB6, PB8, PB28 |

## Choosing Pins

1. Check `SKILL.md` Pin Table first — board-occupied pins take priority
2. From the remaining "available" pins above, pick a free pair (SDA+SCL)
3. I2C0 is the recommended instance (validated with OLED + IMU on PA0/PA1)
4. For external I2C sensors: prefer I2C1 on free pins to avoid bus contention

## Software vs Hardware I2C

| | Software I2C (default) | Hardware I2C (`--i2c hw`) |
|---|---|---|
| Implementation | GPIO bit-bang | `/ti/driverlib/I2C` + DMA |
| Speed | ~100 kHz | Up to 400 kHz |
| CPU usage | Blocks during transfer | DMA, non-blocking |
| Pin flexibility | Any GPIO | Must use I2C-function pins |
| SysConfig | GPIO module only | GPIO + I2C module |
