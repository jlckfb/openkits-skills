#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""serial_log.py — 泰山派 RK3566 调试串口日志抓取（Windows/Linux 兼容）

默认波特率 1500000（泰山派调试串口）。

用法:
  python serial_log.py                       # 未指定端口时列出可用端口
  python serial_log.py --list                # 仅列出可用串口
  python serial_log.py --port COM13          # Windows
  python serial_log.py --port /dev/ttyUSB0   # Linux
  python serial_log.py -p COM13 -b 115200    # 指定波特率
  python serial_log.py -p COM13 --no-timestamp

特性:
  - 默认波特率 1500000
  - 每行时间戳（--no-timestamp 关闭）
  - UTF-8 容错（errors='replace'，不因乱码崩溃）
  - Ctrl+C 优雅退出并关闭串口（Windows 兼容）

依赖: pip install pyserial
"""
import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.stderr.write("缺少 pyserial，请先安装: pip install pyserial\n")
    sys.exit(1)


def list_available_ports():
    ports = list(list_ports.comports())
    if not ports:
        print("未发现串口设备")
        return
    for p in ports:
        print(f"{p.device}\t{p.description}")


def main():
    ap = argparse.ArgumentParser(description="泰山派 RK3566 串口日志抓取")
    ap.add_argument("--port", "-p", help="串口名，如 COM13 / /dev/ttyUSB0")
    ap.add_argument("--baud", "-b", type=int, default=1500000,
                    help="波特率（默认 1500000）")
    ap.add_argument("--list", "-l", action="store_true", help="列出可用串口")
    ap.add_argument("--no-timestamp", action="store_true", help="输出不加时间戳")
    ap.add_argument("--timeout", type=float, default=1.0,
                    help="读超时秒数（默认 1.0）")
    args = ap.parse_args()

    if args.list:
        list_available_ports()
        return 0

    if not args.port:
        print("未指定 --port，可用端口如下：")
        list_available_ports()
        print("示例: python serial_log.py --port COM13 --baud 1500000")
        return 1

    try:
        ser = serial.Serial(args.port, args.baud, timeout=args.timeout)
    except serial.SerialException as e:
        sys.stderr.write(f"打开 {args.port} 失败: {e}\n")
        return 1

    print(f"==> 已连接 {args.port} @ {args.baud}（Ctrl+C 退出）", flush=True)
    buf = bytearray()
    try:
        while True:
            data = ser.read(4096)
            if data:
                buf.extend(data)
                while b"\n" in buf:
                    line, _, buf = buf.partition(b"\n")
                    text = line.decode("utf-8", errors="replace")
                    if args.no_timestamp:
                        print(text, flush=True)
                    else:
                        ts = time.strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{ts}] {text}", flush=True)
            else:
                # 读超时：flush 未换行的尾部数据，避免卡住
                if buf:
                    text = buf.decode("utf-8", errors="replace")
                    if args.no_timestamp:
                        print(text, flush=True)
                    else:
                        ts = time.strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{ts}] {text}", flush=True)
                    buf.clear()
    except KeyboardInterrupt:
        print("\n==> 收到 Ctrl+C，退出。", flush=True)
    finally:
        try:
            ser.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())