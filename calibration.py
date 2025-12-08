from mpu6050 import mpu6050
import time
import datetime
import math

right_stick = mpu6050(0x68)

# 你的 offset（測量後填進來）
ACCEL_OFFSET_RIGHT = {"x": 0.0605, "y": -0.0385, "z": 0.4891}
GYRO_OFFSET_RIGHT  = {"x": -4.2941, "y": -1.2928, "z": 0.2246}

# 初始角度
pitch = 0.0
roll = 0.0
last_time = time.time()

def get_calibrated_data():
    a_raw = right_stick.get_accel_data()
    g_raw = right_stick.get_gyro_data()

    a = {
        "x": a_raw["x"] - ACCEL_OFFSET_RIGHT["x"],
        "y": a_raw["y"] - ACCEL_OFFSET_RIGHT["y"],
        "z": a_raw["z"] - ACCEL_OFFSET_RIGHT["z"]
    }

    g = {
        "x": g_raw["x"] - GYRO_OFFSET_RIGHT["x"],
        "y": g_raw["y"] - GYRO_OFFSET_RIGHT["y"],
        "z": g_raw["z"] - GYRO_OFFSET_RIGHT["z"]
    }

    return a_raw, g_raw, a, g


def get_angles(calibrated_accel, calibrated_gyro):
    global pitch, roll, last_time

    ax = calibrated_accel["x"]
    ay = calibrated_accel["y"]
    az = calibrated_accel["z"]

    gx = calibrated_gyro["x"]
    gy = calibrated_gyro["y"]

    # dt（秒）
    now = time.time()
    dt = now - last_time
    last_time = now

    # 加速度取得角度（短期爛、長期準）
    accel_pitch = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))
    accel_roll  = math.degrees(math.atan2(ay, az))

    # 陀螺儀角度累積（短期準、長期飄）
    pitch += gx * dt
    roll  += gy * dt

    # 融合（Complementary Filter）
    pitch = pitch * 0.98 + accel_pitch * 0.02
    roll  = roll * 0.98 + accel_roll * 0.02

    return pitch, roll


def log_once():
    a_raw, g_raw, a, g = get_calibrated_data()
    pitch, roll = get_angles(a, g)
    t = datetime.datetime.now().strftime("%H:%M:%S")

    print(f"[{t}]")
    print(f" Raw Accel:  x={a_raw['x']:.4f}, y={a_raw['y']:.4f}, z={a_raw['z']:.4f}")
    print(f" Cal Accel:  x={a['x']:.4f}, y={a['y']:.4f}, z={a['z']:.4f}")
    print(f" Raw Gyro :  x={g_raw['x']:.4f}, y={g_raw['y']:.4f}, z={g_raw['z']:.4f}")
    print(f" Cal Gyro :  x={g['x']:.4f}, y={g['y']:.4f}, z={g['z']:.4f}")
    print(f" Pitch={pitch:.2f}°, Roll={roll:.2f}°")
    print("-" * 40)


print("開始 logging，每秒一筆（Ctrl+C 停止）")

while True:
    log_once()
    time.sleep(1)
