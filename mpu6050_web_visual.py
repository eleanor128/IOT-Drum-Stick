"""
MPU6050 Web-based 3D Visualization
透過 Flask 和 Three.js 在瀏覽器即時顯示 MPU6050 感測器的 3D 姿態
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import mpu6050
import math
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mpu6050-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全域變數
sensor = None
sensor_data = {
    'roll': 0.0,
    'pitch': 0.0,
    'yaw': 0.0,
    'accel': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'gyro': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'temperature': 0.0
}

# 互補濾波器參數
alpha = 0.98
dt = 0.01

def init_sensor():
    """初始化 MPU6050 感測器"""
    global sensor
    try:
        sensor = mpu6050.mpu6050(0x68)
        print("✓ MPU6050 感測器初始化成功")
        return True
    except Exception as e:
        print(f"✗ MPU6050 初始化失敗: {e}")
        return False

def calculate_angles():
    """計算 Roll, Pitch, Yaw 角度（使用互補濾波器）"""
    global sensor_data
    
    if sensor is None:
        return
    
    try:
        # 讀取加速度計和陀螺儀數據
        accel = sensor.get_accel_data()
        gyro = sensor.get_gyro_data()
        temp = sensor.get_temp()
        
        # 從加速度計計算角度（度）
        accel_roll = math.atan2(accel['y'], accel['z']) * 180 / math.pi
        accel_pitch = math.atan2(-accel['x'], math.sqrt(accel['y']**2 + accel['z']**2)) * 180 / math.pi
        
        # 從陀螺儀積分角度
        gyro_roll = sensor_data['roll'] + gyro['x'] * dt
        gyro_pitch = sensor_data['pitch'] + gyro['y'] * dt
        gyro_yaw = sensor_data['yaw'] + gyro['z'] * dt
        
        # 互補濾波器融合
        sensor_data['roll'] = alpha * gyro_roll + (1 - alpha) * accel_roll
        sensor_data['pitch'] = alpha * gyro_pitch + (1 - alpha) * accel_pitch
        sensor_data['yaw'] = gyro_yaw
        
        # 更新其他數據
        sensor_data['accel'] = accel
        sensor_data['gyro'] = gyro
        sensor_data['temperature'] = temp
        
    except Exception as e:
        print(f"讀取感測器數據錯誤: {e}")

def sensor_loop():
    """感測器數據讀取迴圈"""
    print("啟動感測器讀取迴圈...")
    while True:
        calculate_angles()
        socketio.emit('sensor_data', sensor_data)
        time.sleep(dt)

@app.route('/')
def index():
    """主頁面"""
    return render_template('mpu6050_visual.html')

@app.route('/api/sensor')
def get_sensor_data():
    """API: 取得當前感測器數據"""
    return jsonify(sensor_data)

@app.route('/api/reset')
def reset_orientation():
    """API: 重置姿態"""
    global sensor_data
    sensor_data['roll'] = 0.0
    sensor_data['pitch'] = 0.0
    sensor_data['yaw'] = 0.0
    return jsonify({'status': 'ok', 'message': '姿態已重置'})

@socketio.on('connect')
def handle_connect():
    """WebSocket 連接"""
    print('客戶端已連接')
    emit('sensor_data', sensor_data)

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 斷線"""
    print('客戶端已斷線')

@socketio.on('reset')
def handle_reset():
    """處理重置請求"""
    global sensor_data
    sensor_data['roll'] = 0.0
    sensor_data['pitch'] = 0.0
    sensor_data['yaw'] = 0.0
    emit('sensor_data', sensor_data, broadcast=True)
    print('姿態已重置')

if __name__ == '__main__':
    print("=" * 60)
    print("MPU6050 Web-based 3D Visualization Server")
    print("=" * 60)
    
    # 初始化感測器
    if init_sensor():
        # 啟動感測器讀取執行緒
        sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
        sensor_thread.start()
        
        print("\n伺服器啟動中...")
        print("請在瀏覽器開啟: http://<樹莓派IP>:5000")
        print("按 Ctrl+C 停止\n")
        
        # 啟動 Flask 伺服器
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    else:
        print("\n無法啟動伺服器：感測器初始化失敗")
        print("請確認:")
        print("  1. MPU6050 已正確連接")
        print("  2. I2C 已啟用 (sudo raspi-config)")
        print("  3. 已安裝 i2c-tools 和 python3-smbus")
