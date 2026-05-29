# I2C on Tianqiaoxing G3519

## I2C Instances

| Instance | Status | Tianqiaoxing Usage |
|----------|--------|--------------------|
| I2C0 (Hardware) | Free | Available on any free pins |
| I2C1 (Hardware) | Free | Available on any free pins |
| Software I2C (PA0/PA1) | Occupied | OLED SSD1312 (2.2kΩ pull-up) |
| Software I2C (PA27/PA28) | Occupied | LSM6DS3 IMU |

## SDK Example

`i2c_controller_rw_multibyte_fifo_poll` — I2C controller read/write via FIFO polling

## Pin Mapping (LP → Tianqiaoxing)

SDK default: I2C2 on PC2(SCL)/PC3(SDA)
Tianqiaoxing: PC2/PC3 not available on LQFP-64 → use I2C0 on free pins

## Recommended Free Pins for Hardware I2C

PA12(SCL) / PA13(SDA) or PA3(SCL) / PA4(SDA)

## Generated Macros (example)

```
I2C_0_INST       → I2C0
GPIO_I2C_0_SDA_PIN → DL_GPIO_PIN_13
GPIO_I2C_0_SCL_PIN → DL_GPIO_PIN_12
```

## Key APIs

```c
DL_I2C_fillControllerTXFIFO(I2C_0_INST, &txData, len);
DL_I2C_startControllerTransfer(I2C_0_INST, addr, DL_I2C_CONTROLLER_DIRECTION_RX, len);
while (DL_I2C_isControllerBusy(I2C_0_INST));
rxData = DL_I2C_receiveControllerData(I2C_0_INST);
```
