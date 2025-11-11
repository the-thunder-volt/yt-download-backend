from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import traceback
import os
import shutil
import uuid
import subprocess

app = Flask(__name__)
CORS(app)

# Temporary download folder
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_downloads")
os.makedirs(TEMP_DIR, exist_ok=True)


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
        print(f"🎥 Downloading: {video_url}")

        # Create a unique temp folder for each request
        session_id = str(uuid.uuid4())[:8]
        session_path = os.path.join(TEMP_DIR, session_id)
        os.makedirs(session_path, exist_ok=True)

        output_template = os.path.join(session_path, "video.%(ext)s")

        # yt-dlp options
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        # Download video + audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get("title", "video")
            final_path = os.path.join(session_path, f"{title}.mp4")

        # Sometimes yt-dlp outputs generic filenames like "video.mp4"
        if not os.path.exists(final_path):
            generic_path = os.path.join(session_path, "video.mp4")
            if os.path.exists(generic_path):
                os.rename(generic_path, final_path)

        print(f"✅ Merged & ready: {final_path}")

        # Send the file to the frontend
        return send_file(
            final_path,
            as_attachment=True,
            download_name=f"{title}.mp4",
            mimetype="video/mp4",
        )

    except Exception as e:
        print("❌ Error in /download route:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup: delete the temp folder for this session
        try:
            if os.path.exists(session_path):
                shutil.rmtree(session_path)
        except Exception as cleanup_err:
            print(f"⚠️ Cleanup failed: {cleanup_err}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
