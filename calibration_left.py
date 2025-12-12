from mpu6050 import mpu6050
import time
import math

sensor = mpu6050(0x69)

ACCEL_OFFSET = {"x": 0.0605, "y": -0.0385, "z": 0.4891}
GYRO_OFFSET  = {"x": -4.2941, "y": -1.2928, "z": 0.2246}

pitch = 0.0
roll  = 0.0
yaw   = 0.0  
alpha = 0.96

prev_time = time.time()   # 用於自動計算 dt


def get_calibrated():
    a_raw = sensor.get_accel_data()
    g_raw = sensor.get_gyro_data()

    ax = a_raw['x'] - ACCEL_OFFSET['x']
    ay = a_raw['y'] - ACCEL_OFFSET['y']
    az = a_raw['z'] - ACCEL_OFFSET['z']

    gx = g_raw['x'] - GYRO_OFFSET['x']
    gy = g_raw['y'] - GYRO_OFFSET['y']
    gz = g_raw['z'] - GYRO_OFFSET['z']

    return ax, ay, az, gx, gy, gz


def complementary_filter(pitch, roll, yaw, ax, ay, az, gx, gy, gz, dt):

    accel_pitch = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))
    accel_roll  = math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))

    gyro_pitch = pitch + gx * dt
    gyro_roll  = roll  + gy * dt
    gyro_yaw   = yaw   + gz * dt  # 使用陀螺儀 Z 軸積分計算 yaw

    pitch = alpha * gyro_pitch + (1 - alpha) * accel_pitch
    roll  = alpha * gyro_roll  + (1 - alpha) * accel_roll
    # yaw 無法從加速度計算，只能使用陀螺儀積分
    yaw   = gyro_yaw

    # 將 yaw 歸一化到 -180° 到 +180° 範圍內
    while yaw > 180:
        yaw -= 360
    while yaw < -180:
        yaw += 360

    return pitch, roll, yaw


def update_angle():
    """hit_detection.py 會呼叫這裡，不會跑迴圈、不輸出"""
    global pitch, roll, yaw, prev_time

    now = time.time()
    dt = now - prev_time
    prev_time = now

    ax, ay, az, gx, gy, gz = get_calibrated()

    pitch, roll, yaw = complementary_filter(pitch, roll, yaw, ax, ay, az, gx, gy, gz, dt)

    return roll, pitch, yaw, ax, ay, az, gx, gy, gz
