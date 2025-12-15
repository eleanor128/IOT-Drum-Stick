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
        self.prev_pitch = 0
        self.peak_pitch = 0
        self.is_rising = False  # 是否正在舉起（pitch 增加中）
        self.rise_threshold = 3  # pitch 增加超過 3 度才算舉起
        self.fall_threshold = 3  # pitch 減少超過 3 度才算落下

    def detect_hit(self, current_pitch):
        """
        偵測「舉起並落下」的擊鼓動作
        返回：True 代表剛落下（擊鼓瞬間），False 代表非擊鼓狀態
        """
        pitch_change = current_pitch - self.prev_pitch

        # 偵測舉起階段（pitch 增加）
        if pitch_change > 0.5:  # pitch 正在增加
            if not self.is_rising:
                self.is_rising = True
                self.peak_pitch = current_pitch
            else:
                # 更新峰值
                if current_pitch > self.peak_pitch:
                    self.peak_pitch = current_pitch

        # 偵測落下階段（pitch 減少）
        elif self.is_rising and pitch_change < -0.5:  # pitch 正在減少
            # 檢查是否有足夠的舉起幅度
            rise_amount = self.peak_pitch - self.prev_pitch
            if rise_amount >= self.rise_threshold:
                # 檢查是否有足夠的落下幅度
                fall_amount = self.peak_pitch - current_pitch
                if fall_amount >= self.fall_threshold:
                    # 擊鼓發生！
                    self.is_rising = False
                    self.peak_pitch = 0
                    self.prev_pitch = current_pitch
                    return True

        self.prev_pitch = current_pitch
        return False

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

    # 使用新的偵測邏輯：pitch 增加又減少 = 舉起並落下 = 擊鼓
    is_hit = right_stick_state.detect_hit(pitch)

    # 只在擊鼓瞬間（落下時）偵測鼓棒尖端位於哪個鼓上方
    hit_drum = None
    if is_hit:
        # 計算落下時的鼓棒尖端位置，判斷在哪個鼓上方
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

    # 使用新的偵測邏輯：pitch 增加又減少 = 舉起並落下 = 擊鼓
    is_hit = left_stick_state.detect_hit(pitch)

    # 只在擊鼓瞬間（落下時）偵測鼓棒尖端位於哪個鼓上方
    hit_drum = None
    if is_hit:
        # 計算落下時的鼓棒尖端位置，判斷在哪個鼓上方
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
