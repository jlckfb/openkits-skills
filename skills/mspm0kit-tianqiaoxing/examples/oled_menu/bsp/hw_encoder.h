#ifndef _HW_ENCODER_H_
#define _HW_ENCODER_H_
#include <stdint.h>
void HW_Encoder_Init(void);
void HW_Encoder_Enable(void);
void HW_Encoder_Disable(void);
int16_t HW_Encoder_GetDelta(void);
#endif
