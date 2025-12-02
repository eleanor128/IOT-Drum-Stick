#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MPU6050 鼓棒位置偵測與診斷工具
用於檢查實際的姿態數據，幫助校準和調試
並儲存校準結果供網頁視覺化使用
"""

from mpu6050 import mpu6050
import time
import math
import json
import os

# 初始化 MPU6050
sensor = mpu6050(0x68)

# 姿態計算參數
ALPHA = 0.98  # 互補濾波器係數
dt = 0.01     # 採樣時間間隔

# 姿態角度
roll = 0.0
pitch = 0.0
yaw = 0.0

# 重力校準
print("🔧 正在校準重力感測器...")
print("   請將鼓棒放在平坦表面上，保持靜止 3 秒...")
time.sleep(1)

gravity_samples = []
for i in range(300):
    accel = sensor.get_accel_data()
    gravity_samples.append(accel)
    time.sleep(0.01)

gravity_offset = {
    'x': sum(s['x'] for s in gravity_samples) / len(gravity_samples),
    'y': sum(s['y'] for s in gravity_samples) / len(gravity_samples),
    'z': sum(s['z'] for s in gravity_samples) / len(gravity_samples)
}

print(f"✓ 重力校準完成: X={gravity_offset['x']:.2f}, Y={gravity_offset['y']:.2f}, Z={gravity_offset['z']:.2f}")
print("\n" + "="*70)
print("🥁 MPU6050 鼓棒位置即時監控")
print("="*70)
print("| Roll (橫滾) | Pitch (俯仰) | Yaw (偏航) | 加速度 | 溫度 | 動作描述")
print("-"*70)

try:
    last_time = time.time()
    
    while True:
        # 讀取感測器數據
        accel_data = sensor.get_accel_data()
        gyro_data = sensor.get_gyro_data()
        temp = sensor.get_temp()
        
        # 計算時間差
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # 移除重力偏移
        accel = {
            'x': accel_data['x'] - gravity_offset['x'],
            'y': accel_data['y'] - gravity_offset['y'],
            'z': accel_data['z'] - gravity_offset['z']
        }
        
        # 從加速度計算角度（用於互補濾波）
        accel_roll = math.atan2(accel['y'], accel['z']) * 180 / math.pi
        accel_pitch = math.atan2(-accel['x'], math.sqrt(accel['y']**2 + accel['z']**2)) * 180 / math.pi
        
        # 從陀螺儀積分角度
        gyro_roll = roll + gyro_data['x'] * dt
        gyro_pitch = pitch + gyro_data['y'] * dt
        yaw = yaw + gyro_data['z'] * dt
        
        # 互補濾波器融合
        roll = ALPHA * gyro_roll + (1 - ALPHA) * accel_roll
        pitch = ALPHA * gyro_pitch + (1 - ALPHA) * accel_pitch
        
        # 計算總加速度
        total_accel = math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)
        
        # 判斷動作
        action = "靜止"
        if total_accel > 15.0:
            action = "🔴 擊打!"
        elif abs(roll) > 30:
            action = "↻ 旋轉"
        elif pitch > 30:
            action = "⬇ 向下"
        elif pitch < -30:
            action = "⬆ 向上"
        elif yaw > 30:
            action = "➡ 向右"
        elif yaw < -30:
            action = "⬅ 向左"
        
        # 顯示即時數據
        print(f"\r| {roll:7.1f}° | {pitch:8.1f}° | {yaw:7.1f}° | {total_accel:6.1f} | {temp:5.1f}°C | {action:15s}", end='', flush=True)
        
        time.sleep(0.05)  # 20Hz 更新頻率

except KeyboardInterrupt:
    print("\n\n" + "="*70)
    print("🛑 程序已停止")
    print("="*70)
    print("\n📊 最終姿態數據:")
    print(f"   Roll (橫滾):  {roll:.1f}°")
    print(f"   Pitch (俯仰): {pitch:.1f}°")
    print(f"   Yaw (偏航):   {yaw:.1f}°")
    print("\n💡 提示:")
    print("   - Roll 接近 0°: 鼓棒水平")
    print("   - Pitch 接近 0°: 鼓棒指向前方")
    print("   - Yaw 變化: 左右旋轉")
    
    # 互動式校準功能
    print("\n" + "="*70)
    print("🎯 互動式方向校準")
    print("="*70)
    print("現在你可以記錄不同方向的鼓棒位置")
    print("請將鼓棒移動到指定位置，然後輸入對應的指令\n")
    
    calibration_data = {}
    
    while True:
        print("\n可用指令:")
        print("  c - 記錄中心位置")
        print("  l - 記錄左側位置")
        print("  r - 記錄右側位置")
        print("  f - 記錄前方位置")
        print("  b - 記錄後方位置")
        print("  s - 儲存並結束")
        print("  q - 不儲存直接結束")
        
        cmd = input("\n請輸入指令: ").strip().lower()
        
        if cmd == 'q':
            print("❌ 未儲存校準數據")
            break
        elif cmd == 's':
            if len(calibration_data) > 0:
                # 儲存到 JSON 檔案
                config_file = 'mpu6050_calibration.json'
                with open(config_file, 'w') as f:
                    json.dump({
                        'calibration': calibration_data,
                        'gravity_offset': gravity_offset,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }, f, indent=2)
                print(f"\n✅ 校準數據已儲存到 {config_file}")
                print(f"   共記錄 {len(calibration_data)} 個方向")
                print("\n📝 記錄的方向:")
                for direction, data in calibration_data.items():
                    print(f"   {direction}: Roll={data['roll']:.1f}°, Pitch={data['pitch']:.1f}°, Yaw={data['yaw']:.1f}°")
            else:
                print("⚠️  沒有記錄任何校準數據")
            break
        elif cmd in ['c', 'l', 'r', 'f', 'b']:
            # 讀取當前姿態
            print("📡 正在讀取當前姿態... (保持靜止1秒)")
            samples = []
            for i in range(20):
                accel_data = sensor.get_accel_data()
                gyro_data = sensor.get_gyro_data()
                
                accel = {
                    'x': accel_data['x'] - gravity_offset['x'],
                    'y': accel_data['y'] - gravity_offset['y'],
                    'z': accel_data['z'] - gravity_offset['z']
                }
                
                accel_roll = math.atan2(accel['y'], accel['z']) * 180 / math.pi
                accel_pitch = math.atan2(-accel['x'], math.sqrt(accel['y']**2 + accel['z']**2)) * 180 / math.pi
                
                samples.append({
                    'roll': accel_roll,
                    'pitch': accel_pitch,
                    'yaw': 0  # Yaw 需要累積，這裡簡化處理
                })
                time.sleep(0.05)
            
            # 計算平均值
            avg_roll = sum(s['roll'] for s in samples) / len(samples)
            avg_pitch = sum(s['pitch'] for s in samples) / len(samples)
            avg_yaw = sum(s['yaw'] for s in samples) / len(samples)
            
            direction_map = {
                'c': 'center',
                'l': 'left',
                'r': 'right',
                'f': 'front',
                'b': 'back'
            }
            direction = direction_map[cmd]
            
            calibration_data[direction] = {
                'roll': round(avg_roll, 2),
                'pitch': round(avg_pitch, 2),
                'yaw': round(avg_yaw, 2)
            }
            
            print(f"✓ {direction} 位置已記錄: Roll={avg_roll:.1f}°, Pitch={avg_pitch:.1f}°, Yaw={avg_yaw:.1f}°")
        else:
            print("❌ 無效的指令")
    
    print()
