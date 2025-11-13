import os
import uuid
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = BASE_DIR / 'static' / 'outputs'
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# detect if the `spleeter` CLI is available; if not, we'll run a lightweight dev fallback
HAVE_SPLEETER = shutil.which('spleeter') is not None
if not HAVE_SPLEETER:
    print('Warning: `spleeter` not found on PATH — server will run in DEV fallback mode (no real separation).')

# detect yt-dlp binary and ffmpeg on PATH; if yt-dlp binary is missing we will try using
# `python -m yt_dlp` as a fallback (so installing the module into the venv is sufficient).
HAVE_YTDLP_BIN = shutil.which('yt-dlp') is not None or shutil.which('yt-dlp.exe') is not None
if not HAVE_YTDLP_BIN:
    print('Notice: yt-dlp binary not found on PATH — will try `python -m yt_dlp` fallback if the module is installed.')

HAVE_FFMPEG = shutil.which('ffmpeg') is not None or shutil.which('ffmpeg.exe') is not None
if not HAVE_FFMPEG:
    print('Warning: ffmpeg not found on PATH — audio conversion/separation may fail. Please install ffmpeg and add to PATH.')


def run_cmd(cmd, cwd=None):
    print('RUN:', ' '.join(cmd))
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return res.returncode, res.stdout


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/separate', methods=['POST'])
def separate():
    # support JSON or multipart/form-data (for cookie file upload)
    data = {}
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
    else:
        data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'ok': False, 'error': 'missing url'}), 400

    job_id = uuid.uuid4().hex[:8]
    job_dir = OUTPUT_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # remember cookie file path so we can securely remove it after processing
    cookies_file = None

    try:
        # 1) download audio from youtube to wav using yt-dlp
        # output path: job_dir / audio.wav
        out_template = str(job_dir / 'audio.%(ext)s')
        # support optional cookies passed from the client:
        # - JSON/form field `cookies_from_browser`: string like 'chrome' or 'firefox'
        # - multipart file field `cookies`: an uploaded cookies.txt
        cookies_from_browser = data.get('cookies_from_browser')
        if request.files and 'cookies' in request.files:
            f = request.files['cookies']
            if f and f.filename:
                saved = job_dir / 'cookies.txt'
                f.save(str(saved))
                cookies_file = str(saved)

        # prefer system yt-dlp binary; if missing, run module via the current python
        # If ffmpeg is available we can ask yt-dlp to extract to WAV (-x). If not, download the
        # best audio format (so we still get an audio file) and continue with a dev fallback.
        if HAVE_YTDLP_BIN:
            if HAVE_FFMPEG:
                cmd = ['yt-dlp', '-x', '--audio-format', 'wav', '-o', out_template, url]
            else:
                cmd = ['yt-dlp', '-f', 'bestaudio', '-o', out_template, url]
        else:
            if HAVE_FFMPEG:
                cmd = [sys.executable, '-m', 'yt_dlp', '-x', '--audio-format', 'wav', '-o', out_template, url]
            else:
                cmd = [sys.executable, '-m', 'yt_dlp', '-f', 'bestaudio', '-o', out_template, url]

        # append cookie args if provided
        if cookies_from_browser:
            # yt-dlp expects: --cookies-from-browser BROWSER
            cmd.extend(['--cookies-from-browser', cookies_from_browser])
        if cookies_file:
            cmd.extend(['--cookies', cookies_file])

        code, out = run_cmd(cmd)
        # persist yt-dlp output for debugging
        try:
            (job_dir / 'yt-dlp.log').write_text(out, encoding='utf-8')
        except Exception:
            pass
        if code != 0:
            return jsonify({'ok': False, 'error': 'yt-dlp failed', 'log': out}), 500

        # locate any downloaded audio file (wav, m4a, webm, mp3, opus)
        audio_candidates = []
        for ext in ('wav','m4a','webm','mp3','opus','aac'):
            audio_candidates.extend(list(job_dir.glob(f'*.{ext}')))
        if not audio_candidates:
            return jsonify({'ok': False, 'error': 'no audio downloaded', 'log': out}), 500
        # prefer wav if present
        wav_files = [p for p in audio_candidates if p.suffix.lower()=='.wav']
        if wav_files:
            wav_path = wav_files[0]
        else:
            wav_path = audio_candidates[0]

        result = {}

        if HAVE_SPLEETER:
            # 2) run spleeter (4stems) to separate drums
            # requires `spleeter` installed and ffmpeg available
            cmd = ['spleeter', 'separate', '-p', 'spleeter:4stems', '-o', str(job_dir), str(wav_path)]
            code, out = run_cmd(cmd)
            # persist spleeter output
            try:
                (job_dir / 'spleeter.log').write_text(out, encoding='utf-8')
            except Exception:
                pass
            if code != 0:
                return jsonify({'ok': False, 'error': 'spleeter failed', 'log': out}), 500

            # 3) locate generated stems
            # spleeter creates a folder named after the audio file stem inside job_dir
            audio_basename = wav_path.stem
            stems_dir = job_dir / audio_basename
            if not stems_dir.exists():
                # fallback: find any folder with stems
                folders = [p for p in job_dir.iterdir() if p.is_dir()]
                stems_dir = folders[0] if folders else None
            if not stems_dir:
                return jsonify({'ok': False, 'error': 'no stems folder found', 'log': out}), 500

            # expected files: drums.wav, bass.wav, other.wav, vocals.wav
            for stem in ['accompaniment.wav', 'drums.wav', 'bass.wav', 'other.wav', 'vocals.wav']:
                p = stems_dir / stem
                if p.exists():
                    # move or copy to job_dir root so it's easy to serve
                    dest = job_dir / stem
                    shutil.copy(p, dest)
                    result[stem.replace('.wav','')] = f'/static/outputs/{job_id}/{dest.name}'

            # always include original
            shutil.copy(wav_path, job_dir / 'original.wav')
            result['original'] = f'/static/outputs/{job_id}/original.wav'

            return jsonify({'ok': True, 'job_id': job_id, 'stems': result})
        else:
            # DEV fallback: spleeter not available — return original as a placeholder "drums"
            shutil.copy(wav_path, job_dir / 'original.wav')
            # create a 'drums.wav' placeholder by copying original
            shutil.copy(wav_path, job_dir / 'drums.wav')
            result['original'] = f'/static/outputs/{job_id}/original.wav'
            result['drums'] = f'/static/outputs/{job_id}/drums.wav'
            return jsonify({'ok': True, 'job_id': job_id, 'stems': result, 'note': 'spleeter not installed — returned original as drums (dev fallback).'})

    except Exception as e:
        # write traceback for inspection
        try:
            (job_dir / 'error.txt').write_text(traceback.format_exc(), encoding='utf-8')
        except Exception:
            pass
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        # remove uploaded cookies file if present to avoid lingering credentials on disk
        try:
            if cookies_file:
                p = Path(cookies_file)
                if p.exists():
                    p.unlink()
        except Exception:
            # don't block or surface deletion errors to the client
            pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
