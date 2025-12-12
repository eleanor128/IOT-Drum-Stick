// --------------------- 多種音效播放方式 ---------------------
let audioCtx;
let audioBuffers = {};
let htmlAudioElements = {};
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
        
        // 初始化 AudioContext
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

        // 載入所有音效檔案
        for (const key in files) {
            try {
                const response = await fetch(files[key]);
                if (!response.ok) {
                    console.error(`Failed to load ${key}: ${response.status}`);
                    continue;
                }
                const arrayBuffer = await response.arrayBuffer();
                audioBuffers[key] = await audioCtx.decodeAudioData(arrayBuffer);
                console.log(`Loaded: ${key}`);
            } catch (err) {
                console.error(`Error loading ${key}:`, err);
            }
        }

        audioEnabled = true;
        btn.textContent = "音效已啟動";
        btn.classList.add('enabled');
        btn.disabled = false;
        status.textContent = `音效已就緒！已載入 ${Object.keys(audioBuffers).length} 個音效`;
        
        // 播放測試音效
        playSound("Snare");
        
    } catch (error) {
        console.error("Audio initialization failed:", error);
        status.textContent = "音效載入失敗";
        btn.textContent = "載入失敗";
        btn.disabled = false;
    }
}

// 播放音效
function playSound(name) {
    if (!audioEnabled) {
        console.log("Audio not enabled yet");
        return;
    }

    if (audioCtx && audioBuffers[name]) {
        try {
            const source = audioCtx.createBufferSource();
            source.buffer = audioBuffers[name];
            
            // 添加音量控制
            const gainNode = audioCtx.createGain();
            gainNode.gain.value = 0.8; // 80% 音量
            
            source.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            source.start(0);
            
            console.log(`Playing: ${name} (Web Audio API)`);
            return;
        } catch (err) {
            console.error(`Web Audio playback error for ${name}:`, err);
        }
    }

    console.warn(`Could not play sound: ${name}`);
}


// --------------------- 畫布 ---------------------
const canvas = document.getElementById("drumCanvas");
const ctx = canvas.getContext("2d");

// 定義每個鼓/鈸的圓心座標 (cx, cy) 和半徑 (r)
// 假設 canvas 寬度約 900，高度約 450
const zones = [
    // 上排 (Tom-High, Tom-Mid, Ride, Symbal)
    // 圓心 (cx, cy) 位於畫布頂部約 1/3 處 (y=150)
    { name: "Hihat",     cx: 150, cy: 150, r: 80, color: "#CCCCCC" }, // 左邊的 Hi-Hat
    { name: "Tom_high",  cx: 350, cy: 150, r: 85, color: "#B8574B" }, // 中高音鼓
    { name: "Tom_mid",   cx: 550, cy: 150, r: 95, color: "#A04C40" }, // 中音鼓
    { name: "Ride",      cx: 800, cy: 100, r: 100, color: "#E0E0E0" }, // 右上方的 Ride 鈸

    // 下排 (Snare, Tom-Floor)
    // 圓心 (cx, cy) 位於畫布底部約 2/3 處 (y=350)
    { name: "Snare",     cx: 250, cy: 380, r: 110, color: "#D1D1D1" }, // 小鼓 (Snare)
    { name: "Tom_floor", cx: 650, cy: 380, r: 120, color: "#8B453A" }, // 落地鼓 (Tom-Floor)
    { name: "Symbal",    cx: 50,  cy: 300, r: 80, color: "#CCCCCC" }, // 增加一個左下角的 Crash Symbal 
];
// 注意：Symbal 和 Hihat 的音效可能需要根據您的實際配置來分配 yaw 區間。
// 由於音效名稱有 Symbal 和 Hihat，我們將其分開繪製。

function mapAngleToXY(pitch, yaw) {
    // X 座標：yaw 控制左右移動
    // 鼓棒向左 → yaw 為正 → 紅點向左
    // 鼓棒向右 → yaw 為負 → 紅點向右
    // yaw = +45° (左) → x = 0 (左邊)
    // yaw = 0° (中) → x = canvas.width / 2 (中間)
    // yaw = -45° (右) → x = canvas.width (右邊)
    let x = (45 - yaw) / 90 * canvas.width;

    // Y 座標：pitch 控制上下
    let y = (pitch + 10) / 45 * canvas.height;

    // 限制範圍在畫布內
    x = Math.max(0, Math.min(canvas.width, x));
    y = Math.max(0, Math.min(canvas.height, y));
    return {x, y};
}

