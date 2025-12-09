# import smbus
# import time
# import math
# import json
# from flask import Flask, render_template, jsonify, request
# from threading import Thread, Lock
# import calibration_right

# # MPU6050 暫存器
# PWR_MGMT_1 = 0x6B
# ACCEL_XOUT_H = 0x3B
# GYRO_XOUT_H = 0x43

# # 兩個 MPU6050 的 I2C 地址
# RIGHT_DRUM_STICK = 0x68
# LEFT_DRUM_STICK = 0x69

# # 初始化 I2C (使用 bus 1)
# bus = smbus.SMBus(1)

# # Flask 應用程式
# app = Flask(__name__)

# # 資料鎖
# data_lock = Lock()

# # 校正數據（訓練用）
# training_calibration = {
#     'ready_position': {
#         'right': {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}},
#         'left': {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}}
#     },
#     'hit_threshold': 2.0,  # 打擊閾值
#     'is_calibrated': False
# }

# # 訓練數據
# training_data = {
#     'left_hand': {'left': [], 'center': [], 'right': []},
#     'right_hand': {'left': [], 'center': [], 'right': []},
#     'is_trained': False
# }

# # 打擊判斷參數（從訓練數據中學習）
# hit_detection_params = {
#     'right': {
#         'left': {'axis': 'x', 'threshold': 0, 'direction': 1},
#         'center': {'axis': 'y', 'threshold': 0, 'direction': -1},
#         'right': {'axis': 'x', 'threshold': 0, 'direction': -1}
#     },
#     'left': {
#         'left': {'axis': 'x', 'threshold': 0, 'direction': 1},
#         'center': {'axis': 'y', 'threshold': 0, 'direction': -1},
#         'right': {'axis': 'x', 'threshold': 0, 'direction': -1}
#     }
# }

# # 全域變數儲存最新數據
# latest_data = {
#     'right': {
#         'accel': {'x': 0, 'y': 0, 'z': 0},
#         'gyro': {'x': 0, 'y': 0, 'z': 0},
#         'angle': {'pitch': 0, 'roll': 0},
#         'magnitude': 0,
#         'is_hitting': False,
#         'hit_position': None  # 'left', 'center', 'right'
#     },
#     'left': {
#         'accel': {'x': 0, 'y': 0, 'z': 0},
#         'gyro': {'x': 0, 'y': 0, 'z': 0},
#         'angle': {'pitch': 0, 'roll': 0},
#         'magnitude': 0,
#         'is_hitting': False,
#         'hit_position': None
#     },
#     'timestamp': time.strftime('%H:%M:%S'),
#     'system_status': 'initializing'  # initializing, ready, calibrating, training, running
# }


# def init_mpu6050(address):
#     """初始化 MPU6050 感測器"""
#     bus.write_byte_data(address, PWR_MGMT_1, 0)
#     time.sleep(0.1)
#     print(f"MPU6050 at address 0x{address:02X} initialized")


# def read_raw_data(address, register):
#     """從 MPU6050 讀取原始數據（16-bit）"""
#     high = bus.read_byte_data(address, register)
#     low = bus.read_byte_data(address, register + 1)
#     value = (high << 8) | low
#     if value > 32768:
#         value = value - 65536
#     return value


# def read_mpu6050_data(address, stick_name=None):
#     """讀取 MPU6050 的加速度和陀螺儀數據"""
#     # 讀取加速度數據
#     acc_x = read_raw_data(address, ACCEL_XOUT_H)
#     acc_y = read_raw_data(address, ACCEL_XOUT_H + 2)
#     acc_z = read_raw_data(address, ACCEL_XOUT_H + 4)

#     # 讀取陀螺儀數據
#     gyro_x = read_raw_data(address, GYRO_XOUT_H)
#     gyro_y = read_raw_data(address, GYRO_XOUT_H + 2)
#     gyro_z = read_raw_data(address, GYRO_XOUT_H + 4)

#     # 轉換為實際單位
#     acc_x_g = acc_x / 16384.0
#     acc_y_g = acc_y / 16384.0
#     acc_z_g = acc_z / 16384.0

#     gyro_x_dps = gyro_x / 131.0
#     gyro_y_dps = gyro_y / 131.0
#     gyro_z_dps = gyro_z / 131.0

#     # 原始數據
#     raw_accel = {'x': acc_x_g, 'y': acc_y_g, 'z': acc_z_g}
#     raw_gyro = {'x': gyro_x_dps, 'y': gyro_y_dps, 'z': gyro_z_dps}

