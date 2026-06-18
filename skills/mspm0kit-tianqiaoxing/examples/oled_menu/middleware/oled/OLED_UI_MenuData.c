#include "OLED_UI_MenuData.h"
#include "OLED_UI.h"
#include "mid_music.h"
#include "stdio.h"

/*此文件用于存放菜单数据。实际上菜单数据可以存放在任何地方，存放于此处是为了规范与代码模块化*/

extern bool ColorMode;
extern bool OLED_UI_ShowFps;
extern BEEPER_Tag Beeper0;
extern int16_t OLED_UI_Brightness;

/* Simple helper: toggle a bool variable */
void ToggleColorMode(void) { ColorMode = !ColorMode; }

/* ---- Window definitions ---- */

MenuWindow SetBrightnessWindow = {
    .General_Width          = 80,
    .General_Height         = 28,
    .General_ContinueTime   = 4.0,
    .General_WindowType     = WINDOW_ROUNDRECTANGLE,
    .Text_String            = "Backlight",
    .Text_FontSize          = OLED_UI_FONT_12,
    .Text_FontSideDistance  = 4,
    .Text_FontTopDistance   = 3,
    .Prob_Data_Int_16       = &OLED_UI_Brightness,
    .Prob_DataStep          = 1,
    .Prob_MinData           = 0,
    .Prob_MaxData           = 255,
    .Prob_BottomDistance    = 2,
    .Prob_SideDistance      = 4,
    .Prob_LineHeight        = 6,
};

/* ---- Window functions ---- */

void BrightnessWindow(void) { OLED_UI_CreateWindow(&SetBrightnessWindow); }
void EmptyWindow(void)      { /* No-op demo window */ }

/* ---- MenuItem arrays ---- */

MenuItem MainMenuItems[] = {
    {"Brightness",  BrightnessWindow, NULL, NULL, NULL},
    {"Show FPS",   NULL, NULL, &OLED_UI_ShowFps, NULL},
    {"Color Mode", ToggleColorMode, NULL, &ColorMode, NULL},
    {"More",        NULL, &MoreMenuPage, NULL, NULL},
    {"About",       EmptyWindow, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL},  /* Terminator */
};

MenuItem SettingsMenuItems[] = {
    {"Brightness",  BrightnessWindow, NULL, NULL, NULL},
    {"Buzzer Vol", NULL, NULL, &Beeper0.Beeper_Enable, NULL},
    {"Show FPS",   NULL, NULL, &OLED_UI_ShowFps, NULL},
    {"Color Mode", ToggleColorMode, NULL, &ColorMode, NULL},
    {"Back",        NULL, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL},
};

MenuItem MoreMenuItems[] = {
    {"Font 8 Demo", NULL, &Font8MenuPage, NULL, NULL},
    {"Font 12 Demo", NULL, &Font12MenuPage, NULL, NULL},
    {"Long Menu",   NULL, &LongMenuPage, NULL, NULL},
    {"Back",        NULL, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL},
};

MenuItem AboutOLED_UIMenuItems[] = {
    {"OLED_UI",  EmptyWindow, NULL, NULL, NULL},
    {"FloatTest", EmptyWindow, NULL, NULL, NULL},
    {"IntTest",  EmptyWindow, NULL, NULL, NULL},
    {"Back",     NULL, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL},
};

/* Font demo menu items */
MenuItem Font8MenuItems[]  = { {"Sample 8",  EmptyWindow, NULL, NULL, NULL}, {"Back", NULL, NULL, NULL, NULL}, {NULL, NULL, NULL, NULL, NULL} };
MenuItem Font12MenuItems[] = { {"Sample 12", EmptyWindow, NULL, NULL, NULL}, {"Back", NULL, NULL, NULL, NULL}, {NULL, NULL, NULL, NULL, NULL} };
MenuItem Font16MenuItems[] = { {"Sample 16", EmptyWindow, NULL, NULL, NULL}, {"Back", NULL, NULL, NULL, NULL}, {NULL, NULL, NULL, NULL, NULL} };
MenuItem Font20MenuItems[] = { {"Sample 20", EmptyWindow, NULL, NULL, NULL}, {"Back", NULL, NULL, NULL, NULL}, {NULL, NULL, NULL, NULL, NULL} };

