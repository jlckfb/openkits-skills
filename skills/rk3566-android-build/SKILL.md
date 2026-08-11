---
name: rk3566-android-build
description: 'RK3566 (TaishanPi 1M) Android 13 SDK build & flash helper: extract, repo sync, build update.img, known issues.'
---

# rk3566-android-build — 泰山派 RK3566 Android13 SDK 编译与烧录

## 使用前提（环境确认）

> 调用本 skill 前，**先逐步确认环境**：一次只问一项，等用户回答后再问下一项；缺什么就给什么教程/下载位置，不一次性倾倒全部内容。

1. **SDK**：有泰山派 Android13 SDK（20260311）吗？
   - 有 → 记录 SDK 路径
   - 没有 → 提供下载位置：立创 wiki 下载中心 `https://wiki.lckfb.com/zh-hans/tspi-rk3566/download-center.html`（含 Android13 SDK 分卷包与泰山派完整资料包）；解压方式 `./complete_sdk_package.sh` → 解压出源码目录
2. **SDK 位置**：本地目录还是远程服务器？
   - 远程 → 问 IP / SSH 账号 / 连接方式，并确认可连通
   - 本地 → 记录绝对路径
3. **编译环境**：本机 Ubuntu 22.04 还是 Docker？
   - 本机 → 检查依赖：git、python（2.7/3.x 按需切换）、openjdk-8-jdk、repo；缺依赖可用 `scripts/android_env_init.sh` 一键初始化
   - Docker → 需 32 核 / 32G 内存 / 400G 磁盘以上（wiki 最低要求），镜像需含 openjdk-8 + Android 工具链
4. **板子**：有泰山派 1M 板子吗？调试通道可用？（adb / 串口 1500000，见 `rk3566-debug`）
5. **烧录工具**：RKDevTool（Windows）/ rkdeveloptool（Linux）就绪？（见 `references/flash-tools.md`）

确认完毕先汇总一份"你的环境清单"，再进入正式流程。

## 交互方式（逐步引导）

调用本 skill 后：
1. **先复述确认**：向用户复述问题，确认需求范围（如：编译哪个版本 userdebug/user、是否只编内核/uboot、是否需改 DTS）。
2. **分步输出**：每步给 1-2 条关键信息 + 简短说明，不一次性倾倒全部内容。
3. **关键决策给选项**：涉及选型/方向（如选 user 还是 userdebug、是否带 -p packages）时，列出选项让用户确认。
4. **每步反馈**：完成一步后明确告知结果（成功/失败/下一步），等待用户继续。
5. **输出风格**：用简洁表格/命令/要点，避免长段落；技术术语和路径保留原文。
6. **收尾开发日志**：任务完成后，主动询问用户"需要输出开发日志吗？"；用户同意则按"开发日志"章节模板在对话中输出完整开发日志（方便其他开发人员查看/复现）。

> 例外：若用户明确要"完整说明"或"直接给结果"，则一次性输出。

## 开发日志（任务完成后可选）

任务完成后主动询问用户是否输出开发日志。用户同意后按以下模板在**对话中**输出（不写入文件）：

```
# 开发日志 — <YYYY-MM-DD> <任务标题>

## 1. 任务概述
- 需求：<用户需求一句话>
- 目标产物：<固件/脚本/文档等>

## 2. 环境
- 主机/服务器：<IP、系统、账号>
- SDK/镜像：<SDK 路径、Docker 镜像>
- 工具链：<工具及版本>

## 3. 实施步骤
1. <步骤 + 命令>
2. ...

## 4. 关键决策
- <为什么选这个方案>

## 5. 踩坑与解决
- <问题> → <解决>

## 6. 产物与验证
- 产物路径：<...>
- 验证方式：<命令/结果>

## 7. 复现方法
- <从头复现的关键步骤>

## 8. 待办/后续
- <下一步>
```

**SoC**: Rockchip RK3566（Cortex-A55 四核）
**SDK**: 泰山派 Android13 SDK（立创官方 20260311，内核 5.10，实测通过）

## 默认工作流

接到"编译/烧录 Android13 固件"类任务时的标准步骤：

1. **确认目标**：版本（userdebug 开发调试 / user 生产）、是否需修改 DTS/内核、产物形式（完整 update.img / 单分区镜像）。
2. **确认环境**：SDK 路径、主机配置（最低 32 核 / 32G / 400G）、依赖（openjdk-8 等）。
3. **准备源码**：解压分卷包（`./complete_sdk_package.sh`）→ `python3 .repo/repo/repo sync -l -j88`。
4. **初始化编译环境**：`source build/envsetup.sh` → `lunch rk3566_tspi_1m-userdebug`（或 `-user`）。
5. **编译**：`./build.sh -AUCKu -J$(nproc)`（-U uboot / -K kernel / -A android / -u update.img）；失败查"五、已知问题速查"。
6. **产物确认**：检查 `rockdev/Image-rk3566_tspi_1m/update.img` 时间戳与大小。
7. **烧录**：Windows RKDevTool / Linux upgrade_tool 烧 update.img，见 `references/flash-tools.md`。
8. **验证**：板子启动后用 `rk3566-debug` skill 查串口日志 / adb 状态。

