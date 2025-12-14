import math
import json
import os

class DrumCollisionDetector:
    def __init__(self, config_path="static/js/3d_settings.js"):
        """從 3d_settings.js 載入鼓的配置"""
        self.drums = self._load_drums_from_js(config_path)
        self.collision_buffer = 0.05  # 從 3d_settings.js 的 COLLISION_BUFFER
        
    def _load_drums_from_js(self, config_path):
        """解析 3d_settings.js 中的 zones 陣列"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 找到 zones 陣列定義
            start = content.find('const zones = [')
            if start == -1:
                raise ValueError("Cannot find zones definition")
            
            end = content.find('];', start)
            if end == -1:
                raise ValueError("Cannot find zones end marker")
            
            # 提取 zones 陣列內容（不包含 'const zones = ' 和最後的 '];'）
            zones_start = start + len('const zones = ')
            zones_content = content[zones_start:end+1]  # 包含 ']'
            
            # 逐行處理，提取每個鼓的配置
            drums = []
            current_obj = {}
            in_obj = False
            
            for line in zones_content.split('\n'):
                line = line.strip()
                
                # 移除註解
                if '//' in line:
                    line = line[:line.index('//')].strip()
                
                if not line:
                    continue
                
                # 開始一個物件
                if '{' in line:
                    in_obj = True
                    current_obj = {}
                    continue
                
                # 結束一個物件
                if '}' in line:
                    if current_obj and 'name' in current_obj and 'pos3d' in current_obj:
                        drums.append({
                            "name": current_obj["name"],
                            "x": current_obj["pos3d"][0],
                            "y": current_obj["pos3d"][1],
                            "z": current_obj["pos3d"][2],
                            "radius": current_obj["radius"]
                        })
                    in_obj = False
                    continue
                
                if not in_obj:
                    continue
                
                # 解析屬性
                if 'name:' in line:
                    # name: "Hihat",
                    name = line.split('"')[1]
                    current_obj["name"] = name
                    
                elif 'pos3d:' in line:
                    # pos3d: [1.8, 0.8, -1],
                    pos_str = line[line.index('[')+1:line.index(']')]
                    pos = [float(x.strip()) for x in pos_str.split(',')]
                    current_obj["pos3d"] = pos
                    
                elif 'radius:' in line:
                    # radius: 0.65,
                    radius_str = line.split(':')[1].strip().rstrip(',')
                    current_obj["radius"] = float(radius_str)
            
            if drums:
                print(f"[DrumCollision] Loaded {len(drums)} drums from {config_path}")
                return drums
            else:
                raise ValueError("No drums found in zones array")
            
        except Exception as e:
            print(f"[DrumCollision] Failed to load {config_path}, using defaults: {e}")
            # 備用硬編碼配置（以防載入失敗）
            return [
                {"name": "Hihat", "x": 1.8, "y": 0.8, "z": -1, "radius": 0.65},
                {"name": "Snare", "x": 0.5, "y": 0.4, "z": -1, "radius": 0.65},
                {"name": "Tom_high", "x": 0.6, "y": 0.8, "z": 0.3, "radius": 0.5},
                {"name": "Tom_mid", "x": -0.6, "y": 0.8, "z": 0.3, "radius": 0.5},
                {"name": "Symbal", "x": 1.7, "y": 1.4, "z": 0.5, "radius": 0.80},
                {"name": "Ride", "x": -1.8, "y": 1.4, "z": -0.1, "radius": 0.90},
                {"name": "Tom_floor", "x": -1.2, "y": 0.2, "z": -1, "radius": 0.80},
            ]
    
    def calculate_stick_tip_position(self, ax, pitch, yaw, hand="right"):
        """
        計算鼓棒前端（敲擊端）的 3D 位置
        完全對應 drum_3d.js 的計算邏輯
        
        參數說明：
        - ax: X軸加速度，控制鼓棒前後深淺
        - pitch: Y軸旋轉角度，控制鼓棒上下揮動
        - yaw: Z軸旋轉角度，控制鼓棒左右位置
        - hand: "right" 或 "left"
        
        返回：
        (x, y, z): 鼓棒前端的 3D 座標
        """
        
        # 1. 計算握把位置（手的位置）- 完全對應 drum_3d.js
        # targetRightX = GRIP_RIGHT_X + (effectiveRightYaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR
        # targetLeftX = GRIP_LEFT_X + (effectiveLeftYaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR
        # GRIP_RIGHT_X = 0.4, GRIP_LEFT_X = 0.6, YAW_SENSITIVITY = 45, YAW_POSITION_FACTOR = 0.8
        if hand == "right":
            hand_x = 0.4 + (yaw / 45) * 0.8  # 右手初始位置靠近 Snare
        else:
            hand_x = 0.6 + (yaw / 45) * 0.8  # 左手在左側
        
        hand_y = 1.5    # 手的高度（提高）
        hand_z = -0.8   # 手的前後位置（與 Snare 的 Z 座標對齊）
        
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
    
    def detect_hit_drum(self, ax, pitch, yaw, hand="right"):
        """
        偵測鼓棒尖端是否打擊到某個鼓，並計算調整後的 pitch 角度
        只要鼓棒尖端碰到鼓面就算打擊到
        
        參數說明：
        - ax: X軸加速度，控制鼓棒前後深涺
        - pitch: Y軸旋轉角度，控制鼓棒上下揮動
        - yaw: Z軸旋轉角度，控制鼓棒左右位置
        - hand: "right" 或 "left"
        
        返回：
        {
            "drum_name": 打擊到的鼓名稱，如果沒打到則為 None,
            "adjusted_pitch": 調整後的 pitch 角度（讓鼓棒停在鼓面上）
        }
        """
        # 計算鼓棒尖端位置
        tip_x, tip_y, tip_z = self.calculate_stick_tip_position(ax, pitch, yaw, hand)
        
        # 計算握把位置（與 drum_3d.js 完全一致）
        if hand == "right":
            hand_x = 0.4 + (yaw / 45) * 0.8  # 右手起始位置在 Snare 上方
        else:
            hand_x = 0.6 + (yaw / 45) * 0.8  # 左手起始位置在 Snare 左側
        hand_y = 1.5
        hand_z = -0.8 + ax * 0.5  # X軸加速度控制前後深淺
        
        # 檢查是否碰撞到任何鼓（按順序檢查，優先偵測較高的鼓）
        for drum in self.drums:
            drum_x, drum_y, drum_z = drum["x"], drum["y"], drum["z"]
            radius = drum["radius"]
            
            # 計算鼓的高度（厚度）
            is_cymbal = "Symbal" in drum["name"] or "Ride" in drum["name"] or "Hihat" in drum["name"]
            if is_cymbal:
                drum_height = 0.05  # 鈸很薄
            elif drum["name"] == "Tom_floor":
                drum_height = 1.0   # 落地鼓較長
            else:
                drum_height = 0.5   # 其他鼓的標準高度
            
            # 計算鼓面高度（中心點 + 半高度）
            drum_top_y = drum_y + drum_height / 2
            
            # 計算鼓棒尖端與鼓中心的水平距離（X-Z 平面）
            dx = tip_x - drum_x
            dz = tip_z - drum_z
            horizontal_dist = math.sqrt(dx * dx + dz * dz)
            
            # 只要鼓棒尖端在鼓的半徑範圍內，且高度接近或低於鼓面，就算打擊到
            if horizontal_dist <= radius and tip_y <= drum_top_y + 0.03:
                # 碰撞發生！計算調整後的 pitch 讓鼓棒尖端停在鼓面上
                # 目標：讓鼓棒尖端的 Y 座標等於鼓面高度 + 0.03（緊貼鼓面）
                target_tip_y = drum_top_y + 0.03
                
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
drum_collision = DrumCollisionDetector()
