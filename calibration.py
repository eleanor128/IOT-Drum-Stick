from mpu6050 import mpu6050
import time
import datetime

sensor = mpu6050(0x68)   # 預設 I2C 位址

def log_once():
    accel = sensor.get_accel_data()
    gyro = sensor.get_gyro_data()
    temp = sensor.get_temp()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[{now}]")
    print(f" Accel: x={accel['x']:.4f}, y={accel['y']:.4f}, z={accel['z']:.4f}")
    print(f" Gyro : x={gyro['x']:.4f}, y={gyro['y']:.4f}, z={gyro['z']:.4f}")
    print(f" Temp : {temp:.2f} °C")
    print("-" * 40)

if __name__ == "__main__":
    print("開始 logging，每秒更新一次（Ctrl+C 結束）")
    while True:
        log_once()
        time.sleep(1)
