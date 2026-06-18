#include "app_key_task.h"
#include "stdio.h"
#include "mid_button.h"
#include "hw_key.h"
#include "mid_music.h"

/*user_add_handle*/
static Button key0;
static Button key1;
static Button key2;

/*user_add_param*/
KEY_MENU_STATUS key_menu = {1, 1, 1, 1};

uint8_t read_button_gpio(uint8_t button_id)
{
    switch (button_id) {
        case 0: return key_scan().back;
        case 1: return key_scan().enter;
        case 2: return key_scan().encoder_sw;
        default: return 1;
    }
}

/*user_add_funtion*/
void user_keyBSP_init(void)
{
    button_init(&key0, read_button_gpio, 0, 0);
    button_init(&key1, read_button_gpio, 0, 1);
    button_init(&key2, read_button_gpio, 0, 2);

    button_attach(&key0, BTN_PRESS_UP,         (BtnCallback)key0_press_up_Handler);
    button_attach(&key0, BTN_LONG_PRESS_START, (BtnCallback)key0_long_press_start_Handler);
    button_attach(&key0, BTN_SINGLE_CLICK,     (BtnCallback)key0_single_click_Handler);
    button_attach(&key0, BTN_PRESS_REPEAT,     (BtnCallback)key0_press_repeat_Handler);

    button_attach(&key1, BTN_PRESS_UP,         (BtnCallback)key1_press_up_Handler);
    button_attach(&key1, BTN_LONG_PRESS_START, (BtnCallback)key1_long_press_start_Handler);
    button_attach(&key1, BTN_SINGLE_CLICK,     (BtnCallback)key1_single_click_Handler);
    button_attach(&key1, BTN_PRESS_REPEAT,     (BtnCallback)key1_press_repeat_Handler);

    button_attach(&key2, BTN_PRESS_UP,         (BtnCallback)key2_press_up_Handler);
    button_attach(&key2, BTN_SINGLE_CLICK,     (BtnCallback)key2_single_click_Handler);
    button_attach(&key2, BTN_LONG_PRESS_START, (BtnCallback)key2_long_press_start_Handler);

    button_start(&key0);
    button_start(&key1);
    button_start(&key2);
}

void key0_press_up_Handler(void *btn)
{
    key_menu.back = RELEASE;
    key_menu.up = RELEASE;
}

void key0_press_repeat_Handler(void *btn)
{
    key_menu.back = RELEASE;
    key_menu.up = PRESS;
    Beeper_Perform(BEEPER_KEYPRESS);
}

void key0_single_click_Handler(void *btn)
{
    key_menu.back = RELEASE;
    key_menu.up = PRESS;
    Beeper_Perform(BEEPER_KEYPRESS);
}

void key0_long_press_start_Handler(void *btn)
{
    key_menu.back = PRESS;
    key_menu.up = RELEASE;
    Beeper_Perform(BEEPER_WARNING);
}

void key1_press_up_Handler(void *btn)
{
    key_menu.enter = RELEASE;
    key_menu.down = RELEASE;
}

void key1_press_repeat_Handler(void *btn)
{
    key_menu.enter = RELEASE;
    key_menu.down = PRESS;
    Beeper_Perform(BEEPER_KEYPRESS);
}

void key1_single_click_Handler(void *btn)
{
    key_menu.enter = RELEASE;
    key_menu.down = PRESS;
    Beeper_Perform(BEEPER_KEYPRESS);
}

void key1_long_press_start_Handler(void *btn)
{
    key_menu.enter = PRESS;
    key_menu.down = RELEASE;
    Beeper_Perform(BEEPER_TRITONE);
}

/* encoder SW button */
void key2_press_up_Handler(void *btn)
{
    key_menu.enter = RELEASE;
    key_menu.back = RELEASE;
}

void key2_single_click_Handler(void *btn)
{
    key_menu.enter = PRESS;
    key_menu.back = RELEASE;
    Beeper_Perform(BEEPER_TRITONE);
}

void key2_long_press_start_Handler(void *btn)
{
    key_menu.enter = RELEASE;
    key_menu.back = PRESS;
    Beeper_Perform(BEEPER_WARNING);
}
