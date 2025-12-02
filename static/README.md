# Static Files 靜態檔案資料夾

這個資料夾用於存放網頁端需要的靜態檔案，例如音效檔案。

## 音效檔案

請將 `big_drum.wav` 複製到這個資料夾中，網頁會透過 Web Audio API 載入並播放。

```bash
# 在樹莓派上執行
cp big_drum.wav static/
```

或者如果音效檔案在其他位置：

```bash
cp /path/to/big_drum.wav static/
```

## 檔案列表

應該包含的檔案：
- `big_drum.wav` - 鼓擊音效（必須）

## 注意事項

1. 音效檔案建議使用標準 WAV 格式（PCM, 44100Hz）
2. 檔案大小建議不超過 1MB，避免載入時間過長
3. 瀏覽器的 Web Audio API 支援多種格式：WAV, MP3, OGG 等
