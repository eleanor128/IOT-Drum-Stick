"""
鼓棒打擊偵測與音效播放
當偵測到 MPU6050 感測器加速度超過閾值時，播放鼓聲音效
"""

import mpu6050
import pygame
import time
import math
import os

class DrumStickDetector:
    """鼓棒打擊偵測器"""
    
    def __init__(self, mpu_address=0x68, sound_file='big_drum.wav'):
        """初始化偵測器
        
        Args:
            mpu_address: MPU6050 I2C 位址 (預設 0x68)
            sound_file: 音效檔案路徑
        """
        print("=" * 60)
        print("🥁 鼓棒打擊偵測系統")
        print("=" * 60)
        
        # 初始化 MPU6050
        print("\n正在初始化 MPU6050 感測器...")
        try:
            self.sensor = mpu6050.mpu6050(mpu_address)
            print("✓ MPU6050 初始化成功")
        except Exception as e:
            print(f"✗ MPU6050 初始化失敗: {e}")
            raise
        
        # 初始化 Pygame 音效系統
        print("正在初始化音效系統...")
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("✓ 音效系統初始化成功")
        except Exception as e:
            print(f"✗ 音效系統初始化失敗: {e}")
            raise
        
        # 載入音效檔案
        self.sound_file = sound_file
        self.sound = None
        self.load_sound()
        
        # 打擊偵測參數
        self.threshold = 2.0  # 加速度閾值 (g)
        self.cooldown = 0.1   # 冷卻時間 (秒)
        self.last_hit_time = 0
        
        # 統計資料
        self.hit_count = 0
        self.max_acceleration = 0.0
        
        print("\n" + "=" * 60)
        print("系統就緒！準備偵測打擊...")
        print("=" * 60)
    
    def load_sound(self):
        """載入音效檔案"""
        # 支援多種音效格式
        extensions = ['.wav', '.mp3', '.ogg']
        sound_path = None
        
        # 尋找音效檔案
        for ext in extensions:
            # 嘗試不同的檔案名稱
            for filename in [self.sound_file, f'big_drum{ext}', f'sounds/big_drum{ext}']:
                if os.path.exists(filename):
                    sound_path = filename
                    break
            if sound_path:
                break
        
        if sound_path:
            try:
                self.sound = pygame.mixer.Sound(sound_path)
                print(f"✓ 音效載入成功: {sound_path}")
                
                # 測試播放 (小聲)
                self.sound.set_volume(0.3)
                self.sound.play()
                print("  (測試音效播放...)")
                time.sleep(0.5)
                self.sound.set_volume(1.0)  # 恢復正常音量
            except Exception as e:
                print(f"✗ 音效載入失敗: {e}")
                self.sound = None
        else:
            print(f"⚠ 找不到音效檔案: {self.sound_file}")
            print("  請確認檔案存在，支援格式: .wav, .mp3, .ogg")
            print("  程式將繼續運行，但不會播放音效")
    
    def calculate_acceleration_magnitude(self, accel_data):
        """計算加速度向量的大小（總加速度）
        
        Args:
            accel_data: 加速度數據字典 {'x': float, 'y': float, 'z': float}
        
        Returns:
            float: 加速度大小 (g)
        """
        x = accel_data['x']
        y = accel_data['y']
        z = accel_data['z']
        
        # 計算向量長度: sqrt(x^2 + y^2 + z^2)
        magnitude = math.sqrt(x**2 + y**2 + z**2)
        
        # 扣除重力影響 (靜止時約 1g)
        # 實際加速度 = 總加速度 - 重力
        net_acceleration = abs(magnitude - 1.0)
        
        return net_acceleration
    
    def detect_hit(self):
        """偵測是否有打擊動作
        
        Returns:
            tuple: (是否打擊, 加速度大小)
        """
        try:
            # 讀取加速度數據
            accel = self.sensor.get_accel_data()
            
            # 計算總加速度
            acceleration = self.calculate_acceleration_magnitude(accel)
            
            # 更新最大加速度紀錄
            if acceleration > self.max_acceleration:
                self.max_acceleration = acceleration
            
            # 檢查是否超過閾值且不在冷卻時間內
            current_time = time.time()
            is_hit = (acceleration > self.threshold and 
                     current_time - self.last_hit_time > self.cooldown)
            
            if is_hit:
                self.last_hit_time = current_time
                self.hit_count += 1
            
            return is_hit, acceleration
        
        except Exception as e:
            print(f"讀取感測器錯誤: {e}")
            return False, 0.0
    
    def play_sound(self, intensity=1.0):
        """播放打擊音效
        
        Args:
            intensity: 強度 (0.0 ~ 1.0)，影響音量
        """
        if self.sound:
            # 根據打擊強度調整音量
            volume = min(1.0, 0.5 + intensity * 0.5)
            self.sound.set_volume(volume)
            self.sound.play()
    
    def get_hit_intensity(self, acceleration):
        """根據加速度計算打擊強度
        
        Args:
            acceleration: 加速度大小 (g)
        
        Returns:
            str: 打擊等級 ('輕', '中', '重')
            float: 強度值 (0.0 ~ 1.0)
        """
        if acceleration < 3.0:
            return '輕', acceleration / 3.0
        elif acceleration < 5.0:
            return '中', 0.5 + (acceleration - 3.0) / 4.0
        else:
            return '重', 1.0
    
    def run(self):
        """主迴圈：持續偵測打擊"""
        print("\n開始偵測打擊動作...")
        print(f"閾值: {self.threshold}g | 冷卻時間: {self.cooldown}s")
        print("\n提示:")
        print("  - 揮動鼓棒來觸發音效")
        print("  - 按 Ctrl+C 停止程式")
        print("  - 加速度值會即時顯示\n")
        print("-" * 60)
        
        try:
            while True:
                # 偵測打擊
                is_hit, acceleration = self.detect_hit()
                
                if is_hit:
                    # 計算打擊強度
                    intensity_level, intensity_value = self.get_hit_intensity(acceleration)
                    
                    # 播放音效
                    self.play_sound(intensity_value)
                    
                    # 顯示打擊資訊
                    print(f"🥁 打擊 #{self.hit_count:3d} | "
                          f"加速度: {acceleration:5.2f}g | "
                          f"強度: {intensity_level} ({intensity_value:.2f})")
                
                # 短暫延遲 (避免 CPU 佔用過高)
                time.sleep(0.01)  # 100 Hz 採樣率
        
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("程式已停止")
            print("=" * 60)
            print(f"\n統計資料:")
            print(f"  總打擊次數: {self.hit_count}")
            print(f"  最大加速度: {self.max_acceleration:.2f}g")
            print(f"  平均每分鐘: {self.hit_count / ((time.time() - self.last_hit_time) / 60):.1f} 次")
            print("\n感謝使用！🎵\n")
        
        finally:
            # 清理資源
            pygame.mixer.quit()


def main():
    """主程式進入點"""
    try:
        # 建立偵測器實例
        detector = DrumStickDetector(
            mpu_address=0x68,
            sound_file='big_drum.wav'
        )
        
        # 開始偵測
        detector.run()
    
    except Exception as e:
        print(f"\n程式發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