function draw(rightPitch, rightYaw, leftPitch, leftYaw) {
    // 1. 清空畫布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 2. 繪製所有鼓組 (使用圓形)
    zones.forEach(z => {
        // 繪製鼓面
        ctx.fillStyle = z.color;
        ctx.beginPath();
        // 使用 cx, cy, r 繪製圓形
        ctx.arc(z.cx, z.cy, z.r, 0, Math.PI * 2); 
        ctx.fill();

        // 繪製鼓框 (增加立體感)
        ctx.strokeStyle = "#333333";
        ctx.lineWidth = 5;
        ctx.stroke();

        // 繪製鼓/鈸名稱
        ctx.fillStyle = (z.name === "Ride" || z.name === "Hihat" || z.name === "Symbal") ? "#333" : "#fff";
        ctx.font = "20px Arial";
        // 將文字置於圓心上方
        ctx.textAlign = "center";
        ctx.fillText(z.name, z.cx, z.cy - z.r / 2); 
    });
    
    // 3. 繪製鼓棒 (R, L) (保持不變)
    
    // 右手鼓棒（紅色）
    const rightPos = mapAngleToXY(rightPitch, rightYaw);
    ctx.fillStyle = "red";
    ctx.beginPath();
    ctx.arc(rightPos.x, rightPos.y, 12, 0, Math.PI * 2);
    ctx.fill();
    
    // 添加標籤
    ctx.fillStyle = "white";
    ctx.font = "12px Arial";
    ctx.fillText("R", rightPos.x, rightPos.y + 4); // 使用 center 對齊

    // 左手鼓棒（藍色）
    const leftPos = mapAngleToXY(leftPitch, leftYaw);
    ctx.fillStyle = "blue";
    ctx.beginPath();
    ctx.arc(leftPos.x, leftPos.y, 12, 0, Math.PI * 2);
    ctx.fill();
    
    // 添加標籤
    ctx.fillStyle = "white";
    ctx.font = "12px Arial";
    ctx.fillText("L", leftPos.x, leftPos.y + 4); // 使用 center 對齊
}
// 注意：這裡的 draw 函式使用的是 zones 的 cx/cy/r 屬性。

// --------------------- HIT 偵測 ---------------------
let rightHitCooldown = 0;
let leftHitCooldown = 0;
function detectZone(pitch, yaw) {
    // 根據 pitch 和 yaw 計算紅點的 X, Y 座標
    const pos = mapAngleToXY(pitch, yaw);

    // 檢查紅點位於哪個圓形區塊 (圓形碰撞偵測)
    for (const zone of zones) {
        // 計算紅點 (pos.x, pos.y) 到圓心 (zone.cx, zone.cy) 的距離
        const distance = Math.sqrt(
            Math.pow(pos.x - zone.cx, 2) + Math.pow(pos.y - zone.cy, 2)
        );

        // 如果距離小於半徑，則視為命中
        if (distance < zone.r) {
            return zone.name;
        }
    }

    // 預設返回 Snare (如果沒有匹配到任何區塊)
    return "Snare";
}

// --------------------- 更新數據顯示面板 ---------------------
function updateSensorDisplay(rightData, leftData) {
    // 右手數據
    document.getElementById('pitch-value').textContent = rightData["pitch (y軸轉)"].toFixed(1) + '° (R)';
    document.getElementById('roll-value').textContent = rightData["roll (x軸轉)"].toFixed(1) + '° (R)';
    document.getElementById('yaw-value').textContent = rightData["yaw (z軸轉)"].toFixed(1) + '° (R)';
    document.getElementById('accel-x-value').textContent = rightData.ax.toFixed(2) + ' g (R)';
    document.getElementById('accel-y-value').textContent = rightData.ay.toFixed(2) + ' g (R)';
    document.getElementById('accel-z-value').textContent = rightData.az.toFixed(2) + ' g (R)';
    
    const rightMagnitude = Math.sqrt(rightData.ax * rightData.ax + rightData.ay * rightData.ay + rightData.az * rightData.az);
    document.getElementById('magnitude-value').textContent = rightMagnitude.toFixed(2) + ' g (R)';
    
    document.getElementById('gyro-x-value').textContent = rightData.gx.toFixed(1) + '°/s (R)';
    document.getElementById('gyro-y-value').textContent = rightData.gy.toFixed(1) + '°/s (R)';
    document.getElementById('gyro-z-value').textContent = rightData.gz.toFixed(1) + '°/s (R)';
}


// --------------------- 主迴圈 ---------------------
// 儲存最新的左右手數據
let rightData = { "pitch (y軸轉)": 0, "yaw (z軸轉)": 0, "roll (x軸轉)": 0, ax: 0, ay: 0, az: 0, gx: 0, gy: 0, gz: 0, is_hit: false };
let leftData = { "pitch (y軸轉)": 0, "yaw (z軸轉)": 0, "roll (x軸轉)": 0, ax: 0, ay: 0, az: 0, gx: 0, gy: 0, gz: 0, is_hit: false };

// 獨立更新右手數據
function updateRight() {
    fetch("/right_data")
        .then(res => res.json())
        .then(data => {
            rightData = data;
            
            // 右手敲擊偵測
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
        .finally(() => {
            // 立即發起下一次請求，不等待動畫幀
            setTimeout(updateRight, 0);
        });
}

// 獨立更新左手數據
function updateLeft() {
    fetch("/left_data")
        .then(res => res.json())
        .then(data => {
            leftData = data;
            
            // 左手敲擊偵測
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
        .finally(() => {
            // 立即發起下一次請求，不等待動畫幀
            setTimeout(updateLeft, 0);
        });
}

// 畫面渲染迴圈（60 FPS）
function render() {
    // 使用最新的數據繪製
    draw(
        rightData["pitch (y軸轉)"], 
        rightData["yaw (z軸轉)"],
        leftData["pitch (y軸轉)"], 
        leftData["yaw (z軸轉)"]
    );
    
    // 更新數據顯示
    updateSensorDisplay(rightData, leftData);
    
    requestAnimationFrame(render);
}

// 啟動所有迴圈
updateRight();
updateLeft();
render();
