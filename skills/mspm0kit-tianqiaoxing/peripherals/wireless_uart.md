# Wireless UART on Tianqiaoxing G3519

**Driver**: `middle/mid_wireless_uart.c/h`

## Hardware

- Module: Onboard 2.4 GHz wireless UART module
- Interface: UART7 on PB17(TX) / PB18(RX)
- Status pin: PB23 (INPUT, PULL_DOWN, low = connected)
- Baud: **115200**

## SysConfig 配置

```js
const UART_WIRELESS = scripting.addModule("/ti/driverlib/UART", {}, false).addInstance();
UART_WIRELESS.$name                    = "UART_WIRELESS";
UART_WIRELESS.targetBaudRate           = 115200;
UART_WIRELESS.enabledInterrupts        = ["RX"];
UART_WIRELESS.peripheral.$assign       = "UART7";
UART_WIRELESS.peripheral.txPin.$assign = "PB17";
UART_WIRELESS.peripheral.rxPin.$assign = "PB18";
```

## Generated Macros

```
UART_WIRELESS_INST              → UART7
UART_WIRELESS_INST_INT_IRQN    → UART7_INT_IRQn
UART_WIRELESS_BAUD_RATE        → 115200
```

## ⚠️ AT_RF 射频开关（关键，必做）

无线模块上电后**射频默认关闭**。发任何数据前必须先发 `AT_RF=ON\r\n` 开启射频，否则模块收发不工作（实测：不发此命令对端收不到任何数据）。退出无线功能时发 `AT_RF=OFF\r\n` 关闭。

```c
/* 上电初始化后，发数据前先开射频 */
wl_puts("AT_RF=ON\r\n");
while (DL_UART_Main_isBusy(UART_WIRELESS_INST));   /* 等命令发完 */
delay_cycles(CPUCLK_FREQ / 1000 * 100);            /* 给模块 ~100ms 处理 */

/* ...正常收发数据... */

/* 退出时关射频 */
wl_puts("AT_RF=OFF\r\n");
```

- AT 命令通过 UART7 发送（和数据同一通道），必须带 `\r\n` 结尾
- 用**中断接收**时，发 AT 命令期间要先 `NVIC_DisableIRQ(UART_WIRELESS_INST_INT_IRQN)`，发完再开，保证 AT 帧连续不被打断（轮询接收无此问题）

## Key APIs

```c
#include "mid_wireless_uart.h"

wireless_uart_init();

// Send
uint8_t data[] = "Hello";
wireless_uart_send(data, sizeof(data));

// Receive (RX interrupt → ring buffer)
uint8_t ch;
if (wireless_uart_read(&ch)) {
    // got one byte
}

// Connection status
bool connected = (DL_GPIO_readPins(WIRELESS_PORT, WIRELESS_LINK_PIN) == 0);
```

## Dependencies

- None (only DriverLib)
