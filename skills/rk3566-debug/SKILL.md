---
name: rk3566-debug
description: 'RK3566 (TaishanPi 1M) debugging & troubleshooting: adb, serial log, dmesg, known-issue resolution.'
---

# rk3566-debug — 泰山派 RK3566 调试与排障

## 使用前提（环境确认）

> 调用本 skill 前，先确认以下两项；缺什么就给什么。

1. **板子**：有泰山派 1M 板子，且已烧录可启动固件（固件编译/烧录见 `rk3566-sdk-build`）。
2. **调试通道**（至少一个）：
   - **adb**：板子 USB 连电脑，`adb devices -l` 能识别
   - **串口**：CH340 USB 转串口，波特率 **1500000**（脚本：`<skill_dir>/scripts/serial_log.py --port COMx --baud 1500000`）

确认完毕再进入排障流程。

## 交互方式（逐步引导）

调用本 skill 后：
1. **先复述确认**：向用户复述问题，确认需求范围（如：查引脚 / 改 DTS / 编译哪个系统 / 排查什么故障）。
2. **分步输出**：每步给 1-2 条关键信息 + 简短说明，不一次性倾倒全部内容。
3. **关键决策给选项**：涉及选型/方向（如选哪个 UART、哪个系统、哪个修复方案）时，列出选项让用户确认。
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



**适用**：板子启动异常、显示黑屏、网络/adb 不可用等问题排查

> **Android13 系统差异**：本 skill 的调试通道（adb / 串口 1500000 / dmesg）对 Android 同样适用。
> - Android 的 adb **默认开启**（无需配置 usbdevice，Linux 才需要）
> - 串口日志波特率同为 1500000，抓取脚本相同（`<skill_dir>/scripts/serial_log.py`）
> - Android 常用：`adb shell dmesg` / `adb logcat`（应用日志）/ `adb reboot loader`（进烧录模式）
> - Android 固件编译/烧录见 `rk3566-android-build` skill


## 一、调试通道

### ADB（最常用）

```bash
adb devices -l          # 查看设备
adb shell               # 进入 shell
adb shell dmesg | tail  # 内核日志
adb shell "cat /sys/class/drm/card0-HDMI-A-1/status"  # 显示状态
```

> Ubuntu 系统 adbd 已开机自启；Buildroot/Debian 需确认 usb gadget 配置。

### 串口（UART，1500000 波特率）

```bash
# 抓串口日志（推荐配套脚本：时间戳 / UTF-8 容错 / Ctrl+C 优雅退出）
python <skill_dir>/scripts/serial_log.py --port COM13 --baud 1500000
python <skill_dir>/scripts/serial_log.py --list          # 列出可用端口
# 省略 --baud 时默认 1500000
```

- 泰山派调试串口波特率 **1500000**
- 常用：COM6/COM13（CH340）

## 二、启动问题排查

### 卡在 logo

1. 串口看日志是否卡在 network：`A start job is running for Raise network interfaces`
   - 修复：`/etc/network/interfaces.d/network-priority` 里接口用 `allow-hotplug` 而非 `auto`
2. 检查磁盘：`df -h /` —— 若 100% 满，一切服务起不来（见下文"磁盘满"）

### rootfs 磁盘满

```bash
df -h /
# 若满：扩容文件系统到分区大小
resize2fs /dev/mmcblk0p6    # 或 /dev/root 对应设备
```

> **根因**：mk-image.sh 的 `resize2fs -M` 会把文件系统缩到最小（5.3G），烧进 12G 分区后仍 5.3G。已修复（mk-image.sh 直接扩 12G）。

### HDMI 黑屏

```bash
# 1. 确认 HDMI 检测
cat /sys/class/drm/card0-HDMI-A-1/status   # 应 connected
# 2. 查 Xorg 日志
tail /var/log/Xorg.0.log
# glamor initialization failed = GPU 驱动问题
#   修复：安装 libmali（Ubuntu: dpkg -i libmali-bifrost-g52-*-x11*.deb）
# 3. 查磁盘（磁盘满会导致 X 崩溃）
df -h /
```

## 三、ADB 不可用

```bash
# 1. 确认服务
adb shell systemctl status adbd.service 2>/dev/null || adb shell ls /usr/bin/usbdevice
# 2. Ubuntu 缺 usbdevice 文件（已知问题，已修复进 repo）
#    缺失时从 debian/overlay 复制：
#      usbdevice, /etc/profile.d/adbd.sh, /etc/profile.d/usbdevice.sh
# 3. 启用自启
adb shell systemctl enable adbd.service
```

## 四、WiFi 扫描为空

```bash
nmcli dev status          # 看 wlan0 是否 unmanaged
nmcli device wifi list    # 扫描
```

- **unmanaged** → NetworkManager 不接管（`managed=false` 或 unmanaged-devices）
  - 修复：`NetworkManager.conf` 改 `managed=true`，移除 wlan0 的 unmanaged 配置
- **扫描空但接口 UP** → 检查天线是否接好（硬件）

## 五、网络/外设验证

```bash
# USB hub
lsusb | grep -i hub
# 网口（无网线时 NO-CARRIER 正常，检测到接口即 OK）
ip link show eth0
# EC20 4G
ls /dev/ttyUSB*  && ip addr show ec20
# WiFi
nmcli device wifi list
```

## 六、常见问题速查表

| 现象 | 根因 | 解决 |
|---|---|---|
| 卡 logo + network job | 接口 auto+dhcp 阻塞 | 改 allow-hotplug |
| HDMI 黑屏 | 磁盘满 或 libmali 缺失 | 扩容 / 装 libmali |
| adb devices 空 | usbdevice 缺失/未 enable | 补齐 3 文件 + enable |
| WiFi 扫描空 | NM 不管理 / 天线 | managed=true / 接天线 |
| oem/userdata 挂载失败 | fstab ext2 挂 ext4 | 改 ext4 |
| X 服务崩溃循环 | rootfs 磁盘满 | resize2fs 扩容 |
