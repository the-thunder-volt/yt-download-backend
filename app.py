from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # allow all origins (frontend)

@app.route("/")
def home():
    return jsonify({"message": "✅ Backend running successfully"}), 200


@app.route("/download", methods=["POST", "OPTIONS"])
def download_video():
    # Handle preflight CORS request
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS OK"}), 200

    try:
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "❌ No URL provided"}), 400

        video_url = data["url"]
        print(f"🎥 Processing URL: {video_url}")

        # Extract video info (not download)
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "best",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get("title", "Unknown Title")
            video_url = info.get("url")

            return jsonify({
                "title": video_title,
                "direct_url": video_url
            }), 200

    except Exception as e:
        import traceback
        print("❌ Error:", traceback.format_exc())  # will show up in Render logs
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
