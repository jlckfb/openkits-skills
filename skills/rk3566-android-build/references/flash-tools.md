# Android13 固件烧录 — RKDevTool / rkdeveloptool

> 与 Linux SDK（`rk3566-sdk-build`）烧录方式相同，均烧 `update.img`。
> 详细 RKDevTool 使用见 `rk3566-sdk-build/references/flash-tools.md`（同板同工具）。

## 产物位置

- 完整固件：`rockdev/Image-rk3566_tspi_1m/update.img`（约 1.8G）
- 单分区：`rockdev/Image-rk3566_tspi_1m/`（uboot.img / boot.img / super.img / dtbo.img / recovery.img 等）

> 实测 Android13 的 update.img 在 `rockdev/Image-rk3566_tspi_1m/` 子目录下，**不在** `rockdev/` 根目录。

## Windows 烧录（RKDevTool）

1. 打开 RKDevTool，板子进入 **Loader 模式**（按住 RECOVERY/音量键 + 上电，或 adb reboot loader）
2. 选中 update.img 固件
3. 点"执行"烧录

## Linux 烧录（rkdeveloptool）

```bash
# 板子进 Loader 模式后
sudo rkdeveloptool ld                       # 列出设备
sudo rkdeveloptool db MiniLoaderAll.bin     # 下载 loader
sudo rkdeveloptool wl 0 update.img          # 写入 update.img（偏移 0）
sudo rkdeveloptool rd                       # 重启
```

## 验证

- 烧录完成后首次启动较慢（Android 首次开机初始化），等待进入桌面/launcher
- `adb devices -l` 应出现设备（Android adb 默认开启）
- 串口日志波特率 **1500000**（CH340，COM6/COM13）
