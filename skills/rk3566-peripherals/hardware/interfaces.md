# 泰山派 RK3566 接口清单（来自官方 .epro2 原理图，SchemCP 解析）

> 数据来源：立创·泰山派 1M RK3566 官方原理图
> 解析工具：SchemCP MCP（semantic-rules/1，确定性规则）

## 已识别接口（22 个）

### I2C
| 接口 | 信号网络 | 页 |
|---|---|---|
| I2C0 (PMIC) | I2C0_SCL_PMIC / I2C0_SDA_PMIC | POWER(RK809-5) |
| HDMI DDC | HDMI_TXDDC_SCL_PORT / HDMI_TXDDC_SDA_PORT | HDMI |
| I2C0 (其他) | I2C0_SCL_PMIC / I2C0_SDA_PMIC | 电源管理 |

### SDIO（SDMMC0）
| 信号 | 网络 |
|---|---|
| CLK | SDMMC0_CLK |
| CMD | SDMMC0_CMD（未解析到，PARTIAL） |
| D0-D2 | SDMMC0_D0/D1/D2（部分） |

### UART
| 信号 | 网络 | 引脚 |
|---|---|---|
| UART0_TX | UART0_TX | GPIO0_C0 |
| UART0_RX | UART0_RX | GPIO0_C1 |

### USB
| 接口 | 信号 | 网络 |
|---|---|---|
| USB OTG | DP/DM | USB_OTG_DP / USB_OTG_DM（DM 未解析到，PARTIAL） |

## 接口状态说明

- 6 个 CANDIDATE（完整信号集）
- 15 个 PARTIAL_CANDIDATE（缺部分信号，如 SDIO CMD、USB DM）
- 1 个 UNRESOLVED
- 全部 ACTIVE（无 DNP）

## 注意

- 接口识别基于确定性规则（signal-set v1），非厂商官方声明
- 部分信号缺失（PARTIAL）多为原理图网络命名差异，不代表硬件缺失
- 装配状态未验证（522 POPULATED / 462 UNKNOWN）