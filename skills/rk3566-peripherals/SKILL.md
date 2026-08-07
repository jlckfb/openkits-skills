---
name: rk3566-peripherals
description: 'RK3566 (TaishanPi 1M) peripheral development: GPIO/I2C/SPI/UART/PWM, DTS, kernel modules, board hardware reference.'
---

# rk3566-peripherals — 泰山派 RK3566 外设开发

## 交互方式（逐步引导）

调用本 skill 后：
1. **先复述确认**：向用户复述问题，确认需求范围（如：查引脚 / 改 DTS / 编译哪个系统 / 排查什么故障）。
2. **分步输出**：每步给 1-2 条关键信息 + 简短说明，不一次性倾倒全部内容。
3. **关键决策给选项**：涉及选型/方向（如选哪个 UART、哪个系统、哪个修复方案）时，列出选项让用户确认。
4. **每步反馈**：完成一步后明确告知结果（成功/失败/下一步），等待用户继续。
5. **输出风格**：用简洁表格/命令/要点，避免长段落；技术术语和路径保留原文。

> 例外：若用户明确要"完整说明"或"直接给结果"，则一次性输出。


**SoC**: Rockchip RK3566（RK3568 同系）
**内核**: 6.1.141（kernel-6.1 目录）

## 硬件参考（来自官方原理图，SchemCP 解析）

> 详细数据见 `hardware/` 目录：
> - `power.md` — 电源树（VDD_CPU/GPU/NPU/LOGIC、VCC_DDR、模拟域）
> - `interfaces.md` — 已识别接口（I2C/SDIO/UART/USB）
> - `project-overview.md` — 工程规模与能力边界

### 关键电源域

| 网络 | 用途 |
|---|---|
| VDD_CPU / VDD_GPU / VDD_NPU / VDD_LOGIC | 核心供电（RK809-5 PMIC） |
| VCC_DDR | LPDDR4 |
| VDDA0V9 / VCCA1V8 | 模拟电源域 |
| VCC_3V3 / VCC5V0_SYS | 系统电源 |

### 已识别接口（SchemCP 确定性规则）

| 类型 | 信号 | 备注 |
|---|---|---|
| I2C0 | I2C0_SCL/SDA_PMIC | PMIC 总线 |
| HDMI DDC | HDMI_TXDDC_SCL/SDA | |
| SDIO0 | SDMMC0_CLK/CMD/D0-D2 | 部分候选 |
| UART0 | UART0_TX/RX (GPIO0_C0/C1) | FPC 座引出 |
| USB OTG | USB_OTG_DP/DM | |

> 引脚复用详情建议配合 RK3566 TRM 或 `hardware/pinmap` 补充。

## 一、设备树开发（DTS）

泰山派 1M 主设备树：
```
kernel-6.1/arch/arm64/boot/dts/rockchip/tspi-rk3566-user-v10-linux.dts
```

### GPIO

```dts
&gpio0 {
    my_led {
        compatible = "gpio-leds";
        led {
            gpios = <&gpio0 RK_PA0 GPIO_ACTIVE_HIGH>;
            default-state = "off";
        };
    };
};
```

- RK3566 GPIO 分组：`gpio0`~`gpio4`，每 bank 32 pin
- 宏：`RK_PA0`~`RK_PD7`（arch/arm64/include/asm/gpio.h）

### 修改后编译

```bash
./build.sh lunch:rockchip_rk3566_taishanpi_1m_v10_defconfig
./build.sh kernel    # 仅重编内核
```

## 二、用户态外设访问

### GPIO (sysfs/chardev)

```bash
# sysfs（旧）
echo 0 > /sys/class/gpio/export
# chardev（推荐，libgpiod）
gpioset gpiochip0 0=1
gpioget gpiochip0 1
```

### I2C

```bash
i2cdetect -y 0        # 扫描 bus 0
i2cget -y 0 0x50 0x00 # 读器件
```

### SPI

```bash
# 设备树使能 spidev 后
echo "spi test" > /dev/spidev0.0
```

### UART

```bash
# ttyS0 等串口
stty -F /dev/ttyS0 115200
echo test > /dev/ttyS0
```

## 三、Pinctrl（引脚复用）

- DTS `&pinctrl` 节点配置 GPIO 功能复用
- RK3566 每个 pin 多功能，需正确设置 iomux

```dts
&pinctrl {
    uart0_xfer: uart0-xfer {
        rockchip,pins = <0 RK_PC0 1 &pcfg_pull_up>,
                        <0 RK_PC1 1 &pcfg_pull_up>;
    };
};
```

## 四、内核模块开发

```bash
# 交叉编译（SDK 内）
cd kernel-6.1
make CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 modules_prepare
# 写模块后
make CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 M=/path/to/module modules
# 推送到板子
adb push module.ko /tmp/ && adb shell insmod /tmp/module.ko
```

## 五、编译/烧录

见 `rk3566-sdk-build` skill（lunch + build + update.img）。

## 六、调试

见 `rk3566-debug` skill（adb/串口/已知问题）。
