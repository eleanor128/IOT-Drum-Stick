from mpu6050 import mpu6050
import time
import json
import statistics

sensor = mpu6050(0x68)

SAMPLES = 200        # 收集多少筆資料（200筆 ≈ 5 秒）
DELAY = 0.025        # 每筆延遲 (40Hz)
SAVE_PATH = "calibration.json"

def collect_data():
    accel_x = []
    accel_y = []
    accel_z = []
    gyro_x = []
    gyro_y = []
    gyro_z = []

    print("開始收集靜止資料（請保持感測器不動）...")

    for _ in range(SAMPLES):
        a = sensor.get_accel_data()
        g = sensor.get_gyro_data()

        accel_x.append(a["x"])
        accel_y.append(a["y"])
        accel_z.append(a["z"])
        gyro_x.append(g["x"])
        gyro_y.append(g["y"])
        gyro_z.append(g["z"])

        time.sleep(DELAY)

    print("資料收集完成！\n")
    return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z


def compute_offset(data):
    return statistics.mean
