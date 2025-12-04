import smbus
import time
import math
from flask import Flask, render_template, jsonify
from threading import Thread

# MPU6050 暫存器
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# 兩個 MPU6050 的 I2C 地址
RIGHT_DRUM_STICK = 0x68
LEFT_DRUM_STICK = 0x69

# 初始化 I2C (使用 bus 1)
bus = smbus.SMBus(1)

# Flask 應用程式
app = Flask(__name__)

# 校正偏移值（陀螺儀）
calibration = {
    'right': {'gyro': {'x': 0, 'y': 0, 'z': 0}},
    'left': {'gyro': {'x': 0, 'y': 0, 'z': 0}},
    'is_calibrated': False
}

# 全域變數儲存最新數據
latest_data = {
    'right': {
        'accel': {'x': 0, 'y': 0, 'z': 0},
        'gyro': {'x': 0, 'y': 0, 'z': 0},
        'angle': {'pitch': 0, 'roll': 0},
        'magnitude': 0,
        'is_hitting': False
    },
    'left': {
        'accel': {'x': 0, 'y': 0, 'z': 0},
        'gyro': {'x': 0, 'y': 0, 'z': 0},
        'angle': {'pitch': 0, 'roll': 0},
        'magnitude': 0,
        'is_hitting': False
    },
    'timestamp': time.strftime('%H:%M:%S'),
    'is_calibrated': False
}


def init_mpu6050(address):
    """初始化 MPU6050 感測器"""
    bus.write_byte_data(address, PWR_MGMT_1, 0)
    time.sleep(0.1)
    print(f"MPU6050 at address 0x{address:02X} initialized")


def read_raw_data(address, register):
    """從 MPU6050 讀取原始數據（16-bit）"""
    high = bus.read_byte_data(address, register)
    low = bus.read_byte_data(address, register + 1)
    value = (high << 8) | low
    if value > 32768:
        value = value - 65536
    return value


def read_mpu6050_data(address, stick_name):
    """讀取 MPU6050 的加速度和陀螺儀數據"""
    # 讀取加速度數據
    acc_x = read_raw_data(address, ACCEL_XOUT_H)
    acc_y = read_raw_data(address, ACCEL_XOUT_H + 2)
    acc_z = read_raw_data(address, ACCEL_XOUT_H + 4)

    # 讀取陀螺儀數據
    gyro_x = read_raw_data(address, GYRO_XOUT_H)
    gyro_y = read_raw_data(address, GYRO_XOUT_H + 2)
    gyro_z = read_raw_data(address, GYRO_XOUT_H + 4)

    # 轉換為實際單位
    acc_x_g = acc_x / 16384.0
    acc_y_g = acc_y / 16384.0
    acc_z_g = acc_z / 16384.0

    gyro_x_dps = gyro_x / 131.0
    gyro_y_dps = gyro_y / 131.0
    gyro_z_dps = gyro_z / 131.0

    # 應用校正偏移
    if calibration['is_calibrated']:
        gyro_x_dps -= calibration[stick_name]['gyro']['x']
        gyro_y_dps -= calibration[stick_name]['gyro']['y']
        gyro_z_dps -= calibration[stick_name]['gyro']['z']

    # 計算加速度總量（用於偵測打擊）
    magnitude = math.sqrt(acc_x_g**2 + acc_y_g**2 + acc_z_g**2)

    # 計算傾斜角度（俯仰角和翻滾角）
    # 根據你的安裝方式：PIN腳平行於鼓棒，朝向尾端
    # X軸：沿著鼓棒方向
    # Y軸：垂直鼓棒（左右）
    # Z軸：垂直鼓棒（上下）

    # 俯仰角 (Pitch)：鼓棒上下擺動的角度
    pitch = math.atan2(acc_y_g, math.sqrt(acc_x_g**2 + acc_z_g**2)) * 180 / math.pi

    # 翻滾角 (Roll)：鼓棒左右旋轉的角度
    roll = math.atan2(-acc_x_g, acc_z_g) * 180 / math.pi

    # 偵測打擊動作（加速度突然增大）
    is_hitting = magnitude > 2.0  # 閾值可調整

    return {
        'accel': {'x': acc_x_g, 'y': acc_y_g, 'z': acc_z_g},
        'gyro': {'x': gyro_x_dps, 'y': gyro_y_dps, 'z': gyro_z_dps},
        'angle': {'pitch': pitch, 'roll': roll},
        'magnitude': magnitude,
        'is_hitting': is_hitting
    }


