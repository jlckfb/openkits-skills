#!/usr/bin/env python3
"""Minimal serial console for UART debug output."""
from __future__ import annotations

import sys
import time
from datetime import datetime


def main(port: str, baud: int = 115200, duration: int = 0) -> None:
    try:
        import serial
    except ImportError:
        print("pyserial required: pip install pyserial")
        sys.exit(1)

    try:
        ser = serial.Serial(port, baud, timeout=1)
    except serial.SerialException as e:
        print(f"Cannot open {port}: {e}")
        sys.exit(1)

    print(f"Connected to {port} @ {baud} baud. Ctrl+C to stop.")
    start = time.time()

    try:
        while True:
            if duration and (time.time() - start) > duration:
                break
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                ts = datetime.now().strftime("%H:%M:%S.%f")[:12]
                try:
                    text = data.decode("utf-8", errors="replace")
                    print(f"[{ts}] {text}", end="", flush=True)
                except Exception:
                    print(f"[{ts}] {data.hex()}")
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        print("\nDisconnected.")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="MSPM0 serial console")
    p.add_argument("port", help="COM port (e.g. COM6)")
    p.add_argument("-b", "--baud", type=int, default=115200)
    p.add_argument("-d", "--duration", type=int, default=0,
                   help="Duration in seconds (0 = forever)")
    p.add_argument("--list", action="store_true",
                   help="List available serial ports")
    args = p.parse_args()

    if args.list:
        try:
            import serial.tools.list_ports
            for port_info in serial.tools.list_ports.comports():
                print(f"{port_info.device}: {port_info.description}")
        except Exception:
            print("Cannot list ports. Install pyserial: pip install pyserial")
    else:
        main(args.port, args.baud, args.duration)
