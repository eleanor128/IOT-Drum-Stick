// ==================== 設定檔引用 ====================
// 所有配置參數已移至 3d_settings.js 統一管理
// 請在 HTML 中先載入: <script src="/static/js/3d_settings.js"></script>

// 複製音效系統（保持不變）
let audioCtx;
let audioBuffers = {};
let audioEnabled = false;
let activeSources = [];  // 記錄所有正在播放的音效源（支援同時播放相同音效）

async function enableAudio() {
    // const btn = document.getElementById('enableAudioBtn');
    const status = document.getElementById('statusText');
    
    if (audioEnabled) {
        status.textContent = "音效已經啟動！";
        return;
    }

    try {
        
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        // 使用 3d_settings.js 中的 SOUND_FILES 配置
        for (const key in SOUND_FILES) {
            try {
                const response = await fetch(SOUND_FILES[key]);
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

// zones 配置已移至 3d_settings.js


// 初始化 3D 場景
function init3D() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(SCENE_BG_COLOR);
    
    camera = new THREE.PerspectiveCamera(CAMERA_FOV, CAMERA_ASPECT, CAMERA_NEAR, CAMERA_FAR);
    camera.position.set(...CAMERA_POSITION);
    camera.lookAt(...CAMERA_LOOKAT);
    
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(900, 600);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);
    
    // 光照 - 從頂端照下來
    const ambientLight = new THREE.AmbientLight(AMBIENT_LIGHT_COLOR, AMBIENT_LIGHT_INTENSITY);
    scene.add(ambientLight);
    
    const topLight = new THREE.DirectionalLight(DIRECTIONAL_LIGHT_COLOR, DIRECTIONAL_LIGHT_INTENSITY);
    topLight.position.set(...DIRECTIONAL_LIGHT_POSITION);  // 從正上方照下來
    topLight.castShadow = true;
    scene.add(topLight);
    
    // 地板
    const floorGeometry = new THREE.PlaneGeometry(FLOOR_SIZE, FLOOR_SIZE);
    const floorMaterial = new THREE.MeshStandardMaterial({ 
        color: FLOOR_COLOR,
        roughness: FLOOR_ROUGHNESS 
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = FLOOR_Y;
    floor.receiveShadow = true;
    scene.add(floor);
    
    // 創建鼓組
    const createdDrums = new Set();
    zones.forEach(zone => {
        if (createdDrums.has(zone.name + zone.pos3d.join())) return;
        createdDrums.add(zone.name + zone.pos3d.join());
        
        const isCymbal = zone.name.includes("Symbal") || zone.name.includes("Ride") || zone.name.includes("Hihat");
        const radius = zone.radius || (isCymbal ? DEFAULT_CYMBAL_RADIUS : DEFAULT_DRUM_RADIUS);
        
        let height;
        if (isCymbal) {
            height = CYMBAL_HEIGHT;
        } else if (zone.name === "Tom_floor") {
            height = TOM_FLOOR_HEIGHT;
        } else {
            height = STANDARD_DRUM_HEIGHT;
        }
        
        // 鼓/鈸主體 - 統一使用深色
        const geometry = new THREE.CylinderGeometry(radius, radius, height, DRUM_SEGMENTS);
        const material = new THREE.MeshStandardMaterial({ 
            color: DRUM_COLOR,
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
        const edgeGeometry = new THREE.TorusGeometry(radius, DRUM_EDGE_TORUS_RADIUS, DRUM_EDGE_TORUS_TUBE, DRUM_SEGMENTS);
        const edgeMaterial = new THREE.MeshStandardMaterial({
            color: zone.color,
            emissive: zone.color,
            emissiveIntensity: DRUM_EDGE_EMISSIVE_INTENSITY,
            metalness: DRUM_EDGE_METALNESS,
            roughness: DRUM_EDGE_ROUGHNESS
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
        const stickBody = new THREE.CylinderGeometry(STICK_RADIUS_TIP, STICK_RADIUS_BASE, STICK_LENGTH, STICK_SEGMENTS);
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
        const tipGeometry = new THREE.SphereGeometry(STICK_TIP_SPHERE_RADIUS, STICK_SPHERE_SEGMENTS, STICK_SPHERE_SEGMENTS);
        const tipMesh = new THREE.Mesh(tipGeometry, stickMaterial);
        tipMesh.position.z = STICK_LENGTH;  // 放在棒子前端（緊貼鼓棒主體）
        tipMesh.castShadow = true;
        drumstick.add(tipMesh);
        
        // 鼓棒底端（握把）- 在後方（靠近相機）
        const gripGeometry = new THREE.SphereGeometry(STICK_GRIP_SPHERE_RADIUS, STICK_SPHERE_SEGMENTS, STICK_SPHERE_SEGMENTS);
        const gripMesh = new THREE.Mesh(gripGeometry, stickMaterial);
        gripMesh.position.z = 0;  // 放在棒子後端（握把處）
        gripMesh.castShadow = true;
        drumstick.add(gripMesh);
        
        return drumstick;
    }
    
    // 創建右手鼓棒（紅色）
    rightStick = createDrumstick(RIGHT_STICK_COLOR, RIGHT_STICK_EMISSIVE);
    // 初始位置：尖端指向z軸正向，棒身水平於xz平面
    rightStick.position.set(0, 1.5, GRIP_BASE_Z);  // 初始位置
    rightStick.rotation.x = 0;  // Pitch = 0 (水平)
    rightStick.rotation.y = 0;  // Yaw = 0 (指向z正向)
    rightStick.rotation.z = 0;  // Roll = 0
    scene.add(rightStick);
    
    // 創建左手鼓棒（藍色）
    leftStick = createDrumstick(LEFT_STICK_COLOR, LEFT_STICK_EMISSIVE);
    // 初始位置：尖端指向z軸正向，棒身水平於xz平面
    leftStick.position.set(0, 1.5, GRIP_BASE_Z);  // 初始位置
    leftStick.rotation.x = 0;  // Pitch = 0 (水平)
    leftStick.rotation.y = 0;  // Yaw = 0 (指向z正向)
    leftStick.rotation.z = 0;  // Roll = 0
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

// 碰撞檢測與修正：計算鼓棒是否穿入鼓/鈸內部（包含頂部、側面、底部），並返回修正後的 Pitch 角度 (弧度)
function solveStickCollision(gripPos, rotX, rotY) {
    const stickLength = 1.2;
    // 分開檢查：尖端用於敲擊判定，棒身用於防止穿模
    const tipPoint = 1.0;      // 尖端位置
    const bodyPoint = 0.7;     // 棒身中段（僅用於防穿模）
    let correctedRotX = rotX;
    let correctedRotY = rotY;
    let hitDrum = null;
    let hitDrumCenter = null;  // 記錄擊中的鼓面中心位置

    zones.forEach(zone => {
        const drumPos = zone.pos3d;
        const drumRot = zone.rotation;
        const isCymbal = zone.name.includes("Symbal") || zone.name.includes("Ride") || zone.name.includes("Hihat");
        const radius = zone.radius || (isCymbal ? 1.2 : 0.9);
        const hitRadius = radius + 0.1; // 碰撞檢測半徑（減小，更精確）

        let drumHeight;
        if (isCymbal) {
            drumHeight = 0.05;
        } else if (zone.name === "Tom_floor") {
            drumHeight = 1.0;
        } else {
            drumHeight = 0.5;
        }

        const buffer = 0.05; // 緩衝距離

        // 計算鼓面(頂部)和鼓底中心點 (考慮旋轉)
        const headCenterY = drumPos[1] + (drumHeight / 2) * Math.cos(drumRot);
        const headCenterZ = drumPos[2] + (drumHeight / 2) * Math.sin(drumRot);
        const bottomCenterY = drumPos[1] - (drumHeight / 2) * Math.cos(drumRot);
        const bottomCenterZ = drumPos[2] - (drumHeight / 2) * Math.sin(drumRot);

        // 計算鼓面法線向量（向上）
        const normalY = Math.cos(drumRot);
        const normalZ = Math.sin(drumRot);

        // 1. 檢查尖端碰撞（用於敲擊判定）
        const tipDist = stickLength * tipPoint;
        const tipX = gripPos[0] + tipDist * Math.cos(rotX) * Math.sin(rotY);
        const tipY = gripPos[1] - tipDist * Math.sin(rotX);
        const tipZ = gripPos[2] + tipDist * Math.cos(rotX) * Math.cos(rotY);

        // 計算尖端到鼓中心軸的水平距離
        const tipDx = tipX - drumPos[0];
        const tipDz = tipZ - headCenterZ;
        const tipHorizontalDist = Math.sqrt(tipDx * tipDx + tipDz * tipDz);
        
        // 檢查是否在鼓的水平範圍內
        if (tipHorizontalDist < hitRadius) {
            // 計算尖端到鼓面的垂直距離（沿法線方向）
            const tipDistToHeadPlane = (tipY - headCenterY) * normalY + (tipZ - headCenterZ) * normalZ;
            const tipDistToBottomPlane = (tipY - bottomCenterY) * normalY + (tipZ - bottomCenterZ) * normalZ;
            
            // 檢查是否在鼓的高度範圍內（從鼓底到鼓面）
            const isAboveBottom = tipDistToBottomPlane > -buffer;  // 在鼓底上方
            const isBelowHead = tipDistToHeadPlane < buffer;        // 在鼓面下方
            
            if (isAboveBottom && isBelowHead) {
                // 尖端在鼓內部或接觸鼓面
                if (tipDistToHeadPlane >= -buffer && tipDistToHeadPlane < buffer) {
                    // 尖端接觸鼓面：修正角度 + 標記為打擊
                    const y_surface_at_tipZ = headCenterY - (normalZ / normalY) * (tipZ - headCenterZ);
                    let maxSin = (gripPos[1] - (y_surface_at_tipZ + buffer)) / tipDist;
                    maxSin = Math.max(-1, Math.min(1, maxSin));
                    const maxRotX = Math.asin(maxSin);

                    if (maxRotX < correctedRotX) {
                        correctedRotX = maxRotX;
                        hitDrum = zone.name;  // 只有尖端碰撞鼓面才標記為打擊
                        // 記錄鼓面中心位置，用於視覺對齊
                        hitDrumCenter = {
                            x: drumPos[0],
                            y: headCenterY,
                            z: headCenterZ
                        };
                    }
                } else {
                    // 尖端在鼓內部：修正角度防止穿入
                    const y_surface_at_tipZ = headCenterY - (normalZ / normalY) * (tipZ - headCenterZ);
                    let maxSin = (gripPos[1] - (y_surface_at_tipZ + buffer)) / tipDist;
                    maxSin = Math.max(-1, Math.min(1, maxSin));
                    const maxRotX = Math.asin(maxSin);

                    if (maxRotX < correctedRotX) {
                        correctedRotX = maxRotX;
                        // 不標記為打擊，僅防止穿入
                    }
                }
            }
        }

        // 2. 檢查棒身碰撞（僅用於防止穿模，不觸發打擊）
        const bodyDist = stickLength * bodyPoint;
        const bodyX = gripPos[0] + bodyDist * Math.cos(rotX) * Math.sin(rotY);
        const bodyY = gripPos[1] - bodyDist * Math.sin(rotX);
        const bodyZ = gripPos[2] + bodyDist * Math.cos(rotX) * Math.cos(rotY);

        // 計算棒身到鼓中心軸的水平距離
        const bodyDx = bodyX - drumPos[0];
        const bodyDz = bodyZ - headCenterZ;
        const bodyHorizontalDist = Math.sqrt(bodyDx * bodyDx + bodyDz * bodyDz);
        
        // 檢查是否在鼓的水平範圍內
        if (bodyHorizontalDist < hitRadius) {
            // 計算棒身到鼓面和鼓底的垂直距離
            const bodyDistToHeadPlane = (bodyY - headCenterY) * normalY + (bodyZ - headCenterZ) * normalZ;
            const bodyDistToBottomPlane = (bodyY - bottomCenterY) * normalY + (bodyZ - bottomCenterZ) * normalZ;
            
            // 檢查是否在鼓的高度範圍內
            const isAboveBottom = bodyDistToBottomPlane > -buffer;
            const isBelowHead = bodyDistToHeadPlane < buffer;
            
            if (isAboveBottom && isBelowHead) {
                // 棒身在鼓內部或接觸鼓面：僅修正角度，不標記為打擊
                const y_surface_at_bodyZ = headCenterY - (normalZ / normalY) * (bodyZ - headCenterZ);
                let maxSin = (gripPos[1] - (y_surface_at_bodyZ + buffer)) / bodyDist;
                maxSin = Math.max(-1, Math.min(1, maxSin));
                const maxRotX = Math.asin(maxSin);

                if (maxRotX < correctedRotX) {
                    correctedRotX = maxRotX;
                    // 不設定 hitDrum，所以不會觸發打擊音效
                }
            }
        }
    });

    // 如果檢測到擊打，微調角度讓尖端對齊鼓面中心（視覺優化）
    if (hitDrum && hitDrumCenter) {
        const tipDist = stickLength * tipPoint;
        
        // 計算當前尖端位置
        const currentTipX = gripPos[0] + tipDist * Math.cos(correctedRotX) * Math.sin(correctedRotY);
        const currentTipY = gripPos[1] - tipDist * Math.sin(correctedRotX);
        const currentTipZ = gripPos[2] + tipDist * Math.cos(correctedRotX) * Math.cos(correctedRotY);
        
        // 計算需要的角度調整讓尖端指向鼓面中心
        const targetDx = hitDrumCenter.x - gripPos[0];
        const targetDy = hitDrumCenter.y - gripPos[1];
        const targetDz = hitDrumCenter.z - gripPos[2];
        
        // 計算目標角度（水平方向 - Yaw）
        const targetRotY = Math.atan2(targetDx, targetDz);
        
        // 計算目標角度（垂直方向 - Pitch）
        const horizontalDist = Math.sqrt(targetDx * targetDx + targetDz * targetDz);
        const targetRotX = -Math.atan2(targetDy, horizontalDist);
        
        // 平滑混合：80% 目標角度 + 20% 原始角度（避免突兀）
        const blendFactor = 0.8;
        correctedRotX = targetRotX * blendFactor + correctedRotX * (1 - blendFactor);
        correctedRotY = targetRotY * blendFactor + correctedRotY * (1 - blendFactor);
    }

    return { correctedRotX, correctedRotY, hitDrum };
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

// 校正偏移量
let rightYawOffset = 0;
let leftYawOffset = 0;

// 按下 'R' 鍵重置方向 (校正漂移)
document.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'r') {
        rightYawOffset = -rightData["yaw (z軸轉)"];
        leftYawOffset = -leftData["yaw (z軸轉)"];
        console.log("Yaw Calibrated (Center Reset)");
    }
});

// 輔助函數：根據鼓的名稱獲取鼓面中心位置
function getDrumCenter(drumName) {
    const zone = zones.find(z => z.name === drumName);
    if (zone && zone.pos3d) {
        return {
            x: zone.pos3d[0],
            y: zone.pos3d[1],
            z: zone.pos3d[2]
        };
    }
    return null;
}

// 全局變量：存儲所有鼓面的幾何數據
let drumSurfaces = {};

// 計算所有鼓面的幾何數據（在應用啟動時執行一次）
function get_drum_surface() {
    drumSurfaces = {};
    
    zones.forEach(zone => {
        const isCymbal = zone.name.includes("Symbal") || zone.name.includes("Ride") || zone.name.includes("Hihat");
        const radius = zone.radius || (isCymbal ? DEFAULT_CYMBAL_RADIUS : DEFAULT_DRUM_RADIUS);
        
        let height;
        if (isCymbal) {
            height = CYMBAL_HEIGHT;
        } else if (zone.name === "Tom_floor") {
            height = TOM_FLOOR_HEIGHT;
        } else {
            height = STANDARD_DRUM_HEIGHT;
        }
        
        const centerPos = zone.pos3d;
        const rotation = zone.rotation !== undefined ? zone.rotation : -Math.PI / 9;
        
        // 計算鼓面（頂部）和鼓底的中心點座標（考慮旋轉）
        const headCenterY = centerPos[1] + (height / 2) * Math.cos(rotation);
        const headCenterZ = centerPos[2] + (height / 2) * Math.sin(rotation);
        const bottomCenterY = centerPos[1] - (height / 2) * Math.cos(rotation);
        const bottomCenterZ = centerPos[2] - (height / 2) * Math.sin(rotation);
        
        // 計算鼓面法線向量（指向上方）
        const normalX = 0;
        const normalY = Math.cos(rotation);
        const normalZ = Math.sin(rotation);
        
        // 存儲鼓面數據
        drumSurfaces[zone.name] = {
            name: zone.name,
            radius: radius,
            height: height,
            centerX: centerPos[0],
            centerY: centerPos[1],
            centerZ: centerPos[2],
            rotation: rotation,
            
            // 鼓面（頂部）數據
            headSurface: {
                centerX: centerPos[0],
                centerY: headCenterY,
                centerZ: headCenterZ,
                normalX: normalX,
                normalY: normalY,
                normalZ: normalZ,
                radius: radius
            },
            
            // 鼓底數據
            bottomSurface: {
                centerX: centerPos[0],
                centerY: bottomCenterY,
                centerZ: bottomCenterZ,
                radius: radius
            },
            
            // 幾何範圍（用於快速碰撞檢測）
            bounds: {
                minX: centerPos[0] - radius,
                maxX: centerPos[0] + radius,
                minY: Math.min(headCenterY, bottomCenterY) - 0.1,
                maxY: Math.max(headCenterY, bottomCenterY) + 0.1,
                minZ: Math.min(headCenterZ, bottomCenterZ) - radius,
                maxZ: Math.max(headCenterZ, bottomCenterZ) + radius
            }
        };
    });
    
    console.log("Drum surfaces calculated:", drumSurfaces);
    return drumSurfaces;
}

// 檢查鼓棒尖端是否碰到鼓面
function checkDrumstickHit(tipX, tipY, tipZ) {
    for (const drumName in drumSurfaces) {
        const drum = drumSurfaces[drumName];
        const surface = drum.headSurface;
        
        // 快速邊界檢查
        if (tipX < drum.bounds.minX || tipX > drum.bounds.maxX ||
            tipY < drum.bounds.minY || tipY > drum.bounds.maxY ||
            tipZ < drum.bounds.minZ || tipZ > drum.bounds.maxZ) {
            continue;
        }
        
        // 檢查尖端到鼓面中心的水平距離
        const dx = tipX - surface.centerX;
        const dz = tipZ - surface.centerZ;
        const horizontalDist = Math.sqrt(dx * dx + dz * dz);
        
        if (horizontalDist > surface.radius) {
            continue;  // 超出鼓面半徑
        }
        
        // 計算尖端到鼓面的垂直距離（沿法線方向）
        const distToSurface = 
            (tipX - surface.centerX) * surface.normalX +
            (tipY - surface.centerY) * surface.normalY +
            (tipZ - surface.centerZ) * surface.normalZ;
        
        // 如果尖端非常接近鼓面（在表面上方或下方很小的範圍內）
        const hitThreshold = 0.05;  // 5cm 容差
        if (Math.abs(distToSurface) < hitThreshold) {
            return {
                hit: true,
                drumName: drumName,
                distance: distToSurface,
                surface: surface
            };
        }
    }
    
    return { hit: false };
}

// 繪製函數（3D版本）- Yaw控制左右，Pitch控制揮擊
function draw(rightPitch, rightYaw, leftPitch, leftYaw, rightAdjustedPitch, leftAdjustedPitch) {
    const smoothFactor = 0.15; // 平滑係數，越小越平滑但延遲越高

    // 應用 Yaw 偏移 (校正漂移)
    const effectiveRightYaw = rightYaw + rightYawOffset;
    const effectiveLeftYaw = leftYaw + leftYawOffset;

    // 限制 Pitch 角度範圍，防止鼓棒尖端低於最低鼓面
    const clampedRightPitch = Math.max(PITCH_MIN, Math.min(PITCH_MAX, rightPitch));
    const clampedLeftPitch = Math.max(PITCH_MIN, Math.min(PITCH_MAX, leftPitch));

    // 偵測是否正在敲擊 (根據陀螺儀 Y 軸速度判斷)
    // 降低閾值以更容易觸發視覺效果
    const rightIsHitting = Math.abs(rightData.gy) > 50;  // 敲擊時陀螺儀 Y 軸速度較大
    const leftIsHitting = Math.abs(leftData.gy) > 50;

    // 計算旋轉角度 (弧度)
    // Pitch 行為：舉起 → pitch 變小(負值)，敲擊向下 → pitch 變大(正值)
    // rotation.x：正值 = 尖端向下 (敲擊姿勢)，負值 = 尖端向上 (舉起姿勢)
    // 平時保持水平 (rotation.x ≈ 0)，敲擊時才大幅旋轉
    let rightRotX, leftRotX;
    if (rightIsHitting) {
        // 敲擊時：pitch 增加 → 鼓棒向上旋轉（尖端Y增加）
        // 增加旋轉幅度：從 /30 改為 /20
        rightRotX = -(clampedRightPitch / 20) * (Math.PI / 2);
    } else {
        // 平時：保持水平，僅微幅調整
        rightRotX = -(clampedRightPitch / 25) * (Math.PI / 8);
    }
    // yaw 增加 → 鼓棒在水平面（平行地面）向左旋轉（尖端X減少）
    // 以手為圓心、鼓棒為半徑，在XZ平面上旋轉
    const rightRotY = -(effectiveRightYaw / 30) * (Math.PI / 3);
    
    // 右手握把位置計算 - 手在 XZ 平面移動，鼓棒旋轉控制尖端
    let targetRightX = GRIP_RIGHT_X;  // 手部X位置基礎值
    let targetRightY = GRIP_BASE_Y;   // 手部Y位置固定（高度）
    let targetRightZ = GRIP_BASE_Z;   // 手部Z位置基礎值

    // 根據 Yaw 調整手部 X 位置（左右移動以打不同位置的鼓）
    targetRightX += (effectiveRightYaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR;
    targetRightX = Math.max(GRIP_RIGHT_X_MIN, Math.min(GRIP_RIGHT_X_MAX, targetRightX));

    // 根據 Pitch 調整手部 Z 位置（前後移動以打過的鼓）
    // 動態深度調整：pitch 變小（舉起）代表打擊前方的鼓
    if (clampedRightPitch < PITCH_THRESHOLD) {
        // 打擊前方的鼓（Symbal, Ride, Tom_high, Tom_mid）- 需要大幅前伸
        const depthFactor = (PITCH_THRESHOLD - clampedRightPitch) / 20;
        targetRightZ += Math.min(PITCH_Z_TILTED_MAX, depthFactor * PITCH_Z_TILTED_FACTOR);
    } else {
        // 打擊後方的鼓（Snare, Tom_floor, Hihat）- 保持在基礎位置附近
        targetRightZ += clampedRightPitch * PITCH_Z_FLAT_FACTOR;
    }

    // 根據 X軸加速度 往深處移動（模擬左右揮動時的自然伸展）
    targetRightZ += Math.min(ACCEL_Z_MAX, Math.abs(rightData.ax) * ACCEL_Z_FACTOR);
    
    // 限制手部Z軸範圍：後方（Hihat）到前方（Symbal）
    targetRightZ = Math.max(GRIP_Z_MIN, Math.min(GRIP_Z_MAX, targetRightZ));
    
    // 應用平滑處理
    const rightX = lerp(rightStick.position.x, targetRightX, smoothFactor);
    const rightY = lerp(rightStick.position.y, targetRightY, smoothFactor);
    const rightZ = lerp(rightStick.position.z, targetRightZ, smoothFactor);
    
    // 左手鼓棒旋轉計算
    if (leftIsHitting) {
        // 敲擊時：pitch 增加 → 鼓棒向上旋轉（尖端Y增加）
        // 增加旋轉幅度：從 /30 改為 /20
        leftRotX = -(clampedLeftPitch / 20) * (Math.PI / 2);
    } else {
        // 平時：保持水平，僅微幅調整
        leftRotX = -(clampedLeftPitch / 25) * (Math.PI / 8);
    }
    // yaw 增加 → 鼓棒向左旋轉（尖端X減少）
    // 增加旋轉幅度：從 /45 改為 /30
    const leftRotY = -(effectiveLeftYaw / 30) * (Math.PI / 3);
    
    // 左手握把位置計算
    let targetLeftX = GRIP_LEFT_X;  // 左手基礎位置（對準左側鼓）
    let targetLeftY = GRIP_BASE_Y;
    let targetLeftZ = GRIP_BASE_Z;  // 基礎位置與右手相同深度
    
    // 根據 Yaw 調整握把 X 位置（手左右移動）
    targetLeftX += (effectiveLeftYaw / YAW_SENSITIVITY) * YAW_POSITION_FACTOR;
    targetLeftX = Math.max(GRIP_LEFT_X_MIN, Math.min(GRIP_LEFT_X_MAX, targetLeftX));

    // 握把 Y 保持在基礎高度（手不上下移動，只有鼓棒旋轉）
    targetLeftY = GRIP_BASE_Y;

    // 根據 Pitch 調整 Z 位置（前後伸展）
    // 動態深度調整（與右手相同邏輯）
    if (clampedLeftPitch < PITCH_THRESHOLD) {
        // 打擊前方的鼓（Symbal, Ride, Tom_high, Tom_mid）
        const leftDepthFactor = (PITCH_THRESHOLD - clampedLeftPitch) / 20;
        targetLeftZ += Math.min(PITCH_Z_TILTED_MAX, leftDepthFactor * PITCH_Z_TILTED_FACTOR);
    } else {
        // 打擊後方的鼓（Snare, Tom_floor, Hihat）
        targetLeftZ += clampedLeftPitch * PITCH_Z_FLAT_FACTOR;
    }

    // 根據 X軸加速度 往深處移動
    targetLeftZ += Math.min(ACCEL_Z_MAX, Math.abs(leftData.ax) * ACCEL_Z_FACTOR);
    
    // 限制手部Z軸範圍
    targetLeftZ = Math.max(GRIP_Z_MIN, Math.min(GRIP_Z_MAX, targetLeftZ));
    
    // 應用平滑處理
    const leftX = lerp(leftStick.position.x, targetLeftX, smoothFactor);
    const leftY = lerp(leftStick.position.y, targetLeftY, smoothFactor);
    const leftZ = lerp(leftStick.position.z, targetLeftZ, smoothFactor);
    
    // 右手感測器敲擊偵測 (從後端取得)
    const rightHitDrum = rightData.is_hit ? rightData.hit_drum : null;
    
    // 檢測右手打擊
    if (rightHitDrum) {
        if (!rightWasColliding && rightHitCooldown <= 0) {
            playSound(rightHitDrum);
            triggerDrumGlow(rightHitDrum); // 觸發發光
            rightHitCooldown = 10; // 冷卻時間 (幀數)
            console.log(`🥁 Right Hit (Sensor): ${rightHitDrum}`);
        }
        rightWasColliding = true;
        
        // 當敲擊時，計算該鼓的中心位置並對齊
        const drumCenter = getDrumCenter(rightHitDrum);
        if (drumCenter) {
            // 計算從鼓中心反推握把位置，確保尖端碰到鼓面
            const stickLength = STICK_LENGTH;
            
            // 計算從當前握把到鼓的方向向量
            let dx = drumCenter.x - rightX;
            let dz = drumCenter.z - rightZ;
            let dy = drumCenter.y - rightY;
            const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
            
            // 標準化方向向量
            dx /= dist;
            dy /= dist;
            dz /= dist;
            
            // 計算目標握把位置：從鼓面沿著方向向量反向移動鼓棒長度
            const targetGripX = drumCenter.x - dx * stickLength;
            const targetGripY = drumCenter.y - dy * stickLength;
            const targetGripZ = drumCenter.z - dz * stickLength;
            
            // 平滑移動握把到目標位置
            rightStick.position.x = lerp(rightX, targetGripX, DRUM_CENTER_BLEND_FACTOR);
            rightStick.position.y = lerp(rightY, targetGripY, DRUM_CENTER_BLEND_FACTOR);
            rightStick.position.z = lerp(rightZ, targetGripZ, DRUM_CENTER_BLEND_FACTOR);
            
            // 計算目標角度讓尖端指向鼓中心
            const targetYaw = Math.atan2(dx, dz);
            const horizontalDist = Math.sqrt(dx * dx + dz * dz);
            const targetPitch = Math.atan2(dy, horizontalDist);
            
            // 混合當前角度和目標角度 (80% 對齊鼓面)
            rightStick.rotation.y = lerp(rightRotY, targetYaw, DRUM_CENTER_BLEND_FACTOR);
            rightStick.rotation.x = lerp(rightRotX, targetPitch, DRUM_CENTER_BLEND_FACTOR);
        }
    } else {
        rightWasColliding = false;
        // 正常狀態：使用感測器角度
        rightStick.rotation.x = rightRotX;
        rightStick.rotation.y = rightRotY;
    }
    if (rightHitCooldown > 0) rightHitCooldown--;
    
    // 更新右手鼓棒位置
    rightStick.position.set(rightX, rightY, rightZ);
    
    // 左手感測器敲擊偵測 (從後端取得)
    const leftHitDrum = leftData.is_hit ? leftData.hit_drum : null;
    
    // 檢測左手打擊
    if (leftHitDrum) {
        if (!leftWasColliding && leftHitCooldown <= 0) {
            playSound(leftHitDrum);
            triggerDrumGlow(leftHitDrum); // 觸發發光
            leftHitCooldown = 10;
            console.log(`🥁 Left Hit (Sensor): ${leftHitDrum}`);
        }
        leftWasColliding = true;
        
        // 當敲擊時，計算該鼓的中心位置並對齊
        const drumCenter = getDrumCenter(leftHitDrum);
        if (drumCenter) {
            // 計算從鼓中心反推握把位置，確保尖端碰到鼓面
            const stickLength = STICK_LENGTH;
            
            // 計算從當前握把到鼓的方向向量
            let dx = drumCenter.x - leftX;
            let dz = drumCenter.z - leftZ;
            let dy = drumCenter.y - leftY;
            const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
            
            // 標準化方向向量
            dx /= dist;
            dy /= dist;
            dz /= dist;
            
            // 計算目標握把位置：從鼓面沿著方向向量反向移動鼓棒長度
            const targetGripX = drumCenter.x - dx * stickLength;
            const targetGripY = drumCenter.y - dy * stickLength;
            const targetGripZ = drumCenter.z - dz * stickLength;
            
            // 平滑移動握把到目標位置
            leftStick.position.x = lerp(leftX, targetGripX, DRUM_CENTER_BLEND_FACTOR);
            leftStick.position.y = lerp(leftY, targetGripY, DRUM_CENTER_BLEND_FACTOR);
            leftStick.position.z = lerp(leftZ, targetGripZ, DRUM_CENTER_BLEND_FACTOR);
            
            // 計算目標角度讓尖端指向鼓中心
            const targetYaw = Math.atan2(dx, dz);
            const horizontalDist = Math.sqrt(dx * dx + dz * dz);
            const targetPitch = Math.atan2(dy, horizontalDist);
            
            // 混合當前角度和目標角度 (80% 對齊鼓面)
            leftStick.rotation.y = lerp(leftRotY, targetYaw, DRUM_CENTER_BLEND_FACTOR);
            leftStick.rotation.x = lerp(leftRotX, targetPitch, DRUM_CENTER_BLEND_FACTOR);
        }
    } else {
        leftWasColliding = false;
        // 正常狀態：使用感測器角度
        leftStick.rotation.x = leftRotX;
        leftStick.rotation.y = leftRotY;
    }
    if (leftHitCooldown > 0) leftHitCooldown--;
    
    // 更新左手鼓棒位置
    leftStick.position.set(leftX, leftY, leftZ);
    
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
get_drum_surface();  // 計算所有鼓面的幾何數據
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