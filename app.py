from flask import Flask, jsonify, render_template
from calibration_right import update_angle

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')

# 追蹤上一次的 pitch 值，用於計算變化量
prev_pitch = 0

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    global prev_pitch

    roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_angle()

    # 計算 pitch 變化量（用於偵測向下揮擊動作）
    delta_pitch = pitch - prev_pitch
    prev_pitch = pitch

    # 只判斷是否有向下揮擊
    is_fast = abs(gy) > 15           # 陀螺儀偵測到快速旋轉
    is_hit_accel = ax > 7.5          # 瞬間加速度增加（撞擊特徵）
    is_downward = delta_pitch < -10  # pitch 快速減少（向下揮）

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
        "delta_pitch": delta_pitch,  # pitch 變化量（用於監控）
        "is_hit": is_hit  # 回傳是否偵測到向下揮擊
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
