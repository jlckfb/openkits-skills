#ifndef __MID_TIMER_STUB_H__
#define __MID_TIMER_STUB_H__
#include "ti_msp_dl_config.h"
#include "stdint.h"
void     timer_init(void);
uint32_t get_sys_tick_ms(void);
#endif
