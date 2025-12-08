from mpu6050 import mpu6050
import time
import math

sensor = mpu6050(0x68)

ACCEL_OFFSET = {"x": 0.0605, "y": -0.0385, "z": 0.4891}
GYRO_OFFSET  = {"x": -4.2941, "y": -1.2928, "z": 0.2246}

# 初始角度
pitch = 0.0
roll  = 0.0

alpha = 0.98      # 互補濾波係數
dt = 0.01         # 100 Hz 更新頻率（你可改）

def get_calibrated():
    a_raw = sensor.get_accel_data()
    g_raw = sensor.get_gyro_data()

    ax = a_raw['x'] - ACCEL_OFFSET['x']
    ay = a_raw['y'] - ACCEL_OFFSET['y']
    az = a_raw['z'] - ACCEL_OFFSET['z']

    gx = (g_raw['x'] - GYRO_OFFSET['x'])
    gy = (g_raw['y'] - GYRO_OFFSET['y'])
    gz = (g_raw['z'] - GYRO_OFFSET['z'])

    return ax, ay, az, gx, gy, gz


def complementary_filter(pitch, roll, ax, ay, az, gx, gy, dt):

    # 加速度角度（慢但穩）
    accel_pitch = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))
    accel_roll  = math.degrees(math.atan2(ay, az))

    # 陀螺儀角度（快但會漂移）
    gyro_pitch = pitch + gx * dt
    gyro_roll  = roll  + gy * dt

    # 互補濾波融合
    pitch = alpha * gyro_pitch + (1 - alpha) * accel_pitch
    roll  = alpha * gyro_roll  + (1 - alpha) * accel_roll

    return pitch, roll


print("開始角度追蹤 (Ctrl+C 停止)")

while True:
    ax, ay, az, gx, gy, gz = get_calibrated()

    pitch, roll = complementary_filter(pitch, roll, ax, ay, az, gx, gy, dt)

    print(f"Pitch={pitch:.2f}°,  Roll={roll:.2f}°")
    time.sleep(dt)
