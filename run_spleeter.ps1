# Automatic Spleeter Runner for Windows
# This script will:
# 1. Detect conda installation
# 2. Create spleeter38 env (if not exists)
# 3. Install spleeter + ffmpeg + libsndfile
# 4. Run separation on party_animal.mp3
# 5. Display results

Write-Host "=== Spleeter Auto Runner ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Find conda
Write-Host "[1/5] Detecting conda installation..." -ForegroundColor Yellow
$condaPaths = @(
    "$env:USERPROFILE\Miniconda3\Scripts\conda.exe",
    "$env:USERPROFILE\miniforge3\Scripts\conda.exe",
    "$env:USERPROFILE\Anaconda3\Scripts\conda.exe",
    "C:\ProgramData\Miniconda3\Scripts\conda.exe",
    "C:\ProgramData\miniforge3\Scripts\conda.exe",
    "C:\ProgramData\Anaconda3\Scripts\conda.exe",
    "C:\tools\miniconda3\Scripts\conda.exe"
)

$condaExe = $null
foreach ($path in $condaPaths) {
    if (Test-Path $path) {
        $condaExe = $path
        Write-Host "  Found conda at: $condaExe" -ForegroundColor Green
        break
    }
}

if (-not $condaExe) {
    Write-Host "  Searching system for conda.exe..." -ForegroundColor Yellow
    $found = Get-ChildItem -Path "C:\" -Filter "conda.exe" -Recurse -ErrorAction SilentlyContinue -Depth 4 | Select-Object -First 1
    if ($found) {
        $condaExe = $found.FullName
        Write-Host "  Found conda at: $condaExe" -ForegroundColor Green
    }
}

if (-not $condaExe) {
    Write-Host "  ERROR: conda not found. Please install Miniconda/Miniforge first:" -ForegroundColor Red
    Write-Host "  Download from: https://github.com/conda-forge/miniforge/releases/latest" -ForegroundColor Red
    Write-Host "  Or run: winget install -e --id conda-forge.Miniforge3" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 1.5: Accept Anaconda TOS if needed
Write-Host ""
Write-Host "[1.5/5] Accepting Anaconda Terms of Service (if required)..." -ForegroundColor Yellow
$tosChannels = @(
    "https://repo.anaconda.com/pkgs/main",
    "https://repo.anaconda.com/pkgs/r",
    "https://repo.anaconda.com/pkgs/msys2"
)
foreach ($channel in $tosChannels) {
    & $condaExe tos accept --override-channels --channel $channel 2>$null | Out-Null
}
Write-Host "  TOS accepted (if applicable)." -ForegroundColor Green

# Step 2: Check/create env
Write-Host ""
Write-Host "[2/5] Checking spleeter38 environment..." -ForegroundColor Yellow
$envExists = & $condaExe env list | Select-String -Pattern "spleeter38"
if ($envExists) {
    Write-Host "  Environment spleeter38 already exists." -ForegroundColor Green
} else {
    Write-Host "  Creating spleeter38 environment (Python 3.8)..." -ForegroundColor Yellow
    Write-Host "  Using conda-forge channel..." -ForegroundColor Gray
    & $condaExe create -n spleeter38 python=3.8 -c conda-forge --override-channels -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to create environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "  Environment created successfully." -ForegroundColor Green
}

# Step 3: Install packages
Write-Host ""
Write-Host "[3/5] Installing ffmpeg + libsndfile via conda..." -ForegroundColor Yellow
& $condaExe run -n spleeter38 conda install -c conda-forge ffmpeg libsndfile -y
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to install conda packages." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  Conda packages installed successfully." -ForegroundColor Green

# Step 3.5: Install Spleeter via pip (conda version is old and Python 3.6/3.7 only)
Write-Host ""
Write-Host "[3.5/5] Installing spleeter via pip..." -ForegroundColor Yellow
Write-Host "  (Using pip because conda spleeter only supports Python 3.6-3.7)" -ForegroundColor Gray
& $condaExe run -n spleeter38 pip install spleeter
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to pip install spleeter." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  Spleeter installed successfully via pip." -ForegroundColor Green

# Step 4: Check audio file
Write-Host ""
Write-Host "[4/5] Checking for party_animal.mp3..." -ForegroundColor Yellow
if (-not (Test-Path "party_animal.mp3")) {
    Write-Host "  ERROR: party_animal.mp3 not found in current directory." -ForegroundColor Red
    Write-Host "  Current directory: $PWD" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  Found party_animal.mp3" -ForegroundColor Green

# Step 4.5: Fix python.exe if missing
Write-Host ""
Write-Host "[4.5/5] Checking Python executable..." -ForegroundColor Yellow
$envPath = Split-Path $condaExe -Parent
$envPath = Join-Path (Split-Path $envPath -Parent) "envs\spleeter38"
$pythonExe = Join-Path $envPath "python.exe"
$pythonwExe = Join-Path $envPath "pythonw.exe"

if (-not (Test-Path $pythonExe)) {
    if (Test-Path $pythonwExe) {
        Write-Host "  python.exe missing, creating copy from pythonw.exe..." -ForegroundColor Yellow
        Copy-Item $pythonwExe $pythonExe
        Write-Host "  python.exe created successfully." -ForegroundColor Green
    } else {
        Write-Host "  ERROR: Neither python.exe nor pythonw.exe found in environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "  python.exe found." -ForegroundColor Green
}

# Step 5: Run separation
Write-Host ""
Write-Host "[5/5] Running Spleeter separation (4 stems)..." -ForegroundColor Yellow
Write-Host "  This will create: separated/party_animal/drums.wav (+ vocals, bass, other)" -ForegroundColor Gray
& $pythonExe -m spleeter separate -p spleeter:4stems -o separated "party_animal.mp3"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Spleeter separation failed." -ForegroundColor Red
    Write-Host "  Try running manually:" -ForegroundColor Yellow
    Write-Host "    & `"$pythonExe`" -m spleeter separate -p spleeter:4stems -o separated `"party_animal.mp3`"" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 1
}

# Display results
Write-Host ""
Write-Host "=== SUCCESS ===" -ForegroundColor Green
Write-Host "Separation complete! Output files:" -ForegroundColor Green
if (Test-Path "separated\party_animal") {
    Get-ChildItem "separated\party_animal" -File | ForEach-Object {
        $sizeKB = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  - $($_.Name) ($sizeKB KB)" -ForegroundColor Cyan
    }
} else {
    Write-Host "  (Check 'separated' folder for output)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
