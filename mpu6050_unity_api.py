"""
MPU6050 Unity API Server
即時讀取 MPU6050 感測器數據並透過 Flask API 傳遞給 Unity
"""

from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)  # 允許跨域請求，讓 Unity 可以訪問

# 初始化感測器
sensor = None
sensor_error = None

def init_sensor(address=0x68):
    """初始化 MPU6050 感測器"""
    global sensor, sensor_error
    
    try:
        import mpu6050
        sensor = mpu6050.mpu6050(address)
        
        # 測試讀取
        test_data = sensor.get_accel_data()
        
        print(f"✓ MPU6050 感測器初始化成功 (地址: 0x{address:02X})")
        print(f"  測試數據: X={test_data['x']:.2f}, Y={test_data['y']:.2f}, Z={test_data['z']:.2f}")
        sensor_error = None
        return True
        
    except Exception as e:
        print(f"✗ MPU6050 初始化失敗 (地址: 0x{address:02X}): {e}")
        sensor_error = str(e)
        sensor = None
        return False

# 嘗試初始化感測器 (先試 0x68，失敗再試 0x69)
print("\n正在初始化 MPU6050 感測器...")
if not init_sensor(0x68):
    print("嘗試備用地址 0x69...")
    init_sensor(0x69)

# 全域變數儲存最新的感測器數據
latest_data = {
    "accelerometer": {"x": 0, "y": 0, "z": 0},
    "gyroscope": {"x": 0, "y": 0, "z": 0},
    "temperature": 0,
    "timestamp": time.time()
}

# 數據更新鎖
data_lock = threading.Lock()


def read_sensor_continuously():
    """
    背景執行緒持續讀取感測器數據
    """
    global latest_data, sensor, sensor_error
    counter = 0
    retry_interval = 5  # 重試間隔（秒）
    last_retry = 0
    
    while True:
        # 如果感測器未初始化，嘗試重新連接
        if sensor is None:
            current_time = time.time()
            if current_time - last_retry > retry_interval:
                print(f"\n[{time.strftime('%H:%M:%S')}] 嘗試重新連接感測器...")
                if init_sensor(0x68) or init_sensor(0x69):
                    print("✓ 感測器重新連接成功")
                    counter = 0
                else:
                    print("✗ 重新連接失敗，將在 5 秒後重試")
                last_retry = current_time
            time.sleep(1)
            continue
            
        try:
            # 讀取加速度計數據
            accel_data = sensor.get_accel_data()
            
            # 讀取陀螺儀數據
            gyro_data = sensor.get_gyro_data()
            
            # 讀取溫度
            temp = sensor.get_temp()
            
            # 更新全域數據
            with data_lock:
                latest_data = {
                    "accelerometer": {
                        "x": round(accel_data['x'], 3),
                        "y": round(accel_data['y'], 3),
                        "z": round(accel_data['z'], 3)
                    },
                    "gyroscope": {
                        "x": round(gyro_data['x'], 3),
                        "y": round(gyro_data['y'], 3),
                        "z": round(gyro_data['z'], 3)
                    },
                    "temperature": round(temp, 2),
                    "timestamp": time.time()
                }
            
            # 每100次打印一次，確認數據持續更新
            counter += 1
            if counter % 100 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] 已讀取 {counter} 次 | Accel: ({accel_data['x']:.2f}, {accel_data['y']:.2f}, {accel_data['z']:.2f})")
            
            # 清除錯誤狀態
            sensor_error = None
            
            # 控制讀取頻率 (100Hz = 每秒100次)
            time.sleep(0.01)
            
        except Exception as e:
            print(f"\n[{time.strftime('%H:%M:%S')}] 讀取感測器數據錯誤: {e}")
            sensor_error = str(e)
            sensor = None  # 標記需要重新初始化
            time.sleep(0.1)


@app.route('/api/mpu6050', methods=['GET'])
def get_mpu6050_data():
    """
    取得最新的 MPU6050 感測器數據
    返回 JSON 格式的加速度計、陀螺儀和溫度數據
    """
    if sensor is None:
        error_msg = sensor_error or "MPU6050 sensor not initialized"
        return jsonify({
            "error": error_msg,
            "status": "error",
            "message": "感測器未連接，請檢查硬體連接或稍後重試"
        }), 500
    
    with data_lock:
        data = latest_data.copy()
    
    return jsonify({
        "status": "success",
        "data": data
    })


@app.route('/api/mpu6050/accel', methods=['GET'])
def get_accelerometer():
    """
    僅取得加速度計數據
    """
    if sensor is None:
        return jsonify({
            "error": sensor_error or "Sensor not initialized",
            "status": "error"
        }), 500
    
    with data_lock:
        accel = latest_data["accelerometer"].copy()
    
    return jsonify({
        "status": "success",
        "accelerometer": accel,
        "timestamp": time.time()
    })


@app.route('/api/mpu6050/gyro', methods=['GET'])
def get_gyroscope():
    """
    僅取得陀螺儀數據
    """
    if sensor is None:
        return jsonify({
            "error": sensor_error or "Sensor not initialized",
            "status": "error"
        }), 500
    
    with data_lock:
        gyro = latest_data["gyroscope"].copy()
    
    return jsonify({
        "status": "success",
        "gyroscope": gyro,
        "timestamp": time.time()
    })


@app.route('/api/mpu6050/temp', methods=['GET'])
def get_temperature():
    """
    僅取得溫度數據
    """
    if sensor is None:
        return jsonify({
            "error": sensor_error or "Sensor not initialized",
            "status": "error"
        }), 500
    
    with data_lock:
        temp = latest_data["temperature"]
    
    return jsonify({
        "status": "success",
        "temperature": temp,
        "timestamp": time.time()
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    檢查 API 伺服器狀態
    """
    return jsonify({
        "status": "running",
        "sensor_connected": sensor is not None,
        "sensor_error": sensor_error,
        "last_update": latest_data["timestamp"],
        "timestamp": time.time()
    })


@app.route('/api/reinit', methods=['POST', 'GET'])
def reinitialize_sensor():
    """
    手動重新初始化感測器
    """
    print("\n收到手動重新初始化請求...")
    success = init_sensor(0x68) or init_sensor(0x69)
    
    return jsonify({
        "status": "success" if success else "failed",
        "sensor_connected": sensor is not None,
        "message": "感測器重新初始化" + ("成功" if success else "失敗")
    })


if __name__ == '__main__':
    # 啟動背景執行緒讀取感測器數據
    sensor_thread = threading.Thread(target=read_sensor_continuously, daemon=True)
    sensor_thread.start()
    
    print("\n" + "=" * 60)
    print("MPU6050 Unity API Server")
    print("=" * 60)
    print("\nAPI Endpoints:")
    print("  - GET  /api/mpu6050       - 取得完整感測器數據")
    print("  - GET  /api/mpu6050/accel - 取得加速度計數據")
    print("  - GET  /api/mpu6050/gyro  - 取得陀螺儀數據")
    print("  - GET  /api/mpu6050/temp  - 取得溫度數據")
    print("  - GET  /api/status        - 檢查伺服器狀態")
    print("  - POST /api/reinit        - 手動重新初始化感測器")
    print("=" * 60)
    
    if sensor is None:
        print("\n⚠ 警告: 感測器初始化失敗")
        print("  系統將自動每 5 秒嘗試重新連接")
        print("  或手動訪問: http://<IP>:5000/api/reinit")
    else:
        print("\n✓ 感測器就緒，開始提供 API 服務")
    
    print("=" * 60 + "\n")
    
    # 啟動 Flask 伺服器
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)