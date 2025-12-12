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

    # 只在向下揮動時觸發
    is_downward_swing = gy < -30  # Y軸角速度為負，表示向下
    is_sudden_stop = az > 8.0     # Z軸加速度偵測到衝擊

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
