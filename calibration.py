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
    return statistics.mean(data)


def generate_calibration(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z):
    return {
        "left": {
            "accel_offset": {
                "x": compute_offset(accel_x),
                "y": compute_offset(accel_y),
                "z": compute_offset(accel_z) - 9.81  # 重力校正
            },
            "gyro_offset": {
                "x": compute_offset(gyro_x),
                "y": compute_offset(gyro_y),
                "z": compute_offset(gyro_z)
            },
            "accel_scale": {"x": 1, "y": 1, "z": 1},
            "gyro_scale": {"x": 1, "y": 1, "z": 1},
            "axis_mapping": {"x": "x", "y": "y", "z": "z"},
            "axis_invert": {"x": False, "y": False, "z": False},
            "rotation": {"pitch": 0, "roll": 0, "yaw": 0}
        },
        "right": "COPY LEFT LATER"  # 你之後可以改
    }


def save_json(data):
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Calibration saved to {SAVE_PATH}")


if __name__ == "__main__":
    ax, ay, az, gx, gy, gz = collect_data()
    calibration_data = generate_calibration(ax, ay, az, gx, gy, gz)
    save_json(calibration_data)
