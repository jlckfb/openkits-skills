# RK3566 PWM 开发（泰山派 1M）

> 配套：[SKILL.md 设备树开发](../SKILL.md)、[SKILL.md 用户态外设访问](../SKILL.md)
> 硬件参考：[hardware/power.md](../hardware/power.md)

## 功能说明

RK3566 提供多路 PWM（pwm0~pwm15，以 TRM 为准），用于 LED 呼吸灯、屏幕背光、电机/舵机等。Linux 侧走 `pwm` 子系统，可由 `pwm-leds` / `pwm-backlight` 等 consumer 使用，也可经 sysfs 导出给用户态。

- 部分 PWM 通道可引出到 IO 引脚（iomux 复用），具体通道→引脚映射以 RK3566 TRM / pinmap 为准
- PWM 的 `period` / `duty_cycle` 单位是**纳秒（ns）**

## DTS 配置示例

### 1. 直接输出 PWM

```dts
&pwm0 {
    status = "okay";
    pinctrl-names = "default";
    pinctrl-0 = <&pwm0_pin>;           // 引脚组名以 dtsi 为准
};
```

### 2. 背光（pwm-backlight）

```dts
/ {
    backlight: backlight {
        compatible = "pwm-backlight";
        pwms = <&pwm0 0 1000000 0>;    // 控制器 通道 周期(ns) 极性
        brightness-levels = <0 10 20 30 50 100>;
        default-brightness-level = <3>;
    };
};
```

## 用户态操作命令

```bash
# sysfs PWM（需 CONFIG_PWM_SYSFS）
echo 0 > /sys/class/pwm/pwmchip0/export
echo 1000000 > /sys/class/pwm/pwmchip0/pwm0/period       # 周期 1ms（1kHz）
echo 500000  > /sys/class/pwm/pwmchip0/pwm0/duty_cycle   # 50% 占空比
echo 1 > /sys/class/pwm/pwmchip0/pwm0/enable
echo 0 > /sys/class/pwm/pwmchip0/pwm0/enable             # 停止
# 背光（若用 pwm-backlight）
cat /sys/class/backlight/*/brightness
echo 128 > /sys/class/backlight/*/brightness
```

## 引脚复用要点

- 每个 PWM 通道的 IO 引脚需在 `&pinctrl` 配置为 pwm 功能（见 SKILL.md「三、Pinctrl」）
- 部分通道可能已被背光等占用，先查板级 dts 默认配置
- 需要引出的具体引脚从 TRM/pinmap 查，本页不臆造逐 pin 映射

## 已知坑

1. **通道被占用**：如背光 PWM 已被 `pwm-backlight` 使用，别重复配置
2. **单位是 ns**：`period`/`duty_cycle` 是纳秒，不是百分比或微秒
3. **极性**：`polarity` 反了会导致亮度/动作相反（如灯常亮变常灭）
4. **`export` 失败**：该通道已被内核驱动占用（`/sys/class/pwm/pwmchipN` 下已存在 pwmX）
5. **输出不稳定**：PWM 时钟源未使能或分频不对，用 `cat /sys/kernel/debug/clk/clk_summary` 检查