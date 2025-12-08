# hit_detection.py
import time
import math
import pygame
from calibration_right import update_angle

# ---- 初始化音效 ----
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
pygame.mixer.init()

sounds = {
    "Hi-hat": pygame.mixer.Sound("sounds/hihat.wav"),
    "Ride": pygame.mixer.Sound("sounds/ride.wav"),
    "Snare": pygame.mixer.Sound("sounds/snare.wav"),
    "Tom 1": pygame.mixer.Sound("sounds/tom_high.wav"),
    "Tom 2": pygame.mixer.Sound("sounds/tom_mid.wav"),
    "Floor Tom": pygame.mixer.Sound("sounds/tom_floor.wav"),
    "Crash": pygame.mixer.Sound("sounds/symbal.wav"),
}

hit_cooldown = 0

def detect_drum(pitch, roll):
    if pitch > -10:
        return None

    if roll < -20:
        return "Hi-hat"
    elif -20 <= roll <= 20:
        return "Snare"
    elif roll > 20:
        return "Ride"

    return None


print("開始敲擊偵測！（Ctrl+C 停止）")

pygame.mixer.init()
sound = pygame.mixer.Sound("sounds/snare.wav")


while True:
    sound.play()
    pitch, roll, ax, ay, az, gx, gy, gz = update_angle()

    # ---- 新增更精準的敲擊條件 ----
    fast_swing = abs(gy) > 80 or abs(gz) > 80   # 快速揮動
    downward_hit = az > 9.5                     # 有朝下撞擊的特徵

    if hit_cooldown == 0:
        if fast_swing and downward_hit:
            drum = detect_drum(pitch, roll)

            if drum:
                print(f"🔥 HIT → {drum} | pitch={pitch:.1f}, roll={roll:.1f}")

                if drum in sounds:
                    sounds[drum].play()

                hit_cooldown = 6
    else:
        hit_cooldown -= 1

    time.sleep(0.01)
