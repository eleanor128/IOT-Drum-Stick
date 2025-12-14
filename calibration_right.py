from mpu6050 import mpu6050
import time
import math
from ahrs.filters import Madgwick
from ahrs.common.orientation import q2euler

sensor = mpu6050(0x68)
# 設定傳感器量程，消除警告訊息
sensor.set_accel_range(mpu6050.ACCEL_RANGE_2G)
sensor.set_gyro_range(mpu6050.GYRO_RANGE_250DEG)

ACCEL_OFFSET = {"x": 0.0605, "y": -0.0385, "z": 0.4891}
GYRO_OFFSET  = {"x": -4.2941, "y": -1.2928, "z": 0.2246}

# Madgwick 濾波器初始化
madgwick = Madgwick(frequency=100, gain=0.033)
quaternion = [1.0, 0.0, 0.0, 0.0]  # 初始四元數 [w, x, y, z]

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
    # 正確的角度計算：
    # pitch (俯仰) = 繞 Y 軸 = 前後傾斜 = 使用 ay
    accel_pitch = math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))
    # roll (翻滾) = 繞 X 軸 = 左右傾斜 = 使用 ax
    accel_roll  = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))

    # 陀螺儀積分（對應正確的軸）
    gyro_pitch = pitch + gy * dt  # pitch 使用 gy
    gyro_roll  = roll  + gx * dt  # roll 使用 gx
    gyro_yaw   = yaw   + gz * dt  # yaw 使用 gz

    # 互補濾波
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


def update_right_angle():
    """hit_detection.py 會呼叫這裡，不會跑迴圈、不輸出"""
    global quaternion, prev_time

    now = time.time()
    dt = now - prev_time
    prev_time = now

    ax, ay, az, gx, gy, gz = get_calibrated()

    # 將角速度從 deg/s 轉換為 rad/s（Madgwick 需要）
    gx_rad = math.radians(gx)
    gy_rad = math.radians(gy)
    gz_rad = math.radians(gz)

    # 使用 Madgwick 濾波器更新姿態
    quaternion = madgwick.updateIMU(
        quaternion,
        gyr=[gx_rad, gy_rad, gz_rad],
        acc=[ax, ay, az]
    )

    # 從四元數計算歐拉角（弧度）
    roll_rad, pitch_rad, yaw_rad = q2euler(quaternion)

    # 轉換為度數
    roll = math.degrees(roll_rad)
    pitch = math.degrees(pitch_rad)
    yaw = math.degrees(yaw_rad)

    return roll, pitch, yaw, ax, ay, az, gx, gy, gz

# 修改