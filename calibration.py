from mpu6050 import mpu6050
import time
import statistics
import datetime

sensor = mpu6050(0x68)

LOG_HZ = 10             # 每秒10筆，想要 1Hz 就改成 1
INTERVAL = 1 / LOG_HZ   # 每筆間隔 0.1 秒
BASELINE_SEC = 1        # 前 1 秒做 baseline
BASELINE_SAMPLES = LOG_HZ * BASELINE_SEC

# 收集 baseline （前1秒）
def collect_baseline():
    print("正在收集 baseline（請保持靜止 1 秒）…")
    ax = []
    ay = []
    az = []
    gx = []
    gy = []
    gz = []

    for _ in range(BASELINE_SAMPLES):
        a = sensor.get_accel_data()
        g = sensor.get_gyro_data()

        ax.append(a["x"])
        ay.append(a["y"])
        az.append(a["z"])

        gx.append(g["x"])
        gy.append(g["y"])
        gz.append(g["z"])

        time.sleep(INTERVAL)

    print("Baseline 收集完成\n")

    return {
        "accel": {
            "x": statistics.mean(ax),
            "y": statistics.mean(ay),
            "z": statistics.mean(az),
        },
        "gyro": {
            "x": statistics.mean(gx),
            "y": statistics.mean(gy),
            "z": statistics.mean(gz),
        },
    }


def live_log(baseline):
    print("開始連續 log （Ctrl+C 停止）")
    while True:
        a = sensor.get_accel_data()
        g = sensor.get_gyro_data()
        now = datetime.datetime.now().strftime("%H:%M:%S")

        # 計算 Δ（方便看漂移）
        da = {k: a[k] - baseline["accel"][k] for k in a}
        dg = {k: g[k] - baseline["gyro"][k] for k in g}

        print(f"[{now}]")
        print(f" Accel: x={a['x']:.4f} (Δ={da['x']:+.4f}), "
              f"y={a['y']:.4f} (Δ={da['y']:+.4f}), "
              f"z={a['z']:.4f} (Δ={da['z']:+.4f})")

        print(f" Gyro : x={g['x']:.4f} (Δ={dg['x']:+.4f}), "
              f"y={g['y']:.4f} (Δ={dg['y']:+.4f}), "
              f"z={g['z']:.4f} (Δ={dg['z']:+.4f})")

        print("-" * 60)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    baseline = collect_baseline()
    live_log(baseline)
