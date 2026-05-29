#include "mid_timer.h"
static volatile uint32_t sys_tick_ms = 0;
void timer_init(void) {
    NVIC_ClearPendingIRQ(TIMER_TICK_INST_INT_IRQN);
    NVIC_EnableIRQ(TIMER_TICK_INST_INT_IRQN);
}
void TIMER_TICK_INST_IRQHandler(void) {
    if (DL_TimerA_getPendingInterrupt(TIMER_TICK_INST) == DL_TIMER_IIDX_ZERO) {
        sys_tick_ms += 5;
    }
}
uint32_t get_sys_tick_ms(void) { return sys_tick_ms; }
