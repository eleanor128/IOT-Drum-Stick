// 複製音效系統（保持不變）
let audioCtx;
let audioBuffers = {};
let audioEnabled = false;
let activeSources = [];  // 記錄所有正在播放的音效源（支援同時播放相同音效）

// 鼓音效播放時長設定（秒）
const DRUM_SOUND_DURATION = 0.3;

async function enableAudio() {
    // const btn = document.getElementById('enableAudioBtn');
    const status = document.getElementById('statusText');
    
    if (audioEnabled) {
        status.textContent = "音效已經啟動！";
        return;
    }

    try {
        
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        const files = {
            "Success": "/static/sounds/success.wav",
            "Symbal": "/static/sounds/symbal.wav",
            "Tom_high": "/static/sounds/tom_high.wav",
            "Tom_mid": "/static/sounds/tom_mid.wav",
            "Ride": "/static/sounds/ride.wav",
            "Hihat": "/static/sounds/hihat.wav",
            "Snare": "/static/sounds/snare.wav",
            "Tom_floor": "/static/sounds/tom_floor.wav",
        };

        for (const key in files) {
            try {
                const response = await fetch(files[key]);
                if (!response.ok) continue;
                const arrayBuffer = await response.arrayBuffer();
                audioBuffers[key] = await audioCtx.decodeAudioData(arrayBuffer);
            } catch (err) {
                console.error(`Error loading ${key}:`, err);
            }
        }

        audioEnabled = true;
        setTimeout(() => {
            playSound("Success");
        }, 800);  // 延遲 800 毫秒（0.8 秒）
        
    } catch (error) {
        console.error("Audio initialization failed:", error);
    }
}

function playSound(name) {
    if (!audioEnabled || !audioCtx || !audioBuffers[name]) return;
    
    try {
        // Success 音效不受限制，完整播放
        if (name === "Success") {
            const source = audioCtx.createBufferSource();
            source.buffer = audioBuffers[name];
            const gainNode = audioCtx.createGain();
            gainNode.gain.value = 0.8;
            source.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            source.start(0);
            return;
        }
        
        // 允許同時播放相同音效（不停止前一個）
        const source = audioCtx.createBufferSource();
        source.buffer = audioBuffers[name];
        const gainNode = audioCtx.createGain();
        gainNode.gain.value = 0.8;
        source.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        // 記錄這個音效源
        activeSources.push(source);
        
        // 播放音效，並在指定時長後停止
        source.start(0);
        source.stop(audioCtx.currentTime + DRUM_SOUND_DURATION);
        
        // 清除記錄
        source.onended = () => {
            const index = activeSources.indexOf(source);
            if (index > -1) {
                activeSources.splice(index, 1);
            }
        };
    } catch (err) {
        console.error(`Playback error:`, err);
    }
}

// --------------------- 加速度數據判斷功能 ---------------------
// 根據加速度數據判斷鼓棒位置和打擊目標
function detectDrumFromAccel(ax, ay, az) {
    // 計算高度（Z軸加速度反映鼓棒垂直位置）
    // az 越大表示鼓棒越向下（打低的鼓）
    const height = 20 - az;  // 轉換：az大→height小
    
    // 計算左右位置（X軸加速度）
    const horizontal = ax;  // 正值=右側，負值=左側
    
    // 計算前後位置（Y軸加速度）
    const depth = ay;
    
    // 判斷邏輯（根據數據分析）
    
    // 1. Symbal & Ride（最高位置，height > 10）
    if (height > 10) {
        if (horizontal > 4) return "Symbal";  // 右側
        if (horizontal < 0) return "Ride";    // 左側
    }
    
    // 2. Tom_high & Tom_mid（中高位置，height 8-10）
    if (height >= 8 && height <= 10) {
        if (horizontal > 2) return "Tom_high";   // 偏右
        if (horizontal < 2) return "Tom_mid";    // 偏左
    }
    
    // 3. Hihat（中等位置，height 6-8，右前方）
    if (height >= 6 && height <= 8 && horizontal > 4) {
        return "Hihat";
    }
    
    // 4. Snare（中等位置，height 5-7，中央）
    if (height >= 5 && height <= 7 && Math.abs(horizontal) < 3) {
        return "Snare";
    }
    
    // 5. Tom_floor（最低位置，height < 5）
    if (height < 5) {
        return "Tom_floor";
    }
    
    // 預設回 Snare
    return "Snare";
}

