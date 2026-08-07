# RK3566 烧录工具与 rootfs 分区表说明

> 配套：[SKILL.md 产物位置](../SKILL.md)、[sdk-layout.md](./sdk-layout.md)

## 一、烧录工具选择

| 工具 | 平台 | 说明 |
|---|---|---|
| RKDevTool | Windows | GUI，整包/分区烧录，需先装 Rockchip 驱动 |
| upgrade_tool | Linux | 命令行：`upgrade_tool uf update.img`、`upgrade_tool ld` |
| rkdeveloptool | Linux | 底层工具（进阶，一般不需要） |

## 二、进入 Loader / MaskROM 模式

- **Loader 模式**：上电前按住 **RECOVERY** 键 → 上电 → `upgrade_tool ld` 应列出 `Loader` 设备
- **MaskROM 模式**：`upgrade_tool ld` 显示 `Maskrom`（固件损坏时的恢复模式）
- Windows 首次使用需安装 Rockchip 驱动（DriverAssitant），否则设备管理器显示未知设备

## 三、烧录 update.img（整包）

### Windows（RKDevTool）

1. 打开 RKDevTool，连接板子并进入 Loader 模式
2. 工具自动识别设备（右侧显示 Loader）
3. 切到"升级固件"页 → 加载 `update.img` → 点"升级"
4. 等待写入完成，板子自动重启

### Linux（upgrade_tool）

```bash
sudo upgrade_tool ld              # 列出设备（应看到 Loader/Maskrom）
sudo upgrade_tool uf update.img   # 整包烧录（最常用）
sudo upgrade_tool rd              # 复位设备
```

> `uf`（upgrade firmware）整包烧录即可；无需手动拆分区。

## 四、rootfs 12G 分区表说明

分区表文件：`device/rockchip/.chips/rk3566_rk3568/parameter-buildroot-fit.txt`

RK parameter 分区表用 `CMDLINE: mtdparts=...` 描述每个分区：

```
CMDLINE: mtdparts=rk29xxnand:0x00002000@0x00004000(uboot),... ,0x0001800000@... (rootfs)
```

- 每段格式：`size@offset(name)`，**size/offset 单位为 512B sector**
- 换算：`1 MiB = 2048 sectors`
- **12 GiB ≈ 25165824 sectors ≈ 0x1800000 sectors**
  （12 × 1024 × 1024 × 1024 ÷ 512 = 25165824 = 0x1800000）
- 分区对齐：RK 工具通常按 0x20000（128KB）对齐，修改分区大小时保持对齐

### 背景：为什么 rootfs 曾被"缩水"

- 旧 `mk-image.sh` 用 `resize2fs -M` 把文件系统缩到最小（约 5.3G），烧进 12G 分区后根分区仍只有 5.3G → 磁盘满
- 已修复：直接扩到 12G，使文件系统大小与分区表一致
- 排查磁盘满：`df -h /` 显示远小于分区，说明文件系统未扩满，用 `resize2fs /dev/mmcblk0p6` 等命令扩容（见 rk3566-debug skill）

## 五、常见烧录问题

| 现象 | 处理 |
|---|---|
| 设备管理器显示未知设备 | 安装 Rockchip 驱动（DriverAssitant） |
| `upgrade_tool ld` 无设备 | 检查 RECOVERY 键是否按住、USB 线是否为数据线 |
| 烧录中断/失败 | 重新进入 Loader，重新整包烧录 |
| 烧完不启动 | 确认 parameter 与固件匹配；`uf` 后再 `rd` 复位 |
| 烧录后 rootfs 仍小 | `resize2fs` 扩容（见上） |