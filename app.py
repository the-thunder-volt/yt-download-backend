from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os, shutil, uuid, subprocess, traceback, time

app = Flask(__name__)
CORS(app)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_downloads")
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route("/")
def home():
    return jsonify({"message": "Backend running ✅"})

# --------------------------
# Get video title
# --------------------------
@app.route("/get_title", methods=["POST"])
def get_title():
    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        ydl_opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title", "video")

        return jsonify({"title": title})
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# --------------------------
# Download + Merge
# --------------------------
@app.route("/download", methods=["POST"])
def download_video():
    session_id = str(uuid.uuid4())[:8]
    workdir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(workdir, exist_ok=True)

    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        # Extract title
        ydl_opts_info = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title", "video")

        # ----------------------------
        # 1️⃣ Download video-only
        # ----------------------------
        raw_video_path = os.path.join(workdir, "raw_video.%(ext)s")
        ydl_video_opts = {
            "format": "bestvideo",
            "outtmpl": raw_video_path,
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_video_opts) as ydl:
            ydl.download([url])

        # Locate downloaded video file
        video_file = next(
            (os.path.join(workdir, f) for f in os.listdir(workdir)
             if f.startswith("raw_video") and f.endswith((".mp4", ".mkv", ".webm"))),
            None
        )
        if not video_file:
            return jsonify({"error": "Video download failed"}), 500

        # Remove audio track
        clean_video = os.path.join(workdir, "video.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_file,
            "-c:v", "copy",
            "-an",
            clean_video
        ], check=True)

        # ----------------------------
        # 2️⃣ Download audio-only + convert to MP3
        # ----------------------------
        ydl_audio_opts = {
            "format": "bestaudio",
            "outtmpl": os.path.join(workdir, "audio.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }],
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_audio_opts) as ydl:
            ydl.download([url])

        audio_file = next(
            (os.path.join(workdir, f) for f in os.listdir(workdir)
             if f.endswith(".mp3")), None
        )
        if not audio_file:
            return jsonify({"error": "Audio download failed"}), 500

        # ----------------------------
        # 3️⃣ Merge MP3 + Video
        # ----------------------------
        final_file = os.path.join(workdir, f"{title}.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", clean_video,
            "-i", audio_file,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            final_file
        ], check=True)

        return send_file(final_file, as_attachment=True, download_name=f"{title}.mp4")

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    finally:
        time.sleep(0.2)
        try:
            shutil.rmtree(workdir)
        except:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
