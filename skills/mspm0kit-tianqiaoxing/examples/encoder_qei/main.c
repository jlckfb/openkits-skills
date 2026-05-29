#include "ti_msp_dl_config.h"
#include "hw_encoder.h"
#include "mid_timer.h"

int main(void)
{
    SYSCFG_DL_init();
    timer_init();
    HW_Encoder_Init();
    HW_Encoder_Enable();

    int16_t last_delta = 0;
    while (1) {
        int16_t delta = HW_Encoder_GetDelta();
        if (delta != last_delta) {
            last_delta = delta;
            // Your encoder handler here
        }
    }
}
