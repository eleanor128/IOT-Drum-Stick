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

    # 參考 hit_detection.py 的邏輯，偵測快速揮動和瞬間停止
    is_fast_swing = abs(gy) > 35  # Y軸角速度 (pitch速度) 夠快
    is_sudden_stop = az > 8.0     # Z軸加速度偵測到衝擊

    # 綜合判斷為敲擊
    is_hit = is_fast_swing and is_sudden_stop

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
