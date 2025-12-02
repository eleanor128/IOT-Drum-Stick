# 音效檔案修復腳本 (Windows PowerShell)
# 用於將 big_drum.wav 複製到 static 資料夾

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🔧 IOT Drum Stick 音效修復工具 (Windows)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 檢查是否在正確目錄
if (-not (Test-Path "mpu6050_web_visual.py")) {
    Write-Host "❌ 錯誤: 請在 IOT_drum_stick 目錄下執行此腳本" -ForegroundColor Red
    exit 1
}

# 建立 static 資料夾
Write-Host "1. 檢查 static 資料夾..." -ForegroundColor Yellow
if (-not (Test-Path "static")) {
    New-Item -ItemType Directory -Path "static" | Out-Null
    Write-Host "   ✓ 已建立 static 資料夾" -ForegroundColor Green
} else {
    Write-Host "   ✓ static 資料夾已存在" -ForegroundColor Green
}

# 檢查音效檔案
Write-Host ""
Write-Host "2. 檢查音效檔案..." -ForegroundColor Yellow
if (Test-Path "big_drum.wav") {
    Write-Host "   ✓ 找到 big_drum.wav" -ForegroundColor Green
    
    # 複製到 static
    Copy-Item "big_drum.wav" -Destination "static\big_drum.wav" -Force
    Write-Host "   ✓ 已複製到 static\" -ForegroundColor Green
    
    # 顯示檔案資訊
    Write-Host ""
    Write-Host "3. 檔案資訊:" -ForegroundColor Yellow
    $file = Get-Item "static\big_drum.wav"
    Write-Host "   路徑: $($file.FullName)" -ForegroundColor White
    Write-Host "   大小: $([math]::Round($file.Length / 1KB, 2)) KB" -ForegroundColor White
    Write-Host "   修改時間: $($file.LastWriteTime)" -ForegroundColor White
    
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "✅ 修復完成！" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Yellow
    Write-Host "  1. 如果伺服器正在運行，不需要重啟" -ForegroundColor White
    Write-Host "  2. 在瀏覽器重新整理頁面 (Ctrl+Shift+R)" -ForegroundColor White
    Write-Host "  3. 點擊頁面一次啟用音效" -ForegroundColor White
    Write-Host "  4. 揮動鼓棒測試" -ForegroundColor White
    Write-Host ""
    Write-Host "驗證音效檔案:" -ForegroundColor Yellow
    Write-Host "  在瀏覽器輸入: http://樹莓派IP:5000/static/big_drum.wav" -ForegroundColor White
    Write-Host "  應該可以下載或播放音效" -ForegroundColor White
    Write-Host ""
    
} else {
    Write-Host "   ❌ 找不到 big_drum.wav" -ForegroundColor Red
    Write-Host ""
    Write-Host "請執行以下其中一個方法:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "方法 1: 如果檔案在其他位置" -ForegroundColor Cyan
    Write-Host '  Copy-Item "路徑\big_drum.wav" -Destination "static\big_drum.wav"' -ForegroundColor White
    Write-Host ""
    Write-Host "方法 2: 使用其他 WAV 音效" -ForegroundColor Cyan
    Write-Host '  Copy-Item "your_sound.wav" -Destination "static\big_drum.wav"' -ForegroundColor White
    Write-Host ""
    Write-Host "方法 3: 找到檔案位置" -ForegroundColor Cyan
    Write-Host '  Get-ChildItem -Path "D:\" -Filter "big_drum.wav" -Recurse -ErrorAction SilentlyContinue' -ForegroundColor White
    Write-Host ""
    exit 1
}
