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
    return jsonify({
        "roll (x軸轉)": roll,
        "pitch (y軸轉)": pitch,
        "yaw (z軸轉)": yaw,
        "ax": ax,
        "ay": ay,
        "az": az,
        "gx": gx,
        "gy": gy,
        "gz": gz
    })

@app.route("/hit_detection")
def hit_detection():
    detect_drum()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
