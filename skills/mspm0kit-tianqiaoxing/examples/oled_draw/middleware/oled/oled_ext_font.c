/**
 * oled_ext_font.c — built-in font version (NO external Flash required)
 * Uses OLED_CF12x12/16x16/20x20 bitmaps from OLED_Fonts.c instead of W25Q128 Flash.
 */
#include "oled_ext_font.h"
#include "OLED.h"
#include "OLED_Fonts.h"
#include <string.h>

extern int Unicode_to_GB2312(uint16_t unicode, uint8_t *gb_high, uint8_t *gb_low);

static void ExtFont_GetParams(uint8_t fontSize, uint32_t* baseAddr, uint8_t* charSize) {
    (void)baseAddr;
    if (fontSize == 12) *charSize = 24;
    else if (fontSize == 20) *charSize = 60;
    else *charSize = 32;
}

void ExtFont_ReadChinese(uint8_t high, uint8_t low, uint8_t* buf, uint8_t fontSize) {
    char index_str[4];
    index_str[0] = (char)high;
    index_str[1] = (char)low;
    index_str[2] = '\0';
    if (fontSize == 12) {
        int i = 0;
        while (OLED_CF12x12[i].Index[0] != '\0') {
            if (strcmp(OLED_CF12x12[i].Index, index_str) == 0) {
                memcpy(buf, OLED_CF12x12[i].Data, 24); return;
            }
            i++;
        }
    } else if (fontSize == 16) {
        int i = 0;
        while (OLED_CF16x16[i].Index[0] != '\0') {
            if (strcmp(OLED_CF16x16[i].Index, index_str) == 0) {
                memcpy(buf, OLED_CF16x16[i].Data, 32); return;
            }
            i++;
        }
    } else {
        int i = 0;
        while (OLED_CF20x20[i].Index[0] != '\0') {
            if (strcmp(OLED_CF20x20[i].Index, index_str) == 0) {
                memcpy(buf, OLED_CF20x20[i].Data, 60); return;
            }
            i++;
        }
    }
    memset(buf, 0, (fontSize == 12) ? 24 : (fontSize == 16) ? 32 : 60);
}

static int8_t ExtFont_NextChinese(char** str, uint8_t* gb_high, uint8_t* gb_low)
{
    uint8_t b0 = (uint8_t)**str;
    if (b0 == '\0') return -1;
    if ((b0 & 0xF0) == 0xE0) {
        uint8_t b1 = (uint8_t)(*str)[1], b2 = (uint8_t)(*str)[2];
        if (b1 == '\0' || b2 == '\0') return -1;
        uint16_t unicode = ((uint16_t)(b0 & 0x0F) << 12) | ((uint16_t)(b1 & 0x3F) << 6) | (uint16_t)(b2 & 0x3F);
        *str += 3;
        if (Unicode_to_GB2312(unicode, gb_high, gb_low) == 0) return 0;
        return -1;
    }
    if (b0 >= 0xA1) {
        uint8_t b1 = (uint8_t)(*str)[1];
        if (b1 == '\0') return -1;
        *gb_high = b0; *gb_low = b1; *str += 2;
        return 0;
    }
    return 1;
}

void OLED_ShowChineseExt(int16_t X, int16_t Y, char *Chinese, uint8_t fontSize)
{
    uint8_t fontBuf[60]; uint8_t gb_high, gb_low;
    while (*Chinese != '\0') {
        int8_t ret = ExtFont_NextChinese(&Chinese, &gb_high, &gb_low);
        if (ret == 0) { ExtFont_ReadChinese(gb_high, gb_low, fontBuf, fontSize);
            OLED_ShowImage(X, Y, fontSize, fontSize, fontBuf); X += fontSize; }
        else if (ret == 1) { Chinese++; }
        else break;
    }
}

void OLED_ShowMixStringExt(int16_t X, int16_t Y, char *String, uint8_t cnFont, uint8_t asciiFont)
{
    uint8_t fontBuf[60]; uint8_t gb_high, gb_low;
    while (*String != '\0') {
        int8_t ret = ExtFont_NextChinese(&String, &gb_high, &gb_low);
        if (ret == 0) { ExtFont_ReadChinese(gb_high, gb_low, fontBuf, cnFont);
            OLED_ShowImage(X, Y, cnFont, cnFont, fontBuf); X += cnFont; }
        else if (ret == 1) { OLED_ShowChar(X, Y, *String, asciiFont); X += asciiFont; String++; }
        else break;
    }
}

void OLED_ShowChineseAreaExt(int16_t RX, int16_t RY, int16_t RW, int16_t RH,
                              int16_t X, int16_t Y, char *Chinese, uint8_t fontSize)
{
    uint8_t fontBuf[60]; uint8_t gb_high, gb_low;
    while (*Chinese != '\0') {
        int8_t ret = ExtFont_NextChinese(&Chinese, &gb_high, &gb_low);
        if (ret == 0) { ExtFont_ReadChinese(gb_high, gb_low, fontBuf, fontSize);
            OLED_ShowImageArea(X, Y, fontSize, fontSize, RX, RY, RW, RH, fontBuf); X += fontSize; }
        else if (ret == 1) Chinese++;
        else break;
    }
}

void OLED_ShowMixStringAreaExt(int16_t RX, int16_t RY, int16_t RW, int16_t RH,
                                int16_t X, int16_t Y, char *String, uint8_t cnFont, uint8_t asciiFont)
{
    uint8_t fontBuf[60]; uint8_t gb_high, gb_low;
    while (*String != '\0') {
        int8_t ret = ExtFont_NextChinese(&String, &gb_high, &gb_low);
        if (ret == 0) { ExtFont_ReadChinese(gb_high, gb_low, fontBuf, cnFont);
            OLED_ShowImageArea(X, Y, cnFont, cnFont, RX, RY, RW, RH, fontBuf); X += cnFont; }
        else if (ret == 1) { OLED_ShowCharArea(RX, RY, RW, RH, X, Y, *String, asciiFont); X += asciiFont; String++; }
        else break;
    }
}
