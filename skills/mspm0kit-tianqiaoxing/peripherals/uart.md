# UART on Tianqiaoxing G3519

## Board UART Instances

| Instance | TX | RX | Baud | 用途 |
|----------|----|----|------|------|
| UART0 | PA10 | PA11 | **9600** | CH340 USB-C 调试串口（排针可共用） |
| UART7 | PB17 | PB18 | **115200** | 2.4G 无线模块 |

## SysConfig 配置

```js
const UART_DEBUG = scripting.addModule("/ti/driverlib/UART", {}, false).addInstance();
UART_DEBUG.$name                    = "UART_DEBUG";
UART_DEBUG.targetBaudRate           = 9600;
UART_DEBUG.enabledInterrupts        = ["RX"];
UART_DEBUG.peripheral.$assign       = "UART0";
UART_DEBUG.peripheral.txPin.$assign = "PA10";
UART_DEBUG.peripheral.rxPin.$assign = "PA11";
```

## Key APIs

```c
// 发送一个字节
DL_UART_transmitDataBlocking(UART_DEBUG_INST, byte);

// 接收（中断模式）
void UART0_IRQHandler(void) {
    if (DL_UART_getPendingInterrupt(UART_DEBUG_INST) == DL_UART_IIDX_RX) {
        uint8_t data = DL_UART_receiveData(UART_DEBUG_INST);
    }
}
```

## Free UART Instances

UART1, UART2, UART3 均可自由使用。引脚选择参考 datasheet pinmux 表。
