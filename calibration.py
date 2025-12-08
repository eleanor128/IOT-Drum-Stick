from mpu6050 import mpu6050
import time
import datetime

sensor = mpu6050(0x68)

def log_once():
    a = sensor.get_accel_data()
    g = sensor.get_gyro_data()
    t = datetime.datetime.now().strftime("%H:%M:%S")

    print(f"[{t}]")
    print(f" Accel: x={a['x']:.4f}, y={a['y']:.4f}, z={a['z']:.4f}")
    print(f" Gyro : x={g['x']:.4f}, y={g['y']:.4f}, z={g['z']:.4f}")
    print("-" * 40)

print("開始 logging，每秒一筆（Ctrl+C 停止）")

while True:
    log_once()
    time.sleep(1)
