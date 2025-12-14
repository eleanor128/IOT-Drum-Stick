# IOT Drum Stick Project - AI Agent Guide

## Project Overview
Real-time air drumming system using dual MPU6050 sensors (accelerometer + gyroscope) on Raspberry Pi, with 3D web visualization and collision detection. Users wave drumsticks to play virtual drums mapped to physical space.

## Architecture

### Hardware-Software Bridge
- **Dual MPU6050 sensors** via I2C at addresses `0x68` (right hand) and `0x69` (left hand)
- **I2C race condition protection**: `app.py` uses `threading.Lock()` (`i2c_lock`) to serialize sensor reads
- **Sensor calibration**: Pre-calculated offsets in `calibration_right.py`/`calibration_left.py` (see `ACCEL_OFFSET`, `GYRO_OFFSET`)
- **Complementary filter**: Fuses gyroscope angular velocity with accelerometer orientation (96% gyro, 4% accel) for drift-resistant angle tracking

### Data Flow
```
MPU6050 sensors → Calibration modules → Flask API endpoints → JavaScript polling → Three.js 3D visualization
```

1. **Backend** (`app.py`): Flask routes `/right_data` and `/left_data` return JSON with 9-axis data (roll/pitch/yaw, ax/ay/az, gx/gy/gz), hit detection, and drum target
2. **Frontend** (`drum_3d.js`): Polls endpoints continuously (`setTimeout(..., 0)` in fetch `.finally()`), updates 3D drumstick positions and triggers audio
3. **Collision detection** (`drum_collision.py`): Calculates 3D stick tip position from angles, checks intersection with drum zones

### Critical Synchronization Points
- **3D coordinate system**: Backend Python calculations in `drum_collision.py` MUST match JavaScript transformations in `drum_3d.js`
  - Drum positions: `self.drums` array (Python) ↔ `zones` array (JS)
  - Stick tip calculation: `calculate_stick_tip_position()` (Python) ↔ `draw()` function (JS)
  - Example: Right hand X = `(yaw - 45) / 90 * 3 + 1` in both files
- **Hit detection thresholds**: Defined in `app.py` routes (`gy > 20`, `az < -1.0`)

## Key Patterns

### Sensor Reading Workflow
```python
# Always use lock when reading sensors
with i2c_lock:
    roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_right_angle()
```

### Angle Calculations (from calibration modules)
- **Pitch** (Y-axis rotation, forward/backward tilt) = `atan2(ay, sqrt(ax² + az²))`
- **Roll** (X-axis rotation, left/right tilt) = `atan2(ax, sqrt(ay² + az²))`
- **Yaw** (Z-axis rotation) = gyroscope integration only (no magnetometer)

### Frontend Real-Time Updates
```javascript
// Aggressive polling (no delay between requests)
fetch("/right_data")
  .then(res => res.json())
  .then(data => { rightData = data; })
  .finally(() => setTimeout(updateRight, 0));  // Immediate retry
```

### Audio Playback Pattern
- User must click page to enable Web Audio API (`audioEnabled` flag)
- Drum sounds cut after `DRUM_SOUND_DURATION = 0.3s` even if buffer is longer
- Multiple hits can play simultaneously (sources stored in `activeSources[]`)

## Development Commands

**Run Flask server** (Raspberry Pi):
```bash
python app.py  # Listens on 0.0.0.0:5000
```

**Test sensor calibration**:
```bash
python mpu6050_test.py  # Uses 0x69 address
```

**Collect training data** (for ML improvements):
```bash
python get_hitting_data.py  # Prompts for 10s per drum position
```

**Audio separation** (for sound processing):
```powershell
.\run_spleeter.ps1  # Uses Spleeter (TensorFlow-based)
```

## Dependencies Setup (Raspberry Pi)
```bash
# Enable I2C hardware
sudo raspi-config  # Interface Options → I2C → Enable

# System packages
sudo apt-get install python3-smbus i2c-tools ffmpeg

# Python packages (use virtualenv for Spleeter's TensorFlow)
pip install -r requirements.txt
```

## Common Pitfalls

1. **I2C address conflicts**: If sensors don't respond, verify addresses with `i2cdetect -y 1`. Change wiring or addresses in code.
2. **Coordinate system mismatches**: When modifying drum positions, update BOTH `drum_collision.py` and `drum_3d.js` identically.
3. **Yaw drift**: Yaw accumulates errors (no correction from accelerometer). Reset by restarting the app.
4. **Web Audio blocking**: Chrome/Firefox require user interaction before playing audio. Wait for click event.
5. **Complementary filter tuning**: `alpha = 0.96` balances responsiveness vs stability. Increase for less noise, decrease for faster response.

## File Responsibilities
- `app.py`: Flask server, I2C locking, hit detection logic
- `calibration_{right,left}.py`: Sensor offset removal, complementary filtering, angle calculation
- `drum_collision.py`: 3D geometry for stick-drum collision detection
- `static/js/drum_3d.js`: Three.js scene, real-time sensor polling, audio playback
- `get_hitting_data.py`: Sensor data collection for analysis/ML
- `templates/index_3d.html`: Main UI with sensor readouts and 3D canvas

## Notes on Chinese Comments
Code contains Chinese comments (Traditional) for local team. Key terms:
- 鼓棒 = drumstick | 感測器 = sensor | 加速度 = acceleration
- 陀螺儀 = gyroscope | 碰撞 = collision | 敲擊 = hit/strike
