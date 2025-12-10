from flask import Flask, jsonify, render_template
from calibration_right import update_angle
from hit_detection import detect_drum

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_angle()

    # 使用 hit_detection.py 的邏輯判斷敲擊
    is_fast = abs(gy) > 40       # 上下揮動
    is_hit_accel = az > 9.0      # 瞬間加速度增加（撞擊特徵）
    drum_name = None

    if is_fast and is_hit_accel:
        drum_name = detect_drum(pitch, roll)

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
        "drum": drum_name  # 回傳偵測到的鼓點名稱
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
