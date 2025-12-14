// ==================== 3D 場景設定檔 ====================
// 將所有配置參數集中管理，方便調整

// 音效設定
const DRUM_SOUND_DURATION = 0.3;  // 鼓音效播放時長（秒）

// 鼓棒設定
const STICK_LENGTH = 1.2;  // 鼓棒長度（米）
const STICK_TIP_POINT = 1.0;   // 尖端碰撞檢測位置（相對於棒長）
const STICK_BODY_POINT = 0.7;  // 棒身碰撞檢測位置（相對於棒長）

// 平滑與靈敏度設定
const SMOOTH_FACTOR = 0.08;  // 位置平滑係數（0-1，越小越平滑但延遲越高）降低以減少閃爍
const PITCH_SENSITIVITY = 30;  // Pitch 角度靈敏度
const PITCH_ANGLE_FACTOR = Math.PI / 2.2;  // Pitch 角度轉換係數
const YAW_SENSITIVITY = 45;  // Yaw 角度靈敏度
const YAW_ANGLE_FACTOR = Math.PI / 4;  // Yaw 角度轉換係數
const YAW_POSITION_FACTOR = 0.8;  // Yaw 對 X 位置的影響係數（降低以減少左右移動幅度）

// Pitch 角度範圍限制（度）
const PITCH_MIN = -30;  // 最小 Pitch（向上抬起的最大角度）
const PITCH_MAX = 45;   // 最大 Pitch（向下最低到鼓面，不會更低）

// 握把位置設定
const GRIP_BASE_Z = -3;  // 握把基礎 Z 位置（定位於可直接打 Snare）
const GRIP_BASE_Y = 1.00;   // 握把基礎 Y 位置（舒適敲擊高度）
const GRIP_RIGHT_X = 0.6;  // 右手握把基礎 X 位置（X負向，視角右側/鼓手右側）
const GRIP_LEFT_X = 0.8;    // 左手握把基礎 X 位置（X正向，視角左側/鼓手左側）

// Z軸移動參數（增強前伸能力以打到前方的鼓）
const PITCH_THRESHOLD = 15;  // Pitch 閾值（度），小於此值代表舉起打前方的鼓
const PITCH_Y_FACTOR = 0.003;  // Pitch 對 Y 軸影響係數
const PITCH_Z_TILTED_MAX = 2.0;  // 打擊傾斜鼓時最大 Z 偏移（增加以達到前方鼓）
const PITCH_Z_TILTED_FACTOR = 1.5;  // 打擊傾斜鼓時 Z 偏移係數（增加靈敏度）
const PITCH_Z_FLAT_FACTOR = 0.005;  // 打擊平面鼓時 Z 偏移係數
const ACCEL_Z_MAX = 0.3;  // 加速度對 Z 軸最大影響（增加）
const ACCEL_Z_FACTOR = 0.02;  // 加速度對 Z 軸影響係數（增加）

// Z軸範圍限制（根據鼓的位置和鼓棒長度自動計算）
const GRIP_Z_MIN = -2.0;  // 握把最後方位置（打 Snare/Hihat/Tom_floor，Z=-1 - 棒長*0.8）
const GRIP_Z_MAX = -0.3;  // 握把最前方位置（打 Symbal，Z=0.5 - 棒長*0.7）

// X軸範圍限制（左右手分開設定，因為起始位置不同）
const GRIP_RIGHT_X_MIN = -0.8;  // 右手握把最小X值（打 Ride，視角右側最遠處）
const GRIP_RIGHT_X_MAX = 0.6;  // 右手握把最大X值（打 Tom_mid，保持在內側）
const GRIP_LEFT_X_MIN = 0.3;    // 左手握把最小X值（打 Snare，保持在內側）
const GRIP_LEFT_X_MAX = 1.5;    // 左手握把最大X值（打 Hihat/Symbal，視角左側最遠處）

// 碰撞檢測設定
const COLLISION_BUFFER = 0.05;  // 碰撞緩衝距離
const HIT_RADIUS_OFFSET = 0.1;  // 碰撞檢測半徑偏移

// 擊打冷卻設定
const HIT_COOLDOWN_FRAMES = 10;  // 擊打冷卻時間（幀數）

// 自動對齊設定
const DRUM_CENTER_BLEND_FACTOR = 0.8;  // 擊打時鼓面中心對齊混合係數（0-1）

// 發光動畫設定
const GLOW_DECAY_RATE = 0.05;  // 發光衰減速度（每幀）
const GLOW_INTENSITY = 1.0;  // 初始發光強度

// 相機設定
const CAMERA_FOV = 60;  // 視角（度）
const CAMERA_ASPECT = 900 / 600;  // 長寬比
const CAMERA_NEAR = 0.1;  // 近平面
const CAMERA_FAR = 1000;  // 遠平面
const CAMERA_POSITION = [0, 3.5, -4];  // 相機位置 [x, y, z]
const CAMERA_LOOKAT = [0, 0, 2];  // 相機看向位置 [x, y, z]

// 場景設定
const SCENE_BG_COLOR = 0x222222;  // 場景背景色
const CANVAS_WIDTH = 900;  // 畫布寬度
const CANVAS_HEIGHT = 600;  // 畫布高度

// 光照設定
const AMBIENT_LIGHT_COLOR = 0xffffff;  // 環境光顏色
const AMBIENT_LIGHT_INTENSITY = 0.4;  // 環境光強度
const DIRECTIONAL_LIGHT_COLOR = 0xffffff;  // 方向光顏色
const DIRECTIONAL_LIGHT_INTENSITY = 0.6;  // 方向光強度
const DIRECTIONAL_LIGHT_POSITION = [0, 10, 0];  // 方向光位置

