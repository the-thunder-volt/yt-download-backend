from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import traceback

app = Flask(__name__)
CORS(app)  # allow all frontend origins

@app.route("/")
def home():
    return jsonify({"message": "✅ Backend running successfully"}), 200


@app.route("/download", methods=["POST", "OPTIONS"])
def download_video():
    # Handle browser preflight (CORS check)
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS OK"}), 200

    try:
        # Get the JSON body
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "❌ No URL provided"}), 400

        video_url = data["url"].strip()
        print(f"🎥 Extracting info from: {video_url}")

        # yt-dlp options
        ydl_opts = {
            "quiet": False,
            "no_warnings": False,
            "format": "best",
        }

        # Extract video metadata (not download)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        video_title = info.get("title", "Unknown Title")
        stream_url = info.get("url")

        print(f"✅ Extracted: {video_title}")
        return jsonify({
            "title": video_title,
            "direct_url": stream_url
        }), 200

    except Exception as e:
        print("❌ Error in /download route:")
        print(traceback.format_exc())  # visible in Render logs
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
