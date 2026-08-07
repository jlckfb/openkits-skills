# RK3566 UART 开发（泰山派 1M）

> 配套：[SKILL.md 设备树开发](../SKILL.md)、[SKILL.md 用户态外设访问](../SKILL.md)、[rk3566-debug 串口](../../rk3566-debug/SKILL.md)
> 硬件参考：[hardware/interfaces.md](../hardware/interfaces.md)

## 功能说明

RK3566 提供多个 UART（uart0~uart9，以 TRM 为准），支持标准串口收发与硬件流控（RTS/CTS）。其中一路通常用作调试串口。

**板级已知（来自原理图解析，[hardware/interfaces.md](../hardware/interfaces.md)）**：

- **UART0**：`UART0_TX / UART0_RX`，引脚 **GPIO0_C0 / GPIO0_C1**
- 泰山派调试串口波特率 **1500000**（抓日志见 [rk3566-debug](../../rk3566-debug/SKILL.md)）

## DTS 配置示例

### 使能一路 UART

```dts
&uart0 {
    status = "okay";
    pinctrl-names = "default";
    pinctrl-0 = <&uart0_xfer>;          // TX/RX 引脚组（含 GPIO0_C0/C1，名称以 dtsi 为准）
    /delete-property/ dmas;             // 可选：关闭 DMA，改用 PIO（见"已知坑 2"）
    /delete-property/ dma-names;
};
```

> 调试串口节点由板级 dts（`stdout-path` / chosen）决定，一般保持不动。

## 用户态操作命令

```bash
ls /dev/ttyS*                          # 查看串口设备
stty -F /dev/ttyS0 115200 cs8 -cstopb -parenb   # 8N1
echo "hello" > /dev/ttyS0              # 发送
cat /dev/ttyS0 &                       # 接收
# 抓调试串口日志（Windows，用配套脚本）
python <rk3566-debug>/scripts/serial_log.py --port COM13 --baud 1500000
python <rk3566-debug>/scripts/serial_log.py --list
```

## 引脚复用要点

- TX/RX 需交叉连接（本板 TX 接对端 RX）
- 流控（RTS/CTS）需在 DTS 配置对应引脚组
- 调试串口波特率是 **1500000**，不是 115200，用错会乱码
- UART0 引脚 GPIO0_C0/C1 若被其他外设占用，先释放复用（见 SKILL.md「三、Pinctrl」）

## 已知坑

1. **波特率不匹配**：调试串口 1500000，误用 115200 会乱码
2. **DMA 收发异常**：某些场景 UART+DMA 不稳定，可删 `dmas`/`dma-names` 走 PIO
3. **`/dev/ttyS*` 编号**：与设备树 alias 有关，先 `ls /dev/ttyS*` 确认实际节点，别想当然用 ttyS0
4. **乱码**：确认波特率/数据位/停止位/校验一致（常见 8N1）
5. **复用冲突**：UART0 引脚被占用时需先改 pinctrl 释放