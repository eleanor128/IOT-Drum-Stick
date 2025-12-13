// 複製音效系統（保持不變）
let audioCtx;
let audioBuffers = {};
let audioEnabled = false;

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
        const source = audioCtx.createBufferSource();
        source.buffer = audioBuffers[name];
        const gainNode = audioCtx.createGain();
        gainNode.gain.value = 0.8;
        source.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        source.start(0);
    } catch (err) {
        console.error(`Playback error:`, err);
    }
}

// --------------------- 3D 場景設置 ---------------------
const container = document.getElementById("drumContainer");
let scene, camera, renderer;
let drumMeshes = {};
let rightStick, leftStick;

const zones = [
    { name: "Hihat",     x: 675, y: 225, w: 225, h: 225, color:"#3232ff", pos3d: [2.5, 1, -0.8], radius: 1.0, rotation: -Math.PI / 9, glowColor: "#3399ff"},
    { name: "Snare",     x: 450, y: 225, w: 225, h: 225, color:"#d9d9d9", pos3d: [1, 0.2, -0.8], radius: 1, rotation: -Math.PI / 12, glowColor: "#ffffff" },
    { name: "Tom_high",  x: 450, y: 0,   w: 225, h: 225, color:"#ff7f2a", pos3d: [1, 1.2, 1.5], radius: 1, rotation: -Math.PI / 7, glowColor: "#ff6600" },
    { name: "Tom_mid",   x: 450, y: 0,   w: 225, h: 225, color:"#ff7f2a", pos3d: [-1, 1.2, 1.5], radius: 1, rotation: -Math.PI / 7, glowColor: "#ff6600" },
    { name: "Symbal",    x: 675, y: 0,   w: 225, h: 225, color:"#e5b3ff", pos3d: [2.5, 2.5, 2], radius: 1.5, rotation: -Math.PI / 6, glowColor: "#ff00ff" },
    { name: "Ride",      x: 0,   y: 0,   w: 225, h: 225, color:"#6eeee7", pos3d: [-2.8, 2.5, 1], radius: 1.5, rotation: -Math.PI / 6, glowColor: "#00ffff" },
    { name: "Tom_floor", x: 675, y: 225, w: 225, h: 225, color:"#4d4d4d", pos3d: [-2, 0.3, -0.8], radius: 1.2, rotation: -Math.PI / 9, glowColor: "#aaaaaa" },
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
            roughness: 0.3
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
        
        drumMeshes[zone.name + zone.pos3d.join()] = mesh;
        
    });
    
    // 創建真實鼓棒（圓柱體 + 球形頂端）
    // 鼓棒從使用者位置（相機）握著，水平於地面
    function createDrumstick(color, emissiveColor) {
        const drumstick = new THREE.Group();
        
        // 鼓棒主體（圓柱）- 沿著 Z 軸方向延伸，加長
        const stickBody = new THREE.CylinderGeometry(0.015, 0.02, 2, 8);
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
        stickMesh.position.z = 1;  // 中心在 z=1，範圍從 0 到 2
        drumstick.add(stickMesh);
        
        // 鼓棒頂端（球形敲擊端）- 在前方
        const tipGeometry = new THREE.SphereGeometry(0.03, 12, 12);
        const tipMesh = new THREE.Mesh(tipGeometry, stickMaterial);
        tipMesh.position.z = 2;  // 放在棒子前端（緊貼鼓棒主體）
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

// 碰撞檢測：檢查鼓棒是否碰到鼓或鈸
function checkCollision(stickPos) {
    let collisionInfo = { hit: false, drumName: null, adjustedPos: [...stickPos] };
    
    zones.forEach(zone => {
        const drumPos = zone.pos3d;
        const isCymbal = zone.name.includes("Symbal") || zone.name.includes("Ride") || zone.name.includes("Hihat");
        const radius = zone.radius || (isCymbal ? 1.2 : 0.9);
        
        // 計算鼓棒與鼓中心的水平距離
        const dx = stickPos[0] - drumPos[0];
        const dz = stickPos[2] - drumPos[2];
        const horizontalDist = Math.sqrt(dx * dx + dz * dz);
        
        // 如果鼓棒在鼓的半徑範圍內
        if (horizontalDist <= radius) {
            const drumTopY = drumPos[1];  // 鼓面的高度
            
            // 如果鼓棒低於或接近鼓面（考慮鼓棒半徑 0.15）
            if (stickPos[1] <= drumTopY + 0.15) {
                collisionInfo.hit = true;
                collisionInfo.drumName = zone.name;
                // 將鼓棒位置調整到鼓面上方
                collisionInfo.adjustedPos[1] = drumTopY + 0.15;
            }
        }
    });
    
    return collisionInfo;
}

// 繪製函數（3D版本）- 以握把端為圓心旋轉鼓棒
function draw(rightPitch, rightYaw, leftPitch, leftYaw, rightAdjustedPitch, leftAdjustedPitch) {
    // 右手鼓棒的握把位置（手的位置）
    // 根據 yaw 控制左右位置，擴大移動範圍
    const rightHandX = (rightYaw - 45) / 90 * 3 + 1;  // 右手初始位置靠近 Snare
    const rightHandY = 1.5;  // 提高握把高度
    const rightHandZ = -0.8;   // 與 Snare 的 Z 座標對齊
    
    // 左手鼓棒的握把位置
    const leftHandX = (leftYaw - 45) / 90 * 3 - 1;  // 左手在左側
    const leftHandY = 1.5;  // 提高握把高度
    const leftHandZ = -0.8;   // 與 Snare 的 Z 座標對齊
    
    // 更新右手鼓棒位置和旋轉
    rightStick.position.set(rightHandX, rightHandY, rightHandZ);
    // 如果有碰撞，使用調整後的 pitch（讓鼓棒停在鼓面上）
    const finalRightPitch = rightAdjustedPitch !== undefined ? rightAdjustedPitch : rightPitch;
    rightStick.rotation.x = (finalRightPitch / 45) * (Math.PI / 3);  // 轉換為弧度，範圍 0-60°
    // yaw 控制左右擺動（繞 Y 軸旋轉）
    rightStick.rotation.y = (rightYaw / 45) * (Math.PI / 6);  // 小範圍旋轉
    
    // 更新左手鼓棒位置和旋轉
    leftStick.position.set(leftHandX, leftHandY, leftHandZ);
    // 如果有碰撞，使用調整後的 pitch（讓鼓棒停在鼓面上）
    const finalLeftPitch = leftAdjustedPitch !== undefined ? leftAdjustedPitch : leftPitch;
    leftStick.rotation.x = (finalLeftPitch / 45) * (Math.PI / 3);
    leftStick.rotation.y = (leftYaw / 45) * (Math.PI / 6);
    
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
            if (rightHitCooldown > 0) {
                rightHitCooldown--;
            } else if (data.is_hit && data.hit_drum) {
                console.log(`🥁 Right Hit: ${data.hit_drum}`);
                playSound(data.hit_drum);
                rightHitCooldown = 8;
            }
        })
        .catch(err => console.log("Right fetch error:", err))
        .finally(() => setTimeout(updateRight, 0));
}

function updateLeft() {
    fetch("/left_data")
        .then(res => res.json())
        .then(data => {
            leftData = data;
            if (leftHitCooldown > 0) {
                leftHitCooldown--;
            } else if (data.is_hit && data.hit_drum) {
                console.log(`🥁 Left Hit: ${data.hit_drum}`);
                playSound(data.hit_drum);
                leftHitCooldown = 8;
            }
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
