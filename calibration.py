"""
MPU6050 鼓棒校準工具
記錄右邊鼓棒揮向左、中、右三個位置的感測器數值
用於建立打擊位置辨識模型
"""

import mpu6050
import time
import json
import os
from datetime import datetime
import math

class DrumStickCalibrator:
    """鼓棒校準器"""
    
    def __init__(self, mpu_address=0x68):
        """初始化校準器"""
        print("=" * 70)
        print("🥁 MPU6050 鼓棒校準工具")
        print("=" * 70)
        
        # 初始化 MPU6050
        print("\n正在初始化 MPU6050 感測器...")
        try:
            self.sensor = mpu6050.mpu6050(mpu_address)
            # 測試讀取
            test_data = self.sensor.get_accel_data()
            print(f"✓ MPU6050 初始化成功")
            print(f"  測試數據: X={test_data['x']:.2f}, Y={test_data['y']:.2f}, Z={test_data['z']:.2f}")
        except Exception as e:
            print(f"✗ MPU6050 初始化失敗: {e}")
            raise
        
        # 校準數據結構
        self.calibration_data = {
            "calibration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "drumstick": "right",  # 右邊鼓棒
            "positions": {
                "left": {
                    "samples": [],
                    "statistics": {}
                },
                "center": {
                    "samples": [],
                    "statistics": {}
                },
                "right": {
                    "samples": [],
                    "statistics": {}
                }
            }
        }
    
    def capture_sample(self):
        """捕捉一次感測器數據樣本"""
        try:
            accel = self.sensor.get_accel_data()
            gyro = self.sensor.get_gyro_data()
            temp = self.sensor.get_temp()
            
            # 計算總加速度
            accel_magnitude = math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)
            gyro_magnitude = math.sqrt(gyro['x']**2 + gyro['y']**2 + gyro['z']**2)
            
            sample = {
                "timestamp": time.time(),
                "accelerometer": {
                    "x": round(accel['x'], 3),
                    "y": round(accel['y'], 3),
                    "z": round(accel['z'], 3),
                    "magnitude": round(accel_magnitude, 3)
                },
                "gyroscope": {
                    "x": round(gyro['x'], 3),
                    "y": round(gyro['y'], 3),
                    "z": round(gyro['z'], 3),
                    "magnitude": round(gyro_magnitude, 3)
                },
                "temperature": round(temp, 2)
            }
            
            return sample
        except Exception as e:
            print(f"✗ 讀取感測器失敗: {e}")
            return None
    
    def calibrate_position(self, position_name, samples_count=50):
        """校準特定位置
        
        Args:
            position_name: 位置名稱 ("left", "center", "right")
            samples_count: 採樣次數
        """
        position_display = {
            "left": "左邊",
            "center": "中間",
            "right": "右邊"
        }
        
        print(f"\n{'='*70}")
        print(f"📍 校準位置: {position_display[position_name]}")
        print(f"{'='*70}")
        
        print(f"\n準備動作:")
        print(f"  1. 拿起右邊鼓棒")
        print(f"  2. 準備揮向 {position_display[position_name]} 的鼓")
        print(f"  3. 準備好後按 Enter 開始...")
        
        input()
        
        print(f"\n開始校準！")
        print(f"請重複揮擊 {position_display[position_name]} 的鼓")
        print(f"將記錄 {samples_count} 次打擊數據\n")
        
        samples = []
        hit_count = 0
        threshold = 2.0  # 加速度閾值 (g)
        cooldown = 0.3   # 冷卻時間
        last_hit_time = 0
        
        print("等待打擊...")
        
        while hit_count < samples_count:
            sample = self.capture_sample()
            if sample is None:
                time.sleep(0.01)
                continue
            
            # 檢測是否為打擊動作
            current_time = time.time()
            accel_mag = sample['accelerometer']['magnitude']
            
            # 扣除重力 (假設靜止時為 ~10 m/s² 或 ~1g)
            net_accel = abs(accel_mag - 1.0) if accel_mag < 8.0 else abs(accel_mag / 9.8 - 1.0)
            
            if net_accel > threshold and current_time - last_hit_time > cooldown:
                hit_count += 1
                samples.append(sample)
                last_hit_time = current_time
                
                print(f"✓ 打擊 #{hit_count:2d}/{samples_count} | "
                      f"加速度: {net_accel:.2f}g | "
                      f"陀螺儀: {sample['gyroscope']['magnitude']:.1f}°/s")
            
            time.sleep(0.01)  # 100 Hz 採樣
        
        print(f"\n✓ 完成 {position_display[position_name]} 位置校準！")
        
        # 儲存樣本
        self.calibration_data["positions"][position_name]["samples"] = samples
        
        # 計算統計資料
        self.calculate_statistics(position_name)
    
    def calculate_statistics(self, position_name):
        """計算位置的統計資料
        
        Args:
            position_name: 位置名稱
        """
        samples = self.calibration_data["positions"][position_name]["samples"]
        
        if not samples:
            return
        
        # 提取數據
        accel_x = [s['accelerometer']['x'] for s in samples]
        accel_y = [s['accelerometer']['y'] for s in samples]
        accel_z = [s['accelerometer']['z'] for s in samples]
        accel_mag = [s['accelerometer']['magnitude'] for s in samples]
        
        gyro_x = [s['gyroscope']['x'] for s in samples]
        gyro_y = [s['gyroscope']['y'] for s in samples]
        gyro_z = [s['gyroscope']['z'] for s in samples]
        gyro_mag = [s['gyroscope']['magnitude'] for s in samples]
        
        # 計算平均值和標準差
        def mean(data):
            return sum(data) / len(data)
        
        def std(data):
            m = mean(data)
            variance = sum((x - m) ** 2 for x in data) / len(data)
            return math.sqrt(variance)
        
        statistics = {
            "sample_count": len(samples),
            "accelerometer": {
                "x": {"mean": round(mean(accel_x), 3), "std": round(std(accel_x), 3)},
                "y": {"mean": round(mean(accel_y), 3), "std": round(std(accel_y), 3)},
                "z": {"mean": round(mean(accel_z), 3), "std": round(std(accel_z), 3)},
                "magnitude": {"mean": round(mean(accel_mag), 3), "std": round(std(accel_mag), 3)}
            },
            "gyroscope": {
                "x": {"mean": round(mean(gyro_x), 3), "std": round(std(gyro_x), 3)},
                "y": {"mean": round(mean(gyro_y), 3), "std": round(std(gyro_y), 3)},
                "z": {"mean": round(mean(gyro_z), 3), "std": round(std(gyro_z), 3)},
                "magnitude": {"mean": round(mean(gyro_mag), 3), "std": round(std(gyro_mag), 3)}
            }
        }
        
        self.calibration_data["positions"][position_name]["statistics"] = statistics
    
    def display_summary(self):
        """顯示校準摘要"""
        print(f"\n{'='*70}")
        print("📊 校準摘要")
        print(f"{'='*70}\n")
        
        positions = {
            "left": "左邊",
            "center": "中間",
            "right": "右邊"
        }
        
        for pos_key, pos_name in positions.items():
            stats = self.calibration_data["positions"][pos_key]["statistics"]
            if not stats:
                continue
            
            print(f"【{pos_name}】")
            print(f"  樣本數: {stats['sample_count']}")
            print(f"  加速度:")
            print(f"    X: {stats['accelerometer']['x']['mean']:6.2f} ± {stats['accelerometer']['x']['std']:.2f}")
            print(f"    Y: {stats['accelerometer']['y']['mean']:6.2f} ± {stats['accelerometer']['y']['std']:.2f}")
            print(f"    Z: {stats['accelerometer']['z']['mean']:6.2f} ± {stats['accelerometer']['z']['std']:.2f}")
            print(f"    總: {stats['accelerometer']['magnitude']['mean']:6.2f} ± {stats['accelerometer']['magnitude']['std']:.2f}")
            print(f"  陀螺儀:")
            print(f"    X: {stats['gyroscope']['x']['mean']:6.1f} ± {stats['gyroscope']['x']['std']:.1f} °/s")
            print(f"    Y: {stats['gyroscope']['y']['mean']:6.1f} ± {stats['gyroscope']['y']['std']:.1f} °/s")
            print(f"    Z: {stats['gyroscope']['z']['mean']:6.1f} ± {stats['gyroscope']['z']['std']:.1f} °/s")
            print(f"    總: {stats['gyroscope']['magnitude']['mean']:6.1f} ± {stats['gyroscope']['magnitude']['std']:.1f} °/s")
            print()
    
    def save_calibration(self, filename="drumstick_calibration.json"):
        """儲存校準數據到檔案
        
        Args:
            filename: 檔案名稱
        """
        try:
            # 確保在正確的目錄
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(script_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.calibration_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ 校準數據已儲存: {filepath}")
            print(f"  檔案大小: {os.path.getsize(filepath) / 1024:.2f} KB")
            
            return True
        except Exception as e:
            print(f"✗ 儲存失敗: {e}")
            return False
    
    def run(self):
        """執行完整校準流程"""
        print("\n" + "=" * 70)
        print("開始校準流程")
        print("=" * 70)
        print("\n你將要校準右邊鼓棒的三個打擊位置:")
        print("  1. 左邊的鼓")
        print("  2. 中間的鼓")
        print("  3. 右邊的鼓")
        print("\n每個位置需要打擊 50 次，讓系統學習你的動作模式")
        
        # 校準三個位置
        positions = [
            ("left", "左邊"),
            ("center", "中間"),
            ("right", "右邊")
        ]
        
        for pos_key, pos_name in positions:
            self.calibrate_position(pos_key, samples_count=50)
        
        # 顯示摘要
        self.display_summary()
        
        # 儲存數據
        print("\n" + "=" * 70)
        self.save_calibration()
        
        print("\n" + "=" * 70)
        print("🎉 校準完成！")
        print("=" * 70)
        print("\n下一步:")
        print("  1. 校準數據已儲存為 drumstick_calibration.json")
        print("  2. 可以使用這些數據訓練位置辨識模型")
        print("  3. 或直接在遊戲中使用這些統計資料進行判斷")


def main():
    """主程式"""
    try:
        calibrator = DrumStickCalibrator()
        calibrator.run()
    
    except KeyboardInterrupt:
        print("\n\n校準已中斷")
    
    except Exception as e:
        print(f"\n程式發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