def calibrate_sensors():
    """校正感測器（記錄靜止時的陀螺儀偏移）"""
    global calibration

    print("\n開始校正...")
    print("請將兩支鼓棒放在平穩的表面上，保持靜止...")
    time.sleep(2)

    samples = 50
    right_gyro_sum = {'x': 0, 'y': 0, 'z': 0}
    left_gyro_sum = {'x': 0, 'y': 0, 'z': 0}

    for i in range(samples):
        right_data = read_mpu6050_data(RIGHT_DRUM_STICK, 'right')
        left_data = read_mpu6050_data(LEFT_DRUM_STICK, 'left')

        right_gyro_sum['x'] += right_data['gyro']['x']
        right_gyro_sum['y'] += right_data['gyro']['y']
        right_gyro_sum['z'] += right_data['gyro']['z']

        left_gyro_sum['x'] += left_data['gyro']['x']
        left_gyro_sum['y'] += left_data['gyro']['y']
        left_gyro_sum['z'] += left_data['gyro']['z']

        time.sleep(0.02)
        print(f"\r校正進度: {i+1}/{samples}", end='')

    calibration['right']['gyro']['x'] = right_gyro_sum['x'] / samples
    calibration['right']['gyro']['y'] = right_gyro_sum['y'] / samples
    calibration['right']['gyro']['z'] = right_gyro_sum['z'] / samples

    calibration['left']['gyro']['x'] = left_gyro_sum['x'] / samples
    calibration['left']['gyro']['y'] = left_gyro_sum['y'] / samples
    calibration['left']['gyro']['z'] = left_gyro_sum['z'] / samples

    calibration['is_calibrated'] = True

    print("\n✓ 校正完成！")
    print(f"右手鼓棒陀螺儀偏移: X={calibration['right']['gyro']['x']:.2f}, "
          f"Y={calibration['right']['gyro']['y']:.2f}, "
          f"Z={calibration['right']['gyro']['z']:.2f}")
    print(f"左手鼓棒陀螺儀偏移: X={calibration['left']['gyro']['x']:.2f}, "
          f"Y={calibration['left']['gyro']['y']:.2f}, "
          f"Z={calibration['left']['gyro']['z']:.2f}")


def update_sensor_data():
    """背景執行緒：持續更新感測器數據"""
    global latest_data

    print("初始化感測器...")
    init_mpu6050(RIGHT_DRUM_STICK)
    init_mpu6050(LEFT_DRUM_STICK)
    print("感測器初始化完成！")

    # 自動校正
    calibrate_sensors()

    while True:
        try:
            latest_data['right'] = read_mpu6050_data(RIGHT_DRUM_STICK, 'right')
            latest_data['left'] = read_mpu6050_data(LEFT_DRUM_STICK, 'left')
            latest_data['timestamp'] = time.strftime('%H:%M:%S')
            latest_data['is_calibrated'] = calibration['is_calibrated']
            time.sleep(0.05)  # 每 50ms 更新一次（提高反應速度）
        except Exception as e:
            print(f"讀取錯誤: {e}")
            time.sleep(1)


@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """API：取得最新感測器數據"""
    return jsonify(latest_data)


@app.route('/api/calibrate', methods=['POST'])
def calibrate():
    """API：重新校正感測器"""
    try:
        calibrate_sensors()
        return jsonify({'status': 'success', 'message': '校正完成'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == "__main__":
    # 啟動背景執行緒讀取感測器數據
    sensor_thread = Thread(target=update_sensor_data, daemon=True)
    sensor_thread.start()

    print("\n" + "=" * 60)
    print("雙鼓棒即時監控系統（含校正與姿態偵測）")
    print("=" * 60)
    print("網頁伺服器啟動中...")
    print("請在瀏覽器開啟: http://localhost:5000")
    print("或從其他裝置開啟: http://<樹莓派IP>:5000")
    print("按 Ctrl+C 停止伺服器")
    print("=" * 60 + "\n")

    # 啟動 Flask 伺服器（允許外部連線）
    app.run(host='0.0.0.0', port=5000, debug=False)
