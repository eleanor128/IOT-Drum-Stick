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
    is_fast = abs(gy) > 20       # 上下揮動
    is_hit_accel = az > 9.0      # 瞬間加速度增加（撞擊特徵）
    is_downward = pitch < -5     # pitch < -5 表示往下揮

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
