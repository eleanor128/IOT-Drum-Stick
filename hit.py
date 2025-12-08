import time
import math
import pygame
from calibration_right import update_angle

# ---- 初始化音效 ----
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
pygame.mixer.init()

sounds = {
    "Hi-hat": pygame.mixer.Sound("static/sounds/hihat.wav"),
    "Ride": pygame.mixer.Sound("static/sounds/ride.wav"),
    "Snare": pygame.mixer.Sound("static/sounds/snare.wav"),
    "Tom 1": pygame.mixer.Sound("static/sounds/tom_high.wav"),
    "Tom 2": pygame.mixer.Sound("static/sounds/tom_mid.wav"),
    "Floor Tom": pygame.mixer.Sound("static/sounds/tom_floor.wav"),
    "Crash": pygame.mixer.Sound("static/sounds/symbal.wav"),
}

# ---- 靈敏敲擊參數 ----
HIT_THRESHOLD = 1.2      # 原本 2g，現在降低到 1.2g 比較靈敏
COOLDOWN = 0.10          # 100ms 冷卻避免連續偵測
last_hit_time = 0

# ---- 角度判斷分區 ----
def detect_drum_by_angle(pitch, roll):

    if pitch > -5:
        return None   # 還沒真的揮下去

    if roll < -40:
        return "Crash"
    elif -40 <= roll < -20:
        return "Hi-hat"
    elif -20 <= roll <= 20:
        return "Snare"
    elif 20 < roll <= 40:
        return "Tom 1"
    elif 40 < roll <= 60:
        return "Tom 2"
    elif roll > 60:
        return "Ride"

    return None


# ---- 計算加速度大小（用舊邏輯的靈敏做法） ----
def accel_magnitude(ax, ay, az):
    return math.sqrt(ax * ax + ay * ay + az * az)


print("🥁 多鼓敲擊偵測開始！（Ctrl+C 停止）")

while True:
    pitch, roll, ax, ay, az, gx, gy, gz = update_angle()

    now = time.time()

    # ---- 計算加速度大小，扣掉 1g 重力 ----
    magnitude = accel_magnitude(ax, ay, az)
    net_acc = abs(magnitude - 9.8)   # 減去重力值

    # ---- 若敲擊過近，進入冷卻 ----
    if now - last_hit_time < COOLDOWN:
        time.sleep(0.005)
        continue

    # ---- 敲擊判斷（靈敏版） ----
    if net_acc > HIT_THRESHOLD:

        drum = detect_drum_by_angle(pitch, roll)

        if drum:
            # 強度影響音量
            volume = min(1.0, 0.2 + (net_acc / 4.0))
            sounds[drum].set_volume(volume)
            sounds[drum].play()

            print(f"🔥 HIT {drum:<7} | pitch={pitch:5.1f}, roll={roll:5.1f} | acc={net_acc:.2f}g | vol={volume:.2f}")

            last_hit_time = now

    time.sleep(0.005)
