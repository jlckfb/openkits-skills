#!/bin/bash
# rk3566-sdk-build 配套脚本：编译 buildroot/debian/ubuntu
# 用法: ./build.sh <system> [defconfig]
#   system: buildroot | debian | ubuntu
#   defconfig 默认: rockchip_rk3566_taishanpi_1m_v10_defconfig
set -e

SYSTEM="${1:-buildroot}"
DEFCONFIG="${2:-rockchip_rk3566_taishanpi_1m_v10_defconfig}"
SDK_DIR="${SDK_DIR:-$(pwd)}"
JOBS="${JOBS:-$(nproc)}"

echo "==> 系统: $SYSTEM"
echo "==> SDK: $SDK_DIR"
cd "$SDK_DIR"

# 1. lunch
echo "==> lunch $DEFCONFIG"
./build.sh lunch:$DEFCONFIG

# 2. 编译
case "$SYSTEM" in
  buildroot)
    ./build.sh
    ;;
  debian)
    # 装 live-build 1:20230131（SDK 自带源码）
    if [ -d tools/live-build-src ]; then
      echo "==> 安装 live-build 1:20230131"
      (cd tools/live-build-src && rm -rf manpages/po/ && sudo make install -j"$JOBS")
    fi
    RK_ROOTFS_SYSTEM=debian ./build.sh
    ;;
  ubuntu)
    echo "==> Ubuntu 编译需进入 ubuntu/ 目录按 wiki 流程"
    echo "    参考: cd ubuntu && sudo env GUI=desktop bash mk-base-ubuntu.sh"
    echo "    然后 mk-ubuntu-rootfs.sh -> mk-image.sh -> ./build.sh updateimg"
    ;;
  *)
    echo "错误: 未知系统 $SYSTEM (buildroot|debian|ubuntu)" >&2
    exit 1
    ;;
esac

echo "==> 完成。固件在 output/update/Image/update.img"
