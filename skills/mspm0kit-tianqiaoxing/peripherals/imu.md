# IMU (LSM6DS3) + Attitude Fusion on Tianqiaoxing G3519

**Driver**: `hardware/hw_lsm6ds3.c/h`
**Fusion**: `middle/FusionAhrs.c/h`, `FusionOffset.c/h`, `FusionConvention.h`, `FusionMath.h`

## Hardware

- Sensor: LSM6DS3 6-axis (3-axis accel + 3-axis gyro)
- Interface: Software I2C on PA28(SDA) / PA27(SCL)
- I2C Address: 0x6A (SA0 to GND)
- Fusion algorithm: AHRS (Mahony) — pitch/yaw/roll output

## Adding to OLED UI project

```bash
python scripts/scaffold_oled.py <name> --with-imu
```

This copies: `hw_lsm6ds3.c/h`, `FusionAhrs.c/h`, `FusionOffset.c/h`, `FusionConvention.h`, `FusionMath.h`, `mid_timer_stub.c/h`

And adds to `.syscfg`: GPIO pins for IMU I2C (PA27/PA28) + TIMA0 5ms periodic timer.

## Generated Macros (from syscfg)

```
IMU_SDA_PIN         → DL_GPIO_PIN_28
IMU_SCL_PIN         → DL_GPIO_PIN_27
TIMER_TICK_INST     → TIMA0
TIMER_TICK_INST_INT_IRQN → TIMA0_INT_IRQn
```

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

LSM6DS3 output rate and full-scale are set at init in `hw_lsm6ds3.c`:
- Accel: ±2g default, up to ±16g
- Gyro: ±245 dps default, up to ±2000 dps
- Change via registers: `CTRL1_XL`, `CTRL2_G`

## Dependencies

- `myiic.c/h` (software I2C, shared with OLED)
- `mid_timer_stub.c/h` (5ms system tick via TIMA0)