#     # 應用校準 (如果有指定stick_name)
#     if stick_name:
#         cal_accel, cal_gyro = calibration_right.apply_calibration(stick_name, raw_accel, raw_gyro)

#         # 對調 X 和 Y 軸
#         cal_accel_swapped = {
#             'x': cal_accel['y'],  # Y → X
#             'y': cal_accel['x'],  # X → Y
#             'z': cal_accel['z']
#         }
#         cal_gyro_swapped = {
#             'x': cal_gyro['y'],
#             'y': cal_gyro['x'],
#             'z': cal_gyro['z']
#         }
#         cal_accel = cal_accel_swapped
#         cal_gyro = cal_gyro_swapped
#     else:
#         cal_accel, cal_gyro = raw_accel, raw_gyro

#     # 計算加速度總量 (使用校準後的數據)
#     magnitude = math.sqrt(cal_accel['x']**2 + cal_accel['y']**2 + cal_accel['z']**2)

#     # 計算鼓棒姿態角度
#     # 新的鼓棒方向設定: 水平於 XZ 平面，尖端指向 Z 軸負向
#     #
#     # 當鼓棒水平靜止時：
#     # - Z 軸加速度 ≈ 0 (鼓棒水平)
#     # - X 軸加速度 ≈ 0 (沒有前後傾斜)
#     # - Y 軸加速度 ≈ -1g (重力向下)

#     # pitch: 鼓棒的俯仰角（上下傾斜）
#     # - 基於 X 軸加速度（向上揮時 X 變負，應產生正 pitch）
#     # - 水平時應為 0°
#     pitch = math.atan2(cal_accel['x'], math.sqrt(cal_accel['y']**2 + cal_accel['z']**2)) * 180 / math.pi

#     # roll: 鼓棒的橫滾角（左右傾斜）
#     # - 基於 Z 軸加速度（向左傾斜為負，向右為正）
#     # - 水平時應為 0°
#     roll = math.atan2(cal_accel['z'], cal_accel['y']) * 180 / math.pi

#     return {
#         'accel': cal_accel,
#         'gyro': cal_gyro,
#         'angle': {'pitch': pitch, 'roll': roll},
#         'magnitude': magnitude
#     }


# def detect_hit_position(stick_name, accel_data):
#     """根據加速度數據判斷打擊位置"""
#     if not training_data['is_trained']:
#         return None

#     params = hit_detection_params[stick_name]

#     # 取得預備位置的參考值
#     ready_accel = training_calibration['ready_position'][stick_name]['accel']

#     # 計算相對於預備位置的加速度變化
#     delta = {
#         'x': accel_data['x'] - ready_accel['x'],
#         'y': accel_data['y'] - ready_accel['y'],
#         'z': accel_data['z'] - ready_accel['z']
#     }

#     # 判斷最可能的打擊位置
#     max_score = 0
#     best_position = None

#     for position in ['left', 'center', 'right']:
#         param = params[position]
#         axis_value = delta[param['axis']]

#         # 檢查方向是否正確
#         if param['direction'] * axis_value > param['threshold']:
#             score = abs(axis_value)
#             if score > max_score:
#                 max_score = score
#                 best_position = position

#     return best_position


# def analyze_training_data():
#     """分析訓練數據，找出最佳的判斷參數"""
#     global hit_detection_params

#     for hand in ['right', 'left']:
#         for position in ['left', 'center', 'right']:
#             data_list = training_data[f'{hand}_hand'][position]

#             if len(data_list) == 0:
#                 continue

#             # 計算相對於預備位置的平均加速度變化
#             ready_accel = training_calibration['ready_position'][hand]['accel']

#             avg_delta = {'x': 0, 'y': 0, 'z': 0}
#             for data in data_list:
#                 avg_delta['x'] += data['accel']['x'] - ready_accel['x']
#                 avg_delta['y'] += data['accel']['y'] - ready_accel['y']
#                 avg_delta['z'] += data['accel']['z'] - ready_accel['z']

#             n = len(data_list)
#             avg_delta['x'] /= n
#             avg_delta['y'] /= n
#             avg_delta['z'] /= n

#             # 找出變化最大的軸
#             max_axis = 'x'
#             max_value = abs(avg_delta['x'])

#             if abs(avg_delta['y']) > max_value:
#                 max_axis = 'y'
#                 max_value = abs(avg_delta['y'])

