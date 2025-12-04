# MPU6050 座標系統配置文件

## 📐 感測器安裝方式

根據實際安裝在鼓棒上的 MPU6050 方向：

```
           Y 軸 (左右)
              ↑
              |
              |
    Z 軸 ←----+----→ (上下，敲擊方向)
            /
           /
          ↓
      X 軸 (鼓棒長度方向)
```

### 軸向定義

| 軸 | 方向 | 說明 |
|---|------|------|
| **X 軸** | 鼓棒長度方向 | 從握把指向鼓棒頭（前後） |
| **Y 軸** | 左右方向 | 橫向移動（水平左右） |
| **Z 軸** | 上下方向 | 敲擊方向（垂直上下） |

## 🔄 角度定義

基於右手定則的旋轉角度：

### Roll（橫滾）- 繞 X 軸旋轉
- **定義**: `Roll = atan2(Y, Z)`
- **物理意義**: 鼓棒向左/右傾斜
- **正方向**: 右手拇指指向 X 軸正向，四指彎曲方向為正
- **範例**: 
  - Roll = +90° → Y 軸指向原本 Z 軸的正方向（向左傾）
  - Roll = -90° → Y 軸指向原本 Z 軸的負方向（向右傾）

### Pitch（俯仰）- 繞 Y 軸旋轉
- **定義**: `Pitch = atan2(-Z, sqrt(X² + Y²))`
- **物理意義**: 鼓棒上下擺動（敲擊動作）
- **正方向**: 右手拇指指向 Y 軸正向，四指彎曲方向為正
- **範例**:
  - Pitch = +45° → 鼓棒向上抬起
  - Pitch = -45° → 鼓棒向下壓（準備敲擊）

### Yaw（偏航）- 繞 Z 軸旋轉
- **定義**: 陀螺儀積分 `Yaw += gyro_z × dt`
- **物理意義**: 鼓棒水平面旋轉
- **正方向**: 右手拇指指向 Z 軸正向，四指彎曲方向為正
- **範例**:
  - Yaw = +90° → 鼓棒向右轉 90 度
  - Yaw = -90° → 鼓棒向左轉 90 度

## 📊 加速度計讀值對應

### 靜止狀態（鼓棒水平放置）

```
accel_x ≈ 0 g    (鼓棒長度方向無重力分量)
accel_y ≈ 0 g    (左右方向無重力分量)
accel_z ≈ -1 g   (重力向下，Z軸向上為正)
```

### 敲擊動作（向下揮動）

```
accel_x: 較小變化（主要是鼓棒前後移動）
accel_y: 較小變化（可能有左右偏移）
accel_z: 大幅變化（向下加速，會看到負值峰值）
```

## 🎯 打擊偵測

打擊主要發生在 **Z 軸方向**（上下方向）：

```python
# 總加速度計算
magnitude = sqrt(x² + y² + z²)

# 淨加速度（去除重力）
net_accel = |magnitude - 1.0g|

# 檢測閾值
if net_accel > 2.0g:
    # 偵測到打擊！
```

### Z 軸加速度特徵

- **向下揮動**: `accel_z` 會先變得更負（加速向下）
- **碰撞瞬間**: `accel_z` 急劇上升（反向加速度）
- **回彈**: `accel_z` 逐漸回到 -1g

## 🔧 校準建議

### 1. 零點校準

將鼓棒水平放置在桌面上：
- Roll 應接近 0°（無左右傾斜）
- Pitch 應接近 0°（水平）
- Yaw 可為任意值（需要在使用時歸零）

### 2. 方向驗證

| 動作 | 預期變化 |
|------|---------|
| 向左傾斜 | Roll 增加（正值） |
| 向右傾斜 | Roll 減少（負值） |
| 向上抬起 | Pitch 增加（正值） |
| 向下壓 | Pitch 減少（負值） |
| 順時針轉 | Yaw 增加（正值） |
| 逆時針轉 | Yaw 減少（負值） |

### 3. 如果方向相反

使用校準頁面的「軸方向反轉」功能：
- 訪問: `http://localhost:5001/calibration`
- 勾選需要反轉的軸
- 儲存設定

## 💻 程式碼實現

### Python 後端（mpu6050_web_visual.py）

```python
# 從加速度計計算角度
accel_roll = math.atan2(accel['y'], accel['z']) * 180 / math.pi
accel_pitch = math.atan2(-accel['z'], math.sqrt(accel['x']**2 + accel['y']**2)) * 180 / math.pi

# 陀螺儀積分
gyro_roll += gyro['x'] * dt   # 繞 X 軸
gyro_pitch += gyro['y'] * dt  # 繞 Y 軸  
gyro_yaw += gyro['z'] * dt    # 繞 Z 軸

# 互補濾波器
sensor_data['roll'] = alpha * gyro_roll + (1 - alpha) * accel_roll
sensor_data['pitch'] = alpha * gyro_pitch + (1 - alpha) * accel_pitch
sensor_data['yaw'] = gyro_yaw
```

### JavaScript 前端（Three.js）

```javascript
// Three.js 預設座標系統：
// X = 右, Y = 上, Z = 前

// 鼓棒旋轉（需要對應轉換）
drumStick.rotation.set(
    baseRotation + pitch,  // X 軸旋轉
    yaw,                    // Y 軸旋轉
    roll                    // Z 軸旋轉
);
```

## 📝 注意事項

1. **加速度計只能測量靜態角度**
   - Roll 和 Pitch 可以從重力分量計算
   - Yaw 無法從加速度計得知（需要磁力計或陀螺儀積分）

2. **陀螺儀會漂移**
   - 長時間積分會累積誤差
   - 使用互補濾波器結合加速度計修正

3. **動態情況下加速度計不準**
   - 揮動時加速度計讀值包含運動加速度
   - 此時更依賴陀螺儀數據

4. **打擊偵測的挑戰**
   - Z 軸在敲擊時會有巨大變化
   - 需要設定適當的閾值避免誤觸發
   - 冷卻時間避免連續觸發

## 🔗 相關檔案

- `mpu6050_web_visual.py` - 後端角度計算實現
- `templates/calibration.html` - 校準頁面（含軸反轉功能）
- `templates/mpu6050_visual.html` - 主視覺化頁面
- `AXIS_INVERSION_GUIDE.md` - 軸方向反轉指南

## 📚 參考資料

- [MPU6050 Datasheet](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet1.pdf)
- [MPU6050 Register Map](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf)
- 互補濾波器原理
- Three.js 座標系統

---

**文件版本**: 1.0  
**更新日期**: 2025-12-02  
**作者**: Eleanor  
**專案**: IOT Drum Stick
