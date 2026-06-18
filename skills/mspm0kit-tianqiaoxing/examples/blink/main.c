/**
 * LED Blink — Tianqiaoxing MSPM0G3519
 * PB22 onboard LED, active-low (SET=OFF, CLEAR=ON)
 * Default clock: 32 MHz (CPUCLK_FREQ = 32000000)
 */
#include "ti_msp_dl_config.h"

int main(void)
{
    SYSCFG_DL_init();

    while (1) {
        DL_GPIO_clearPins(GPIO_LED_PORT, GPIO_LED_PIN_PIN);   // LED ON
        delay_cycles(CPUCLK_FREQ / 1000 * 100);              // 100 ms
        DL_GPIO_setPins(GPIO_LED_PORT, GPIO_LED_PIN_PIN);     // LED OFF
        delay_cycles(CPUCLK_FREQ / 1000 * 100);              // 100 ms
    }
}
