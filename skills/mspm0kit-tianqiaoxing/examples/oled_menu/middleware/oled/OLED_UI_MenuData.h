#ifndef __OLED_UI_MENUDATA_H
#define __OLED_UI_MENUDATA_H
#ifdef __cplusplus
extern "C" {
#endif
#include "OLED_UI.h"

extern MenuItem MainMenuItems[], SettingsMenuItems[], MoreMenuItems[], AboutOLED_UIMenuItems[];
extern MenuItem Font8MenuItems[], Font12MenuItems[], Font16MenuItems[], Font20MenuItems[];
extern MenuItem LongMenuItems[], SpringMenuItems[], SmallAreaMenuItems[];
extern MenuPage MainMenuPage, SettingsMenuPage, AboutOLED_UIMenuPage, MoreMenuPage;
extern MenuPage Font8MenuPage, Font12MenuPage, Font16MenuPage, Font20MenuPage;
extern MenuPage LongMenuPage, SpringMenuPage, LongListMenuPage, SmallAreaMenuPage;

void BrightnessWindow(void);
void EmptyWindow(void);

#ifdef __cplusplus
}
#endif
#endif
