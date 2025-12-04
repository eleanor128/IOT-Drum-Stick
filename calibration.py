"""
Calibration parameters management module
For storing and managing MPU6050 sensor calibration parameters
Including XYZ axis offset, scaling, rotation, etc.
"""

import json
import os

# Calibration file path
CALIBRATION_FILE = 'calibration_params.json'

# Default calibration parameters
DEFAULT_PARAMS = {
    'left': {
        'accel_offset': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'gyro_offset': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'accel_scale': {'x': 1.0, 'y': 1.0, 'z': 1.0},
        'gyro_scale': {'x': 1.0, 'y': 1.0, 'z': 1.0},
        'axis_mapping': {
            'x': 'x',
            'y': 'y',
            'z': 'z'
        },
        'axis_invert': {
            'x': False,
            'y': False,
            'z': False
        },
        'rotation': {
            'pitch': 0.0,
            'roll': 0.0,
            'yaw': 0.0
        }
    },
    'right': {
        'accel_offset': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'gyro_offset': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'accel_scale': {'x': 1.0, 'y': 1.0, 'z': 1.0},
        'gyro_scale': {'x': 1.0, 'y': 1.0, 'z': 1.0},
        'axis_mapping': {
            'x': 'x',
            'y': 'y',
            'z': 'z'
        },
        'axis_invert': {
            'x': False,
            'y': False,
            'z': False
        },
        'rotation': {
            'pitch': 0.0,
            'roll': 0.0,
            'yaw': 0.0
        }
    },
    'global': {
        'hit_threshold': 2.0,
        'smooth_factor': 0.5,
        'dead_zone': 0.1
    }
}

# Current calibration parameters (global variable)
current_params = None


def load_calibration():
    """Load calibration parameters"""
    global current_params

    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r', encoding='utf-8') as f:
                current_params = json.load(f)
                print(f"Loaded calibration parameters: {CALIBRATION_FILE}")
                return current_params
        except Exception as e:
            print(f"Failed to load calibration: {e}")
            current_params = DEFAULT_PARAMS.copy()
            return current_params
    else:
        print("Using default calibration parameters")
        current_params = DEFAULT_PARAMS.copy()
        return current_params


def save_calibration(params=None):
    """Save calibration parameters"""
    global current_params

    if params is not None:
        current_params = params

    try:
        with open(CALIBRATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_params, f, indent=2, ensure_ascii=False)
        print(f"Calibration parameters saved: {CALIBRATION_FILE}")
        return True
    except Exception as e:
        print(f"Failed to save calibration: {e}")
        return False


def get_params():
    """Get current calibration parameters"""
    global current_params

    if current_params is None:
        load_calibration()

    return current_params


def update_params(stick, category, key, value):
    """Update a single parameter"""
    global current_params

    if current_params is None:
        load_calibration()

    try:
        if category == 'global':
            current_params['global'][key] = value
        else:
            current_params[stick][category][key] = value

        save_calibration()
        return True
    except Exception as e:
        print(f"Failed to update parameter: {e}")
        return False


def reset_calibration(stick=None):
    """Reset calibration parameters"""
    global current_params

    if stick is None:
        current_params = DEFAULT_PARAMS.copy()
    else:
        current_params[stick] = DEFAULT_PARAMS[stick].copy()

    save_calibration()
    print(f"Reset calibration: {stick if stick else 'all'}")


def apply_calibration(stick, raw_accel, raw_gyro):
    """
    Apply calibration parameters to raw sensor data

    Args:
        stick: 'left' or 'right'
        raw_accel: {'x': float, 'y': float, 'z': float}
        raw_gyro: {'x': float, 'y': float, 'z': float}

    Returns:
        calibrated_accel, calibrated_gyro
    """
    if current_params is None:
        load_calibration()

    params = current_params[stick]

    # Step 1: Apply offset
    accel = {
        'x': raw_accel['x'] - params['accel_offset']['x'],
        'y': raw_accel['y'] - params['accel_offset']['y'],
        'z': raw_accel['z'] - params['accel_offset']['z']
    }

    gyro = {
        'x': raw_gyro['x'] - params['gyro_offset']['x'],
        'y': raw_gyro['y'] - params['gyro_offset']['y'],
        'z': raw_gyro['z'] - params['gyro_offset']['z']
    }

    # Step 2: Apply scaling
    accel = {
        'x': accel['x'] * params['accel_scale']['x'],
        'y': accel['y'] * params['accel_scale']['y'],
        'z': accel['z'] * params['accel_scale']['z']
    }

    gyro = {
        'x': gyro['x'] * params['gyro_scale']['x'],
        'y': gyro['y'] * params['gyro_scale']['y'],
        'z': gyro['z'] * params['gyro_scale']['z']
    }

    # Step 3: Apply axis mapping and inversion
    mapped_accel = {}
    mapped_gyro = {}

    for real_axis in ['x', 'y', 'z']:
        sensor_axis = params['axis_mapping'][real_axis]

        # Accelerometer
        value_accel = accel[sensor_axis]
        if params['axis_invert'][real_axis]:
            value_accel = -value_accel
        mapped_accel[real_axis] = value_accel

        # Gyroscope
        value_gyro = gyro[sensor_axis]
        if params['axis_invert'][real_axis]:
            value_gyro = -value_gyro
        mapped_gyro[real_axis] = value_gyro

    # Step 4: Apply dead zone
    dead_zone = current_params['global']['dead_zone']
    for axis in ['x', 'y', 'z']:
        if abs(mapped_accel[axis]) < dead_zone:
            mapped_accel[axis] = 0.0
        if abs(mapped_gyro[axis]) < dead_zone:
            mapped_gyro[axis] = 0.0

    return mapped_accel, mapped_gyro


def get_calibration_summary():
    """Get calibration parameters summary (for display)"""
    if current_params is None:
        load_calibration()

    summary = {
        'left': {
            'has_offset': any(v != 0 for v in current_params['left']['accel_offset'].values()),
            'has_scale': any(v != 1.0 for v in current_params['left']['accel_scale'].values()),
            'has_mapping': any(current_params['left']['axis_mapping'][k] != k for k in ['x', 'y', 'z']),
            'has_invert': any(current_params['left']['axis_invert'].values())
        },
        'right': {
            'has_offset': any(v != 0 for v in current_params['right']['accel_offset'].values()),
            'has_scale': any(v != 1.0 for v in current_params['right']['accel_scale'].values()),
            'has_mapping': any(current_params['right']['axis_mapping'][k] != k for k in ['x', 'y', 'z']),
            'has_invert': any(current_params['right']['axis_invert'].values())
        }
    }

    return summary


# Initialize: load calibration parameters
load_calibration()


if __name__ == '__main__':
    # Test program
    print("Calibration Module Test")
    print("=" * 60)

    # Load parameters
    params = get_params()
    print("Current parameters:")
    print(json.dumps(params, indent=2))

    # Test applying calibration
    print("\nTest applying calibration:")
    raw_accel = {'x': 1.0, 'y': 0.5, 'z': -0.2}
    raw_gyro = {'x': 10.0, 'y': -5.0, 'z': 3.0}

    cal_accel, cal_gyro = apply_calibration('left', raw_accel, raw_gyro)
    print(f"Raw accel: {raw_accel}")
    print(f"Calibrated accel: {cal_accel}")
    print(f"Raw gyro: {raw_gyro}")
    print(f"Calibrated gyro: {cal_gyro}")

    # Test summary
    print("\nCalibration summary:")
    summary = get_calibration_summary()
    print(json.dumps(summary, indent=2))
