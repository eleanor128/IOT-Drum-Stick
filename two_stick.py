import smbus
import time
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

# 全域變數儲存最新數據
latest_data = {
    'right': {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}},
    'left': {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}},
    'timestamp': time.strftime('%H:%M:%S')
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


def read_mpu6050_data(address):
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

    return {
        'accel': {'x': acc_x_g, 'y': acc_y_g, 'z': acc_z_g},
        'gyro': {'x': gyro_x_dps, 'y': gyro_y_dps, 'z': gyro_z_dps}
    }


def update_sensor_data():
    """背景執行緒：持續更新感測器數據"""
    global latest_data

    print("初始化感測器...")
    init_mpu6050(RIGHT_DRUM_STICK)
    init_mpu6050(LEFT_DRUM_STICK)
    print("感測器初始化完成！")

    while True:
        try:
            latest_data['right'] = read_mpu6050_data(RIGHT_DRUM_STICK)
            latest_data['left'] = read_mpu6050_data(LEFT_DRUM_STICK)
            latest_data['timestamp'] = time.strftime('%H:%M:%S')
            time.sleep(0.1)  # 每 100ms 更新一次
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


if __name__ == "__main__":
    # 啟動背景執行緒讀取感測器數據
    sensor_thread = Thread(target=update_sensor_data, daemon=True)
    sensor_thread.start()

    print("\n" + "=" * 60)
    print("雙鼓棒即時監控系統")
    print("=" * 60)
    print("網頁伺服器啟動中...")
    print("請在瀏覽器開啟: http://localhost:5000")
    print("或從其他裝置開啟: http://<樹莓派IP>:5000")
    print("按 Ctrl+C 停止伺服器")
    print("=" * 60 + "\n")

    # 啟動 Flask 伺服器（允許外部連線）
    app.run(host='0.0.0.0', port=5000, debug=False)
