from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import traceback
from pathlib import Path
import os
import time

app = Flask(__name__)
CORS(app)

# Temporary download directory
TEMP_DIR = Path(__file__).parent / "temp_downloads"
TEMP_DIR.mkdir(exist_ok=True)

@app.route("/")
def home():
    return jsonify({"message": "✅ Backend running successfully"}), 200


@app.route("/download", methods=["POST", "OPTIONS"])
def download_video():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS OK"}), 200

    try:
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "❌ No URL provided"}), 400

        video_url = data["url"].strip()
        print(f"🎥 Downloading from: {video_url}")

        # output template (temporary file)
        output_template = str(TEMP_DIR / "%(title)s.%(ext)s")

        # yt-dlp options: best video + MP3 audio + merged MP4 output
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "quiet": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                },
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = ydl.prepare_filename(info)

        # Ensure final mp4 filename
        final_path = Path(downloaded_file).with_suffix(".mp4")
        if not final_path.exists():
            for ext in [".webm", ".mkv", ".m4a"]:
                alt = Path(downloaded_file).with_suffix(ext)
                if alt.exists():
                    alt.rename(final_path)
                    break

        print(f"✅ Sending file: {final_path.name}")

        # Send file to frontend for direct download
        response = send_file(
            str(final_path),
            as_attachment=True,
            download_name=final_path.name,
            mimetype="video/mp4"
        )

        # Schedule deletion after short delay (safe cleanup)
        def remove_file(path):
            time.sleep(3)  # give time to finish sending
            try:
                os.remove(path)
                print(f"🗑️ Deleted temp file: {path}")
            except Exception as e:
                print(f"⚠️ Could not delete {path}: {e}")

        import threading
        threading.Thread(target=remove_file, args=(final_path,)).start()

        return response

    except Exception as e:
        print("❌ Error in /download route:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
