from flask import Flask, jsonify, render_template
from calibration_right import update_right_angle
from calibration_left import update_left_angle
from drum_collision import drum_collision
import threading

# I2C 總線鎖，防止左右手感測器同時讀取造成衝突
i2c_lock = threading.Lock()

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')

# 擊鼓偵測狀態追蹤
class DrumStickState:
    def __init__(self):
        self.prev_az = 0  # 上一次的 az 值（用於計算重力補償後的加速度）
        self.az_hit_threshold = 0.8  # az 變化閾值（向下敲擊時 az 會突然增加）降低以提高靈敏度
        self.gravity_az = 0  # 重力分量（靜止時的 az 基準值）
        self.calibration_samples = []  # 校準樣本
        self.is_calibrated = False  # 是否已校準

    def calibrate(self, az):
        """
        校準重力分量（收集靜止時的 az 值）
        前 10 個樣本用於計算靜止時的重力分量（減少校準時間）
        """
        if not self.is_calibrated:
            self.calibration_samples.append(az)
            if len(self.calibration_samples) >= 10:
                # 計算平均值作為重力基準
                self.gravity_az = sum(self.calibration_samples) / len(self.calibration_samples)
                self.is_calibrated = True
                print(f"[DrumStick] Calibrated gravity_az = {self.gravity_az:.2f}")

    def detect_hit(self, az):
        """
        簡化的擊鼓偵測：只看 az 加速度變化
        - 扣除重力分量
        - 偵測向下加速（az 突然增加）

        返回：True 代表擊鼓瞬間，False 代表非擊鼓狀態
        """
        # 先進行校準
        if not self.is_calibrated:
            self.calibrate(az)
            self.prev_az = az
            return False

        # 扣除重力分量，得到真實加速度
        az_compensated = az - self.gravity_az

        # 計算加速度變化（向下加速時 az 會突然增加）
        az_change = az_compensated - (self.prev_az - self.gravity_az)

        # 偵測擊鼓：az 突然增加超過閾值
        is_hit = az_change > self.az_hit_threshold

        self.prev_az = az
        return is_hit

# 為左右手各創建一個狀態追蹤器
right_stick_state = DrumStickState()
left_stick_state = DrumStickState()



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/3d")
def index_3d():
    return render_template("index_3d.html")

@app.route("/right_data")
def right_data():
    with i2c_lock:
        roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_right_angle()

    # 簡化的偵測邏輯：只看 az 加速度變化（扣除重力後）
    is_hit = right_stick_state.detect_hit(az)

    # 只在擊鼓瞬間偵測鼓棒尖端位於哪個鼓上方
    hit_drum = None
    if is_hit:
        # 計算擊鼓時的鼓棒尖端位置，判斷在哪個鼓上方
        collision_info = drum_collision.detect_hit_drum(ax, az, pitch, yaw, hand="right")
        hit_drum = collision_info["drum_name"]

    return jsonify({
        "roll (x軸轉)": roll,
        "pitch (y軸轉)": pitch,
        "yaw (z軸轉)": yaw,
        "ax": ax,
        "ay": ay,
        "az": az,
        "gx": gx,
        "gy": gy,
        "gz": gz,
        "is_hit": is_hit,
        "hit_drum": hit_drum
    })

@app.route("/left_data")
def left_data():
    with i2c_lock:
        roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_left_angle()

    # 簡化的偵測邏輯：只看 az 加速度變化（扣除重力後）
    is_hit = left_stick_state.detect_hit(az)

    # 只在擊鼓瞬間偵測鼓棒尖端位於哪個鼓上方
    hit_drum = None
    if is_hit:
        # 計算擊鼓時的鼓棒尖端位置，判斷在哪個鼓上方
        collision_info = drum_collision.detect_hit_drum(ax, az, pitch, yaw, hand="left")
        hit_drum = collision_info["drum_name"]

    return jsonify({
        "roll (x軸轉)": roll,
        "pitch (y軸轉)": pitch,
        "yaw (z軸轉)": yaw,
        "ax": ax,
        "ay": ay,
        "az": az,
        "gx": gx,
        "gy": gy,
        "gz": gz,
        "is_hit": is_hit,
        "hit_drum": hit_drum
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
