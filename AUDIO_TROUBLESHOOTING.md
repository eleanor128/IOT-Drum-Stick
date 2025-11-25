# 網頁音效故障排除指南

## 🔍 常見問題與解決方案

### ❌ 問題 1: 音效檔案不存在（最可能）

**症狀：**
- 瀏覽器控制台出現 404 錯誤
- 打擊指示器顯示「⚠ 音效載入失敗」

**原因：**
`static/big_drum.wav` 檔案不存在

**解決方法：**
```bash
# 在樹莓派上執行
cd /path/to/IOT_drum_stick
cp big_drum.wav static/

# 或者如果在其他位置
cp /path/to/big_drum.wav static/
```

**確認檔案存在：**
```bash
ls -lh static/big_drum.wav
```

---

### ❌ 問題 2: 沒有點擊頁面啟用音效

**症狀：**
- 沒有錯誤訊息
- 打擊指示器一直顯示「待機中...」
- 沒有「✓ 音效已就緒」提示

**原因：**
瀏覽器的 Autoplay 政策要求使用者互動後才能播放音效

**解決方法：**
1. 打開網頁後
2. **點擊頁面任意位置一次**
3. 應該會看到「✓ 音效已就緒」提示

---

### ❌ 問題 3: 瀏覽器不支援 Web Audio API

**症狀：**
- 控制台出現「Web Audio 初始化失敗」錯誤

**原因：**
舊版瀏覽器不支援 Web Audio API

**解決方法：**
更新瀏覽器到最新版本：
- Chrome 34+
- Firefox 25+
- Safari 6+
- Edge（所有版本）

---

### ❌ 問題 4: 音效格式不相容

**症狀：**
- 控制台出現「decodeAudioData」錯誤
- 音效載入失敗

**原因：**
音效檔案格式問題

**解決方法：**
轉換為標準 WAV 格式：
```bash
ffmpeg -i big_drum.wav -acodec pcm_s16le -ar 44100 -ac 2 static/big_drum_fixed.wav
```

然後更新 HTML 中的檔案名稱（或將 `big_drum_fixed.wav` 重新命名）

---

### ❌ 問題 5: CORS 跨域問題

**症狀：**
- 控制台出現「CORS policy」錯誤

**原因：**
Flask 沒有正確設定 CORS

**解決方法：**
已在程式中設定 `cors_allowed_origins="*"`，應該沒問題。
如果仍有問題，確認 Flask-SocketIO 正確安裝：
```bash
pip3 install flask-socketio
```

---

### ❌ 問題 6: 音效檔案權限問題

**症狀：**
- 403 Forbidden 錯誤

**原因：**
檔案沒有讀取權限

**解決方法：**
```bash
chmod 644 static/big_drum.wav
```

---

## 🛠️ 完整診斷步驟

### 1. 檢查音效檔案
```bash
# 在樹莓派上執行
cd /path/to/IOT_drum_stick
ls -lh static/big_drum.wav

# 應該看到類似：
# -rw-r--r-- 1 pi pi 123K Nov 25 10:00 static/big_drum.wav
```

### 2. 檢查 Flask 伺服器
```bash
# 啟動時應該看到：
python3 mpu6050_web_visual.py

# 輸出應包含：
# ✓ MPU6050 感測器初始化成功
# ✓ 校準完成！基準值: 1.00g
# 🌐 伺服器啟動中...
```

### 3. 檢查瀏覽器控制台

**Chrome/Edge：**
按 `F12` → Console 標籤

**應該看到：**
```
✓ Web Audio Context 初始化成功
✓ 鼓聲音效載入成功
```

**如果看到錯誤：**
- `404 Not Found` → 音效檔案不存在
- `Failed to fetch` → 網路或伺服器問題
- `decodeAudioData` → 音效格式問題

### 4. 測試音效載入

打開瀏覽器開發者工具，在 Console 輸入：
```javascript
// 檢查音效是否初始化
console.log('Audio initialized:', audioInitialized);

// 檢查音效緩衝區
console.log('Sound buffer:', drumSoundBuffer);

// 手動播放測試
if (drumSoundBuffer) {
    playDrumSound(1.0);
}
```

---

## 🔧 快速修復腳本

建立一個自動修復腳本：

```bash
#!/bin/bash
# fix_audio.sh

echo "=== 音效診斷與修復 ==="

# 1. 檢查音效檔案
if [ ! -f "big_drum.wav" ]; then
    echo "❌ big_drum.wav 不存在於當前目錄"
    echo "請確認音效檔案位置"
    exit 1
fi

# 2. 建立 static 資料夾
mkdir -p static

# 3. 複製音效檔案
cp big_drum.wav static/
echo "✓ 已複製 big_drum.wav 到 static/"

# 4. 設定權限
chmod 644 static/big_drum.wav
echo "✓ 已設定檔案權限"

# 5. 檢查檔案
ls -lh static/big_drum.wav
echo "✓ 檔案資訊如上"

echo ""
echo "=== 修復完成 ==="
echo "請重新啟動伺服器並刷新網頁"
```

**使用方法：**
```bash
chmod +x fix_audio.sh
./fix_audio.sh
```

---

## 📱 測試清單

完整測試流程：

- [ ] 1. 確認 `static/big_drum.wav` 存在
- [ ] 2. 啟動 Flask 伺服器無錯誤
- [ ] 3. 瀏覽器開啟 `http://<樹莓派IP>:5000`
- [ ] 4. 點擊頁面任意位置
- [ ] 5. 看到「✓ 音效已就緒」提示
- [ ] 6. 揮動鼓棒觸發打擊
- [ ] 7. 聽到鼓聲音效
- [ ] 8. 打擊指示器顯示「🥁 輕擊/中擊/重擊」

---

## 💡 替代方案

如果 Web Audio 仍然無法運作，可以使用 HTML5 Audio 元素作為備用方案：

在 HTML 中加入：
```html
<audio id="drum-audio" preload="auto">
    <source src="/static/big_drum.wav" type="audio/wav">
</audio>

<script>
// 備用播放方法
function playDrumSoundFallback() {
    const audio = document.getElementById('drum-audio');
    audio.currentTime = 0;
    audio.play().catch(e => console.error('播放失敗:', e));
}
</script>
```

---

## 📞 仍然無法解決？

請提供以下資訊：

1. **瀏覽器控制台錯誤訊息**（完整複製貼上）
2. **Flask 伺服器輸出**（啟動時的訊息）
3. **檔案檢查結果**
   ```bash
   ls -lh static/
   file static/big_drum.wav
   ```
4. **瀏覽器版本**
   - Chrome: `chrome://version`
   - Firefox: `about:support`

這樣可以更精確地診斷問題！
