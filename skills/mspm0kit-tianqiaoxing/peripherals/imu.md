# IMU (LSM6DS3) + Attitude Fusion on Tianqiaoxing G3519

**Driver**: `hardware/hw_lsm6ds3.c/h`
**Fusion**: `middle/FusionAhrs.c/h`, `FusionOffset.c/h`, `FusionConvention.h`, `FusionMath.h`

## Hardware

- Sensor: LSM6DS3TRC 6-axis (3-axis accel + 3-axis gyro)
- Interface: **Software I2C on PA0(SDA) / PA1(SCL)** — 与 OLED 共享同一 I2C 总线
- I2C Address: 0x6A (SA0 to GND)
- Fusion algorithm: AHRS (Mahony) — pitch/yaw/roll output

## Adding to OLED UI project

```bash
python scripts/scaffold_oled.py <name> --with-imu
```

This copies: `hw_lsm6ds3.c/h`, `FusionAhrs.c/h`, `FusionOffset.c/h`, `FusionConvention.h`, `FusionMath.h`, `mid_timer_stub.c/h`

## Key APIs

```c
#include "hw_lsm6ds3.h"
#include "FusionAhrs.h"

// Init (after SYSCFG_DL_init)
LSM6DS3_Init();
timer_init();

// Read sensor data
LSM6DS3_ReadAccel(&ax, &ay, &az);   // float, m/s²
LSM6DS3_ReadGyro(&gx, &gy, &gz);    // float, rad/s

// Run AHRS fusion (call at fixed interval, e.g. 10ms)
FusionAhrsUpdate(gx, gy, gz, ax, ay, az, dt);
float pitch = FusionAhrsGetPitch();  // degrees
float yaw   = FusionAhrsGetYaw();
float roll  = FusionAhrsGetRoll();
```

## Configuration

LSM6DS3 output rate and full-scale (init in `hw_lsm6ds3.c`):
- Accel: ±2g default, up to ±16g
- Gyro: ±245 dps default, up to ±2000 dps
- Registers: `CTRL1_XL` (0x10), `CTRL2_G` (0x11)

## Dependencies

- `myiic.c/h` (software I2C on PA0/PA1, shared with OLED)
- `mid_timer_stub.c/h` (5ms system tick via TIMA0)
