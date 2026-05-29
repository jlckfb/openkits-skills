
#include "ti_msp_dl_config.h"
#include "hw_delay.h"
#include "OLED_UI.h"

extern MenuPage MainMenuPage;

int main(void)
{
    SYSCFG_DL_init();

    OLED_Init();
    OLED_Clear();
    OLED_ShowString(0, 0, "OLED UI Framework", OLED_8X16_HALF);  // ASCII 8x16 half-width
    OLED_ShowString(0, 16, "TianQiaoXing G3519", OLED_8X16_HALF);  // ASCII 8x16 half-width
    OLED_Update();
    delay_cycles(16000000);

    OLED_UI_Init(&MainMenuPage);

    while (1) {
        OLED_UI_MainLoop();
    }
}