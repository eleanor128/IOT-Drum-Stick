from mpu6050 import mpu6050
import time
import datetime

sensor = mpu6050(0x68)

# 你的 offset（測量後填進來）
ACCEL_OFFSET = {"x": 0.0571, "y": -0.4970, "z": 0.4590}
GYRO_OFFSET  = {"x": -4.1900, "y": -1.2740, "z": 0.2100}



def get_calibrated_data():
    a_raw = sensor.get_accel_data()
    g_raw = sensor.get_gyro_data()

    a = {
        "x": a_raw["x"] - ACCEL_OFFSET["x"],
        "y": a_raw["y"] - ACCEL_OFFSET["y"],
        "z": a_raw["z"] - ACCEL_OFFSET["z"]
    }

    g = {
        "x": g_raw["x"] - GYRO_OFFSET["x"],
        "y": g_raw["y"] - GYRO_OFFSET["y"],
        "z": g_raw["z"] - GYRO_OFFSET["z"]
    }

    return a_raw, g_raw, a, g

def log_once():
    a_raw, g_raw, a, g = get_calibrated_data()
    t = datetime.datetime.now().strftime("%H:%M:%S")

    print(f"[{t}]")
    print(f" Raw Accel:  x={a_raw['x']:.4f}, y={a_raw['y']:.4f}, z={a_raw['z']:.4f}")
    print(f" Cal Accel:  x={a['x']:.4f}, y={a['y']:.4f}, z={a['z']:.4f}")
    print(f" Raw Gyro :  x={g_raw['x']:.4f}, y={g_raw['y']:.4f}, z={g_raw['z']:.4f}")
    print(f" Cal Gyro :  x={g['x']:.4f}, y={g['y']:.4f}, z={g['z']:.4f}")
    print("-" * 40)

print("開始 logging，每秒一筆（Ctrl+C 停止）")

while True:
    log_once()
    time.sleep(1)