#             if abs(avg_delta['z']) > max_value:
#                 max_axis = 'z'
#                 max_value = abs(avg_delta['z'])

#             # 設定參數
#             hit_detection_params[hand][position]['axis'] = max_axis
#             hit_detection_params[hand][position]['threshold'] = max_value * 0.5  # 50% 的閾值
#             hit_detection_params[hand][position]['direction'] = 1 if avg_delta[max_axis] > 0 else -1

#     print("\n✓ 訓練完成！打擊判斷參數：")
#     print(json.dumps(hit_detection_params, indent=2))

#     training_data['is_trained'] = True


# def update_sensor_data():
#     """背景執行緒：持續更新感測器數據"""
#     global latest_data

#     print("初始化感測器...")
#     init_mpu6050(RIGHT_DRUM_STICK)
#     init_mpu6050(LEFT_DRUM_STICK)
#     print("感測器初始化完成！")

#     with data_lock:
#         latest_data['system_status'] = 'ready'

#     while True:
#         try:
#             right_data = read_mpu6050_data(RIGHT_DRUM_STICK, 'right')
#             left_data = read_mpu6050_data(LEFT_DRUM_STICK, 'left')

#             # 判斷是否在打擊
#             right_hitting = right_data['magnitude'] > training_calibration['hit_threshold']
#             left_hitting = left_data['magnitude'] > training_calibration['hit_threshold']

#             # 判斷打擊位置
#             right_position = None
#             left_position = None

#             if right_hitting and training_data['is_trained']:
#                 right_position = detect_hit_position('right', right_data['accel'])

#             if left_hitting and training_data['is_trained']:
#                 left_position = detect_hit_position('left', left_data['accel'])

#             with data_lock:
#                 latest_data['right'] = {
#                     **right_data,
#                     'is_hitting': right_hitting,
#                     'hit_position': right_position
#                 }
#                 latest_data['left'] = {
#                     **left_data,
#                     'is_hitting': left_hitting,
#                     'hit_position': left_position
#                 }
#                 latest_data['timestamp'] = time.strftime('%H:%M:%S')

#             time.sleep(0.05)
#         except Exception as e:
#             print(f"讀取錯誤: {e}")
#             time.sleep(1)


# @app.route('/')
# def index():
#     """主頁面"""
#     return render_template('index.html')


# @app.route('/api/data')
# def get_data():
#     """API：取得最新感測器數據"""
#     with data_lock:
#         return jsonify({
#             **latest_data,
#             'calibration_status': training_calibration['is_calibrated'],
#             'training_status': training_data['is_trained']
#         })


# @app.route('/gemini')
# def gemini():
#     return render_template('gemini_drum.html')


# @app.route('/calibration')
# def calibration_page():
#     """校準頁面"""
#     return render_template('calibration.html')


# @app.route('/api/calibration/get')
# def get_calibration():
#     """API：取得校準參數"""
#     import calibration_right as cal_module
#     params = cal_module.get_params()
#     return jsonify({
#         'status': 'success',
#         'params': params
#     })


# @app.route('/api/calibration/update', methods=['POST'])
# def update_calibration():
#     """API：更新校準參數"""
#     try:
#         import calibration_right as cal_module
#         data = request.get_json()
#         stick = data.get('stick')  # 'left' or 'right'
#         category = data.get('category')  # 'accel_offset', 'gyro_offset', etc.
#         key = data.get('key')  # 'x', 'y', 'z'
#         value = data.get('value')

#         success = cal_module.update_params(stick, category, key, value)

#         if success:
#             return jsonify({'status': 'success', 'message': 'Parameter updated'})
#         else:
#             return jsonify({'status': 'error', 'message': 'Failed to update parameter'})
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


# @app.route('/api/calibration/save', methods=['POST'])
# def save_calibration():
#     """API：儲存校準參數"""
#     try:
#         import calibration_right as cal_module
#         success = cal_module.save_calibration()

#         if success:
#             return jsonify({'status': 'success', 'message': 'Calibration saved'})
#         else:
#             return jsonify({'status': 'error', 'message': 'Failed to save calibration'})
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


# @app.route('/api/calibration/reset', methods=['POST'])
# def reset_calibration():
#     """API：重置校準參數"""
#     try:
#         import calibration_right as cal_module
#         data = request.get_json()
#         stick = data.get('stick')  # None for all, 'left' or 'right' for specific

