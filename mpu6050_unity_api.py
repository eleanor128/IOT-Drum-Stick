"""
MPU6050 Unity API Server
即時讀取 MPU6050 感測器數據並透過 Flask API 傳遞給 Unity
"""

from flask import Flask, jsonify
from flask_cors import CORS
import mpu6050
import threading
import time

app = Flask(__name__)
CORS(app)  # 允許跨域請求，讓 Unity 可以訪問

# 初始化 MPU6050 感測器
try:
    sensor = mpu6050.mpu6050(0x68)
    print("MPU6050 感測器初始化成功")
except Exception as e:
    print(f"MPU6050 感測器初始化失敗: {e}")
    sensor = None

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
    global latest_data
    counter = 0
    
    while True:
        if sensor is None:
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
                print(f"[背景執行緒] 已讀取 {counter} 次數據 | Accel X:{accel_data['x']:.2f}")
            
            # 控制讀取頻率 (100Hz = 每秒100次)
            time.sleep(0.01)
            
        except Exception as e:
            print(f"讀取感測器數據錯誤: {e}")
            time.sleep(0.1)


@app.route('/api/mpu6050', methods=['GET'])
def get_mpu6050_data():
    """
    取得最新的 MPU6050 感測器數據
    返回 JSON 格式的加速度計、陀螺儀和溫度數據
    """
    print("=" * 50)
    print("收到 Unity 請求!")
    
    if sensor is None:
        print("❌ 感測器未初始化")
        return jsonify({
            "error": "MPU6050 sensor not initialized",
            "status": "error"
        }), 500
    
    with data_lock:
        data = latest_data.copy()
    
    print(f"✅ 傳送數據: {data}")
    print("=" * 50)
    
    return jsonify({
        "status": "success",
        "data": data
    })


@app.route('/api/mpu6050/accel', methods=['GET'])
def get_accelerometer():
    """
    僅取得加速度計數據
    """
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
        "timestamp": time.time()
    })


if __name__ == '__main__':
    # 啟動背景執行緒讀取感測器數據
    sensor_thread = threading.Thread(target=read_sensor_continuously, daemon=True)
    sensor_thread.start()
    
    print("=" * 50)
    print("MPU6050 Unity API Server 啟動中...")
    print("=" * 50)
    print("API Endpoints:")
    print("  - GET /api/mpu6050       - 取得完整感測器數據")
    print("  - GET /api/mpu6050/accel - 取得加速度計數據")
    print("  - GET /api/mpu6050/gyro  - 取得陀螺儀數據")
    print("  - GET /api/mpu6050/temp  - 取得溫度數據")
    print("  - GET /api/status        - 檢查伺服器狀態")
    print("=" * 50)
    
    # 啟動 Flask 伺服器
    # host='0.0.0.0' 允許外部設備訪問
    # port=5000 預設端口
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
