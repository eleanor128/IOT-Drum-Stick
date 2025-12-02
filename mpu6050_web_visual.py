"""
MPU6050 Web-based 3D Visualization with Hit Detection
透過 Flask 和 Three.js 在瀏覽器即時顯示 MPU6050 感測器的 3D 姿態
並偵測鼓棒打擊動作，在網頁端播放音效
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
    'temperature': 0.0,
    'hit_detected': False,
    'hit_intensity': 0.0,
    'hit_count': 0
}

# 互補濾波器參數
alpha = 0.98
dt = 0.01

# 打擊偵測參數
gravity_baseline = 1.0
unit_scale = 1.0
threshold = 2.0  # 加速度閾值 (g)
cooldown = 0.1   # 冷卻時間 (秒)
last_hit_time = 0
hit_count = 0
max_acceleration = 0.0

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

def calibrate_gravity(samples=50):
    """校準重力基準值"""
    global gravity_baseline, unit_scale
    
    print("\n正在校準重力基準值...")
    print("請保持感測器靜止...")
    
    gravity_values = []
    for i in range(samples):
        try:
            accel = sensor.get_accel_data()
            x, y, z = accel['x'], accel['y'], accel['z']
            magnitude = math.sqrt(x**2 + y**2 + z**2)
            gravity_values.append(magnitude)
            time.sleep(0.02)
        except:
            continue
    
    if not gravity_values:
        print("⚠ 校準失敗，使用預設值")
        gravity_baseline = 1.0
        unit_scale = 1.0
        return
    
    avg_gravity = sum(gravity_values) / len(gravity_values)
    
    # 檢查單位
    if avg_gravity > 8.0:
        print(f"  偵測到單位為 m/s²，轉換為 g")
        unit_scale = 1.0 / 9.8
        avg_gravity = avg_gravity * unit_scale
    else:
        unit_scale = 1.0
    
    gravity_baseline = avg_gravity
    print(f"✓ 校準完成！基準值: {gravity_baseline:.2f}g")

def calculate_angles():
    """計算 Roll, Pitch, Yaw 角度並偵測打擊（使用互補濾波器）"""
    global sensor_data, last_hit_time, hit_count, max_acceleration
    
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
        
        # ===== 打擊偵測 =====
        # 計算總加速度
        x, y, z = accel['x'], accel['y'], accel['z']
        magnitude = math.sqrt(x**2 + y**2 + z**2) * unit_scale
        net_acceleration = abs(magnitude - gravity_baseline)
        
        # 更新最大加速度
        if net_acceleration > max_acceleration:
            max_acceleration = net_acceleration
        
        # 檢查是否打擊
        current_time = time.time()
        is_hit = (net_acceleration > threshold and 
                 current_time - last_hit_time > cooldown)
        
        if is_hit:
            last_hit_time = current_time
            hit_count += 1
            
            # 計算強度
            if net_acceleration < 3.0:
                intensity = net_acceleration / 3.0
            elif net_acceleration < 5.0:
                intensity = 0.5 + (net_acceleration - 3.0) / 4.0
            else:
                intensity = 1.0
            
            # 更新 sensor_data
            sensor_data['hit_detected'] = True
            sensor_data['hit_intensity'] = intensity
            sensor_data['hit_count'] = hit_count
            
            # 不在伺服器端播放音效，改由網頁端播放
            
            print(f"🥁 打擊 #{hit_count} | 加速度: {net_acceleration:.2f}g | 強度: {intensity:.2f}")
        else:
            sensor_data['hit_detected'] = False
            sensor_data['hit_intensity'] = 0.0
        
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

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供靜態檔案（音效等）"""
    from flask import send_from_directory
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return send_from_directory(static_dir, filename)

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
    print("🥁 MPU6050 3D 視覺化 + 打擊偵測系統")
    print("=" * 60)
    
    # 初始化感測器
    if not init_sensor():
        print("\n無法啟動伺服器：感測器初始化失敗")
        print("請確認:")
        print("  1. MPU6050 已正確連接")
        print("  2. I2C 已啟用 (sudo raspi-config)")
        print("  3. 已安裝 i2c-tools 和 python3-smbus")
        exit(1)
    
    # 校準重力
    calibrate_gravity()
    
    # 啟動感測器讀取執行緒
    sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
    sensor_thread.start()
    
    print("\n" + "=" * 60)
    print("🌐 伺服器啟動中...")
    print("=" * 60)
    print(f"\n請在瀏覽器開啟: http://<樹莓派IP>:5000")
    print(f"\n功能:")
    print(f"  ✓ 3D 鼓棒視覺化")
    print(f"  ✓ 爵士鼓場景")
    print(f"  ✓ 打擊偵測（閾值: {threshold}g）")
    print(f"  ✓ 網頁端音效播放")
    print(f"\n按 Ctrl+C 停止\n")
    print("=" * 60 + "\n")
    
    try:
        # 啟動 Flask 伺服器
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n程式已停止")
        print(f"總打擊次數: {hit_count}")
        print(f"最大加速度: {max_acceleration:.2f}g")
        print("\n感謝使用！🎵")
