from flask import Flask, jsonify, render_template
from calibration_right import update_angle

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    pitch, roll, ax, ay, az, gx, gy, gz = update_angle()
    return jsonify({
        "pitch": pitch,
        "roll": roll,
        "ax": ax,
        "ay": ay,
        "az": az,
        "gy": gy,
        "gz": gz
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
