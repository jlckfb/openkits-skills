# UART on Tianmengxing G3507

## Available UART Instances

| Instance | Status | Notes |
|----------|--------|-------|
| UART0 | Occupied (sharable) | PA10(TX)/PA11(RX) → CH340 USB-C; header pins can share |
| UART1 | Free | Any free pins |
| UART2 | Free | Any free pins |
| UART3 | Free | Any free pins |
| UART7 | Free | Any free pins |

## SDK Examples

| Example | What It Does |
|---------|-------------|
| `uart_rw_multibyte_fifo_poll` | TX/RX 4 bytes via FIFO polling, loopback test, LED toggle |
| `uart_tx_console_multibyte_repeated_fifo_dma` | Console TX via DMA, 115200 baud |
| `uart_echo_interrupts_standby` | Echo with RX interrupt + standby |
| `uart_external_loopback_interrupt` | TX/RX with external loopback test |

## Pin Mapping (LP → Tianmengxing)

SDK default: PA10(TX)/PA11(RX) → Keep same (CH340 on board, can share)

## Recommended Pattern (Debug Console)

1. Run: `python scripts/scaffold.py <name> uart_rw_multibyte_fifo_poll`
2. Edit .syscfg: baud = 115200 (change from default 9600)
3. Build and flash.
4. Monitor: `python scripts/serial_console.py -p <COM_PORT> -b 115200`

## Generated Macros (after SysConfig)

```
UART_0_INST         → UART0
UART_0_BAUD_RATE    → 115200
GPIO_UART_0_TX_PIN  → DL_GPIO_PIN_10
GPIO_UART_0_RX_PIN  → DL_GPIO_PIN_11
```

## Baud Rate & Clock Source Constraint

| Clock Source | Max Baud Rate | Notes |
|-------------|---------------|-------|
| LFCLK (32768 Hz) | ~10900 | **无法支持 115200**。需 115200+ 时必须切换时钟源 |
| MFCLK (4 MHz) | ~1.3M | 推荐用于 115200 |
| BUSCLK (40 MHz) | ~13M | 高速通信 |

> SDK 示例 `uart_rw_multibyte_fifo_poll` 默认使用 LFCLK。如果用户需要 115200，必须先在 `.syscfg` 中将 UART 时钟源从 LFCLK 切换为 MFCLK 或 BUSCLK。

## Key APIs

```c
DL_UART_Main_fillTXFIFO(UART_0_INST, data, len);
DL_UART_receiveDataBlocking(UART_0_INST);
while (DL_UART_Main_isBusy(UART_0_INST));
```
