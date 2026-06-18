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

## 数据流：原始寄存器 → 角度

完整链路（参考固件验证）：

```c
#include "hw_lsm6ds3.h"
#include "FusionAhrs.h"

/* ---- 1. 初始化 ---- */
LSM6DS3_Init();
timer_init();       /* 5ms tick via TIMA0 */

/* ---- 2. 定时读取（如 10ms ISR 或主循环定时） ---- */
float ax, ay, az;   /* accel  m/s² */
float gx, gy, gz;   /* gyro   rad/s  */

LSM6DS3_ReadAccel(&ax, &ay, &az);
LSM6DS3_ReadGyro(&gx, &gy, &gz);

/* ---- 3. 运行 AHRS 融合（dt 单位：秒） ---- */
float dt = 0.01f;   /* 10ms */
FusionAhrsUpdate(gx, gy, gz, ax, ay, az, dt);

/* ---- 4. 获取欧拉角（度） ---- */
float pitch = FusionAhrsGetPitch();  /* X轴旋转，抬头为正 */
float yaw   = FusionAhrsGetYaw();    /* Z轴旋转，北向为0，随时间漂移 */
float roll  = FusionAhrsGetRoll();   /* Y轴旋转，右倾为正 */

/* 可选：融合四元数 */
FusionAhrs.quaternion.element;       /* w, x, y, z */
```

## 单位与坐标约定

| 量 | 函数 | 单位 | 范围 |
|----|------|------|------|
| 加速度 | `LSM6DS3_ReadAccel` | m/s² | ±2g（默认），可配 ±4/±8/±16g |
| 角速度 | `LSM6DS3_ReadGyro` | rad/s | ±245°/s（默认），可配 ±500/±1000/±2000°/s |
| 俯仰角 | `FusionAhrsGetPitch` | 度 (°) | -90 ~ +90 |
| 偏航角 | `FusionAhrsGetYaw` | 度 (°) | 0 ~ 360（累计漂移） |
| 滚转角 | `FusionAhrsGetRoll` | 度 (°) | -180 ~ +180 |

## 传感器配置

寄存器（`hw_lsm6ds3.c` 初始化中设置）：
- Accel: ±2g → `CTRL1_XL` (0x10)
- Gyro: ±245 dps → `CTRL2_G` (0x11)
- 状态寄存器 0x1E：bit0=accel ready, bit1=gyro ready

## Dependencies

- `myiic.c/h` (software I2C on PA0/PA1, shared with OLED)
- `mid_timer_stub.c/h` (5ms system tick via TIMA0)
