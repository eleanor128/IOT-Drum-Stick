# IOT 空氣鼓棒系統

使用雙 MPU6050 感測器實現的即時空氣打鼓系統，透過 3D 視覺化和碰撞檢測，讓使用者揮動鼓棒即可演奏虛擬鼓組。

## 系統架構

```
MPU6050 感測器 → Raspberry Pi (Flask) → HTTP Polling → 瀏覽器 (Three.js)
     ↓                  ↓                                    ↓
  校正濾波          碰撞檢測                          3D 渲染 + 音效
```

### 硬體
- **雙 MPU6050 感測器**：I2C 位址 `0x68`(右手) / `0x69`(左手)
- **Madgwick 濾波器**：融合加速度計與陀螺儀，實現穩定姿態估計
- **I2C 鎖**：防止多執行緒讀取衝突

### 軟體
- **後端 (Flask)**：感測器數據處理、碰撞檢測、XZ 平面投影判斷
- **前端 (Three.js)**：3D 鼓棒渲染、即時位置追蹤、鼓面發光動畫

## 主要檔案

| 檔案 | 說明 |
|------|------|
| `app.py` | Flask 伺服器，提供 `/right_data` 和 `/left_data` API |
| `calibration_right.py` / `calibration_left.py` | Madgwick 濾波器，計算 roll/pitch/yaw 角度 |
| `drum_collision.py` | 碰撞檢測，計算鼓棒尖端位置並判斷擊中的鼓 |
| `static/js/3d_settings.js` | **集中配置檔**，所有參數統一管理 |
| `static/js/drum_3d.js` | Three.js 場景、鼓棒動畫、音效播放 |
| `templates/index_3d.html` | 主介面，顯示 3D 場景與感測器數值 |

## 快速開始

### 1. 安裝依賴
```bash
# Raspberry Pi
sudo apt-get install python3-smbus i2c-tools
pip install -r requirements.txt
```

### 2. 啟用 I2C
```bash
sudo raspi-config  # Interface Options → I2C → Enable
i2cdetect -y 1     # 確認感測器位址
```

### 3. 運行系統
```bash
python app.py      # 啟動 Flask，監聽 0.0.0.0:5000
```

開啟瀏覽器訪問 `http://<Raspberry-Pi-IP>:5000`，點擊畫面啟用音效。

## 關鍵配置 (`3d_settings.js`)

### 座標系統
- **X 軸**：正向 = 鼓手左側，負向 = 鼓手右側
- **Y 軸**：正向 = 上方
- **Z 軸**：正向 = 前方

### 運動邏輯
- **Pitch 增加**（舉起）→ 鼓棒向上旋轉，手往前伸 → 打前方鼓 (Symbal, Tom)
- **Yaw 增加**（左轉）→ 鼓棒與手往 X 負向移動
- **手部 Y 高度固定**在 `GRIP_BASE_Y = 1.0` 米

### 初始位置
- 握把：`(0.4/0.6, 1.0, -2.2)` 米（左右手）
- 鼓棒尖端：XZ 平面投影對準 Snare 中心 `(0.5, -1.0)`

### 自動範圍計算
所有握把移動範圍根據鼓組位置與鼓棒長度動態計算，確保兩支鼓棒都能打到全部 7 個鼓。

## 碰撞檢測

採用 **XZ 平面 2D 投影**：
1. 計算鼓棒尖端 3D 位置（握把位置 + 旋轉向量）
2. 投影到 XZ 平面，計算與鼓面中心的距離
3. 距離 ≤ 鼓半徑時觸發擊中，播放對應音效

## 測試工具

```bash
python mpu6050_test.py           # 測試感測器讀取
python get_hitting_data.py       # 收集訓練數據
.\run_spleeter.ps1               # 音效分離（需 TensorFlow）
```

## 材料清單
1. MPU6050 sensor × 2
2. Breadboard × 1
3. Raspberry Pi 4 × 1
4. Drum stick × 2
5. Lots of wires and tapes

## 注意事項

1. **Yaw 漂移**：無磁力計校正，長時間使用需按 `R` 鍵重置中心
2. **Web Audio 限制**：需使用者點擊畫面才能播放音效
3. **配置同步**：修改 `3d_settings.js` 後，後端會自動重新載入