/* Long menu demo */
MenuItem LongMenuItems[] = {
    {"Item 01", EmptyWindow, NULL, NULL, NULL},
    {"Item 02", EmptyWindow, NULL, NULL, NULL},
    {"Item 03", EmptyWindow, NULL, NULL, NULL},
    {"Item 04", EmptyWindow, NULL, NULL, NULL},
    {"Item 05", EmptyWindow, NULL, NULL, NULL},
    {"Item 06", EmptyWindow, NULL, NULL, NULL},
    {"Item 07", EmptyWindow, NULL, NULL, NULL},
    {"Item 08", EmptyWindow, NULL, NULL, NULL},
    {"Item 09", EmptyWindow, NULL, NULL, NULL},
    {"Item 10", EmptyWindow, NULL, NULL, NULL},
    {"Back",    NULL, NULL, NULL, NULL},
    {NULL, NULL, NULL, NULL, NULL},
};

MenuItem SpringMenuItems[]  = { {"Spring 1", EmptyWindow, NULL, NULL, NULL}, {"Spring 2", EmptyWindow, NULL, NULL, NULL}, {"Back", NULL, NULL, NULL, NULL}, {NULL, NULL, NULL, NULL, NULL} };
MenuItem SmallAreaMenuItems[] = { {"Small 1", EmptyWindow, NULL, NULL, NULL}, {"Back", NULL, NULL, NULL, NULL}, {NULL, NULL, NULL, NULL, NULL} };

/* ---- MenuPage definitions ---- */

MenuPage MainMenuPage = {
    .General_MenuType     = MENU_TYPE_LIST,
    .General_MovingSpeed  = 0,
    .General_CursorStyle  = 0,
    .General_MoveStyle    = 0,
    .General_FontSize     = OLED_UI_FONT_8,
    .General_ParentMenuPage = NULL,
    .General_MenuItems    = MainMenuItems,
    .General_LineSpace    = 2,
};

MenuPage SettingsMenuPage = {
    .General_MenuType     = MENU_TYPE_LIST,
    .General_FontSize     = OLED_UI_FONT_8,
    .General_ParentMenuPage = &MainMenuPage,
    .General_MenuItems    = SettingsMenuItems,
};

MenuPage MoreMenuPage = {
    .General_MenuType     = MENU_TYPE_LIST,
    .General_FontSize     = OLED_UI_FONT_8,
    .General_ParentMenuPage = &MainMenuPage,
    .General_MenuItems    = MoreMenuItems,
};

MenuPage AboutOLED_UIMenuPage = {
    .General_MenuType     = MENU_TYPE_LIST,
    .General_FontSize     = OLED_UI_FONT_8,
    .General_ParentMenuPage = &MainMenuPage,
    .General_MenuItems    = AboutOLED_UIMenuItems,
};

MenuPage Font8MenuPage  = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_8,  .General_MenuItems = Font8MenuItems };
MenuPage Font12MenuPage = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_12, .General_MenuItems = Font12MenuItems };
MenuPage Font16MenuPage = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_16, .General_MenuItems = Font16MenuItems };
MenuPage Font20MenuPage = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_20, .General_MenuItems = Font20MenuItems };
MenuPage LongMenuPage    = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_8,  .General_MenuItems = LongMenuItems };
MenuPage SpringMenuPage  = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_8,  .General_MenuItems = SpringMenuItems };
MenuPage LongListMenuPage = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_8,  .General_MenuItems = LongListMenuItems };
MenuPage SmallAreaMenuPage = { .General_MenuType = MENU_TYPE_LIST, .General_FontSize = OLED_UI_FONT_8, .General_MenuItems = SmallAreaMenuItems };
