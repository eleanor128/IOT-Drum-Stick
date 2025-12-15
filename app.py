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
        self.prev_ay = 0  # 上一次的 ay 值
        self.prev_az = 0  # 上一次的 az 值
        self.hit_threshold = 1.0  # 綜合加速度變化閾值（降低以提高靈敏度）
        self.is_calibrated = False  # 是否已校準
        self.calibration_count = 0  # 校準計數

    def calibrate(self, ay, az):
        """
        簡單校準：只需要幾個樣本就開始偵測
        """
        if not self.is_calibrated:
            self.calibration_count += 1
            if self.calibration_count >= 5:
                self.is_calibrated = True
                print(f"[DrumStick] Calibration complete")

    def detect_hit(self, ay, az):
        """
        改進的擊鼓偵測：結合 ay 和 az 加速度變化
        - ay: 前後方向加速度（向前揮擊時增加）
        - az: 垂直方向加速度（向下揮擊時增加）

        返回：True 代表擊鼓瞬間，False 代表非擊鼓狀態
        """
        # 先進行校準
        if not self.is_calibrated:
            self.calibrate(ay, az)
            self.prev_ay = ay
            self.prev_az = az
            return False

        # 計算加速度變化
        ay_change = ay - self.prev_ay
        az_change = az - self.prev_az

        # 計算綜合加速度變化（向量長度）
        # 向下揮擊時，ay 和 az 都會有明顯變化
        combined_change = (ay_change**2 + az_change**2) ** 0.5

        # 偵測擊鼓：綜合加速度變化超過閾值
        # 同時確保是向下方向（az_change > 0）
        is_hit = combined_change > self.hit_threshold and az_change > 0.3

        # 更新前一次的值
        self.prev_ay = ay
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

    # 改進的偵測邏輯：結合 ay 和 az 加速度變化
    is_hit = right_stick_state.detect_hit(ay, az)

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

    # 改進的偵測邏輯：結合 ay 和 az 加速度變化
    is_hit = left_stick_state.detect_hit(ay, az)

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
