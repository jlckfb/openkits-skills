# RK3566 GPIO 开发（泰山派 1M）

> 配套：[SKILL.md 设备树开发](../SKILL.md)、[SKILL.md 用户态外设访问](../SKILL.md)、[SKILL.md Pinctrl](../SKILL.md)
> 硬件参考：[hardware/interfaces.md](../hardware/interfaces.md)、[hardware/power.md](../hardware/power.md)

## 功能说明

RK3566 提供 **5 组 GPIO（GPIO0~GPIO4）**，每组 32 个 pin（PA0~PD7）。特性：

- IO 电平：由对应 VCCIO 电源域决定（1.8V / 3.3V，见 [hardware/power.md](../hardware/power.md)）
- 支持上下拉、驱动能力、开漏配置
- 支持电平/边沿中断（具体 IRQ 映射以 RK3566 TRM 为准）
- 每个 pin 复位后默认为 GPIO；多数 pin 可复用作 I2C/SPI/UART/PWM 等（见"引脚复用要点"）

> ⚠️ 板上哪些 pin 实际引出到排针，以官方原理图为准；本页只保证芯片级能力，不臆造排针逐 pin 标注。

## DTS 配置示例

### 1. LED（gpio-leds）

```dts
/ {
    leds {
        compatible = "gpio-leds";
        led_work: led-work {
            label = "work";
            gpios = <&gpio0 RK_PA0 GPIO_ACTIVE_HIGH>;
            default-state = "off";
        };
    };
};
```

### 2. 按键（gpio-keys）

```dts
/ {
    keys {
        compatible = "gpio-keys";
        key_test: key-test {
            label = "test";
            linux,code = <KEY_ENTER>;
            gpios = <&gpio0 RK_PA1 GPIO_ACTIVE_LOW>;
        };
    };
};
```

### 3. 独立 GPIO + pinctrl（声明引脚为普通 GPIO）

```dts
&pinctrl {
    my_gpio: my-gpio {
        rockchip,pins = <0 RK_PA2 RK_FUNC_GPIO &pcfg_pull_none>;
    };
};
```

- `RK_FUNC_GPIO` = 0（默认功能），明确声明可防止被其他外设复用
- 宏定义见 `arch/arm64/include/asm/gpio.h` 与 `include/dt-bindings/pinctrl/rockchip.h`

## 用户态操作命令

### sysfs（旧接口，兼容性写法）

```bash
echo 0 > /sys/class/gpio/export        # 导出 GPIO0_PA0
echo out > /sys/class/gpio/gpio0/direction
echo 1 > /sys/class/gpio/gpio0/value   # 输出高
echo in > /sys/class/gpio/gpio0/direction
cat /sys/class/gpio/gpio0/value        # 读输入
```

> sysfs 编号 = bank × 32 + pin，如 GPIO0_PA0 = 0、GPIO1_PC3 = 35。内核 6.1 默认仍支持（`CONFIG_GPIO_SYSFS`）。

### libgpiod（推荐）

```bash
gpiodetect                # 列出 gpiochip
gpioinfo gpiochip0        # 查看 line 信息
gpioset gpiochip0 0=1     # line0（GPIO0_PA0）输出高
gpioget gpiochip0 1       # 读 line1
gpiofind "work"           # 按 DT 标签查 line 号
```

> 板上需 `apt install gpiod`（或 libgpiod-tools）。

## 引脚复用要点

- 引脚宏：`RK_PA0`~`RK_PD7`，DTS 写法 `<&gpioN RK_Px ...>`
- 复用为外设需在 `&pinctrl` 配置 iomux（见 SKILL.md「三、Pinctrl」）
- 特殊引脚：boot 相关（RECOVERY/BOOT）、PMIC 相关（I2C0）等已被占用，改动前先确认
- 中断配置：`interrupt-parent = <&gpioX>` + `interrupts = <RK_Px IRQ_TYPE_...>`

## 已知坑

1. **别动已占用 pin**：I2C0 是 PMIC 总线（RK809-5，见 [hardware/interfaces.md](../hardware/interfaces.md)），对应 GPIO 不可随意复用
2. **`export` 失败**：该 pin 已被 pinctrl 申请或复用为外设，先查 `gpioinfo` 与 DTS
3. **电平不匹配**：1.8V 域引脚直连 3.3V 外设可能损坏，先确认该 pin 的 VCCIO 电源域
4. **中断不触发**：检查触发类型（电平/边沿）与复用冲突；GPIO 复用与外设功能互斥
5. **上电瞬间电平**：`default-state` 不保证上电前电平稳定，关键外设需自行处理上电时序