// 判斷是否為有效打擊（向下揮動）
function isValidHit(ax, ay, az, gx, gy, gz) {
    // 1. 向下加速度檢測（Z軸加速度 - 必須條件）
    const zAccelThreshold = 10;  // 向下打擊，提高閾值確保是向下
    if (az < zAccelThreshold) {
        return false;  // 如果不是向下，直接返回 false
    }
    
    // 2. 陀螺儀Y軸檢測（手腕向下揮動的旋轉）
    const gyroYThreshold = 50;  // Y軸旋轉速度（向下揮動特徵）
    const hasDownwardSwing = Math.abs(gy) > gyroYThreshold;
    
    // 3. 加速度幅度檢測（打擊力道）
    const magnitude = Math.sqrt(ax * ax + ay * ay + az * az);
    const magnitudeThreshold = 12;  // 最小打擊力道
    
    // 4. 陀螺儀總幅度檢測（快速揮動）
    const gyroMagnitude = Math.sqrt(gx * gx + gy * gy + gz * gz);
    const gyroThreshold = 80;  // 最小旋轉速度
    
    // 必須同時滿足：向下加速 + (向下揮動 或 強力打擊)
    return (hasDownwardSwing || magnitude > magnitudeThreshold || gyroMagnitude > gyroThreshold);
}

// 計算手部位置（握把位置）- 固定作為揮擊圓心
function mapAccelTo3D(ax, ay, az, isLeft = false) {
    // 手部位置相對固定（握把位置）
    // X軸（左右）：左右手基礎位置
    const baseX = isLeft ? 0.8 : 0.2;
    
    // Y軸（高度）：手部高度，微調
    const baseY = 0.8; // 手部基礎高度
    const y3d = baseY + (10 - az) * 0.02; // az 越小（手舉高）越高
    
    // Z軸（前後）：手部位置（握把）基礎位置 + X軸加速度影響
    // X軸加速度大時（左右快速移動），手會稍微往深處移動以打到後方的鼓
    const baseZ = -2.0; // 手部握把基礎位置
    const zOffset = Math.abs(ax) * 0.08; // X軸加速度越大，往深處偏移越多（幅度較小）
    const z3d = baseZ + zOffset;
    
    // 限制範圍
    return [
        Math.max(-2.0, Math.min(2.0, baseX)),
        Math.max(0.5, Math.min(1.5, y3d)),
        Math.max(-2.0, Math.min(-1.0, z3d)) // Z軸限制在 -2.0 到 -1.0 之間
    ];
}

// --------------------- 3D 場景設置 ---------------------
const container = document.getElementById("drumContainer");
let scene, camera, renderer;
let drumMeshes = {};
let rightStick, leftStick;

// pos3d: [x, y中心點, z], 鼓面高度 = y中心點 + (鼓高度/2)
// 鼓面高度：Hihat=1.025m, Snare=0.65m, Tom_high=1.25m, Tom_mid=1.25m, Symbal=1.825m, Ride=1.725m, Tom_floor=0.9m
const zones = [
    { name: "Hihat",     x: 675, y: 225, w: 225, h: 225, color:"#3232ff", pos3d: [1.6, 1.0, -0.8], radius: 0.65, rotation: -Math.PI / 9, glowColor: "#3399ff"},   // 鼓面高度: 1.025m
    { name: "Snare",     x: 450, y: 225, w: 225, h: 225, color:"#d9d9d9", pos3d: [0.5, 0.4, -0.8], radius: 0.65, rotation: -Math.PI / 12, glowColor: "#ffffff" }, // 鼓面高度: 0.65m
    { name: "Tom_high",  x: 450, y: 0,   w: 225, h: 225, color:"#ff7f2a", pos3d: [0.6, 1.0, 0.8], radius: 0.55, rotation: -Math.PI / 7, glowColor: "#ff6600" },   // 鼓面高度: 1.25m
    { name: "Tom_mid",   x: 450, y: 0,   w: 225, h: 225, color:"#ff7f2a", pos3d: [-0.6, 1.0, 0.8], radius: 0.55, rotation: -Math.PI / 7, glowColor: "#ff6600" },  // 鼓面高度: 1.25m
    { name: "Symbal",    x: 675, y: 0,   w: 225, h: 225, color:"#e5b3ff", pos3d: [1.6, 1.8, 1.2], radius: 0.80, rotation: -Math.PI / 6, glowColor: "#ff00ff" },   // 鼓面高度: 1.825m
    { name: "Ride",      x: 0,   y: 0,   w: 225, h: 225, color:"#6eeee7", pos3d: [-1.6, 1.7, 1.0], radius: 0.90, rotation: -Math.PI / 6, glowColor: "#00ffff" },  // 鼓面高度: 1.725m
    { name: "Tom_floor", x: 675, y: 225, w: 225, h: 225, color:"#4d4d4d", pos3d: [-1, 0.2, -0.8], radius: 0.80, rotation: -Math.PI / 9, glowColor: "#aaaaaa" }, // 鼓面高度: 0.9m
];
// 修改 glowColor 來自定義每個鼓的發光顏色 (格式: 0xRRGGBB)
// Math.PI / 18	10°	微微傾斜
// Math.PI / 9	20°	中度傾斜
// Math.PI / 6	30°	明顯傾斜


