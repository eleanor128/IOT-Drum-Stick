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

hit_cooldown = 0


def detect_drum(pitch, roll):
    """
    根據 roll (左右角度) 分區，pitch 要往下才能敲擊
    """

    if pitch > -5:   # pitch > -5 表示還沒往下揮
        return None

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


print("開始敲擊偵測！（Ctrl+C 停止）")

while True:
    roll, pitch, yaw, ax, ay, az, gx, gy, gz = update_angle()

    # ---- 更靈敏的敲擊條件 ----
    is_fast = abs(gy) > 40       # 上下揮動
    is_hit_accel = az > 9.0      # 瞬間加速度增加（撞擊特徵）

    if hit_cooldown == 0:
        if is_fast and is_hit_accel:

            drum = detect_drum(pitch, roll)

            if drum:
                print(f"🔥 HIT → {drum} | pitch={pitch:.1f}, roll={roll:.1f}")

                if drum in sounds:
                    sounds[drum].play()

                hit_cooldown = 8   # 冷卻避免連續誤觸發
    else:
        hit_cooldown -= 1

    time.sleep(0.01)
