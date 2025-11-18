# 🥁 鼓棒打擊偵測使用說明

## 功能說明

`hit.py` 會持續監測 MPU6050 感測器，當偵測到鼓棒揮擊動作時自動播放鼓聲音效。

## 安裝步驟

### 1. 在樹莓派上安裝相依套件

```bash
# 更新套件列表
sudo apt-get update

# 安裝 Pygame（音效播放）
sudo apt-get install -y python3-pygame

# 或使用 pip 安裝
pip3 install pygame
```

### 2. 準備音效檔案

將你的鼓聲音效檔案命名為 `small_drum.wav` 並放在以下任一位置：

- 專案根目錄: `IOT_drum_stick/small_drum.wav`
- sounds 資料夾: `IOT_drum_stick/sounds/small_drum.wav`

支援的音效格式:
- `.wav` (建議，延遲最低)
- `.mp3`
- `.ogg`

## 使用方法

### 在樹莓派上執行

```bash
cd ~/IOT-Drum-Stick
python3 hit.py
```

你會看到：

```
============================================================
🥁 鼓棒打擊偵測系統
============================================================

正在初始化 MPU6050 感測器...
✓ MPU6050 初始化成功
正在初始化音效系統...
✓ 音效系統初始化成功
✓ 音效載入成功: small_drum.wav
  (測試音效播放...)

============================================================
系統就緒！準備偵測打擊...
============================================================

開始偵測打擊動作...
閾值: 2.0g | 冷卻時間: 0.1s

提示:
  - 揮動鼓棒來觸發音效
  - 按 Ctrl+C 停止程式
  - 加速度值會即時顯示

------------------------------------------------------------
🥁 打擊 #  1 | 加速度:  2.35g | 強度: 輕 (0.78)
🥁 打擊 #  2 | 加速度:  4.12g | 強度: 中 (0.78)
🥁 打擊 #  3 | 加速度:  6.50g | 強度: 重 (1.00)
```

## 參數調整

### 調整打擊靈敏度

編輯 `hit.py`，修改 `__init__` 方法中的參數：

```python
# 打擊偵測參數
self.threshold = 2.0  # 加速度閾值 (g) - 降低此值會更靈敏
self.cooldown = 0.1   # 冷卻時間 (秒) - 防止重複觸發
```

**建議值:**
- **靈敏**: `threshold = 1.5` (輕輕揮動就會觸發)
- **標準**: `threshold = 2.0` (預設值)
- **遲鈍**: `threshold = 3.0` (需要用力揮動)

### 調整音量

預設音量會根據打擊強度自動調整 (50% ~ 100%)。

若要固定音量，修改 `play_sound` 方法：

```python
def play_sound(self, intensity=1.0):
    if self.sound:
        self.sound.set_volume(0.8)  # 固定 80% 音量
        self.sound.play()
```

## 打擊強度分級

系統會根據加速度自動分級：

| 加速度範圍 | 等級 | 音量 |
|-----------|------|------|
| < 3.0g    | 輕   | 50% ~ 100% |
| 3.0 ~ 5.0g | 中   | 75% ~ 100% |
| > 5.0g    | 重   | 100% |

## 測試建議

### 1. 靜止測試
將樹莓派放在桌上，確認不會誤觸發。

### 2. 輕打測試
輕輕揮動鼓棒，觀察是否能穩定觸發。

### 3. 連打測試
快速連續揮動，測試冷卻時間是否適當。

### 4. 強度測試
用不同力道揮動，確認強度分級是否合理。

## 常見問題

### Q1: 找不到音效檔案

**錯誤訊息:**
```
⚠ 找不到音效檔案: small_drum.wav
```

**解決方法:**
- 確認檔案名稱正確 (區分大小寫)
- 確認檔案位於專案根目錄或 `sounds/` 資料夾
- 檢查檔案格式 (建議使用 `.wav`)

### Q2: 音效無法播放

**錯誤訊息:**
```
✗ 音效系統初始化失敗
```

**解決方法:**
```bash
# 檢查樹莓派音效設備
aplay -l

# 測試音效
speaker-test -t wav -c 2

# 重新安裝 Pygame
pip3 uninstall pygame
sudo apt-get install python3-pygame
```

### Q3: 太容易誤觸發

**現象:** 輕微移動就會播放音效

**解決方法:**
- 提高閾值: `self.threshold = 3.0`
- 增加冷卻時間: `self.cooldown = 0.2`

### Q4: 不夠靈敏

**現象:** 用力揮動才會觸發

**解決方法:**
- 降低閾值: `self.threshold = 1.5`
- 檢查 MPU6050 連接是否穩固
- 確認感測器數據正常 (可先執行 `mpu6050_test.py`)

## 進階功能

### 多重音效

如果想要不同強度播放不同音效：

```python
# 在 __init__ 中載入多個音效
self.sound_light = pygame.mixer.Sound('sounds/light_hit.wav')
self.sound_medium = pygame.mixer.Sound('sounds/medium_hit.wav')
self.sound_heavy = pygame.mixer.Sound('sounds/heavy_hit.wav')

# 在 play_sound 中根據強度選擇
def play_sound(self, intensity=1.0):
    if intensity < 0.5:
        self.sound_light.play()
    elif intensity < 0.8:
        self.sound_medium.play()
    else:
        self.sound_heavy.play()
```

### 記錄打擊數據

程式會在停止時 (Ctrl+C) 顯示統計資料：

```
統計資料:
  總打擊次數: 42
  最大加速度: 7.23g
  平均每分鐘: 35.2 次
```

### 結合網頁視覺化

可以同時執行 `mpu6050_web_visual.py` 來觀看即時 3D 姿態：

```bash
# Terminal 1: 啟動視覺化
python3 mpu6050_web_visual.py

# Terminal 2: 啟動打擊偵測
python3 hit.py
```

## 技術原理

### 加速度計算

```python
# 計算向量大小
magnitude = sqrt(x² + y² + z²)

# 扣除重力影響 (靜止時約 1g)
net_acceleration = |magnitude - 1.0|

# 超過閾值即判定為打擊
if net_acceleration > threshold:
    trigger_sound()
```

### 冷卻機制

防止單次揮動觸發多次音效：

```python
if acceleration > threshold and (current_time - last_hit_time) > cooldown:
    play_sound()
    last_hit_time = current_time
```

## 下一步整合

此程式是節奏遊戲的核心打擊偵測模組，未來可以整合：

1. **節拍偵測** (Todo 3) - 比對打擊時間與音樂節拍
2. **遊戲計分** (Todo 4) - 根據時間差給予評分 (Perfect/Good/Miss)
3. **視覺回饋** - 在網頁上顯示打擊效果

---

**🎵 享受你的 IoT 鼓棒！**