// 地板設定
const FLOOR_SIZE = 15;  // 地板尺寸
const FLOOR_COLOR = 0x2d2d2d;  // 地板顏色
const FLOOR_ROUGHNESS = 0.8;  // 地板粗糙度
const FLOOR_Y = -0.5;  // 地板 Y 位置

// 鼓棒視覺設定
const STICK_RADIUS_TIP = 0.015;  // 鼓棒前端半徑
const STICK_RADIUS_BASE = 0.02;  // 鼓棒後端半徑
const STICK_SEGMENTS = 8;  // 鼓棒圓柱分段數
const STICK_TIP_SPHERE_RADIUS = 0.03;  // 鼓棒尖端球體半徑
const STICK_GRIP_SPHERE_RADIUS = 0.022;  // 鼓棒握把球體半徑
const STICK_SPHERE_SEGMENTS = 12;  // 球體分段數

// 鼓棒顏色設定
const RIGHT_STICK_COLOR = 0xff0000;  // 右手鼓棒顏色（紅色）
const RIGHT_STICK_EMISSIVE = 0x660000;  // 右手鼓棒發光色
const LEFT_STICK_COLOR = 0x0000ff;  // 左手鼓棒顏色（藍色）
const LEFT_STICK_EMISSIVE = 0x000066;  // 左手鼓棒發光色


// 鼓區域設定
const zones = [
    { 
        name: "Hihat", 
        x: 675, y: 225, w: 225, h: 225, 
        color: "#3232ff", 
        pos3d: [1.8, 0.8, -1], 
        radius: 0.65, 
        rotation: -Math.PI / 9,  // -20°
        glowColor: "#3399ff"
    },   
    { 
        name: "Snare", 
        x: 450, y: 225, w: 225, h: 225, 
        color: "#d9d9d9", 
        pos3d: [0.5, 0.4, -1], 
        radius: 0.65, 
        rotation: -Math.PI / 12,  // -15°
        glowColor: "#ffffff" 
    }, 
    { 
        name: "Tom_high", 
        x: 450, y: 0, w: 225, h: 225, 
        color: "#ff7f2a", 
        pos3d: [0.6, 0.8, 0.3], 
        radius: 0.5, 
        rotation: -Math.PI / 5,  // -36°
        glowColor: "#ff6600" 
    },   
    { 
        name: "Tom_mid", 
        x: 450, y: 0, w: 225, h: 225, 
        color: "#ff7f2a", 
        pos3d: [-0.6, 0.8, 0.3], 
        radius: 0.5, 
        rotation: -Math.PI / 5,  // -36°
        glowColor: "#ff6600" 
    },  
    { 
        name: "Symbal", 
        x: 675, y: 0, w: 225, h: 225, 
        color: "#e5b3ff", 
        pos3d: [1.7, 1.4, 0.5], 
        radius: 0.80, 
        rotation: -Math.PI / 6,  // -30°
        glowColor: "#ff00ff" 
    },   
    { 
        name: "Ride", 
        x: 0, y: 0, w: 225, h: 225, 
        color: "#6eeee7", 
        pos3d: [-1.8, 1.4, -0.1], 
        radius: 0.90, 
        rotation: -Math.PI / 6,  // -30°
        glowColor: "#00ffff" 
    },  
    { 
        name: "Tom_floor", 
        x: 675, y: 225, w: 225, h: 225, 
        color: "#4d4d4d", 
        pos3d: [-1.2, 0.2, -1], 
        radius: 0.80, 
        rotation: -Math.PI / 9,  // -20°
        glowColor: "#aaaaaa" 
    }, 
];

// 鼓的高度設定
const CYMBAL_HEIGHT = 0.05;  // 鈸高度
const TOM_FLOOR_HEIGHT = 1.0;  // 落地通鼓高度
const STANDARD_DRUM_HEIGHT = 0.5;  // 標準鼓高度

// 鼓的預設半徑
const DEFAULT_CYMBAL_RADIUS = 1.2;  // 預設鈸半徑
const DEFAULT_DRUM_RADIUS = 0.9;  // 預設鼓半徑

// 鼓的視覺設定
const DRUM_COLOR = 0x1a1a1a;  // 鼓主體顏色（深灰色）
const DRUM_SEGMENTS = 32;  // 鼓圓柱分段數
const DRUM_EDGE_TORUS_RADIUS = 0.03;  // 鼓邊緣環半徑
const DRUM_EDGE_TORUS_TUBE = 8;  // 鼓邊緣環管道分段
const DRUM_EDGE_EMISSIVE_INTENSITY = 1.5;  // 鼓邊緣發光強度
const DRUM_EDGE_METALNESS = 0.8;  // 鼓邊緣金屬度
const DRUM_EDGE_ROUGHNESS = 0.2;  // 鼓邊緣粗糙度

// 音效文件路徑
const SOUND_FILES = {
    "Success": "/static/sounds/success.wav",
    "Symbal": "/static/sounds/symbal.wav",
    "Tom_high": "/static/sounds/tom_high.wav",
    "Tom_mid": "/static/sounds/tom_mid.wav",
    "Ride": "/static/sounds/ride.wav",
    "Hihat": "/static/sounds/hihat.wav",
    "Snare": "/static/sounds/snare.wav",
    "Tom_floor": "/static/sounds/tom_floor.wav",
};
