#include "ti_msp_dl_config.h"
#include "hw_ws2812.h"
#include "hw_ws2812_effects.h"
#include "mid_timer_stub.h"

int main(void)
{
    SYSCFG_DL_init();
    timer_init();

    PWM_WS2812B_Init();
    WS2812_SetLEDCount(4);
    WS2812_SetBrightness(20);
    WS2812_SetMode(MODE_FLOW);

    while (1) {
        ws2812_effect_update();
    }
}
