#!/bin/bash
# 音效修復腳本
# 用於快速設定音效檔案到正確位置

echo "======================================"
echo "🔧 IOT Drum Stick 音效修復工具"
echo "======================================"
echo ""

# 檢查是否在正確目錄
if [ ! -f "mpu6050_web_visual.py" ]; then
    echo "❌ 錯誤: 請在 IOT_drum_stick 目錄下執行此腳本"
    exit 1
fi

# 建立 static 資料夾
echo "1. 檢查 static 資料夾..."
if [ ! -d "static" ]; then
    mkdir static
    echo "   ✓ 已建立 static 資料夾"
else
    echo "   ✓ static 資料夾已存在"
fi

# 檢查音效檔案
echo ""
echo "2. 檢查音效檔案..."
if [ -f "big_drum.wav" ]; then
    echo "   ✓ 找到 big_drum.wav"
    
    # 複製到 static
    cp big_drum.wav static/
    echo "   ✓ 已複製到 static/"
    
    # 設定權限
    chmod 644 static/big_drum.wav
    echo "   ✓ 已設定檔案權限"
    
    # 顯示檔案資訊
    echo ""
    echo "3. 檔案資訊:"
    ls -lh static/big_drum.wav
    
    echo ""
    echo "======================================"
    echo "✅ 修復完成！"
    echo "======================================"
    echo ""
    echo "下一步:"
    echo "  1. 啟動伺服器: python3 mpu6050_web_visual.py"
    echo "  2. 開啟瀏覽器: http://<樹莓派IP>:5000"
    echo "  3. 點擊頁面一次啟用音效"
    echo "  4. 揮動鼓棒測試"
    echo ""
    
else
    echo "   ❌ 找不到 big_drum.wav"
    echo ""
    echo "請執行以下其中一個方法:"
    echo ""
    echo "方法 1: 如果檔案在其他位置"
    echo "  cp /path/to/big_drum.wav static/"
    echo ""
    echo "方法 2: 如果沒有音效檔案"
    echo "  請先取得 big_drum.wav 檔案"
    echo "  或使用其他 WAV 格式音效"
    echo ""
    exit 1
fi
