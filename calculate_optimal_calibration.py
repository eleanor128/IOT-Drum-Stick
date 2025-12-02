#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
計算最佳校準參數
根據收集的數據計算出精確的校準 offset
"""

import json
import numpy as np
from pathlib import Path

def load_calibration_data(json_path):
    """載入校準數據"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def calculate_position_calibration(data_points):
    """
    計算單一位置的校準參數
    
    策略:
    1. 使用中位數 (median) 而非平均值,更能抵抗異常值
    2. 考慮揮動時的穩定姿態 (排除極端值)
    """
    rolls = [d['roll'] for d in data_points]
    pitches = [d['pitch'] for d in data_points]
    yaws = [d['yaw'] for d in data_points]
    
    # 計算統計值
    stats = {
        'roll': {
            'median': np.median(rolls),
            'mean': np.mean(rolls),
            'std': np.std(rolls),
            'q25': np.percentile(rolls, 25),
            'q75': np.percentile(rolls, 75)
        },
        'pitch': {
            'median': np.median(pitches),
            'mean': np.mean(pitches),
            'std': np.std(pitches),
            'q25': np.percentile(pitches, 25),
            'q75': np.percentile(pitches, 75)
        },
        'yaw': {
            'median': np.median(yaws),
            'mean': np.mean(yaws),
            'std': np.std(yaws),
            'q25': np.percentile(yaws, 25),
            'q75': np.percentile(yaws, 75)
        }
    }
    
    return stats

def calculate_calibration_offsets(center_stats, left_stats, right_stats):
    """
    計算校準偏移量
    
    目標姿態定義:
    - Center (正前方): Roll=0°, Pitch=-90° (水平,X軸指向前), Yaw=0°
    - Left (左方):     Roll=0°, Pitch=-90°, Yaw=-90° (水平,X軸指向左)
    - Right (右方):    Roll=0°, Pitch=-90°, Yaw=90°  (水平,X軸指向右)
    
    但實際上,我們需要考慮:
    1. Pitch: 如果 -84.8° 是水平,那應該校準到 -90°
    2. Roll: 揮動時應該保持在 0° 附近
    3. Yaw: 根據方向不同而不同
    """
    
    print("\n" + "="*80)
    print("計算校準偏移量")
    print("="*80)
    
    # 方案 1: 基於 Center 位置的絕對校準 (最簡單)
    print("\n【方案 1: 單一校準 - 基於 CENTER 位置】")
    print("適用於: 使用固定校準值,不考慮方向變化")
    
    center_offset = {
        'roll': -center_stats['roll']['median'],
        'pitch': -90 - center_stats['pitch']['median'],  # 目標是 -90°
        'yaw': -center_stats['yaw']['median']
    }
    
    print(f"  Roll offset:  {center_offset['roll']:>8.2f}°")
    print(f"  Pitch offset: {center_offset['pitch']:>8.2f}°")
    print(f"  Yaw offset:   {center_offset['yaw']:>8.2f}°")
    
    # 驗證效果
    print("\n  驗證 (校準後的期望值):")
    print(f"    Center: Roll={center_stats['roll']['median'] + center_offset['roll']:.2f}°, "
          f"Pitch={center_stats['pitch']['median'] + center_offset['pitch']:.2f}°, "
          f"Yaw={center_stats['yaw']['median'] + center_offset['yaw']:.2f}°")
    
    # 方案 2: 位置特定校準 (更精確,但需要位置偵測)
    print("\n【方案 2: 多位置校準 - 根據 Yaw 自動切換】")
    print("適用於: 自動偵測位置並套用對應校準")
    
    # Center 位置的校準
    center_calibration = {
        'roll': -center_stats['roll']['median'],
        'pitch': -90 - center_stats['pitch']['median'],
        'yaw': -center_stats['yaw']['median']
    }
    
    # Left 位置的校準
    left_calibration = {
        'roll': -left_stats['roll']['median'],
        'pitch': -90 - left_stats['pitch']['median'],
        'yaw': -90 - left_stats['yaw']['median']  # 目標 -90° (指向左)
    }
    
    # Right 位置的校準
    right_calibration = {
        'roll': -right_stats['roll']['median'],
        'pitch': -90 - right_stats['pitch']['median'],
        'yaw': 90 - right_stats['yaw']['median']  # 目標 90° (指向右)
    }
    
    print(f"\n  CENTER:")
    print(f"    roll={center_calibration['roll']:.2f}°, "
          f"pitch={center_calibration['pitch']:.2f}°, "
          f"yaw={center_calibration['yaw']:.2f}°")
    
    print(f"\n  LEFT:")
    print(f"    roll={left_calibration['roll']:.2f}°, "
          f"pitch={left_calibration['pitch']:.2f}°, "
          f"yaw={left_calibration['yaw']:.2f}°")
    
    print(f"\n  RIGHT:")
    print(f"    roll={right_calibration['roll']:.2f}°, "
          f"pitch={right_calibration['pitch']:.2f}°, "
          f"yaw={right_calibration['yaw']:.2f}°")
    
    # 方案 3: 簡化版 - 只校準 Center,其他靠旋轉處理
    print("\n【方案 3: 簡化校準 + 旋轉矩陣】")
    print("適用於: 校準 Center 位置,其他方向用代碼旋轉處理")
    
    # 只需要校準到 Center 位置
    simple_offset = {
        'roll': -center_stats['roll']['median'],
        'pitch': -90 - center_stats['pitch']['median'],
        'yaw': -center_stats['yaw']['median']
    }
    
    print(f"  基準校準: roll={simple_offset['roll']:.2f}°, "
          f"pitch={simple_offset['pitch']:.2f}°, "
          f"yaw={simple_offset['yaw']:.2f}°")
    print(f"  Left 時額外旋轉:  Yaw -= 90°")
    print(f"  Right 時額外旋轉: Yaw += 90°")
    
    return {
        'single': center_offset,
        'multi': {
            'center': center_calibration,
            'left': left_calibration,
            'right': right_calibration
        },
        'simple': simple_offset
    }

