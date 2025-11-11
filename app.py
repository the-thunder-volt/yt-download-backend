from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import traceback
import os
import shutil
import uuid
import tempfile
from pathlib import Path

app = Flask(__name__)
CORS(app)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_downloads")
os.makedirs(TEMP_DIR, exist_ok=True)


@app.route("/")
def home():
    return jsonify({"message": "✅ Backend running"}), 200


def build_ydl_opts(output_template, cookiefile_path=None):
    opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        # make requests look like a modern browser
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/",
        },
        # Optional helpful options
        "geo_bypass": True,
        "ratelimit": None,  # set a string like "1M" to limit speed if needed
        "sleep_interval_requests": 1.0,  # small delay between requests
        "sleep_interval": 1.0,
    }
    if cookiefile_path:
        opts["cookiefile"] = cookiefile_path
    return opts


@app.route("/download", methods=["POST", "OPTIONS"])
def download_video():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS OK"}), 200

    session_id = None
    cookie_temp_path = None
    try:
        # Support multipart form: url + optional cookies file
        url = None
        if request.content_type and "multipart/form-data" in request.content_type:
            # form-data: url field + optional 'cookies' file
            url = request.form.get("url")
            cookies_file = request.files.get("cookies")
            if cookies_file:
                # save to a temp file, pass path to yt-dlp
                fd, cookie_temp_path = tempfile.mkstemp(suffix=".txt")
                os.close(fd)
                cookies_file.save(cookie_temp_path)
        else:
            # JSON body: {"url":"..."}
            data = request.get_json(silent=True) or {}
            url = data.get("url")
            # you can optionally support a cookie token in JSON too (not recommended)

        if not url:
            return jsonify({"error": "No URL provided"}), 400

        url = url.strip()
        print(f"🎥 Download requested: {url}")

        # create unique temp session folder
        session_id = str(uuid.uuid4())[:8]
        session_path = os.path.join(TEMP_DIR, session_id)
        os.makedirs(session_path, exist_ok=True)
        output_template = os.path.join(session_path, "video.%(ext)s")

        ydl_opts = build_ydl_opts(output_template, cookiefile_path=cookie_temp_path)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "video")
                # yt-dlp will create a final mp4 (merged) in session folder
                # try to find it:
                final_mp4 = None
                for candidate in [f for f in os.listdir(session_path) if f.lower().endswith(".mp4")]:
                    final_mp4 = os.path.join(session_path, candidate)
                    break
                if not final_mp4:
                    # fallback to constructed filename
                    candidate = ydl.prepare_filename(info)
                    candidate_mp4 = os.path.splitext(candidate)[0] + ".mp4"
                    if os.path.exists(candidate_mp4):
                        final_mp4 = candidate_mp4
        except yt_dlp.utils.DownloadError as de:
            msg = str(de)
            # Detect the exact "sign in to confirm you're not a bot" message
            if "Sign in to confirm" in msg or "use --cookies" in msg or "cookies" in msg.lower():
                # tell frontend to ask user for their own cookies (not developer cookies)
                return (
                    jsonify({
                        "error": "youtube_requires_cookies",
                        "message": "YouTube requires login/cookies for this video. Upload your cookies.txt in the request or use a browser to access it."
                    }),
                    403,
                )
            # other download errors
            return jsonify({"error": "download_error", "message": msg}), 500

        if not final_mp4 or not os.path.exists(final_mp4):
            return jsonify({"error": "file_not_found", "message": "Merged mp4 not found"}), 500

        # send file and ensure cleanup
        response = send_file(final_mp4, as_attachment=True, download_name=os.path.basename(final_mp4), mimetype="video/mp4")
        return response

    except Exception as e:
        print("Exception in download:", traceback.format_exc())
        return jsonify({"error": "internal", "message": str(e)}), 500

    finally:
        # cleanup cookie temp file if used
        try:
            if cookie_temp_path and os.path.exists(cookie_temp_path):
                os.remove(cookie_temp_path)
        except Exception:
            pass
        # cleanup session folder (delay not necessary; send_file will stream before returning)
        try:
            if session_id:
                session_path = os.path.join(TEMP_DIR, session_id)
                if os.path.exists(session_path):
                    shutil.rmtree(session_path)
        except Exception:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