// 初始化 3D 場景
function init3D() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222);
    
    camera = new THREE.PerspectiveCamera(60, 900 / 600, 0.1, 1000);
    camera.position.set(0, 3, -4);
    camera.lookAt(0, 0, 2);
    
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(900, 600);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);
    
    // 光照 - 從頂端照下來
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);
    
    const topLight = new THREE.DirectionalLight(0xffffff, 0.6);
    topLight.position.set(0, 10, 0);  // 從正上方照下來
    topLight.castShadow = true;
    scene.add(topLight);
    
    // 地板
    const floorGeometry = new THREE.PlaneGeometry(15, 15);
        const floorMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x2d2d2d,  // 從 0x444444 改為 0x2d2d2d
        roughness: 0.8 
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.5;
    floor.receiveShadow = true;
    scene.add(floor);
    
    // 創建鼓組
    const createdDrums = new Set();
    zones.forEach(zone => {
        if (createdDrums.has(zone.name + zone.pos3d.join())) return;
        createdDrums.add(zone.name + zone.pos3d.join());
        
        const isCymbal = zone.name.includes("Symbal") || zone.name.includes("Ride") || zone.name.includes("Hihat");
        const radius = zone.radius || (isCymbal ? 1.2 : 0.9);  // 使用自定義半徑或預設值
        
        let height;
        if (isCymbal) {
            height = 0.05;  // 鈸很薄
        } else if (zone.name === "Tom_floor") {
            height = 1;   // 落地通鼓較長
        } else {
            height = 0.5;   // 其他鼓的標準高度
        }
        
        // 鼓/鈸主體 - 統一使用深色
        const geometry = new THREE.CylinderGeometry(radius, radius, height, 32);
        const material = new THREE.MeshStandardMaterial({ 
            color: 0x1a1a1a,        // 深灰色
            metalness: isCymbal ? 0.7 : 0.2,
            roughness: 0.3,
            emissive: 0x000000,     // 初始不發光
            emissiveIntensity: 0
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(...zone.pos3d);
        
        // 使用自定義的傾斜角度
        mesh.rotation.x = zone.rotation !== undefined ? zone.rotation : -Math.PI / 9;
        
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        scene.add(mesh);
        
        // 霓虹發光邊緣環
        const edgeGeometry = new THREE.TorusGeometry(radius, 0.03, 8, 32);
        const edgeMaterial = new THREE.MeshStandardMaterial({
            color: zone.color,      // 使用原本的顏色作為發光色
            emissive: zone.color,   // 自發光
            emissiveIntensity: 1.5, // 發光強度
            metalness: 0.8,
            roughness: 0.2
        });
        const edgeMesh = new THREE.Mesh(edgeGeometry, edgeMaterial);
        edgeMesh.position.copy(mesh.position);
        edgeMesh.rotation.copy(mesh.rotation);
        // 圓環默認在 XY 平面，需旋轉到水平
        edgeMesh.rotation.x += Math.PI / 2;
        scene.add(edgeMesh);
        
        drumMeshes[zone.name] = mesh; // 改用名稱作為 Key，方便查找
        
    });
    
    // 創建真實鼓棒（圓柱體 + 球形頂端）
    // 鼓棒從使用者位置（相機）握著，水平於地面
    function createDrumstick(color, emissiveColor) {
        const drumstick = new THREE.Group();
        
        // 鼓棒主體（圓柱）- 沿著 Z 軸方向延伸，加長
        const stickBody = new THREE.CylinderGeometry(0.015, 0.02, 1.2, 8);
        const stickMaterial = new THREE.MeshStandardMaterial({ 
            color: color,
            emissive: emissiveColor,
            roughness: 0.7,
            metalness: 0.1
        });
        const stickMesh = new THREE.Mesh(stickBody, stickMaterial);
        stickMesh.castShadow = true;
        
        // 旋轉鼓棒，讓它水平（沿著 Z 軸）
        stickMesh.rotation.x = Math.PI / 2;
        stickMesh.position.z = 0.6;  // 中心在 z=0.6，範圍從 0 到 1.2
        drumstick.add(stickMesh);
        
        // 鼓棒頂端（球形敲擊端）- 在前方
        const tipGeometry = new THREE.SphereGeometry(0.03, 12, 12);
        const tipMesh = new THREE.Mesh(tipGeometry, stickMaterial);
        tipMesh.position.z = 1.2;  // 放在棒子前端（緊貼鼓棒主體）
        tipMesh.castShadow = true;
        drumstick.add(tipMesh);
        
        // 鼓棒底端（握把）- 在後方（靠近相機）
        const gripGeometry = new THREE.SphereGeometry(0.022, 12, 12);
        const gripMesh = new THREE.Mesh(gripGeometry, stickMaterial);
        gripMesh.position.z = 0;  // 放在棒子後端（握把處）
        gripMesh.castShadow = true;
        drumstick.add(gripMesh);
        
        return drumstick;
    }
    
    // 創建右手鼓棒（紅色）
    rightStick = createDrumstick(0xff0000, 0x660000);
    scene.add(rightStick);
    
    // 創建左手鼓棒（藍色）
    leftStick = createDrumstick(0x0000ff, 0x000066);
    scene.add(leftStick);
}

// 感測器角度轉 2D 座標（用於敲擊偵測）
// yaw: 左移增大、右移減小
// pitch: 鼓棒舉起增大、向下減小
// roll: 不影響位置（僅鼓棒自轉）
function mapAngleToXY(pitch, yaw) {
    let x = (45 - yaw) / 90 * 900;      // yaw 增加（左移）→ x減小（往左）
    let y = (pitch + 10) / 45 * 450;    // pitch 用於 2D 偵測
    x = Math.max(0, Math.min(900, x));
    y = Math.max(0, Math.min(450, y));
    return {x, y, pitch, yaw};
}

// 將 2D 座標 + pitch 轉換為 3D 位置
// X軸（左右）: yaw 控制，左移 yaw增加
// Y軸（上下）: pitch 控制，舉起 pitch增加
// Z軸（前後）: 固定位置
function mapXYto3D(x, y, pitch) {
    // X軸：yaw 左移（增加）→ 畫面左移，反轉 x 方向
    let x3d = (0.5 - x / 900) * 8;
    
    // Y軸：pitch 舉起（增加）→ 往上，向下（減小）→ 往下
    // 調整基準高度，讓 pitch=0 時鼓棒在較高的位置
    let y3d = 1.5 + (pitch / 45) * 2.0;         // pitch=0→y=1.5, pitch=45→y=3.5
    
    // Z軸：固定在鼓組中間，不要太靠近相機
    const z3d = 0.5;
    
    // 限制鼓棒不超出相機視角
    x3d = Math.max(-3.5, Math.min(3.5, x3d));   // X軸範圍: -3.5 到 3.5
    y3d = Math.max(0.5, Math.min(3.5, y3d));    // Y軸範圍: 0.5 到 3.5
    
    return [x3d, y3d, z3d];
}

// 碰撞檢測與修正：計算鼓棒是否穿入鼓面，並返回修正後的 Pitch 角度 (弧度)
function solveStickCollision(gripPos, rotX, rotY) {
    const stickLength = 1.2;
    let correctedRotX = rotX;
    let hitDrum = null;
    
    zones.forEach(zone => {
        const drumPos = zone.pos3d;
        const isCymbal = zone.name.includes("Symbal") || zone.name.includes("Ride") || zone.name.includes("Hihat");
        const radius = zone.radius || (isCymbal ? 1.2 : 0.9);
        
        // 增加碰撞檢測半徑，確保打到邊緣也能觸發，並防止邊緣穿模
        const hitRadius = radius + 0.15;
        
        let drumHeight;
        if (isCymbal) {
            drumHeight = 0.05;  // 鈸很薄
        } else if (zone.name === "Tom_floor") {
            drumHeight = 1.0;   // 落地鼓較長
        } else {
            drumHeight = 0.5;   // 其他鼓的標準高度
        }
        
        const drumTopY = drumPos[1] + drumHeight / 2;
        
        // 計算鼓棒尖端位置 (Tip)
        // 鼓棒握把在 gripPos，長度 1.2
        // 旋轉：X軸為 Pitch (正值向下), Y軸為 Yaw
        const tipX = gripPos[0] + stickLength * Math.cos(rotX) * Math.sin(rotY);
        const tipZ = gripPos[2] + stickLength * Math.cos(rotX) * Math.cos(rotY);
        
        // 檢查水平距離 (XZ平面)
        const dx = tipX - drumPos[0];
        const dz = tipZ - drumPos[2];
        
        if (dx * dx + dz * dz < hitRadius * hitRadius) {
            // 檢查垂直穿透
            // 尖端 Y = gripY - L * sin(rotX)
            const currentTipY = gripPos[1] - stickLength * Math.sin(rotX);
            
            // 如果尖端低於鼓面 (增加緩衝到 0.05，確保視覺上不穿模)
            const buffer = 0.05;
            if (currentTipY < drumTopY + buffer) {
                // 計算限制角度：sin(rotX) <= (gripY - drumTopY) / L
                let maxSin = (gripPos[1] - (drumTopY + buffer)) / stickLength;
                
                // 限制 maxSin 在 [-1, 1] 範圍內，防止 NaN (當握把過低或過高時)
                maxSin = Math.max(-1, Math.min(1, maxSin));
                
                const maxRotX = Math.asin(maxSin);
                // 因為 rotX 越大越向下，所以取最小值
                if (maxRotX < correctedRotX) {
                    correctedRotX = maxRotX;
                    hitDrum = zone.name;
                }
            }
        }
    });
    
    return { correctedRotX, hitDrum };
}

// 線性插值函數，用於平滑移動
function lerp(start, end, factor) {
    return start + (end - start) * factor;
}

// 觸發鼓面發光動畫
function triggerDrumGlow(drumName) {
    const mesh = drumMeshes[drumName];
    if (mesh && mesh.material) {
        const zone = zones.find(z => z.name === drumName);
        if (zone) {
            mesh.material.emissive.set(zone.glowColor);
            mesh.material.emissiveIntensity = 1.0; // 設定發光強度
        }
    }
}

// 更新發光衰減（每一幀呼叫）
function updateDrumGlows() {
    for (const key in drumMeshes) {
        const mesh = drumMeshes[key];
        if (mesh.material.emissiveIntensity > 0) {
            mesh.material.emissiveIntensity = Math.max(0, mesh.material.emissiveIntensity - 0.05); // 衰減速度
            if (mesh.material.emissiveIntensity === 0) {
                mesh.material.emissive.set(0x000000); // 歸零後重置顏色
            }
        }
    }
}

// 碰撞狀態追蹤（防止按住不放時連續觸發）
let rightWasColliding = false;
let leftWasColliding = false;

// 繪製函數（3D版本）- Yaw控制左右，Pitch控制揮擊
function draw(rightPitch, rightYaw, leftPitch, leftYaw, rightAdjustedPitch, leftAdjustedPitch) {
    const smoothFactor = 0.15; // 平滑係數，越小越平滑但延遲越高

    // 右手握把位置（手部位置，作為圓心）
    const [baseRightX, baseRightY, baseRightZ] = mapAccelTo3D(
        rightData.ax, rightData.ay, rightData.az, false
    );
    
    // 計算旋轉角度 (弧度)
    const rightRotX = (rightPitch / 45) * (Math.PI / 3);  // Pitch: 上下揮擊
    const rightRotY = (rightYaw / 45) * (Math.PI / 4);     // Yaw: 左右擺動（降低靈敏度）
    
    // 根據 Yaw 計算左右偏移（以手部為圓心的左右擺動）
    const rightYawOffsetX = Math.sin(rightRotY) * 0.35; // 左右擺動範圍（降低幅度）
    
    // 應用 Yaw 偏移到手部位置
    const targetRightX = baseRightX + rightYawOffsetX;
    const targetRightY = baseRightY;
    const targetRightZ = baseRightZ;
    
    // 應用平滑處理
    const rightX = lerp(rightStick.position.x, targetRightX, smoothFactor);
    const rightY = lerp(rightStick.position.y, targetRightY, smoothFactor);
    const rightZ = lerp(rightStick.position.z, targetRightZ, smoothFactor);
    
    // 左手握把位置
    const [baseLeftX, baseLeftY, baseLeftZ] = mapAccelTo3D(
        leftData.ax, leftData.ay, leftData.az, true
    );
    
    const leftRotX = (leftPitch / 45) * (Math.PI / 3);
    const leftRotY = (leftYaw / 45) * (Math.PI / 4);
    
    const leftYawOffsetX = Math.sin(leftRotY) * 0.35;
    
    const targetLeftX = baseLeftX + leftYawOffsetX;
    const targetLeftY = baseLeftY;
    const targetLeftZ = baseLeftZ;
    
    // 應用平滑處理
    const leftX = lerp(leftStick.position.x, targetLeftX, smoothFactor);
    const leftY = lerp(leftStick.position.y, targetLeftY, smoothFactor);
    const leftZ = lerp(leftStick.position.z, targetLeftZ, smoothFactor);
    
    // 應用碰撞修正 (防止穿模)
    const rightResult = solveStickCollision([rightX, rightY, rightZ], rightRotX, rightRotY);
    
    // 檢測右手打擊
    if (rightResult.hitDrum) {
        if (!rightWasColliding && rightHitCooldown <= 0) {
            playSound(rightResult.hitDrum);
            triggerDrumGlow(rightResult.hitDrum); // 觸發發光
            rightHitCooldown = 10; // 冷卻時間 (幀數)
            console.log(`🥁 Right Hit (3D): ${rightResult.hitDrum}`);
        }
        rightWasColliding = true;
    } else {
        rightWasColliding = false;
    }
    if (rightHitCooldown > 0) rightHitCooldown--;
    
    // 更新右手鼓棒位置和旋轉
    rightStick.position.set(rightX, rightY, rightZ);
    rightStick.rotation.x = rightResult.correctedRotX;
    rightStick.rotation.y = rightRotY; // Yaw 控制左右
    
    // 左手同理
    const leftResult = solveStickCollision([leftX, leftY, leftZ], leftRotX, leftRotY);
    
    // 檢測左手打擊
    if (leftResult.hitDrum) {
        if (!leftWasColliding && leftHitCooldown <= 0) {
            playSound(leftResult.hitDrum);
            triggerDrumGlow(leftResult.hitDrum); // 觸發發光
            leftHitCooldown = 10;
            console.log(`🥁 Left Hit (3D): ${leftResult.hitDrum}`);
        }
        leftWasColliding = true;
    } else {
        leftWasColliding = false;
    }
    if (leftHitCooldown > 0) leftHitCooldown--;
    
    // 更新左手鼓棒位置和旋轉
    leftStick.position.set(leftX, leftY, leftZ);
    leftStick.rotation.x = leftResult.correctedRotX;
    leftStick.rotation.y = leftRotY;
    
    // 渲染場景
    renderer.render(scene, camera);
}

// 保持原有的 detectZone 邏輯
let rightHitCooldown = 0;
let leftHitCooldown = 0;

function detectZone(pitch, yaw) {
    const pos = mapAngleToXY(pitch, yaw);
    for (const zone of zones) {
        if (pos.x >= zone.x && pos.x < zone.x + zone.w &&
            pos.y >= zone.y && pos.y < zone.y + zone.h) {
            return zone.name;
        }
    }
    return "Snare";
}

// 更新感測器數據顯示（左右手分開顯示）
function updateSensorDisplay(rightData, leftData) {
    // 除錯：檢查數據
    // console.log('Right:', rightData["pitch (y軸轉)"], 'Left:', leftData["pitch (y軸轉)"]);
    
    // 右手數據
    document.getElementById('pitch-value').textContent = rightData["pitch (y軸轉)"].toFixed(1) + '°';
    document.getElementById('roll-value').textContent = rightData["roll (x軸轉)"].toFixed(1) + '°';
    document.getElementById('yaw-value').textContent = rightData["yaw (z軸轉)"].toFixed(1) + '°';
    document.getElementById('accel-x-value').textContent = rightData.ax.toFixed(2) + ' g';
    document.getElementById('accel-y-value').textContent = rightData.ay.toFixed(2) + ' g';
    document.getElementById('accel-z-value').textContent = rightData.az.toFixed(2) + ' g';
    
    const rightMagnitude = Math.sqrt(rightData.ax ** 2 + rightData.ay ** 2 + rightData.az ** 2);
    document.getElementById('magnitude-value').textContent = rightMagnitude.toFixed(2) + ' g';
    
    document.getElementById('gyro-x-value').textContent = rightData.gx.toFixed(1) + '°/s';
    document.getElementById('gyro-y-value').textContent = rightData.gy.toFixed(1) + '°/s';
    document.getElementById('gyro-z-value').textContent = rightData.gz.toFixed(1) + '°/s';
    
    // 左手數據
    document.getElementById('left-pitch-value').textContent = leftData["pitch (y軸轉)"].toFixed(1) + '°';
    document.getElementById('left-roll-value').textContent = leftData["roll (x軸轉)"].toFixed(1) + '°';
    document.getElementById('left-yaw-value').textContent = leftData["yaw (z軸轉)"].toFixed(1) + '°';
    document.getElementById('left-accel-x-value').textContent = leftData.ax.toFixed(2) + ' g';
    document.getElementById('left-accel-y-value').textContent = leftData.ay.toFixed(2) + ' g';
    document.getElementById('left-accel-z-value').textContent = leftData.az.toFixed(2) + ' g';
    
    const leftMagnitude = Math.sqrt(leftData.ax ** 2 + leftData.ay ** 2 + leftData.az ** 2);
    document.getElementById('left-magnitude-value').textContent = leftMagnitude.toFixed(2) + ' g';
    
    document.getElementById('left-gyro-x-value').textContent = leftData.gx.toFixed(1) + '°/s';
    document.getElementById('left-gyro-y-value').textContent = leftData.gy.toFixed(1) + '°/s';
    document.getElementById('left-gyro-z-value').textContent = leftData.gz.toFixed(1) + '°/s';
}

// 保持原有的數據更新邏輯
let rightData = { "pitch (y軸轉)": 0, "yaw (z軸轉)": 0, "roll (x軸轉)": 0, ax: 0, ay: 0, az: 0, gx: 0, gy: 0, gz: 0, is_hit: false };
let leftData = { "pitch (y軸轉)": 0, "yaw (z軸轉)": 0, "roll (x軸轉)": 0, ax: 0, ay: 0, az: 0, gx: 0, gy: 0, gz: 0, is_hit: false };

function updateRight() {
    fetch("/right_data")
        .then(res => res.json())
        .then(data => {
            rightData = data;
        })
        .catch(err => console.log("Right fetch error:", err))
        .finally(() => setTimeout(updateRight, 0));
}

function updateLeft() {
    fetch("/left_data")
        .then(res => res.json())
        .then(data => {
            leftData = data;
        })
        .catch(err => console.log("Left fetch error:", err))
        .finally(() => setTimeout(updateLeft, 0));
}

function render() {
    draw(
        rightData["pitch (y軸轉)"], 
        rightData["yaw (z軸轉)"],
        leftData["pitch (y軸轉)"], 
        leftData["yaw (z軸轉)"],
        rightData.adjusted_pitch,
        leftData.adjusted_pitch
    );
    updateSensorDisplay(rightData, leftData);
    updateDrumGlows(); // 更新發光動畫狀態
    requestAnimationFrame(render);
}

// 初始化並啟動
init3D();
updateRight();
updateLeft();
render();

// 點擊畫面任意處啟動音效
let audioAutoEnabled = false;
document.addEventListener('click', () => {
    if (!audioAutoEnabled && !audioEnabled) {
        audioAutoEnabled = true;
        enableAudio();
    }
}, { once: false });
