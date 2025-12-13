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
// --------------------- 3D 場景設置 ---------------------
const container = document.getElementById("drumContainer");
let scene, camera, renderer;
let drumMeshes = {};
let rightStick, leftStick;

// 調整 zones 陣列，新增更逼真的顏色和材質設定
const zones = [
    // 鼓組部分
    { name: "Snare",     pos3d: [0.8, 0.2, -0.5], radius: 0.8, height: 0.4, color: 0xDCDCDC, metalness: 0.1, roughness: 0.5 }, // 小鼓 (Snare Drum - 偏白)
    { name: "Tom_high",  pos3d: [1, 0.3, 1.5],    radius: 0.7, height: 0.4, color: 0xBA4A00, metalness: 0.4, roughness: 0.4 }, // 高音Tom (偏暖棕色/紅木)
    { name: "Tom_mid",   pos3d: [-1, 0.3, 1.5],   radius: 0.8, height: 0.45, color: 0xA04000, metalness: 0.4, roughness: 0.4 }, // 中音Tom
    { name: "Tom_floor", pos3d: [-2, 0.3, -0.5],  radius: 1.1, height: 0.5, color: 0x8B4513, metalness: 0.5, roughness: 0.4 }, // 落地鼓 (深棕色)
    
    // 鈸組部分 (通常材質為金屬)
    { name: "Hihat",     pos3d: [3, 0.8, -0.5],   radius: 0.6, height: 0.05, color: 0xC0C0C0, metalness: 0.9, roughness: 0.2 }, // Hi-Hat (銀色/高反射)
    { name: "Symbal",    pos3d: [2.5, 1.5, 2],    radius: 1.1, height: 0.05, color: 0xD4AF37, metalness: 0.9, roughness: 0.3 }, // Crash 鈸 (金色/高反射)
    { name: "Ride",      pos3d: [-2.5, 1.5, 2],   radius: 1.3, height: 0.05, color: 0xD4AF37, metalness: 0.9, roughness: 0.3 }, // Ride 鈸 (金色/高反射)
];


// 初始化 3D 場景
function init3D() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a); // 背景調暗，突出鼓組

    // 攝影機和渲染器保持不變
    camera = new THREE.PerspectiveCamera(60, 900 / 600, 0.1, 1000);
    camera.position.set(0, 4, -4);
    camera.lookAt(0, 0, 0);
    
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(900, 600);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap; // 軟陰影
    container.appendChild(renderer.domElement);
    
    // --- 調整光照以更逼真 ---
    // 1. 環境光 (AmbientLight): 提供整體亮度
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);
    
    // 2. 半球光 (HemisphereLight): 模擬天空光，提供柔和的漸變光
    const hemiLight = new THREE.HemisphereLight(0xb1e1ff, 0xb97a20, 0.4); 
    scene.add(hemiLight);
    
    // 3. 主定向光 (DirectionalLight): 創造強烈陰影和高光
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight.position.set(5, 10, 5);
    directionalLight.castShadow = true;
    
    // 設置陰影參數以獲得更清晰的陰影
    directionalLight.shadow.mapSize.width = 1024;
    directionalLight.shadow.mapSize.height = 1024;
    directionalLight.shadow.camera.top = 5;
    directionalLight.shadow.camera.bottom = -5;
    directionalLight.shadow.camera.left = -5;
    directionalLight.shadow.camera.right = 5;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 20;
    
    scene.add(directionalLight);
    
    // 4. 背光/邊緣光 (DirectionalLight): 增加物體邊緣的立體感
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.2);
    rimLight.position.set(-5, 5, -5);
    scene.add(rimLight);


    // 地板 (保持不變)
    const floorGeometry = new THREE.PlaneGeometry(15, 15);
    const floorMaterial = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 }); // 增加粗糙度
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.5;
    floor.receiveShadow = true;
    scene.add(floor);
    
    // 添加xyz三軸坐標系 (保持不變)
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);
    
    // 創建鼓組
    const createdDrums = new Set();
    zones.forEach(zone => {
        if (createdDrums.has(zone.name + zone.pos3d.join())) return;
        createdDrums.add(zone.name + zone.pos3d.join());
        
        // 使用 zones 中定義的半徑和高度
        const radius = zone.radius; 
        const height = zone.height;
        
        const geometry = new THREE.CylinderGeometry(radius, radius, height, 32);
        
        // --- 逼真的材質設置 ---
        const material = new THREE.MeshStandardMaterial({ 
            color: zone.color,
            metalness: zone.metalness,   // 金屬感
            roughness: zone.roughness,   // 粗糙度
            side: THREE.DoubleSide       // 確保鈸兩面都可見
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(...zone.pos3d);
        
        // 讓鼓面傾斜朝向相機（向前傾斜約20度）
        mesh.rotation.x = -Math.PI / 9; 
        
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        scene.add(mesh);
        
        drumMeshes[zone.name + zone.pos3d.join()] = mesh;
        
        // 標籤 (保持不變)
        createLabel(zone.name, zone.pos3d);
    });
    
    // 鼓棒（球體）
    const stickGeometry = new THREE.SphereGeometry(0.15, 16, 16);
    
    // 調整鼓棒材質，使其具有發光效果 (Emissive)
    const rightMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0x880000, roughness: 0.3 });
    rightStick = new THREE.Mesh(stickGeometry, rightMaterial);
    rightStick.castShadow = true;
    scene.add(rightStick);
    
    const leftMaterial = new THREE.MeshStandardMaterial({ color: 0x0000ff, emissive: 0x000088, roughness: 0.3 });
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
    let x = (45 - yaw) / 90 * 900;
    let y = (pitch + 10) / 45 * 450;
    x = Math.max(0, Math.min(900, x));
    y = Math.max(0, Math.min(450, y));
    return {x, y};
}

