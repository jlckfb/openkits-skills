#include "ti_msp_dl_config.h"
#include "mid_wireless_uart.h"

int main(void)
{
    SYSCFG_DL_init();
    wireless_uart_init();

    wireless_uart_send((uint8_t *)"Wireless UART7 ready\r\n", 21);

    while (1) {
        uint8_t ch;
        if (wireless_uart_read(&ch)) {
            wireless_uart_send(&ch, 1); /* echo */
        }
    }
}
