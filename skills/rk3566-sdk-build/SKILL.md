---
name: rk3566-sdk-build
description: 'RK3566 (TaishanPi 1M) Linux SDK build & flash helper: extract, repo sync, build buildroot/debian/ubuntu, generate update.img.'
---

# rk3566-sdk-build — 泰山派 RK3566 SDK 编译与烧录

## 使用前提（环境确认）

> 调用本 skill 前，**先逐步确认使用环境**：一次只问一项，等用户回答后再问下一项；缺什么就给什么教程/下载位置，不一次性倾倒全部内容。

1. **SDK**：有泰山派 kernel6.1 Linux SDK（20260403）吗？
   - 有 → 记录 SDK 路径
   - 没有 → 提供下载位置：立创 wiki 下载中心 `https://wiki.lckfb.com/zh-hans/tspi-rk3566/download-center.html`（含 SDK 分卷包与泰山派完整资料包）；解压方式 `./extract_sdk.sh` → `./extracted_sdk`
2. **SDK 位置**：本地目录还是远程服务器？
   - 远程 → 问 IP / SSH 账号 / 连接方式，并确认可连通
   - 本地 → 记录绝对路径
3. **编译环境**：本机 Ubuntu 22.04 还是 Docker？
   - 本机 → 检查依赖：repo（Python 3）、git、tar、xz
   - Docker → 问是否有镜像 `tspi-kernel6-1-env:latest`；没有 → 给 Dockerfile 构建教程（见"五、Docker 编译"）
4. **板子**：有泰山派 1M 板子吗？调试通道可用？（adb / 串口 1500000，见 `rk3566-debug`）
5. **烧录工具**：RKDevTool（Windows）/ rkdeveloptool（Linux）就绪？（见 `references/flash-tools.md`）

确认完毕先汇总一份"你的环境清单"，再进入正式流程。

## 交互方式（逐步引导）

调用本 skill 后：
1. **先复述确认**：向用户复述问题，确认需求范围（如：查引脚 / 改 DTS / 编译哪个系统 / 排查什么故障）。
2. **分步输出**：每步给 1-2 条关键信息 + 简短说明，不一次性倾倒全部内容。
3. **关键决策给选项**：涉及选型/方向（如选哪个 UART、哪个系统、哪个修复方案）时，列出选项让用户确认。
4. **每步反馈**：完成一步后明确告知结果（成功/失败/下一步），等待用户继续。
5. **输出风格**：用简洁表格/命令/要点，避免长段落；技术术语和路径保留原文。

> 例外：若用户明确要"完整说明"或"直接给结果"，则一次性输出。


**SoC**: Rockchip RK3566（Cortex-A55 四核）
**SDK**: 泰山派 kernel6.1 Linux SDK（立创官方 20260403 + 修复）

## 默认工作流

接到"编译/烧录 RK3566 固件"类任务时的标准步骤：

1. **确认目标**：系统类型（buildroot / debian / ubuntu）、产物形式（完整 update.img / 单 rootfs 镜像）、是否需修改 DTS/内核。
2. **确认环境**：本机 Ubuntu 22.04 或 Docker（无 sudo 用户必须用 Docker，见"五、Docker 编译"）。
3. **准备源码**：解压 SDK（`./extract_sdk.sh`）→ `python3 .repo/repo/repo sync -l -j88`；ubuntu 额外 `git clone .repo/projects/ubuntu22.04-rootfs.git ubuntu`。
4. **选择 defconfig**：`./build.sh lunch:rockchip_rk3566_taishanpi_1m_v10_defconfig`。
5. **编译**：按目标系统执行（见"三、编译系统"）；失败查"六、已知问题速查"。
6. **产物确认**：检查 `output/update/Image/update.img` 时间戳与大小。
7. **烧录**：Windows RKDevTool / Linux upgrade_tool 烧 update.img，要点与 rootfs 12G 分区表见 `references/flash-tools.md`；SDK 目录结构见 `references/sdk-layout.md`。
8. **验证**：板子启动后用 `rk3566-debug` skill 查串口日志 / adb 状态。

## 一、获取与解压 SDK

```bash
# 1. 解压分卷包（生成 extract_sdk.sh 的官方方式）
./extract_sdk.sh            # 解压到 ./extracted_sdk
# 或指定目录
./extract_sdk.sh /path/to/target
```

