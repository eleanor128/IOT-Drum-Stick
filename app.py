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

    # 閥值靈敏度在這邊調整
    # 根據數據分析調整閾值：|gy| > 50 更容易觸發
    is_downward_swing = abs(gy) > 50  # Y軸角速度絕對值，向下揮動
    has_acceleration = abs(az) > 0.5 or abs(ax) > 0.5  # 任意方向加速度

    # 綜合判斷為敲擊（降低門檻，更容易觸發）
    is_hit = is_downward_swing and has_acceleration

    # 偵測打擊到哪個鼓，並取得調整後的 pitch（傳入 ax, az 加速度）
    collision_info = drum_collision.detect_hit_drum(ax, az, pitch, yaw, hand="right")
    hit_drum = collision_info["drum_name"]
    adjusted_pitch = collision_info["adjusted_pitch"]

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
        "hit_drum": hit_drum,
        "adjusted_pitch": adjusted_pitch
    })

@app.route("/left_data")
def left_data():
    with i2c_lock:
        roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_left_angle()

    # 左手敲擊偵測（同樣的邏輯）
    is_downward_swing = abs(gy) > 50  # Y軸角速度絕對值
    has_acceleration = abs(az) > 0.5 or abs(ax) > 0.5  # 任意方向加速度
    is_hit = is_downward_swing and has_acceleration

    # 偵測打擊到哪個鼓，並取得調整後的 pitch（傳入 ax, az 加速度）
    collision_info = drum_collision.detect_hit_drum(ax, az, pitch, yaw, hand="left")
    hit_drum = collision_info["drum_name"]
    adjusted_pitch = collision_info["adjusted_pitch"]

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
        "hit_drum": hit_drum,
        "adjusted_pitch": adjusted_pitch
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
