from flask import Flask, jsonify, render_template
from calibration_right import update_angle

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_angle()

    # 只判斷是否有向下揮擊（使用 hit_detection.py 的條件）
    # 降低閾值以提高靈敏度
    is_fast = abs(gy) > 15       # 上下揮動（降低閾值）
    is_hit_accel = az > 7.5      # 瞬間加速度增加（降低閾值）
    is_downward = pitch < 0      # pitch < 0 表示往下揮（放寬限制）

    # 只回傳是否敲擊，不判斷是哪個鼓點
    is_hit = is_fast and is_hit_accel and is_downward

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
        "is_hit": is_hit  # 回傳是否偵測到向下揮擊
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
