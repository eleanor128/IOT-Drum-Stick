# 🥁 鼓棒打擊偵測使用說明

## 📋 功能簡介

`hit.py` 是一個即時鼓棒打擊偵測程式，透過 MPU6050 感測器偵測揮擊動作，並播放對應的鼓聲音效。

## 🔧 硬體需求

- **Raspberry Pi** (任何型號)
- **MPU6050** 感測器 (I2C 連接)
- **音效輸出** (3.5mm 音源孔或 HDMI)

### MPU6050 接線

| MPU6050 | Raspberry Pi |
|---------|--------------|
| VCC     | 3.3V (Pin 1) |
| GND     | GND (Pin 6)  |
| SDA     | GPIO 2 (Pin 3) |
| SCL     | GPIO 3 (Pin 5) |

## 📦 軟體安裝

### 1. 啟用 I2C

```bash
sudo raspi-config
# → Interface Options → I2C → Enable
```

### 2. 安裝系統套件

```bash
sudo apt-get update
sudo apt-get install -y python3-pip i2c-tools python3-smbus python3-pygame
```

### 3. 安裝 Python 套件

```bash
cd ~/IOT-Drum-Stick
pip3 install mpu6050-raspberrypi pygame
```

### 4. 驗證 I2C 連接

```bash
i2cdetect -y 1
```

應該會在 `0x68` 位置看到 MPU6050。

## 🎵 準備音效檔案

將你的鼓聲音效檔案命名為 `big_drum.wav`，並放在以下任一位置：

- 專案根目錄: `IOT-Drum-Stick/big_drum.wav`
- sounds 資料夾: `IOT-Drum-Stick/sounds/big_drum.wav`

支援的格式：`.wav` (推薦), `.mp3`, `.ogg`

## 🚀 執行程式

```bash
cd ~/IOT-Drum-Stick
python3 hit.py
```

## 🎮 使用方式

### 啟動後畫面

```
============================================================
🥁 鼓棒打擊偵測系統
============================================================

正在初始化 MPU6050 感測器...
✓ MPU6050 初始化成功
正在初始化音效系統...
✓ 音效系統初始化成功
✓ 音效檔案載入成功: big_drum.wav

偵測參數設定:
  加速度閾值: 2.0g
  冷卻時間: 0.1 秒
  強度分級: 輕擊(2.0-3.0g) / 中擊(3.0-5.0g) / 重擊(>5.0g)

============================================================
開始偵測鼓棒打擊...
按 Ctrl+C 停止
============================================================
```

### 即時監控

程式執行時，每秒會顯示當前狀態：

```
[00:05] 加速度: 1.02g | 打擊次數: 3
```

### 偵測到打擊時

```
🥁 打擊! 強度: 2.45g (輕擊) | 總計: 4
```

### 結束程式

按 `Ctrl+C` 停止程式，會顯示統計資料：

```
統計資料:
  總打擊次數: 15
  輕擊: 8 次
  中擊: 5 次
  重擊: 2 次
  執行時間: 00:01:23
```

## ⚙️ 參數調整

如果需要調整偵測靈敏度，可以修改 `hit.py` 中的參數：

### 加速度閾值 (第 49 行)

```python
self.threshold = 2.0  # 預設 2.0g
```

- **降低** (例如 1.5g): 更容易觸發，適合輕柔敲擊
- **提高** (例如 3.0g): 需要更大力，避免誤觸發

### 冷卻時間 (第 50 行)

```python
self.cooldown = 0.1  # 預設 0.1 秒 (100ms)
```

- **降低** (例如 0.05): 可以更快速連擊
- **提高** (例如 0.2): 避免重複偵測

### 強度分級 (第 53-55 行)

```python
self.light_hit = 3.0   # 輕擊上限
self.medium_hit = 5.0  # 中擊上限
```

## 🔍 故障排除

### 問題 1: 找不到 MPU6050

```
✗ MPU6050 初始化失敗: [Errno 121] Remote I/O error
```

**解決方法:**
1. 檢查接線是否正確
2. 確認 I2C 已啟用: `sudo raspi-config`
3. 檢測設備: `i2cdetect -y 1`

### 問題 2: 找不到音效檔案

```
✗ 音效檔案載入失敗: 找不到 big_drum.wav
```

**解決方法:**
1. 確認檔案名稱為 `big_drum.wav`
2. 放在專案根目錄或 `sounds/` 資料夾
3. 檢查檔案權限: `ls -l big_drum.wav`

### 問題 3: 沒有聲音

**解決方法:**
1. 測試音效系統:
   ```bash
   speaker-test -t wav -c 2
   ```

2. 調整音量:
   ```bash
   alsamixer
   ```

3. 確認音效輸出裝置:
   ```bash
   sudo raspi-config
   # → System Options → Audio
   ```

### 問題 4: 太容易或太難觸發

**解決方法:**
調整 `threshold` 參數:

```python
# 太容易觸發 → 提高閾值
self.threshold = 3.0

# 太難觸發 → 降低閾值
self.threshold = 1.5
```

### 問題 5: 偵測到連續多次打擊

**解決方法:**
增加冷卻時間:

```python
self.cooldown = 0.2  # 從 0.1 改為 0.2 秒
```

## 📊 校準建議

執行程式後，測試不同強度的揮擊：

1. **靜止狀態**: 加速度應約 1.0g
2. **輕柔移動**: 約 1.2-1.5g
3. **正常鼓擊**: 約 2.5-4.0g
4. **用力鼓擊**: 約 5.0-8.0g

根據實際測試結果調整 `threshold` 和強度分級參數。

## 🎯 進階功能

### 整合 Web 視覺化

可以同時執行 `mpu6050_web_visual.py` 和 `hit.py`，但需要修改其中一個的 MPU6050 初始化方式，避免衝突。

### 記錄打擊資料

程式會自動記錄所有打擊事件，可以加入檔案儲存功能：

```python
# 在偵測到打擊時
with open('hits.log', 'a') as f:
    f.write(f"{time.time()},{magnitude:.2f},{intensity}\n")
```

### 多種音效

可以根據打擊強度播放不同音效：

```python
if intensity == "輕擊":
    self.light_sound.play()
elif intensity == "中擊":
    self.medium_sound.play()
else:
    self.heavy_sound.play()
```

## 📝 授權

本專案使用 MIT 授權。

---

**🎉 祝你玩得開心！有問題歡迎回報 issue！**
