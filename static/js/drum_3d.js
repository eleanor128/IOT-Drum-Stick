// 複製音效系統（保持不變）
let audioCtx;
let audioBuffers = {};
let audioEnabled = false;

async function enableAudio() {
    const btn = document.getElementById('enableAudioBtn');
    const status = document.getElementById('statusText');
    
    if (audioEnabled) {
        status.textContent = "音效已經啟動！";
        return;
    }

    try {
        btn.textContent = "⏳ 載入中...";
        btn.disabled = true;
        
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        const files = {
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
        btn.textContent = "音效已啟動";
        btn.classList.add('enabled');
        status.textContent = `音效已就緒！已載入 ${Object.keys(audioBuffers).length} 個音效`;
        playSound("Snare");
        
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
    { name: "Hihat",     x: 675, y: 225, w: 225, h: 225, color:"#3232ff", pos3d: [2.5, 1, -0.8], radius: 1.0, rotation: -Math.PI / 9 },
    { name: "Snare",     x: 450, y: 225, w: 225, h: 225, color:"#d9d9d9", pos3d: [1, 0.2, -0.8], radius: 1, rotation: -Math.PI / 12 },
    { name: "Tom_high",  x: 450, y: 0,   w: 225, h: 225, color:"#ff7f2a", pos3d: [1, 1, 1.5], radius: 1, rotation: -Math.PI / 7 },
    { name: "Tom_mid",   x: 450, y: 0,   w: 225, h: 225, color:"#ff7f2a", pos3d: [-1, 1, 1.5], radius: 1, rotation: -Math.PI / 7 },
    { name: "Symbal",    x: 675, y: 0,   w: 225, h: 225, color:"#e5b3ff", pos3d: [2.5, 2.5, 2], radius: 1.5, rotation: -Math.PI / 6 },
    { name: "Ride",      x: 0,   y: 0,   w: 225, h: 225, color:"#6eeee7", pos3d: [-2.8, 2.5, 1], radius: 1.5, rotation: -Math.PI / 6 },
    { name: "Tom_floor", x: 675, y: 225, w: 225, h: 225, color:"#4d4d4d", pos3d: [-2, 0.3, -0.8], radius: 1.2, rotation: 0 },
];
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
    
    // 光照
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const light1 = new THREE.DirectionalLight(0xffffff, 0.8);
    light1.position.set(5, 10, 5);
    light1.castShadow = true;
    scene.add(light1);
    
    const light2 = new THREE.DirectionalLight(0xffffff, 0.3);
    light2.position.set(-5, 5, -5);
    scene.add(light2);
    
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
    
    // 添加xyz三軸坐標系
    // 軸長度為5，紅色=X軸，綠色=Y軸，藍色=Z軸
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);
    
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
        
        const geometry = new THREE.CylinderGeometry(radius, radius, height, 32);
        const material = new THREE.MeshStandardMaterial({ 
            color: zone.color,
            metalness: isCymbal ? 0.8 : 0.3,
            roughness: 0.4
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(...zone.pos3d);
        
        // 使用自定義的傾斜角度
        mesh.rotation.x = zone.rotation !== undefined ? zone.rotation : -Math.PI / 9;
        
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        scene.add(mesh);
        
        drumMeshes[zone.name + zone.pos3d.join()] = mesh;
        
        // // 標籤
        // createLabel(zone.name, zone.pos3d);
    });
    
    // 鼓棒（球體）
    const stickGeometry = new THREE.SphereGeometry(0.1, 16, 16);
    
    const rightMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0x660000 });
    rightStick = new THREE.Mesh(stickGeometry, rightMaterial);
    rightStick.castShadow = true;
    scene.add(rightStick);
    
    const leftMaterial = new THREE.MeshStandardMaterial({ color: 0x0000ff, emissive: 0x000066 });
    leftStick = new THREE.Mesh(stickGeometry, leftMaterial);
    leftStick.castShadow = true;
    scene.add(leftStick);
}

function createLabel(text, position) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 256;
    canvas.height = 64;
    
    context.fillStyle = 'white';
    context.font = 'bold 36px Arial';
    context.textAlign = 'center';
    context.fillText(text, 128, 45);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture });
    const sprite = new THREE.Sprite(material);
    sprite.position.set(position[0], position[1] + 1.2, position[2]);
    sprite.scale.set(1.5, 0.4, 1);
    scene.add(sprite);
}

// 保持原有的 mapAngleToXY 邏輯（用於敲擊偵測）
function mapAngleToXY(pitch, yaw) {
    let x = (yaw + 45) / 90 * 900;      // yaw 減少 → 鼓棒往左，yaw 增加 → 鼓棒往右
    let y = (pitch + 10) / 45 * 450;
    x = Math.max(0, Math.min(900, x));
    y = Math.max(0, Math.min(450, y));
    return {x, y, pitch, yaw};  // 同時返回原始角度
}

// 將 2D 坐標轉換為 3D 位置（用於顯示鼓棒）
function mapXYto3D(x, y, pitch) {
    let x3d = (x / 900 - 0.5) * 8;              // yaw 控制左右
    let y3d = 2 + (pitch / 45) * 1.5;           // pitch 控制上下：pitch增加→往上，pitch減少→往下
    const z3d = -1;                             // 前後固定在中間位置
    
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

// 繪製函數（3D版本）
function draw(rightPitch, rightYaw, leftPitch, leftYaw) {
    // 計算 2D 坐標（用於敲擊偵測）
    const rightPos2D = mapAngleToXY(rightPitch, rightYaw);
    const leftPos2D = mapAngleToXY(leftPitch, leftYaw);
    
    // 轉換為 3D 位置（pitch 控制上下）
    let rightPos3D = mapXYto3D(rightPos2D.x, rightPos2D.y, rightPitch);
    let leftPos3D = mapXYto3D(leftPos2D.x, leftPos2D.y, leftPitch);
    
    // 碰撞檢測：右手鼓棒
    const rightCollision = checkCollision(rightPos3D);
    if (rightCollision.hit) {
        rightPos3D = rightCollision.adjustedPos;
        // console.log('🔴 右手碰到:', rightCollision.drumName);
    }
    
    // 碰撞檢測：左手鼓棒
    const leftCollision = checkCollision(leftPos3D);
    if (leftCollision.hit) {
        leftPos3D = leftCollision.adjustedPos;
        // console.log('🔵 左手碰到:', leftCollision.drumName);
    }
    
    // 更新鼓棒位置
    rightStick.position.set(...rightPos3D);
    leftStick.position.set(...leftPos3D);
    
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
            } else if (data.is_hit) {
                const zone = detectZone(data["pitch (y軸轉)"], data["yaw (z軸轉)"]);
                console.log(`🥁 Right Hit: ${zone}`);
                playSound(zone);
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
            } else if (data.is_hit) {
                const zone = detectZone(data["pitch (y軸轉)"], data["yaw (z軸轉)"]);
                console.log(`🥁 Left Hit: ${zone}`);
                playSound(zone);
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
        leftData["yaw (z軸轉)"]
    );
    updateSensorDisplay(rightData, leftData);
    requestAnimationFrame(render);
}

// 初始化並啟動
init3D();
updateRight();
updateLeft();
render();
