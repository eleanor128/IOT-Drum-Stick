import time
import json
from datetime import datetime
import mpu6050

# 鼓的位置列表
drum_positions = [
    "Hihat",
    "Snare",
    "Tom_high",
    "Tom_mid",
    "Symbal",
    "Ride",
    "Tom_floor"
]

# 初始化 MPU6050 感測器
sensor = mpu6050.mpu6050(0x69)

def collect_sensor_data(duration=10):
    """收集指定時間的感測器數據"""
    data = []
    
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            # 讀取加速度計數據
            accelerometer_data = sensor.get_accel_data()
            
            # 讀取陀螺儀數據
            gyroscope_data = sensor.get_gyro_data()
            
            # 讀取溫度
            temperature = sensor.get_temp()
            
            # 組合數據
            sensor_reading = {
                'timestamp': time.time(),
                'accelerometer': accelerometer_data,
                'gyroscope': gyroscope_data,
                'temperature': temperature
            }
            
            data.append(sensor_reading)
            
            # 等待 0.05 秒（與 mpu6050_test.py 相同的採樣率）
            time.sleep(0.05)
            
        except Exception as e:
            print(f"讀取感測器錯誤: {e}")
            continue
    
    return data

def main():
    print("=== 鼓棒感測器數據收集程式 ===")
    print("準備開始收集數據...\n")
    
    all_data = {}
    
    for position in drum_positions:
        print(f"請用左右手敲擊 {position} 10秒")
        print("按 Enter 開始收集...")
        input()
        
        print(f"正在收集 {position} 數據... (10秒)")
        sensor_data = collect_sensor_data(duration=10)
        all_data[position] = sensor_data
        
        print(f"✓ {position} 數據收集完成 (共 {len(sensor_data)} 筆)\n")
    
    # 儲存數據
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"drum_sensor_data_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== 數據收集完成 ===")
    print(f"檔案已儲存: {filename}")
    print(f"總共收集 {len(drum_positions)} 個位置的數據")
    
    # 顯示統計資訊
    for pos, data in all_data.items():
        print(f"  {pos}: {len(data)} 筆數據")

if __name__ == "__main__":
    main()