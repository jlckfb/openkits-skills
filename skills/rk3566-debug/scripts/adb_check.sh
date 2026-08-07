#!/bin/bash
# adb_check.sh — 泰山派 RK3566 adb 连通性检查 + 修复建议
# 用法: ./adb_check.sh [设备序列号]
#   - 不传参数：检查当前连接的全部设备
#   - 传序列号：只检查指定设备
set -u

DEV="${1:-}"
MISSING=0

echo "==> 1. adb devices"
adb devices -l
if [ -n "$DEV" ] && ! adb devices -l | grep -q "${DEV}"; then
    echo "    [失败] 未找到设备: $DEV"
    exit 1
fi

echo ""
echo "==> 2. adb shell 连通性"
if ! adb shell echo ok 2>/dev/null | grep -q ok; then
    echo "    [失败] adb shell 不通"
    echo "    建议:"
    echo "      - 确认 USB 数据线（非充电线）已连接"
    echo "      - 确认板子已开机、adbd 已启动"
    echo "      - Linux: sudo adb kill-server && sudo adb start-server"
    echo "      - Windows: 设备管理器确认 Rockchip/ADB 驱动正常"
    exit 1
fi
echo "    [OK] adb shell 已连通"

echo ""
echo "==> 3. 检查 usbdevice 三文件"
# Ubuntu 已知问题：缺少这三文件则 adb 不可用
for f in /usr/bin/usbdevice /etc/profile.d/adbd.sh /etc/profile.d/usbdevice.sh; do
    if adb shell "test -f $f && echo FOUND" 2>/dev/null | grep -q FOUND; then
        echo "    [OK] $f"
    else
        echo "    [缺失] $f"
        MISSING=1
    fi
done

echo ""
echo "==> 4. adbd 服务状态"
if adb shell systemctl is-active adbd.service 2>/dev/null | grep -q active; then
    echo "    [OK] adbd.service 运行中"
elif [ "$MISSING" -eq 0 ]; then
    echo "    adbd.service 未运行，尝试启用自启:"
    echo "      adb shell systemctl enable adbd.service"
    echo "      adb shell systemctl start adbd.service"
fi

echo ""
if [ "$MISSING" -ne 0 ]; then
    echo "==> 修复建议（usbdevice 三文件缺失，Ubuntu 已知问题）:"
    echo "    从 SDK debian/overlay 复制到板子:"
    echo "      usbdevice      -> /usr/bin/usbdevice"
    echo "      adbd.sh        -> /etc/profile.d/adbd.sh"
    echo "      usbdevice.sh   -> /etc/profile.d/usbdevice.sh"
    echo "    之后重启板子，或直接烧录已修复的 rootfs。"
    echo "    参考 SKILL.md「三、ADB 不可用」。"
else
    echo "==> usbdevice 三文件齐全。"
fi