def main():
    # 讀取數據
    json_path = r"C:\Users\elean\Downloads\drumstick_calibration_1764661222663.json"
    
    print("="*80)
    print("最佳校準參數計算工具")
    print("="*80)
    print(f"\n讀取數據: {json_path}")
    
    data = load_calibration_data(json_path)
    
    print(f"\n總樣本數: {data['metadata']['totalSamples']}")
    print(f"位置分佈: {data['metadata']['positions']}")
    
    # 分離各位置的數據
    center_data = [d for d in data['data'] if d['position'] == 'center']
    left_data = [d for d in data['data'] if d['position'] == 'left']
    right_data = [d for d in data['data'] if d['position'] == 'right']
    
    print(f"\n實際數據點: Center={len(center_data)}, Left={len(left_data)}, Right={len(right_data)}")
    
    # 計算各位置統計
    print("\n" + "="*80)
    print("各位置姿態統計 (中位數)")
    print("="*80)
    
    center_stats = calculate_position_calibration(center_data)
    left_stats = calculate_position_calibration(left_data)
    right_stats = calculate_position_calibration(right_data)
    
    print(f"\nCENTER: Roll={center_stats['roll']['median']:.2f}°, "
          f"Pitch={center_stats['pitch']['median']:.2f}°, "
          f"Yaw={center_stats['yaw']['median']:.2f}°")
    
    print(f"LEFT:   Roll={left_stats['roll']['median']:.2f}°, "
          f"Pitch={left_stats['pitch']['median']:.2f}°, "
          f"Yaw={left_stats['yaw']['median']:.2f}°")
    
    print(f"RIGHT:  Roll={right_stats['roll']['median']:.2f}°, "
          f"Pitch={right_stats['pitch']['median']:.2f}°, "
          f"Yaw={right_stats['yaw']['median']:.2f}°")
    
    # 計算校準偏移
    calibrations = calculate_calibration_offsets(center_stats, left_stats, right_stats)
    
    # 推薦方案
    print("\n" + "="*80)
    print("推薦使用方案")
    print("="*80)
    
    print("\n🎯 【推薦】使用方案 1 - 單一校準")
    print("   最簡單,直接套用到 calibration.html 的預設按鈕")
    print("\n   在 calibration.html 中修改:")
    print("   ```javascript")
    print(f"   const rotationOffset = {{")
    print(f"       roll: {calibrations['single']['roll']:.2f},")
    print(f"       pitch: {calibrations['single']['pitch']:.2f},")
    print(f"       yaw: {calibrations['single']['yaw']:.2f}")
    print(f"   }};")
    print("   ```")
    
    print("\n📊 如果你想要更精確的多位置校準:")
    print("   可以使用 /calibration-advanced 頁面")
    print("   該頁面會根據 Yaw 值自動判斷位置並套用對應校準")
    
    # 生成配置檔案
    output_config = {
        'calibration_date': data['metadata']['timestamp'],
        'total_samples': data['metadata']['totalSamples'],
        'recommended': {
            'method': 'single_offset',
            'roll': round(calibrations['single']['roll'], 2),
            'pitch': round(calibrations['single']['pitch'], 2),
            'yaw': round(calibrations['single']['yaw'], 2)
        },
        'advanced': {
            'method': 'position_specific',
            'center': {
                'roll': round(calibrations['multi']['center']['roll'], 2),
                'pitch': round(calibrations['multi']['center']['pitch'], 2),
                'yaw': round(calibrations['multi']['center']['yaw'], 2)
            },
            'left': {
                'roll': round(calibrations['multi']['left']['roll'], 2),
                'pitch': round(calibrations['multi']['left']['pitch'], 2),
                'yaw': round(calibrations['multi']['left']['yaw'], 2)
            },
            'right': {
                'roll': round(calibrations['multi']['right']['roll'], 2),
                'pitch': round(calibrations['multi']['right']['pitch'], 2),
                'yaw': round(calibrations['multi']['right']['yaw'], 2)
            }
        },
        'position_detection': {
            'yaw_ranges': {
                'center': {'min': 15, 'max': 28, 'median': round(center_stats['yaw']['median'], 2)},
                'left': {'min': 28, 'max': 38, 'median': round(left_stats['yaw']['median'], 2)},
                'right': {'min': 5, 'max': 15, 'median': round(right_stats['yaw']['median'], 2)}
            }
        },
        'drum_hit_threshold': {
            'z_accel': 34.83,
            'description': '重力加速度 + 2倍標準差'
        }
    }
    
    # 儲存配置
    output_path = Path(__file__).parent / 'calibration_config.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 校準配置已儲存至: {output_path}")
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
