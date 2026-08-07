# RK3566 SPI 开发（泰山派 1M）

> 配套：[SKILL.md 设备树开发](../SKILL.md)、[SKILL.md 用户态外设访问](../SKILL.md)
> 硬件参考：[hardware/interfaces.md](../hardware/interfaces.md)

## 功能说明

RK3566 提供多个 SPI 控制器（spi0~spi3，以 TRM 为准），支持 master/slave 模式，可与 `spidev` 结合做用户态访问。SPI 典型 4 线：SCLK / MOSI / MISO / CS，一个控制器可有多个片选（cs0/cs1）。

## DTS 配置示例

### 1. spidev（用户态测试用）

```dts
&spi0 {
    status = "okay";
    max-freq = <50000000>;
    pinctrl-names = "default";
    pinctrl-0 = <&spi0_pins>;            // 引脚组名以 dtsi 为准

    spidev0: spidev@0 {
        compatible = "rockchip,spidev";
        reg = <0>;                        // cs0
        spi-max-frequency = <10000000>;
    };
};
```

### 2. 挂自定义 SPI 器件

```dts
&spi0 {
    status = "okay";

    mydev: mydev@0 {
        compatible = "vendor,device";
        reg = <0>;
        spi-max-frequency = <5000000>;
        spi-cpol;                          // 按器件手册选择 CPOL/CPHA
        spi-cpha;
    };
};
```

## 用户态操作命令

```bash
ls /dev/spidev*             # spidevX.Y：X=控制器，Y=片选
# spidev_test（内核自带用户态测试工具，Linux 源码 tools/spidev/）
spidev_test -D /dev/spidev0.0 -p "hello" -s 1000000
# 直接读写
echo "spi test" > /dev/spidev0.0
```

## 引脚复用要点

- SPI 引脚（SCLK/MOSI/MISO/CS）需在 `&pinctrl` 配置为 spi 功能
- 多片选对应多个 `/dev/spidevX.Y`（Y = 0/1）
- 复用前确认引脚未被其他外设占用（见 SKILL.md「三、Pinctrl」）

## 已知坑

1. **spidev 需显式使能**：DTS 加 spidev 子节点 + `status = "okay"`，否则 `/dev/spidev*` 不存在
2. **片选极性**：`spi-cs-high` 与从设备/线缆不匹配时通信异常
3. **MISO 无数据**：检查 MOSI/MISO 是否接反、从设备供电、CS 是否拉对
4. **速率过高**：`spi-max-frequency` 太高会采样错位，从低往高调试
5. **模式（CPOL/CPHA）不匹配**：与从设备手册不一致会导致数据错位