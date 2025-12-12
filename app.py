from flask import Flask, jsonify, render_template
from calibration_right import update_right_angle
from calibration_left import update_left_angle
import threading

# I2C 總線鎖，防止左右手感測器同時讀取造成衝突
i2c_lock = threading.Lock()

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/right_data")
def right_data():
    with i2c_lock:
        roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_right_angle()

    # 閥值靈敏度在這邊調整
    # 只在向下揮動時觸發
    is_downward_swing = gy > 20  # Y軸角速度為正，表示向下
    is_sudden_stop = az < -1.0     # Z軸加速度偵測到衝擊

    # 綜合判斷為敲擊
    is_hit = is_downward_swing and is_sudden_stop

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
        "is_hit": is_hit
    })

@app.route("/left_data")
def left_data():
    with i2c_lock:
        roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_left_angle()

    # 左手敲擊偵測（同樣的邏輯）
    is_downward_swing = gy > 20
    is_sudden_stop = az < -1.0
    is_hit = is_downward_swing and is_sudden_stop

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
        "is_hit": is_hit
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
