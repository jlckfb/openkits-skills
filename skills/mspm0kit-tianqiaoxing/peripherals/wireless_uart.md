# Wireless UART on Tianqiaoxing G3519

**Driver**: `middle/mid_wireless_uart.c/h`

## Hardware

- Module: Onboard 2.4 GHz wireless UART module
- Interface: UART7 on PB17(TX) / PB18(RX)
- Status pin: PB23 (INPUT, PULL_DOWN, low = connected)
- Default baud: 9600

## Adding to OLED UI project

```bash
python scripts/scaffold_oled.py <name> --with-wireless
```

This copies: `mid_wireless_uart.c/h`

And adds to `.syscfg`: UART7 on PB17/PB18 with RX interrupt enabled.

## Generated Macros (from syscfg)

```
UART_WIRELESS_INST              → UART7
GPIO_UART_WIRELESS_TX_PIN       → DL_GPIO_PIN_17
GPIO_UART_WIRELESS_RX_PIN       → DL_GPIO_PIN_18
UART_WIRELESS_INST_INT_IRQN     → UART7_INT_IRQn
UART_WIRELESS_INST_FREQUENCY    → 40000000
UART_WIRELESS_BAUD_RATE         → 9600
```

## Key APIs

```c
#include "mid_wireless_uart.h"

// Init (after SYSCFG_DL_init)
wireless_uart_init();

// Send data
uint8_t data[] = "Hello";
wireless_uart_send(data, sizeof(data));

// Receive: RX interrupt stores data in ring buffer
// Read with:
uint8_t ch;
if (wireless_uart_read(&ch)) {
    // got one byte
}

// Connection status (PB23)
bool connected = (DL_GPIO_readPins(WIRELESS_PORT, WIRELESS_LINK_PIN) == 0);
```

## Dependencies

- None (clean, only depends on DriverLib from syscfg)

## Note

Wireless module baud rate is set in hardware (fixed at 9600). If communication fails, verify:
- Both devices on same channel/ID
- Module powered (check onboard regulator)
- PB23 reads LOW when paired
