"""
鼓棒碰撞偵測模組
根據鼓棒的 pitch/yaw 角度計算鼓棒前端的 3D 位置，並判斷是否打擊到特定的鼓
"""

import math

class DrumCollision:
    def __init__(self):
        # 定義每個鼓的 3D 位置和半徑（完全對應 drum_3d.js 中的 zones）
        self.drums = [
            {"name": "Hihat",     "pos3d": [2.5, 1.0, -0.8],   "radius": 1.0},
            {"name": "Snare",     "pos3d": [1.0, 0.2, -0.8],   "radius": 1.0},
            {"name": "Tom_high",  "pos3d": [1.0, 1.2, 1.5],    "radius": 1.0},
            {"name": "Tom_mid",   "pos3d": [-1.0, 1.2, 1.5],   "radius": 1.0},
            {"name": "Symbal",    "pos3d": [2.5, 2.5, 2.0],    "radius": 1.5},
            {"name": "Ride",      "pos3d": [-2.8, 2.5, 1.0],   "radius": 1.5},
            {"name": "Tom_floor", "pos3d": [-2.0, 0.3, -0.8],  "radius": 1.2},
        ]
    
    def calculate_stick_tip_position(self, pitch, yaw, hand="right"):
        """
        計算鼓棒前端（敲擊端）的 3D 位置
        完全對應 drum_3d.js 的計算邏輯
        
        參數說明：
        - pitch: Y軸旋轉角度，控制鼓棒上下揮動
        - yaw: Z軸旋轉角度，控制鼓棒左右位置
        - hand: "right" 或 "left"
        
        返回：
        (x, y, z): 鼓棒前端的 3D 座標
        """
        
        # 1. 計算握把位置（手的位置）- 完全對應 drum_3d.js
        # rightHandX = (rightYaw - 45) / 90 * 3 + 1;  // 右手初始位置靠近 Snare
        # leftHandX = (leftYaw - 45) / 90 * 3 - 1;   // 左手在左側
        if hand == "right":
            hand_x = (yaw - 45) / 90 * 3 + 1  # 右手初始位置靠近 Snare
        else:
            hand_x = (yaw - 45) / 90 * 3 - 1  # 左手在左側
        
        hand_y = 1.5   # 手的高度（提高）
        hand_z = -0.5  # 手的前後位置（更靠近鼓組）
        
        # 2. 計算鼓棒的旋轉角度（弧度）
        # 完全對應 drum_3d.js 的旋轉計算
        # rightStick.rotation.x = (finalRightPitch / 45) * (Math.PI / 3);
        # rightStick.rotation.y = (rightYaw / 45) * (Math.PI / 6);
        rotation_x = (pitch / 45) * (math.pi / 3)  # pitch 控制上下揮擊（繞 X 軸）
        rotation_y = (yaw / 45) * (math.pi / 6)    # yaw 控制左右擺動（繞 Y 軸）
        
        # 3. 鼓棒長度（從握把到前端的距離）
        # 對應 drum_3d.js 中 tipMesh.position.z = 2
        stick_length = 2.0
        
        # 4. 計算鼓棒前端相對於握把的偏移量
        # 鼓棒初始方向是沿著 Z 軸正向（向前）
        # 經過 X 軸和 Y 軸旋轉後的位置
        dx = stick_length * math.sin(rotation_y) * math.cos(rotation_x)
        dy = -stick_length * math.sin(rotation_x)  # 負號：pitch 增加時鼓棒往下
        dz = stick_length * math.cos(rotation_y) * math.cos(rotation_x)
        
        # 5. 計算鼓棒前端的絕對位置
        tip_x = hand_x + dx
        tip_y = hand_y + dy
        tip_z = hand_z + dz
        
        return tip_x, tip_y, tip_z
    
    def detect_hit_drum(self, pitch, yaw, hand="right"):
        """
        偵測鼓棒尖端是否打擊到某個鼓，並計算調整後的 pitch 角度
        只要鼓棒尖端碰到鼓面就算打擊到
        
        返回：
        {
            "drum_name": 打擊到的鼓名稱，如果沒打到則為 None,
            "adjusted_pitch": 調整後的 pitch 角度（讓鼓棒停在鼓面上）
        }
        """
        # 計算鼓棒尖端位置
        tip_x, tip_y, tip_z = self.calculate_stick_tip_position(pitch, yaw, hand)
        
        # 計算握把位置（與 drum_3d.js 完全一致）
        if hand == "right":
            hand_x = (yaw - 45) / 90 * 3 + 1
        else:
            hand_x = (yaw - 45) / 90 * 3 - 1
        hand_y = 1.5
        hand_z = -0.5
        
        # 檢查是否碰撞到任何鼓（按順序檢查，優先偵測較高的鼓）
        for drum in self.drums:
            drum_x, drum_y, drum_z = drum["pos3d"]
            radius = drum["radius"]
            
            # 計算鼓棒尖端與鼓中心的水平距離（X-Z 平面）
            dx = tip_x - drum_x
            dz = tip_z - drum_z
            horizontal_dist = math.sqrt(dx * dx + dz * dz)
            
            # 只要鼓棒尖端在鼓的半徑範圍內，且高度接近或低於鼓面，就算打擊到
            if horizontal_dist <= radius and tip_y <= drum_y + 0.05:
                # 碰撞發生！計算調整後的 pitch 讓鼓棒尖端停在鼓面上
                # 目標：讓鼓棒尖端的 Y 座標等於 drum_y + 0.03（緊貼鼓面）
                target_tip_y = drum_y + 0.03
                
                # 計算需要的高度差
                delta_y = target_tip_y - hand_y  # 從握把到目標高度的 Y 差
                
                # 使用反三角函數計算調整後的 pitch 角度
                # dy = -stick_length * sin(rotation_x)
                # => rotation_x = asin(-dy / stick_length)
                stick_length = 2.0
                if abs(delta_y) <= stick_length:
                    rotation_x = math.asin(-delta_y / stick_length)
                    adjusted_pitch = rotation_x / (math.pi / 3) * 45
                else:
                    adjusted_pitch = pitch  # 如果算不出來，保持原角度
                
                return {
                    "drum_name": drum["name"],
                    "adjusted_pitch": adjusted_pitch
                }
        
        # 如果沒有碰撞到任何鼓，返回原始 pitch
        return {"drum_name": None, "adjusted_pitch": pitch}

# 創建全局實例
drum_collision = DrumCollision()
