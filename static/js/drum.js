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
        btn.textContent = "✅ 音效已啟動";
        btn.classList.add('enabled');
        btn.disabled = false;
        status.textContent = `音效已就緒！已載入 ${Object.keys(audioBuffers).length} 個音效`;
        
        // 播放測試音效
        playSound("Snare");
        
    } catch (error) {
        console.error("Audio initialization failed:", error);
        status.textContent = "音效載入失敗";
        btn.textContent = "❌ 載入失敗";
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

const zones = [
    { name: "Symbal",    x: 0,   y: 0,   w: 225, h: 225, color:"#e5b3ff" },
    { name: "Tom_high",  x: 225, y: 0,   w: 225, h: 225, color:"#00c864" },
    { name: "Tom_mid",   x: 450, y: 0,   w: 225, h: 225, color:"#ff7f2a" },
    { name: "Ride",      x: 675, y: 0,   w: 225, h: 225, color:"#6eeee7" },

    { name: "Hihat",     x: 0,   y: 225, w: 225, h: 225, color:"#3232ff" },
    { name: "Snare",     x: 225, y: 225, w: 225, h: 225, color:"#d9d9d9" },
    { name: "Snare",     x: 450, y: 225, w: 225, h: 225, color:"#d9d9d9" },
    { name: "Tom_floor", x: 675, y: 225, w: 225, h: 225, color:"#4d4d4d" },
];

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

function draw(pitch, yaw) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    zones.forEach(z => {
        ctx.fillStyle = z.color;
        ctx.fillRect(z.x, z.y, z.w, z.h);

        ctx.fillStyle = "#fff";
        ctx.font = "20px Arial";
        ctx.fillText(z.name, z.x + 10, z.y + 30);
    });

    // 鼓棒紅點
    const pos = mapAngleToXY(pitch, yaw);
    ctx.fillStyle = "red";
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 12, 0, Math.PI * 2);
    ctx.fill();
}


// --------------------- HIT 偵測 ---------------------
let hitCooldown = 0;

function detectZone(pitch, yaw) {
    // 根據 pitch 和 yaw 計算紅點的 X, Y 座標
    const pos = mapAngleToXY(pitch, yaw);

    // 檢查紅點位於哪個區塊
    for (const zone of zones) {
        if (pos.x >= zone.x && pos.x < zone.x + zone.w &&
            pos.y >= zone.y && pos.y < zone.y + zone.h) {
            return zone.name;
        }
    }

    // 預設返回 Snare（如果沒有匹配到任何區塊）
    return "Snare";
}


// --------------------- 更新數據顯示面板 ---------------------
function updateSensorDisplay(data) {
    // 更新角度數據
    document.getElementById('pitch-value').textContent = data["pitch (y軸轉)"].toFixed(1) + '°';
    document.getElementById('roll-value').textContent = data["roll (x軸轉)"].toFixed(1) + '°';
    document.getElementById('yaw-value').textContent = data["yaw (z軸轉)"].toFixed(1) + '°';

    // 更新加速度數據
    document.getElementById('accel-x-value').textContent = data.ax.toFixed(2) + ' g';
    document.getElementById('accel-y-value').textContent = data.ay.toFixed(2) + ' g';
    document.getElementById('accel-z-value').textContent = data.az.toFixed(2) + ' g';

    // 計算總加速度
    const magnitude = Math.sqrt(data.ax * data.ax + data.ay * data.ay + data.az * data.az);
    document.getElementById('magnitude-value').textContent = magnitude.toFixed(2) + ' g';

    // 更新陀螺儀數據
    document.getElementById('gyro-x-value').textContent = data.gx.toFixed(1) + '°/s';
    document.getElementById('gyro-y-value').textContent = data.gy.toFixed(1) + '°/s';
    document.getElementById('gyro-z-value').textContent = data.gz.toFixed(1) + '°/s';
}


// --------------------- 主迴圈 ---------------------
function update() {
    fetch("/data")
        .then(res => res.json())
        .then(data => {
            // 更新畫布
            draw(data["pitch (y軸轉)"], data["yaw (z軸轉)"]);

            // 更新數據顯示面板
            updateSensorDisplay(data);

            // 使用後端的敲擊偵測 + 前端的位置判斷
            if (hitCooldown > 0) {
                hitCooldown--;
            } else if (data.is_hit) {
                // 後端確認有向下揮擊，前端根據紅點位置決定音效
                const zone = detectZone(data["pitch (y軸轉)"], data["yaw (z軸轉)"]);
                console.log(`🥁 Hit detected at zone: ${zone}`);
                playSound(zone);
                hitCooldown = 8;  // 與 hit_detection.py 相同的 cooldown
            }
        })
        .catch(err => console.log("Fetch error:", err));

    requestAnimationFrame(update);
}

update();