## 一、获取与解压 SDK

```bash
# 1. 解压分卷包（官方方式，生成源码目录）
./complete_sdk_package.sh
# 2. 校验（可选）
sha256sum -c sdk_parts_checksums.sha256
```

> 分卷包形如 `rk3566_android13_sdk_20260311_package/`，解压后得到源码目录（含 `build.sh`、`.repo`、`kernel-5.10` 等）。

## 二、同步源码（wiki 官方方式）

```bash
cd <解压出的源码目录>
# 此 SDK 的 repo 是 Python 3 版本；若 repo 需 python2 则先切换（见下）
python3 .repo/repo/repo sync -l -j88
```

- `-l` 本地同步（用 .repo 内对象，不联网）
- `-j88` 并行度（按机器核数调整）
- python 版本切换：`sudo update-alternatives --config python`（repo 对 python2/3 敏感，报错则换版本重试）

## 三、编译系统

### 0. 编译环境最低配置（wiki 官方）

| 项 | 要求 |
|---|---|
| CPU | 32 核 |
| 内存 | 32GB |
| 磁盘 | 400GB |
| 系统 | Ubuntu 22.04 |

> 低于此配置未验证，可能出现莫名错误。实测服务器：88 核 / 125G 内存 / 1.8T 磁盘，增量编译约 8 分钟。

### 1. 初始化编译环境

```bash
source build/envsetup.sh    # 加载 Android 编译工具链（每次新终端都要执行）
lunch rk3566_tspi_1m-userdebug
```

lunch 选项：
- `rk3566_tspi_1m-userdebug`：开发调试版，dts `tspi-rk3566-user-v10-linux.dts`，镜像较大
- `rk3566_tspi_1m-user`：生产版，镜像较小

### 2. 一键编译

```bash
./build.sh -AUCKu -J$(nproc)
```

参数：
- `-U`：编译 u-boot
- `-K`：编译 kernel
- `-A`：编译 android
- `-u`：生成 update.img
- `-p`：编译 packages 并安装至镜像
- `-J`：指定并行度（`$(nproc)` 自动检测核心数）
- `-C`：build kernel with Clang
- `-o`：build OTA package
- `-v`：build android with 'user' or 'userdebug'

### 3. 单独编译内核

```bash
# 方式一：SDK 编译脚本
./build.sh -K
# 方式二：直接进内核目录（需先 source envsetup + lunch）
cd kernel-5.10
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- rockchip_defconfig android-13.config rk356x.config
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
```

## 四、产物位置

| 产物 | 路径 |
|---|---|
| 完整固件 | `rockdev/Image-rk3566_tspi_1m/update.img`（约 1.8G） |
| 单分区镜像 | `rockdev/Image-rk3566_tspi_1m/`（uboot.img / boot.img / super.img / dtbo.img 等） |

> 实测：update.img 在 `rockdev/Image-rk3566_tspi_1m/` 下，不在 `rockdev/` 根目录。

## 五、已知问题速查

| 现象 | 解决 |
|---|---|
| repo sync 报错 | 切换 python 版本（`update-alternatives --config python`）或改 `python3 .repo/repo/repo sync -l` |
| 缺 openjdk-8 | `sudo apt-get install -y openjdk-8-jdk`（Android13 必须 JDK8） |
| 磁盘不足 | 最低 400G；`out/` 会占 95G+ |
| lunch 失败 | 先 `source build/envsetup.sh`（每次新终端都要 source） |
| qemu-aarch64 相关 | 环境初始化脚本（`scripts/android_env_init.sh`）含 QEMU/binfmt 配置，可一键修复 |

## 六、环境初始化脚本

`scripts/android_env_init.sh`（来自立创 wiki，6 阶段）：

1. 系统环境检查（sudo 权限 / Ubuntu 22.04 / CPU / 磁盘）
2. 配置 apt 镜像源 + 网络
3. 安装编译依赖（含 live-build；openjdk-8 需单独安装，见"五、已知问题速查"）
4. 系统配置（内核模块 / QEMU / 时区）
5. Repo 配置检查（manifest 本地化跟踪）
6. 环境验证（QEMU / binfmt）

```bash
# 在 SDK 源码目录下运行（需 sudo）
sudo bash scripts/android_env_init.sh
```
