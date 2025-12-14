import math
import json
import os

class DrumCollisionDetector:
    def __init__(self, config_path="static/js/3d_settings.js"):
        """從 3d_settings.js 載入所有配置"""
        self.config = self._load_config_from_js(config_path)
        self.drums = self.config["drums"]
        self.collision_buffer = self.config.get("COLLISION_BUFFER", 0.05)
        
    def _load_config_from_js(self, config_path):
        """解析 3d_settings.js 中的所有配置參數"""
        config = {
            "drums": [],
            # 預設值（萬一讀取失敗）
            "GRIP_RIGHT_X": -0.6,
            "GRIP_LEFT_X": 0.4,
            "GRIP_BASE_Y": 1.0,
            "GRIP_BASE_Z": -3.0,
            "YAW_SENSITIVITY": 45,
            "YAW_POSITION_FACTOR": 0.8,
            "PITCH_THRESHOLD": 15,
            "PITCH_Y_FACTOR": 0.003,
            "PITCH_Z_TILTED_MAX": 2.0,
            "PITCH_Z_TILTED_FACTOR": 1.5,
            "PITCH_Z_FLAT_FACTOR": 0.005,
            "ACCEL_Z_FACTOR": 0.02,
            "ACCEL_Z_MAX": 0.3,
            "GRIP_Z_MIN": -2.0,
            "GRIP_Z_MAX": -0.3,
            "GRIP_RIGHT_X_MIN": -1.4,
            "GRIP_RIGHT_X_MAX": -0.2,
            "GRIP_LEFT_X_MIN": 0.3,
            "GRIP_LEFT_X_MAX": 1.5,
            "COLLISION_BUFFER": 0.05,
            "STICK_LENGTH": 1.2,
        }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析常數定義
            import re
            const_pattern = r'const\s+(\w+)\s*=\s*([^;]+);'
            matches = re.findall(const_pattern, content)
            
            for name, value in matches:
                value = value.strip()
                
                # 移除註解
                if '//' in value:
                    value = value[:value.index('//')].strip()
                
                # 解析數值
                try:
                    # 替換 Math.PI
                    value = value.replace('Math.PI', str(math.pi))
                    
                    # 嘗試計算表達式
                    if any(op in value for op in ['+', '-', '*', '/']):
                        parsed_value = eval(value)
                    else:
                        # 嘗試轉換為浮點數
                        parsed_value = float(value)
                    
                    if name in config:
                        config[name] = parsed_value
                        
                except (ValueError, SyntaxError):
                    pass  # 無法解析的值跳過
            
            # 解析 zones 陣列
            config["drums"] = self._parse_zones_array(content)
            
            print(f"[DrumCollision] Loaded config from {config_path}")
            print(f"  - {len(config['drums'])} drums")
            print(f"  - PITCH_THRESHOLD = {config['PITCH_THRESHOLD']}")
            print(f"  - YAW_POSITION_FACTOR = {config['YAW_POSITION_FACTOR']}")
            print(f"  - GRIP_BASE_Z = {config['GRIP_BASE_Z']}")
            
            return config
            
        except Exception as e:
            print(f"[DrumCollision] Failed to load config: {e}")
            config["drums"] = self._get_default_drums()
            return config
    
    def _parse_zones_array(self, content):
        """解析 3d_settings.js 中的 zones 陣列"""
        try:
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
                return drums
            else:
                raise ValueError("No drums found in zones array")
            
        except Exception as e:
            print(f"[DrumCollision] Failed to parse zones: {e}")
            return self._get_default_drums()
    
    def _get_default_drums(self):
        """備用硬編碼配置（以防載入失敗）"""
        return [
            {"name": "Hihat", "x": 1.8, "y": 0.8, "z": -1, "radius": 0.65},
            {"name": "Snare", "x": 0.5, "y": 0.4, "z": -1, "radius": 0.65},
            {"name": "Tom_high", "x": 0.6, "y": 0.8, "z": 0.3, "radius": 0.5},
            {"name": "Tom_mid", "x": -0.6, "y": 0.8, "z": 0.3, "radius": 0.5},
            {"name": "Symbal", "x": 1.7, "y": 1.4, "z": 0.5, "radius": 0.80},
            {"name": "Ride", "x": -1.8, "y": 1.4, "z": -0.1, "radius": 0.90},
            {"name": "Tom_floor", "x": -1.2, "y": 0.2, "z": -1, "radius": 0.80},
        ]
    
    def calculate_stick_tip_position(self, ax, az, pitch, yaw, hand="right"):
        """
        計算鼓棒前端（敲擊端）的 3D 位置
        完全對應 drum_3d.js 的計算邏輯
        
        參數說明：
        - ax: X軸加速度，控制鼓棒前後深淺
        - az: Z軸加速度，用於判斷是否在敲擊狀態
        - pitch: Y軸旋轉角度，控制鼓棒上下揮動
        - yaw: Z軸旋轉角度，控制鼓棒左右位置
        - hand: "right" 或 "left"
        
        返回：
        (x, y, z): 鼓棒前端的 3D 座標
        """
        
        # 從配置讀取所有參數（自動與 3d_settings.js 同步）
        cfg = self.config
        GRIP_RIGHT_X = cfg["GRIP_RIGHT_X"]
        GRIP_LEFT_X = cfg["GRIP_LEFT_X"]
        GRIP_BASE_Y = cfg["GRIP_BASE_Y"]
        GRIP_BASE_Z = cfg["GRIP_BASE_Z"]
        YAW_SENSITIVITY = cfg["YAW_SENSITIVITY"]
        YAW_POSITION_FACTOR = cfg["YAW_POSITION_FACTOR"]
        PITCH_THRESHOLD = cfg["PITCH_THRESHOLD"]
        PITCH_Y_FACTOR = cfg["PITCH_Y_FACTOR"]
        PITCH_Z_TILTED_MAX = cfg["PITCH_Z_TILTED_MAX"]
        PITCH_Z_TILTED_FACTOR = cfg["PITCH_Z_TILTED_FACTOR"]
        PITCH_Z_FLAT_FACTOR = cfg["PITCH_Z_FLAT_FACTOR"]
        ACCEL_Z_FACTOR = cfg["ACCEL_Z_FACTOR"]
        ACCEL_Z_MAX = cfg["ACCEL_Z_MAX"]
        GRIP_Z_MIN = cfg["GRIP_Z_MIN"]
        GRIP_Z_MAX = cfg["GRIP_Z_MAX"]
        
        # 1. 計算握把 X 位置（yaw增加→手往X負向/左側移動）
        if hand == "right":
            hand_x = GRIP_RIGHT_X - (yaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR
        else:
            hand_x = GRIP_LEFT_X - (yaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR
        
        # 2. 計算握把 Y 位置
        hand_y = GRIP_BASE_Y + pitch * PITCH_Y_FACTOR
        
        # 3. 計算握把 Z 位置（與前端完全一致）
        hand_z = GRIP_BASE_Z
        
        if pitch > PITCH_THRESHOLD:
            # 打擊前方的鼓（舉起）- pitch 大於閾值時代表舉高打前方鼓
            depth_factor = (pitch - PITCH_THRESHOLD) / 20
            hand_z += min(PITCH_Z_TILTED_MAX, depth_factor * PITCH_Z_TILTED_FACTOR)
        else:
            # 打擊後方的鼓（向下）- pitch 小於閾值時打後方鼓
            hand_z += abs(pitch) * PITCH_Z_FLAT_FACTOR
        
        # 加入加速度影響
        az_contribution = max(-ACCEL_Z_MAX, min(ACCEL_Z_MAX, abs(ax) * ACCEL_Z_FACTOR))
        hand_z += az_contribution
        
        # 限制範圍
        hand_z = max(GRIP_Z_MIN, min(GRIP_Z_MAX, hand_z))
        
        # 手部 Y 位置固定在基礎高度（不受 pitch 影響）
        hand_y = GRIP_BASE_Y
        
        # 2. 限制 Pitch 角度範圍並計算旋轉
        PITCH_MIN = cfg.get("PITCH_MIN", -30)
        PITCH_MAX = cfg.get("PITCH_MAX", 45)
        clamped_pitch = max(PITCH_MIN, min(PITCH_MAX, pitch))
        
        # 3. 簡化的鼓棒尖端位置計算
        # 使用與前端一致的 3D 旋轉計算
        # 確保視覺上的鼓棒尖端與碰撞檢測的尖端位置完全一致
        stick_length = cfg["STICK_LENGTH"]
        
        # 將角度轉換為弧度（與前端 drum_3d.js 完全一致）
        # 前端：rightRotX = -(clampedRightPitch / 20) * (Math.PI / 2)
        # 前端：rightRotY = -(effectiveRightYaw / 30) * (Math.PI / 3)
        
        # 判斷是否在敲擊狀態（az < -1.0 為敲擊）
        is_hitting = (az < -1.0)
        
        if is_hitting:
            # 敲擊時：pitch 增加 → 鼓棒向上旋轉
            pitch_radians = -(pitch / 20) * (math.pi / 2)
        else:
            # 平時：保持水平，僅微幅調整
            pitch_radians = -(pitch / 25) * (math.pi / 8)
        
        # yaw 增加 → 鼓棒向左旋轉
        # 注意：前端使用負號，所以這裡也要用負號
        yaw_radians = -(yaw / 30) * (math.pi / 3)
        
        # 3D 旋轉公式（與 drum_3d.js 的 rightTipX/Y/Z 計算完全一致）：
        # rightTipX = rightX + stickLength * Math.sin(rightRotY) * Math.cos(rightRotX)
        # rightTipY = rightY - stickLength * Math.sin(rightRotX)
        # rightTipZ = rightZ + stickLength * Math.cos(rightRotY) * Math.cos(rightRotX)
        
        dx = stick_length * math.sin(yaw_radians) * math.cos(pitch_radians)  # X: 左右
        dy = -stick_length * math.sin(pitch_radians)                         # Y: 上下
        dz = stick_length * math.cos(yaw_radians) * math.cos(pitch_radians)  # Z: 前後
        
        # 確保 dz > 0（尖端始終在手的前方）
        dz = max(0.1, dz)
        
        # 4. 計算鼓棒前端的絕對位置
        tip_x = hand_x + dx
        tip_y = hand_y + dy
        tip_z = hand_z + dz
        
        return tip_x, tip_y, tip_z
    
    def detect_hit_drum(self, ax, az, pitch, yaw, hand="right"):
        """
        偵測鼓棒尖端是否打擊到某個鼓（基於 XZ 平面投影）
        將鼓和鼓棒都映射到 XZ 平面（俯視圖），只檢查 2D 距離
        
        參數說明：
        - ax: X軸加速度，控制鼓棒前後深度
        - az: Z軸加速度，用於判斷是否在敲擊狀態
        - pitch: Y軸旋轉角度，控制鼓棒上下揮動
        - yaw: Z軸旋轉角度，控制鼓棒左右位置
        - hand: "right" 或 "left"
        
        返回：
        {
            "drum_name": 打擊到的鼓名稱，如果沒打到則為 None,
            "adjusted_pitch": 調整後的 pitch 角度（讓鼓棒停在鼓面上）
        }
        """
        # 計算鼓棒尖端 3D 位置
        tip_x, tip_y, tip_z = self.calculate_stick_tip_position(ax, az, pitch, yaw, hand)
        
        # 計算握把位置（與 drum_3d.js 完全一致）
        # 使用與 calculate_stick_tip_position 相同的邏輯（從配置讀取）
        cfg = self.config
        GRIP_RIGHT_X = cfg["GRIP_RIGHT_X"]
        GRIP_LEFT_X = cfg["GRIP_LEFT_X"]
        GRIP_BASE_Y = cfg["GRIP_BASE_Y"]
        GRIP_BASE_Z = cfg["GRIP_BASE_Z"]
        YAW_SENSITIVITY = cfg["YAW_SENSITIVITY"]
        YAW_POSITION_FACTOR = cfg["YAW_POSITION_FACTOR"]
        PITCH_THRESHOLD = cfg["PITCH_THRESHOLD"]
        PITCH_Y_FACTOR = cfg["PITCH_Y_FACTOR"]
        PITCH_Z_TILTED_MAX = cfg["PITCH_Z_TILTED_MAX"]
        PITCH_Z_TILTED_FACTOR = cfg["PITCH_Z_TILTED_FACTOR"]
        PITCH_Z_FLAT_FACTOR = cfg["PITCH_Z_FLAT_FACTOR"]
        ACCEL_Z_FACTOR = cfg["ACCEL_Z_FACTOR"]
        ACCEL_Z_MAX = cfg["ACCEL_Z_MAX"]
        GRIP_Z_MIN = cfg["GRIP_Z_MIN"]
        GRIP_Z_MAX = cfg["GRIP_Z_MAX"]
        
        if hand == "right":
            hand_x = GRIP_RIGHT_X - (yaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR
        else:
            hand_x = GRIP_LEFT_X - (yaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR
        
        # 手部 Y 位置固定在基礎高度
        hand_y = GRIP_BASE_Y
        
        # 計算 Z 位置（與前端和 calculate_stick_tip_position 完全一致）
        hand_z = GRIP_BASE_Z
        if pitch > PITCH_THRESHOLD:
            # 打擊前方的鼓（舉起）- pitch 大於閾值時代表舉高打前方鼓
            depth_factor = (pitch - PITCH_THRESHOLD) / 20
            hand_z += min(PITCH_Z_TILTED_MAX, depth_factor * PITCH_Z_TILTED_FACTOR)
        else:
            # 打擊後方的鼓（向下）- pitch 小於閾值時打後方鼓
            hand_z += abs(pitch) * PITCH_Z_FLAT_FACTOR
        
        az_contribution = max(-ACCEL_Z_MAX, min(ACCEL_Z_MAX, abs(ax) * ACCEL_Z_FACTOR))
        hand_z += az_contribution
        hand_z = max(GRIP_Z_MIN, min(GRIP_Z_MAX, hand_z))
        
        # 檢查是否碰撞到任何鼓（XZ 平面 2D 投影檢測）
        for drum in self.drums:
            drum_x, drum_y, drum_z = drum["x"], drum["y"], drum["z"]
            radius = drum["radius"]
            
            # 計算鼓棒尖端與鼓中心在 XZ 平面上的 2D 距離（俯視圖）
            dx = tip_x - drum_x
            dz = tip_z - drum_z
            distance_2d = math.sqrt(dx * dx + dz * dz)
            
            # 只要鼓棒尖端在鼓的 XZ 投影範圍內，就算打擊到
            # 不考慮 Y 軸高度，讓擊中更容易
            if distance_2d <= radius:
                # 碰撞發生！計算調整後的 pitch 讓鼓棒尖端停在鼓面上
                
                # 計算鼓面高度
                is_cymbal = "Symbal" in drum["name"] or "Ride" in drum["name"] or "Hihat" in drum["name"]
                if is_cymbal:
                    drum_height = 0.05  # 鈸很薄
                elif drum["name"] == "Tom_floor":
                    drum_height = 1.0   # 落地鼓較長
                else:
                    drum_height = 0.5   # 其他鼓的標準高度
                
                drum_top_y = drum_y + drum_height / 2
                target_tip_y = drum_top_y + 0.03  # 鼓棒尖端停在鼓面上方 3cm
                
                # 計算需要的高度差
                delta_y = target_tip_y - hand_y  # 從握把到目標高度的 Y 差
                
                # 使用反三角函數計算調整後的 pitch 角度
                stick_length = cfg["STICK_LENGTH"]
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
