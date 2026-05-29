#include "ti_msp_dl_config.h"
#include "hw_lsm6ds3.h"
#include "myiic.h"
#include "mid_timer_stub.h"
#include "FusionAhrs.h"
#include <math.h>

int main(void)
{
    SYSCFG_DL_init();
    timer_init();

    /* Init software I2C for IMU */
    IMU_I2C_Init();
    LSM6DS3_Init();

    float ax, ay, az, gx, gy, gz;
    while (1) {
        LSM6DS3_ReadAccel(&ax, &ay, &az);
        LSM6DS3_ReadGyro(&gx, &gy, &gz);

        /* Simple AHRS fusion at ~100Hz */
        FusionAhrsUpdate(gx, gy, gz, ax, ay, az, 0.01f);

        float pitch = FusionAhrsGetPitch();
        float roll  = FusionAhrsGetRoll();

        (void)pitch; (void)roll;
        delay_cycles(800000); /* ~10ms delay at 80MHz */
    }
}
