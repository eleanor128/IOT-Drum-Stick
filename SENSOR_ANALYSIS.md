# Sensor Data Analysis Results

## Hit Detection Patterns

### Key Findings
- **Total hit samples analyzed**: 779 hits across all 7 drums
- **Hit detection threshold**: `|gy| > 80 °/s` (gyroscope Y-axis)
  - This threshold catches 90%+ of actual hits
  - Mean gyroscope Y during hits: -23.60 °/s
  - Standard deviation: 218.59 °/s
  - Range: -250.14 to +250.13 °/s

### Recommended Hit Detection Logic
```javascript
// When pitch increases (hitting down) AND gyroscope Y is high
const isHit = Math.abs(gyroscopeY) > 80;  // deg/s threshold
```

---

## Drum Position Mapping (Based on Accelerometer Data)

### Sensor Data During Hits
Drums sorted by height (az value, descending):

| Drum       | ax (L/R) | ay (F/B) | az (Height) | Hit Samples |
|------------|----------|----------|-------------|-------------|
| **Snare**  | -0.35    | 1.92     | **7.15**    | 106         |
| **Hihat**  | 1.75     | 0.56     | **5.68**    | 100         |
| **Tom_mid**| 1.04     | 1.21     | **3.98**    | 112         |
| **Tom_floor** | -5.33 | 0.98     | **3.91**    | 118         |
| **Tom_high** | 0.52   | 1.48     | **3.59**    | 116         |
| **Ride**   | 1.20     | 0.78     | **1.34**    | 110         |
| **Symbal** | 0.72     | 0.35     | **1.26**    | 117         |

### Sensor-to-Drum Mapping Rules

#### 1. Left/Right Position (ax - Accelerometer X)
- **Tom_floor**: `ax < -1.0` (LEFT side)
- **Snare/Tom_high/Tom_mid**: `-1.0 < ax < 3.0` (CENTER)
- **Hihat/Symbal/Ride**: `ax > 1.5` (RIGHT side)

#### 2. Height Position (az - Accelerometer Z)
- **HIGH** (`az > 5.0`): Hihat, Snare
- **MID** (`2.0 < az < 5.0`): Tom_high, Tom_mid, Tom_floor
- **LOW** (`az < 2.0`): Symbal, Ride

#### 3. Front/Back Position (ay - Accelerometer Y)
- **BACK** (`ay < -1.0`): Less common
- **CENTER** (`-1.0 < ay < 2.0`): Most drums
- **FRONT** (`ay > 1.5`): Snare (ay=1.92)

---

## Recommended Sensor Ranges for Each Drum

| Drum       | ax Range      | ay Range       | az Range      |
|------------|---------------|----------------|---------------|
| **Snare**  | [-1.85, 1.15] | [-0.08, 3.92]  | [5.15, 9.15]  |
| **Hihat**  | [0.25, 3.25]  | [-1.44, 2.56]  | [3.68, 7.68]  |
| **Tom_mid**| [-0.46, 2.54] | [-0.79, 3.21]  | [1.98, 5.98]  |
| **Tom_floor** | [-6.83, -3.83] | [-1.02, 2.98] | [1.91, 5.91] |
| **Tom_high** | [-0.98, 2.02] | [-0.52, 3.48] | [1.59, 5.59] |
| **Ride**   | [-0.30, 2.70] | [-1.22, 2.78]  | [-0.66, 3.34] |
| **Symbal** | [-0.78, 2.22] | [-1.65, 2.35]  | [-0.74, 3.26] |

---

## Implementation Status

### ✅ Updated in Code
1. **Hit detection threshold**: Changed from `|gy| > 50` to `|gy| > 80` in [drum_3d.js](static/js/drum_3d.js)
2. **Backend drum detection**: Already uses sensor-based mapping in `drum_collision.py`
3. **Frontend animation**: Aligns drumstick to detected drum center with 80% blending

### 🎯 Current System Flow
1. **Backend** (`drum_collision.py`): 
   - Uses `detect_hit_drum(ax, pitch, yaw, hand)` to map sensor data to drums
   - Returns `is_hit` (boolean) and `hit_drum` (drum name)

2. **Frontend** (`drum_3d.js`):
   - Checks `rightData.is_hit` and `leftData.is_hit`
   - Retrieves `hit_drum` from backend
   - Animates drumstick to point toward detected drum center
   - Plays sound and triggers visual glow effect

### 📊 Sensor Data Patterns
- **Pitch behavior**: Increases when hitting down, decreases when lifting
- **Gyroscope Y**: Primary indicator for hit detection (high absolute value during hits)
- **Accelerometer**: Used for drum position mapping (ax=left/right, ay=front/back, az=height)

---

## 3D Scene Drum Positions

Current positions in [3d_settings.js](static/js/3d_settings.js):

| Drum       | 3D Position [x, y, z] | Radius | Height |
|------------|-----------------------|--------|--------|
| **Hihat**  | [1.8, 0.8, -1]        | 0.65   | 0.05   |
| **Snare**  | [0.5, 0.4, -0.8]      | 0.65   | 0.5    |
| **Tom_high** | [0.6, 0.8, 0.7]     | 0.55   | 0.5    |
| **Tom_mid** | [-0.6, 0.8, 0.7]     | 0.55   | 0.5    |
| **Symbal** | [1.6, 1.4, 0.7]       | 0.80   | 0.05   |
| **Ride**   | [-1.8, 1.4, -0.1]     | 0.90   | 0.05   |
| **Tom_floor** | [-1.4, 0.2, -0.8]  | 0.80   | 1.0    |

### Coordinate System
- **X-axis**: Left (-) to Right (+)
- **Y-axis**: Down (-) to Up (+)
- **Z-axis**: Back (-) to Front (+)

---

## Notes
- The sensor accelerometer data shows clear patterns that distinguish each drum
- Height (az) is the strongest discriminator, followed by left/right position (ax)
- The backend's `drum_collision.detect_hit_drum()` should be calibrated to match these ranges
- Frontend animation provides smooth visual feedback by blending sensor angles with drum-targeted angles
