# RK3566 I2C 开发（泰山派 1M）

> 配套：[SKILL.md 设备树开发](../SKILL.md)、[SKILL.md 用户态外设访问](../SKILL.md)
> 硬件参考：[hardware/interfaces.md](../hardware/interfaces.md)

## 功能说明

RK3566 提供多个 I2C 控制器（i2c0~i2c4，以 TRM 为准），标准 I2C 主机模式，`clock-frequency` 可配（常见 100kHz / 400kHz）。

**板级已知（来自原理图解析，[hardware/interfaces.md](../hardware/interfaces.md)）**：

- **I2C0 是 PMIC 总线**：`I2C0_SCL_PMIC / I2C0_SDA_PMIC` 连接 RK809-5 —— **已被占用，不可外接器件**
- HDMI DDC 独立于 I2C 控制器，用于 HDMI 显示通道

## DTS 配置示例

### 在空闲 I2C 上挂器件（如 EEPROM）

```dts
&i2c1 {
    status = "okay";
    clock-frequency = <400000>;
    pinctrl-names = "default";
    pinctrl-0 = <&i2c1_xfer>;          // 引脚组名以 dtsi 为准

    eeprom: eeprom@50 {
        compatible = "atmel,24c02";
        reg = <0x50>;                  // 7bit 从机地址
        pagesize = <8>;
    };
};
```

> 使能后需重编内核并烧录：`./build.sh kernel`（见 SKILL.md「一、设备树开发」）。

## 用户态操作命令

```bash
ls /dev/i2c-*              # 查看可用 i2c bus
i2cdetect -y 0             # 扫描 bus 0 上的器件地址
i2cget -y 0 0x50 0x00      # 读 0x50 的寄存器 0x00
i2cset -y 0 0x50 0x00 0x01 # 写
i2ctransfer -y 0 w2@0x50 0x00 0x01 r1   # 组合写后读
```

> 工具包：板上 `apt install i2c-tools`。内核需启用 `CONFIG_I2C_CHARDEV`（默认开启）才有 `/dev/i2c-*`。

## 引脚复用要点

- 每个 i2c 节点对应 `&pinctrl` 中 `i2cX_xfer` 引脚组，选择哪组引脚由该配置决定
- **I2C0 已被 PMIC 占用**，选 bus 时避开（见 [hardware/interfaces.md](../hardware/interfaces.md)）
- I2C 需要上拉电阻；板上已有上拉，自接长线器件可考虑外部上拉

## 已知坑

1. **I2C0 不能外接**：PMIC 总线，擅自挂器件会干扰电源管理（RK809-5）
2. **扫描不到器件**：检查地址（7bit）、供电、上拉、SDA/SCL 是否接反
3. **`i2cdetect` 出现"幽灵"地址（如 0x68/0x50）**：部分器件对随机地址有响应，需结合 datasheet 判断
4. **改 DTS 未生效**：确认 `status = "okay"`、已重编内核并烧录、bus 编号对得上
5. **时序不匹配**：`clock-frequency` 太高时降速测试（400k → 100k）