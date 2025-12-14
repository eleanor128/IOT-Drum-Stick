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

// 握把位置設定
const GRIP_BASE_Z = -2.2;  // 握把基礎 Z 位置（後方）
const GRIP_BASE_Y = 0.6;   // 握把基礎 Y 位置（高度）
const GRIP_RIGHT_X = 0.2;  // 右手握把基礎 X 位置
const GRIP_LEFT_X = 0.8;   // 左手握把基礎 X 位置

// Z軸移動參數
const PITCH_THRESHOLD = 5;  // Pitch 閾值（度），小於此值代表舉起打後方的鼓
const PITCH_Y_FACTOR = 0.002;  // Pitch 對 Y 軸影響係數
const PITCH_Z_TILTED_MAX = 0.8;  // 打擊傾斜鼓時最大 Z 偏移
const PITCH_Z_TILTED_FACTOR = 0.6;  // 打擊傾斜鼓時 Z 偏移係數
const PITCH_Z_FLAT_FACTOR = 0.003;  // 打擊平面鼓時 Z 偏移係數
const ACCEL_Z_MAX = 0.15;  // 加速度對 Z 軸最大影響
const ACCEL_Z_FACTOR = 0.01;  // 加速度對 Z 軸影響係數

// Z軸範圍限制
const GRIP_Z_MIN = -2.2;  // 握把最後方位置
const GRIP_Z_MAX = -0.5;  // 握把最前方位置

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

// 鼓/鈸配置
// pos3d: [x, y中心點, z], 鼓/鈸的完整幾何位置（傾斜圓柱體）
// 
// 【每個鼓/鈸的幾何範圍】(鼓面=頂部, 鼓底=底部)
// 1. Hihat (鈸): 中心點 [1.8, 0.8, -1], 半徑=0.65, 高度=0.05, 傾斜=-20°
//    範圍: Y=[0.776~0.824], Z=[-1.009~-0.991], X=[1.15~2.45]
// 2. Snare (鼓): 中心點 [0.5, 0.4, -0.8], 半徑=0.65, 高度=0.5, 傾斜=-15°
//    範圍: Y=[0.158~0.642], Z=[-0.865~-0.735], X=[-0.15~1.15]
// 3. Tom_high (鼓): 中心點 [0.6, 0.8, 0.7], 半徑=0.55, 高度=0.5, 傾斜=-26°
//    範圍: Y=[0.575~1.025], Z=[0.592~0.808], X=[0.05~1.15]
// 4. Tom_mid (鼓): 中心點 [-0.6, 0.8, 0.7], 半徑=0.55, 高度=0.5, 傾斜=-26°
//    範圍: Y=[0.575~1.025], Z=[0.592~0.808], X=[-1.15~-0.05]
// 5. Symbal (鈸): 中心點 [1.6, 1.4, 0.7], 半徑=0.80, 高度=0.05, 傾斜=-30°
//    範圍: Y=[1.378~1.422], Z=[0.688~0.713], X=[0.8~2.4]
// 6. Ride (鈸): 中心點 [-1.8, 1.4, -0.1], 半徑=0.90, 高度=0.05, 傾斜=-30°
//    範圍: Y=[1.378~1.422], Z=[-0.113~-0.088], X=[-2.7~-0.9]
// 7. Tom_floor (鼓): 中心點 [-1.4, 0.2, -0.8], 半徑=0.80, 高度=1.0, 傾斜=-20°
//    範圍: Y=[-0.270~0.670], Z=[-0.971~-0.629], X=[-2.2~-0.6]
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
        pos3d: [0.5, 0.4, -0.8], 
        radius: 0.65, 
        rotation: -Math.PI / 12,  // -15°
        glowColor: "#ffffff" 
    }, 
    { 
        name: "Tom_high", 
        x: 450, y: 0, w: 225, h: 225, 
        color: "#ff7f2a", 
        pos3d: [0.6, 0.8, 0.7], 
        radius: 0.55, 
        rotation: -Math.PI / 7,  // -26°
        glowColor: "#ff6600" 
    },   
    { 
        name: "Tom_mid", 
        x: 450, y: 0, w: 225, h: 225, 
        color: "#ff7f2a", 
        pos3d: [-0.6, 0.8, 0.7], 
        radius: 0.55, 
        rotation: -Math.PI / 7,  // -26°
        glowColor: "#ff6600" 
    },  
    { 
        name: "Symbal", 
        x: 675, y: 0, w: 225, h: 225, 
        color: "#e5b3ff", 
        pos3d: [1.6, 1.4, 0.7], 
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
        pos3d: [-1.4, 0.2, -0.8], 
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
