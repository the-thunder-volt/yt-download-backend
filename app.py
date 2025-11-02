from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"])  # allow frontend access

@app.route("/")
def home():
    return jsonify({"message": "Backend running fine"}), 200

@app.route("/download", methods=["POST", "OPTIONS"])
def download_video():
    if request.method == "OPTIONS":
        # Handle preflight CORS request
        return jsonify({"message": "CORS preflight OK"}), 200

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "No URL provided"}), 400

    video_url = data["url"]
    try:
    ydl_opts = {"quiet": False, "no_warnings": False, "format": "best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return jsonify({
            "title": info.get("title"),
            "url": info.get("url"),
        }), 200
except Exception as e:
    import traceback
    print("❌ ERROR in /download:", traceback.format_exc())
    return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
