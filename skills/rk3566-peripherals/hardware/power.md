# 泰山派 RK3566 电源树（来自官方 .epro2 原理图，SchemCP 解析）

> 数据来源：立创·泰山派 1M RK3566 官方原理图（29 页 .epro2 工程）
> 解析工具：SchemCP MCP（嘉立创 EDA 专业版原理图解析）

## 电源域总览

| 电源网络 | 用途 | 来源页 |
|---|---|---|
| `+12V` | 外部输入电源（DC 12V） | POWER |
| `VCC5V0_SYS` | 5V 系统电源 | POWER |
| `VCC3V3_SYS` | 3.3V 系统电源 | POWER |
| `VCC_3V3` | 3.3V 通用电源 | 多页 |
| `VCCIO_FLASH` | Flash 接口 IO 电源 | FLASH |
| `VDD_CPU` | CPU 核心电源 | RK3566_POWER&GND |
| `VDD_GPU` | GPU 核心电源 | RK3566_POWER&GND |
| `VDD_NPU` | NPU 核心电源 | RK3566_POWER&GND |
| `VDD_LOGIC` | 逻辑核心电源 | RK3566_POWER&GND |
| `VCC_DDR` | DDR 内存电源 | DDR_PHY / LPDDR4 |
| `VDDA0V9_PMU` | PMU 0.9V 模拟电源 | OSC/PLL/PMU |
| `VDDA0V9_IMAGE` | 图像/VPU 0.9V 模拟 | VI INTERFACE |
| `VDDA_0V9` | 0.9V 模拟电源 | 多页 |
| `VCCA1V8_PMU` | PMU 1.8V 模拟 | OSC/PLL/PMU |
| `VCCA1V8_IMAGE` | 图像 1.8V 模拟 | VI INTERFACE |
| `VCCA_1V8` | 1.8V 模拟电源 | 多页 |
| `VIN_LDO` / `VIN_LDO_OUT` | LDO 输入/输出 | POWER |
| `MIPI_DSI_VCC_LED+/-` | MIPI DSI 背光 LED 电源 | 显示 |

## 供电架构（RK809-5 PMIC）

- **主 PMIC**：RK809-5（页 `POWER(RK809-5)` + `POWER(RK809-5)_2_EXTENSION`）
- 外部 `+12V` → `VCC5V0_SYS` → PMIC 多路输出（CPU/GPU/NPU/LOGIC/DDR/模拟域）
- LPDDR4 使用 `VCC_DDR` 域

## 电源树边（POWER_LOAD 候选，SchemCP 确定性规则）

- 79 条电源负载边（CANDIDATE 状态），107 个电源节点
- 所有 `GND` 网络为统一地（多页共享）

## 注意

- 电源边状态为 `CANDIDATE`（原理图级解析，未经网表/电气真值验证）
- 装配状态：522 个组件 POPULATED，462 个 ASSEMBLY_UNKNOWN
- 如需精确电源路径，建议配合 `.enet` 网表做交叉验证