> 注意：分卷文件形如 `rk3566_linux_sdk_*.tar.xz.part.NN`，解压脚本会自动校验+合并+解压。

## 二、同步源码（wiki 官方方式）

```bash
cd <解压目录>
# 需 python3（此 SDK 的 repo 是 Python 3 版本）
python3 .repo/repo/repo sync -l -j88
```

- `-l` 本地同步（用 .repo 内对象，不联网）
- `-j88` 并行度（按机器核数调整，如 -j8）

### Ubuntu 额外步骤

```bash
# ubuntu 源码不在 manifest 中，需手动 clone
git clone .repo/projects/ubuntu22.04-rootfs.git ubuntu
```

## 三、编译系统

### 0. 选择 defconfig

```bash
./build.sh lunch:rockchip_rk3566_taishanpi_1m_v10_defconfig
```

### 1. Buildroot

```bash
./build.sh
```

### 2. Debian

```bash
# 先安装支持 bookworm 的 live-build（SDK 自带源码）
cd tools/live-build-src && rm -rf manpages/po/ && sudo make install -j8
cd ../../ && RK_ROOTFS_SYSTEM=debian ./build.sh
```

### 3. Ubuntu（desktop 版）

```bash
cd ubuntu
sudo env GUI=desktop bash mk-base-ubuntu.sh
# 内核 deb 包（mk-ubuntu-rootfs 需要）
cd ../kernel-6.1
make CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 LOCALVERSION= bindeb-pkg -j$(nproc)
cd ../ubuntu
sudo env GUI=desktop bash mk-ubuntu-rootfs.sh
sudo env GUI=desktop bash mk-image.sh
# 合成完整 update.img
cd .. && rm -f rockdev/rootfs.img
cp ubuntu/ubuntu-jammy.img rockdev/rootfs.img
./build.sh updateimg
```

> `sudo env GUI=desktop`：GUI 变量必须显式传（sudo 清空环境变量），否则脚本进入交互死循环。

## 四、产物位置

| 系统 | 完整固件 | rootfs 镜像 |
|---|---|---|
| buildroot | `output/update/Image/update.img` | — |
| debian | `output/update/Image/update.img` | `debian/linaro-rootfs.img` |
| ubuntu | `output/update/Image/update.img` | `ubuntu/ubuntu-jammy.img` |

- 分区表：`device/rockchip/.chips/rk3566_rk3568/parameter-buildroot-fit.txt`（rootfs 已扩 12G）
- 烧录工具：RKDevTool（Windows）/ upgrade_tool（Linux），烧 `update.img` 即可

## 五、Docker 编译（无 sudo 用户）

```bash
# 镜像已构建（基础 ubuntu:22.04 + 交叉工具链）
docker run -d --name tspi-sdk-build --privileged \
  -v <SDK路径>:/home/liguoyi/EX_DISK_2T/tspi-1m-linux-kernel6-1-sdk/extracted_sdk \
  tspi-kernel6-1-env:latest sleep infinity

# 环境修复（binfmt + live-build）
docker exec -u liguoyi tspi-sdk-build bash <SDK>/tools/tspi-docker-env-fix.sh

# 编译
docker exec -u liguoyi tspi-sdk-build bash -c \
  'cd /home/liguoyi/EX_DISK_2T/tspi-1m-linux-kernel6-1-sdk/extracted_sdk && ./build.sh'
```

> **路径约束**：编译产物硬编码 `/home/liguoyi/EX_DISK_2T/tspi-1m-linux-kernel6-1-sdk/extracted_sdk`，
> 容器挂载目标必须与此一致，否则 fakeroot 报 `libfakeroot.so not found`。

## 六、已知问题速查

| 现象 | 解决 |
|---|---|
| buildroot 下载 404 | dl 缓存已预置（`buildroot/dl/`），零下载 |
| Debian 报 live-build 不支持 | 装 `tools/live-build-src`（1:20230131） |
| qemu-aarch64 broken | 容器内 `mount binfmt_misc` + `update-binfmts --enable qemu-aarch64` |
| fakeroot lib 找不到 | 挂载路径与硬编码路径一致 |
| cleanall 后交互式选 defconfig | 先重新 `./build.sh lunch:...` |
