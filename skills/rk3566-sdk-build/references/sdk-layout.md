# 泰山派 RK3566 Linux SDK 目录结构

> 说明 extract_sdk.sh 解压后 SDK 的关键目录与作用，帮助快速定位源码、配置、编译产物。
> 配套：[SKILL.md 默认工作流](../SKILL.md)、[flash-tools.md](./flash-tools.md)

## 顶层结构（extract_sdk.sh 解压后）

| 目录/文件 | 作用 |
|---|---|
| `build.sh` | 编译总入口（lunch / build / updateimg / kernel ...） |
| `device/rockchip/` | 板级配置：defconfig、parameter.txt 分区表、BoardConfig |
| `kernel-6.1/` | Linux 内核源码（6.1.141） |
| `u-boot/` | U-Boot 源码 |
| `buildroot/` | Buildroot rootfs 工程 |
| `debian/` | Debian rootfs（linaro-rootfs.img） |
| `ubuntu/` | Ubuntu rootfs（由 ubuntu22.04-rootfs.git clone 生成，见 SKILL.md「二、同步源码」） |
| `tools/` | 辅助工具（含 live-build-src） |
| `rockdev/` | 产物软链/输出目录 |
| `output/` | 编译输出（update.img 等） |
| `.repo/` | repo 元数据（repo 工具与本地对象库） |
| `extract_sdk.sh` | 官方分卷解压脚本 |
| `docs/` / `RKDocs/` | SDK 文档 |
| `app/` | Rockchip 应用源码 |
| `scripts/` | 编译辅助脚本 |

## 板级配置（device/rockchip/）

- `device/rockchip/.chips/rk3566_rk3568/` — 芯片通用配置
  - `parameter-buildroot-fit.txt` — 分区表（rootfs 已扩 12G，见 [flash-tools.md](./flash-tools.md)）
- 泰山派板级：
  - defconfig：`rockchip_rk3566_taishanpi_1m_v10_defconfig`
  - 主设备树：`kernel-6.1/arch/arm64/boot/dts/rockchip/tspi-rk3566-user-v10-linux.dts`

## 内核目录

```
kernel-6.1/
├─ arch/arm64/boot/dts/rockchip/   # 设备树源码
├─ drivers/                        # 驱动源码
├─ include/                        # 头文件（含 dt-bindings 宏）
└─ .config                         # 内核配置（build 后生成）
```

> 外设宏 `RK_PA0`~`RK_PD7` 在 `arch/arm64/include/asm/gpio.h`；dt-bindings 宏在 `include/dt-bindings/`。

## 产物位置速查

| 产物 | 路径 |
|---|---|
| 完整固件 | `output/update/Image/update.img` |
| debian rootfs | `debian/linaro-rootfs.img` |
| ubuntu rootfs | `ubuntu/ubuntu-jammy.img` |
| 内核 Image | `kernel-6.1/arch/arm64/boot/Image` |
| 设备树 | `kernel-6.1/arch/arm64/boot/dts/rockchip/*.dtb` |

## 修改后的重编流程

- 仅改设备树/内核：`./build.sh kernel`（见 SKILL.md「三、编译系统」）
- 改 rootfs：对应系统的 mk-image 流程
- 重新合成整包：`./build.sh updateimg`