#         cal_module.reset_calibration(stick)

#         return jsonify({'status': 'success', 'message': f'Calibration reset for {stick if stick else "all"}'})
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


# @app.route('/api/calibrate_ready_position', methods=['POST'])
# def calibrate_ready_position():
#     """API：校正預備位置"""
#     try:
#         print("\n開始校正預備位置...")
#         time.sleep(1)

#         # 讀取多次數據取平均
#         samples = 30
#         right_sum = {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}}
#         left_sum = {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}}

#         for i in range(samples):
#             right_data = read_mpu6050_data(RIGHT_DRUM_STICK)
#             left_data = read_mpu6050_data(LEFT_DRUM_STICK)

#             for axis in ['x', 'y', 'z']:
#                 right_sum['accel'][axis] += right_data['accel'][axis]
#                 right_sum['gyro'][axis] += right_data['gyro'][axis]
#                 left_sum['accel'][axis] += left_data['accel'][axis]
#                 left_sum['gyro'][axis] += left_data['gyro'][axis]

#             time.sleep(0.02)

#         # 計算平均值
#         for axis in ['x', 'y', 'z']:
#             training_calibration['ready_position']['right']['accel'][axis] = right_sum['accel'][axis] / samples
#             training_calibration['ready_position']['right']['gyro'][axis] = right_sum['gyro'][axis] / samples
#             training_calibration['ready_position']['left']['accel'][axis] = left_sum['accel'][axis] / samples
#             training_calibration['ready_position']['left']['gyro'][axis] = left_sum['gyro'][axis] / samples

#         training_calibration['is_calibrated'] = True

#         print("✓ 預備位置校正完成！")
#         print(f"右手: {training_calibration['ready_position']['right']}")
#         print(f"左手: {training_calibration['ready_position']['left']}")

#         return jsonify({'status': 'success', 'message': '預備位置校正完成'})
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


# @app.route('/api/record_training_hit', methods=['POST'])
# def record_training_hit():
#     """API：記錄訓練打擊"""
#     try:
#         data = request.get_json()
#         hand = data.get('hand')  # 'left' or 'right'
#         position = data.get('position')  # 'left', 'center', or 'right'

#         # 讀取當前數據
#         if hand == 'right':
#             sensor_data = read_mpu6050_data(RIGHT_DRUM_STICK)
#         else:
#             sensor_data = read_mpu6050_data(LEFT_DRUM_STICK)

#         # 儲存訓練數據
#         training_data[f'{hand}_hand'][position].append(sensor_data)

#         current_count = len(training_data[f'{hand}_hand'][position])
#         print(f"記錄 {hand} 手 {position} 側打擊 #{current_count}")

#         return jsonify({
#             'status': 'success',
#             'count': current_count,
#             'data': sensor_data
#         })
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


# @app.route('/api/finish_training', methods=['POST'])
# def finish_training():
#     """API：完成訓練，分析數據"""
#     try:
#         analyze_training_data()

#         with data_lock:
#             latest_data['system_status'] = 'running'

#         return jsonify({
#             'status': 'success',
#             'message': '訓練完成！系統已準備就緒',
#             'params': hit_detection_params
#         })
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


# @app.route('/api/reset_training', methods=['POST'])
# def reset_training():
#     """API：重置訓練數據"""
#     global training_data

#     training_data = {
#         'left_hand': {'left': [], 'center': [], 'right': []},
#         'right_hand': {'left': [], 'center': [], 'right': []},
#         'is_trained': False
#     }

#     with data_lock:
#         latest_data['system_status'] = 'ready'

#     return jsonify({'status': 'success', 'message': '訓練數據已重置'})


# if __name__ == "__main__":
#     # 啟動背景執行緒讀取感測器數據
#     sensor_thread = Thread(target=update_sensor_data, daemon=True)
#     sensor_thread.start()

#     print("\n" + "=" * 60)
#     print("智能鼓棒系統 - 含位置識別訓練")
#     print("=" * 60)
#     print("網頁伺服器啟動中...")
#     print("請在瀏覽器開啟: http://localhost:5000")
#     print("或從其他裝置開啟: http://<樹莓派IP>:5000")
#     print("按 Ctrl+C 停止伺服器")
#     print("=" * 60 + "\n")

#     # 啟動 Flask 伺服器（允許外部連線）
#     app.run(host='0.0.0.0', port=5000, debug=False)