// 將 2D 坐標轉換為 3D 位置（用於顯示鼓棒）
function mapXYto3D(x, y) {
    const x3d = (x / 900 - 0.5) * 8;
    const z3d = (y / 450 - 0.5) * 4;
    const y3d = 2;
    return [x3d, y3d, z3d];
}

// 繪製函數（3D版本）
function draw(rightPitch, rightYaw, leftPitch, leftYaw) {
    // 計算 2D 坐標（用於敲擊偵測）
    const rightPos2D = mapAngleToXY(rightPitch, rightYaw);
    const leftPos2D = mapAngleToXY(leftPitch, leftYaw);
    
    // 轉換為 3D 位置
    const rightPos3D = mapXYto3D(rightPos2D.x, rightPos2D.y);
    const leftPos3D = mapXYto3D(leftPos2D.x, leftPos2D.y);
    
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

// 保持原有的數據顯示邏輯
function updateSensorDisplay(rightData, leftData) {
    document.getElementById('pitch-value').textContent = rightData["pitch (y軸轉)"].toFixed(1) + '° (R)';
    document.getElementById('roll-value').textContent = rightData["roll (x軸轉)"].toFixed(1) + '° (R)';
    document.getElementById('yaw-value').textContent = rightData["yaw (z軸轉)"].toFixed(1) + '° (R)';
    document.getElementById('accel-x-value').textContent = rightData.ax.toFixed(2) + ' g (R)';
    document.getElementById('accel-y-value').textContent = rightData.ay.toFixed(2) + ' g (R)';
    document.getElementById('accel-z-value').textContent = rightData.az.toFixed(2) + ' g (R)';
    
    const rightMagnitude = Math.sqrt(rightData.ax ** 2 + rightData.ay ** 2 + rightData.az ** 2);
    document.getElementById('magnitude-value').textContent = rightMagnitude.toFixed(2) + ' g (R)';
    
    document.getElementById('gyro-x-value').textContent = rightData.gx.toFixed(1) + '°/s (R)';
    document.getElementById('gyro-y-value').textContent = rightData.gy.toFixed(1) + '°/s (R)';
    document.getElementById('gyro-z-value').textContent = rightData.gz.toFixed(1) + '°/s (R)';
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
