#!/usr/bin/env python3
"""
音效檔案診斷工具
用於檢查音效檔案格式和相容性
"""

import os
import sys
import struct

def check_audio_file(filename):
    """檢查音效檔案"""
    print("=" * 60)
    print(f"音效檔案診斷: {filename}")
    print("=" * 60)
    
    # 1. 檢查檔案存在
    if not os.path.exists(filename):
        print(f"\n✗ 檔案不存在: {filename}")
        return False
    
    print(f"\n✓ 檔案存在: {filename}")
    
    # 2. 檢查檔案大小
    size = os.path.getsize(filename)
    print(f"  檔案大小: {size:,} bytes ({size/1024:.2f} KB)")
    
    if size == 0:
        print(f"  ✗ 檔案是空的！")
        return False
    
    # 3. 檢查權限
    readable = os.access(filename, os.R_OK)
    print(f"  讀取權限: {'✓ 可讀' if readable else '✗ 無權限'}")
    
    if not readable:
        print(f"\n建議執行: chmod 644 {filename}")
        return False
    
    # 4. 讀取檔案標頭 (WAV 格式檢查)
    if filename.lower().endswith('.wav'):
        try:
            print(f"\n檢查 WAV 格式...")
            with open(filename, 'rb') as f:
                header = f.read(44)  # WAV 標頭通常是 44 bytes
                
                if len(header) < 44:
                    print(f"  ✗ 檔案太小，不是有效的 WAV 檔案")
                    return False
                
                # 檢查 RIFF 標記
                if header[0:4] != b'RIFF':
                    print(f"  ✗ 不是有效的 WAV 檔案 (缺少 RIFF 標記)")
                    print(f"     實際標記: {header[0:4]}")
                    return False
                
                # 檢查 WAVE 標記
                if header[8:12] != b'WAVE':
                    print(f"  ✗ 不是有效的 WAV 檔案 (缺少 WAVE 標記)")
                    print(f"     實際標記: {header[8:12]}")
                    return False
                
                print(f"  ✓ WAV 格式標頭正確")
                
                # 解析格式資訊
                try:
                    audio_format = struct.unpack('<H', header[20:22])[0]
                    num_channels = struct.unpack('<H', header[22:24])[0]
                    sample_rate = struct.unpack('<I', header[24:28])[0]
                    byte_rate = struct.unpack('<I', header[28:32])[0]
                    bits_per_sample = struct.unpack('<H', header[34:36])[0]
                    
                    print(f"\n  格式資訊:")
                    print(f"    音訊格式: {audio_format} ({'PCM' if audio_format == 1 else '壓縮格式'})")
                    print(f"    聲道數: {num_channels} ({'單聲道' if num_channels == 1 else '立體聲' if num_channels == 2 else f'{num_channels}聲道'})")
                    print(f"    取樣率: {sample_rate} Hz")
                    print(f"    位元率: {byte_rate} bytes/sec")
                    print(f"    位元深度: {bits_per_sample} bit")
                    
                    # 檢查 pygame 相容性
                    compatible = True
                    issues = []
                    
                    if audio_format != 1:
                        compatible = False
                        issues.append("音訊格式必須是 PCM (格式碼 1)")
                    
                    if bits_per_sample not in [8, 16]:
                        issues.append(f"位元深度 {bits_per_sample} 可能不支援 (建議 16-bit)")
                    
                    if sample_rate not in [22050, 44100, 48000]:
                        issues.append(f"取樣率 {sample_rate} Hz 可能不支援 (建議 44100 Hz)")
                    
                    if issues:
                        print(f"\n  ⚠ 相容性問題:")
                        for issue in issues:
                            print(f"    - {issue}")
                        print(f"\n  建議轉換指令:")
                        base_name = os.path.splitext(filename)[0]
                        print(f"    ffmpeg -i {filename} -acodec pcm_s16le -ar 44100 -ac 2 {base_name}_fixed.wav")
                    else:
                        print(f"\n  ✓ 格式相容")
                        
                except Exception as e:
                    print(f"  ⚠ 解析格式資訊時發生錯誤: {e}")
                    
        except Exception as e:
            print(f"\n  ✗ 讀取檔案標頭失敗: {e}")
            return False
    
    # 5. 嘗試用 pygame 載入
    print(f"\n測試 Pygame 載入...")
    try:
        import pygame
        
        # 嘗試初始化 mixer
        try:
            pygame.mixer.quit()  # 先關閉舊的
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print(f"  ✓ Pygame mixer 初始化成功")
        except Exception as e:
            print(f"  ✗ Mixer 初始化失敗: {e}")
            return False
        
        # 嘗試載入音效
        try:
            sound = pygame.mixer.Sound(filename)
            length = sound.get_length()
            
            print(f"  ✓ 音效載入成功")
            print(f"    音效長度: {length:.2f} 秒")
            
            # 測試播放
            print(f"\n  測試播放...")
            sound.play()
            import time
            time.sleep(min(1.0, length))
            pygame.mixer.quit()
            
            print(f"  ✓ 播放測試完成")
            
            print(f"\n{'='*60}")
            print(f"✅ 結論: 音效檔案正常，可以使用！")
            print(f"{'='*60}")
            return True
            
        except pygame.error as e:
            print(f"  ✗ 音效載入失敗: {e}")
            
            print(f"\n{'='*60}")
            print(f"❌ 結論: 音效檔案格式不相容")
            print(f"{'='*60}")
            print(f"\n建議解決方法:")
            print(f"  1. 轉換為標準 WAV 格式:")
            base_name = os.path.splitext(filename)[0]
            print(f"     ffmpeg -i {filename} -acodec pcm_s16le -ar 44100 -ac 2 {base_name}_fixed.wav")
            print(f"\n  2. 然後使用轉換後的檔案:")
            print(f"     在 hit.py 中將 '{os.path.basename(filename)}' 改為 '{os.path.basename(base_name)}_fixed.wav'")
            return False
        
    except ImportError:
        print(f"  ✗ Pygame 未安裝")
        print(f"\n請執行: pip3 install pygame")
        return False
        
    except Exception as e:
        print(f"  ✗ 未知錯誤: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("音效檔案診斷工具")
        print("=" * 60)
        print("\n用法:")
        print(f"  python3 {os.path.basename(__file__)} <音效檔案>")
        print("\n範例:")
        print(f"  python3 {os.path.basename(__file__)} big_drum.wav")
        print(f"  python3 {os.path.basename(__file__)} sounds/kick.wav")
        print("\n功能:")
        print("  - 檢查檔案是否存在")
        print("  - 檢查檔案權限")
        print("  - 分析 WAV 格式")
        print("  - 測試 Pygame 相容性")
        print("  - 提供修復建議")
        sys.exit(1)
    
    filename = sys.argv[1]
    success = check_audio_file(filename)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
