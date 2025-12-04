#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即時讀取兩個 MPU6050 感測器的數據（不包含溫度）
MPU6050 #1: 地址 0x68
MPU6050 #2: 地址 0x69
"""

import smbus
import time

# MPU6050 暫存器
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# 兩個 MPU6050 的 I2C 地址
MPU6050_ADDR_1 = 0x68  # 第一個感測器（AD0 接地或懸空）
MPU6050_ADDR_2 = 0x69  # 第二個感測器（AD0 接 VCC）

# 初始化 I2C (使用 bus 1)
bus = smbus.SMBus(1)


def init_mpu6050(address):
    """初始化 MPU6050 感測器"""
    # 喚醒 MPU6050（預設是睡眠模式）
    bus.write_byte_data(address, PWR_MGMT_1, 0)
    time.sleep(0.1)
    print(f"MPU6050 at address 0x{address:02X} initialized")


def read_raw_data(address, register):
    """從 MPU6050 讀取原始數據（16-bit）"""
    # 讀取高位元組和低位元組
    high = bus.read_byte_data(address, register)
    low = bus.read_byte_data(address, register + 1)

    # 合併成 16-bit 值
    value = (high << 8) | low

    # 轉換為有符號數
    if value > 32768:
        value = value - 65536

    return value


def read_mpu6050_data(address):
    """讀取 MPU6050 的加速度和陀螺儀數據"""
    # 讀取加速度數據
    acc_x = read_raw_data(address, ACCEL_XOUT_H)
    acc_y = read_raw_data(address, ACCEL_XOUT_H + 2)
    acc_z = read_raw_data(address, ACCEL_XOUT_H + 4)

    # 讀取陀螺儀數據
    gyro_x = read_raw_data(address, GYRO_XOUT_H)
    gyro_y = read_raw_data(address, GYRO_XOUT_H + 2)
    gyro_z = read_raw_data(address, GYRO_XOUT_H + 4)

    # 轉換為實際單位
    # 加速度：LSB Sensitivity = 16384 LSB/g (±2g range)
    acc_x_g = acc_x / 16384.0
    acc_y_g = acc_y / 16384.0
    acc_z_g = acc_z / 16384.0

    # 陀螺儀：LSB Sensitivity = 131 LSB/(°/s) (±250°/s range)
    gyro_x_dps = gyro_x / 131.0
    gyro_y_dps = gyro_y / 131.0
    gyro_z_dps = gyro_z / 131.0

    return {
        'accel': {'x': acc_x_g, 'y': acc_y_g, 'z': acc_z_g},
        'gyro': {'x': gyro_x_dps, 'y': gyro_y_dps, 'z': gyro_z_dps}
    }


def main():
    """主程式"""
    print("=" * 60)
    print("雙 MPU6050 即時數據讀取程式")
    print("=" * 60)

    try:
        # 初始化兩個 MPU6050
        init_mpu6050(MPU6050_ADDR_1)
        init_mpu6050(MPU6050_ADDR_2)

        print("\n開始讀取數據... (按 Ctrl+C 停止)\n")
        time.sleep(1)

        # 持續讀取數據
        while True:
            # 讀取兩個感測器的數據
            data1 = read_mpu6050_data(MPU6050_ADDR_1)
            data2 = read_mpu6050_data(MPU6050_ADDR_2)

            # 清空終端機（可選）
            # print("\033[2J\033[H", end="")

            # 顯示數據
            print("=" * 60)
            print(f"時間: {time.strftime('%H:%M:%S')}")
            print("-" * 60)

            # 感測器 1
            print("【感測器 1 - 0x68】")
            print(f"  加速度 (g):   X={data1['accel']['x']:7.3f}  Y={data1['accel']['y']:7.3f}  Z={data1['accel']['z']:7.3f}")
            print(f"  陀螺儀 (°/s): X={data1['gyro']['x']:7.2f}  Y={data1['gyro']['y']:7.2f}  Z={data1['gyro']['z']:7.2f}")

            print("-" * 60)

            # 感測器 2
            print("【感測器 2 - 0x69】")
            print(f"  加速度 (g):   X={data2['accel']['x']:7.3f}  Y={data2['accel']['y']:7.3f}  Z={data2['accel']['z']:7.3f}")
            print(f"  陀螺儀 (°/s): X={data2['gyro']['x']:7.2f}  Y={data2['gyro']['y']:7.2f}  Z={data2['gyro']['z']:7.2f}")

            print("=" * 60)
            print()

            # 延遲（調整讀取頻率）
            time.sleep(0.1)  # 每 100ms 讀取一次

    except KeyboardInterrupt:
        print("\n\n程式已停止")

    except Exception as e:
        print(f"\n錯誤: {e}")
        print("\n請確認:")
        print("1. 兩個 MPU6050 已正確連接")
        print("2. 第一個 MPU6050 的 AD0 接地 (地址 0x68)")
        print("3. 第二個 MPU6050 的 AD0 接 VCC (地址 0x69)")
        print("4. I2C 已啟用 (sudo raspi-config)")


if __name__ == "__main__":
    main()
